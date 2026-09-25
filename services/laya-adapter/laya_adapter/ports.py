from typing import Protocol

from .domain import Choice


class DecisionEngine(Protocol):
    async def choose(self, choice: Choice) -> str: ...

    async def ready(self) -> bool: ...
