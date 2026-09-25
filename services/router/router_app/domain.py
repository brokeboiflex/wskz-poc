"""Application values and failures, independent of HTTP and model libraries."""

from dataclasses import dataclass
from enum import StrEnum


class Department(StrEnum):
    HR = "human-resources@example.com"
    HELP_DESK = "help-desk@example.com"
    IT = "it@example.com"
    PAYROLL = "kadry@example.com"
    OTHER = "other@example.com"


@dataclass(frozen=True)
class Message:
    email: str
    message: str


@dataclass(frozen=True)
class Delivery:
    request_id: str
    recipient: str
    status: str
    message_id: str


class RoutingError(Exception):
    def __init__(self, code: str, request_id: str = ""):
        self.code = code
        self.request_id = request_id
        super().__init__(code)
