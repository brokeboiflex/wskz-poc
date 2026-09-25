from .domain import AdapterError, Choice
from .ports import DecisionEngine


class ChoiceService:
    def __init__(self, engine: DecisionEngine):
        self.engine = engine

    async def choose(self, choice: Choice) -> str:
        selected = await self.engine.choose(choice)
        if selected not in choice.options:
            raise AdapterError("invalid_engine_choice")
        return selected

    async def ready(self) -> bool:
        return await self.engine.ready()
