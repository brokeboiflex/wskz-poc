import logging
from dataclasses import asdict
from typing import Annotated

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from .domain import Message, RoutingError
from .service import RoutingService

logger = logging.getLogger("router")


class MessageBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr
    message: str = Field(min_length=1, max_length=4000)

    @field_validator("message")
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("message must contain text")
        return value  # Preserve original whitespace and content in the email.


class RoutedResponse(BaseModel):
    request_id: str
    recipient: str
    status: str
    message_id: str


def service_for(request: Request) -> RoutingService:
    return request.app.state.service


def install_routes(app: FastAPI) -> None:
    @app.exception_handler(RoutingError)
    async def routing_error(_request: Request, exc: RoutingError):
        logger.warning("routing_failed request_id=%s code=%s", exc.request_id, exc.code)
        return JSONResponse(
            status_code=502,
            content={"code": exc.code, "request_id": exc.request_id},
        )

    @app.get("/health/live", include_in_schema=False)
    async def live():
        return {"status": "alive"}

    @app.get("/health/ready", include_in_schema=False)
    async def ready(service: Annotated[RoutingService, Depends(service_for)]):
        healthy = await service.ready()
        return JSONResponse(
            {"status": "ready" if healthy else "unavailable"}, status_code=200 if healthy else 503
        )

    @app.post(
        "/api/v1/messages",
        response_model=RoutedResponse,
        responses={
            502: {
                "description": "Model/tool/delivery failure; inspect code and request_id. Do not blindly retry."
            }
        },
    )
    async def route_message(
        body: MessageBody, service: Annotated[RoutingService, Depends(service_for)]
    ):
        receipt = await service.route(Message(email=str(body.email), message=body.message))
        logger.info(
            "message_submitted request_id=%s recipient=%s", receipt.request_id, receipt.recipient
        )
        return asdict(receipt)
