from typing import Protocol

from .domain import Delivery, Department, Message


class DeliveryGateway(Protocol):
    async def send(self, request_id: str, recipient: Department, message: Message) -> Delivery: ...

    async def ready(self) -> bool: ...


class RoutingAgent(Protocol):
    async def run(
        self, request_id: str, message: Message, delivery: DeliveryGateway
    ) -> Delivery: ...

    async def ready(self) -> bool: ...
