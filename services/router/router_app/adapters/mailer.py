import httpx
from pydantic import BaseModel, ConfigDict, ValidationError

from ..domain import Delivery, Department, Message, RoutingError


class Receipt(BaseModel):
    model_config = ConfigDict(extra="ignore")
    request_id: str
    recipient: str
    status: str
    message_id: str


class HttpDeliveryGateway:
    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    async def ready(self) -> bool:
        try:
            return (await self.client.get("health/ready", timeout=5)).status_code == 200
        except httpx.HTTPError:
            return False

    async def send(self, request_id: str, recipient: Department, message: Message) -> Delivery:
        try:
            response = await self.client.post(
                "internal/v1/deliveries",
                json={
                    "request_id": request_id,
                    "recipient": recipient.value,
                    "reply_to": message.email,
                    "message": message.message,
                },
            )
        except httpx.ConnectError as exc:
            raise RoutingError("mailer_unavailable") from exc
        except httpx.HTTPError as exc:
            # A lost response is not proof that the mailer did not submit the email.
            raise RoutingError("delivery_unknown") from exc
        if response.status_code != 200:
            try:
                code = response.json()["code"]
            except (ValueError, KeyError, TypeError):
                code = "delivery_unknown"
            allowed = {
                "delivery_failed",
                "delivery_unknown",
                "delivery_in_progress",
                "idempotency_conflict",
                "mailer_unavailable",
            }
            raise RoutingError(code if code in allowed else "delivery_unknown")
        try:
            result = Receipt.model_validate(response.json())
        except (ValueError, ValidationError) as exc:
            raise RoutingError("delivery_unknown") from exc
        if (
            result.request_id != request_id
            or result.recipient != recipient.value
            or result.status != "submitted"
            or not result.message_id
        ):
            raise RoutingError("delivery_unknown")
        return Delivery(**result.model_dump())
