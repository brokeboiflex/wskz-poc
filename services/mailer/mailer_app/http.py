import hmac
import logging
from dataclasses import asdict
from typing import Annotated
from uuid import UUID

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from .domain import DeliveryError, SendCommand
from .service import DeliveryService

logger = logging.getLogger("mailer")


class DeliveryBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: UUID
    recipient: EmailStr
    reply_to: EmailStr
    message: str = Field(min_length=1, max_length=4000)

    @field_validator("message")
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("message must contain text")
        return value


class DeliveryResponse(BaseModel):
    request_id: str
    recipient: str
    status: str
    message_id: str


def get_service(request: Request) -> DeliveryService:
    return request.app.state.service


def authenticated(request: Request, authorization: Annotated[str | None, Header()] = None) -> None:
    expected = ("Bearer " + request.app.state.token).encode()
    if not hmac.compare_digest((authorization or "").encode(), expected):
        raise HTTPException(status_code=401, detail="unauthorized")


def install_routes(app: FastAPI) -> None:
    @app.exception_handler(DeliveryError)
    async def delivery_error(_request: Request, exc: DeliveryError):
        status = 409 if exc.code in {"idempotency_conflict", "delivery_in_progress"} else 502
        if exc.code == "recipient_not_allowed":
            status = 422
        return JSONResponse({"code": exc.code}, status_code=status)

    @app.get("/health/live", include_in_schema=False)
    def live():
        return {"status": "alive"}

    @app.get("/health/ready", include_in_schema=False)
    def ready(service: Annotated[DeliveryService, Depends(get_service)]):
        healthy = service.ready()
        return JSONResponse(
            {"status": "ready" if healthy else "unavailable"}, status_code=200 if healthy else 503
        )

    @app.post(
        "/internal/v1/deliveries",
        response_model=DeliveryResponse,
        dependencies=[Depends(authenticated)],
    )
    def send(body: DeliveryBody, service: Annotated[DeliveryService, Depends(get_service)]):
        command = SendCommand(
            str(body.request_id), str(body.recipient), str(body.reply_to), body.message
        )
        try:
            receipt = service.send(command)
        except DeliveryError as exc:
            logger.warning("delivery_failed request_id=%s code=%s", command.request_id, exc.code)
            raise
        logger.info("delivery_submitted request_id=%s", receipt.request_id)
        return asdict(receipt)

    @app.get(
        "/internal/v1/deliveries/{request_id}",
        response_model=DeliveryResponse,
        dependencies=[Depends(authenticated)],
    )
    def status(request_id: UUID, service: Annotated[DeliveryService, Depends(get_service)]):
        receipt = service.status(str(request_id))
        if receipt is None:
            raise HTTPException(status_code=404, detail="delivery_not_found")
        return asdict(receipt)
