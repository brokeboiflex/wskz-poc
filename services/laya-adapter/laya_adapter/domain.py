from dataclasses import dataclass


@dataclass(frozen=True)
class Choice:
    state: str
    instructions: str
    options: tuple[str, ...]
    descriptions: tuple[str, ...] = ()


class AdapterError(Exception):
    pass
