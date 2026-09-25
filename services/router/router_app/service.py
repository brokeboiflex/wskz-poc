"""Use cases depend on ports, never on frameworks or transports."""

import asyncio
from uuid import uuid4

from .domain import Delivery, Message, RoutingError
from .ports import DeliveryGateway, RoutingAgent


class RoutingService:
    def __init__(self, agent: RoutingAgent, delivery: DeliveryGateway):
        self.agent = agent
        self.delivery = delivery

    async def route(self, message: Message) -> Delivery:
        request_id = str(uuid4())
        try:
            result = await self.agent.run(request_id, message, self.delivery)
            if result.request_id != request_id or result.status != "submitted":
                raise RoutingError("delivery_unconfirmed")
            return result
        except RoutingError as exc:
            exc.request_id = request_id
            raise

    async def ready(self) -> bool:
        model, mailer = await asyncio.gather(self.agent.ready(), self.delivery.ready())
        return model and mailer
