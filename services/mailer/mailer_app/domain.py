from dataclasses import dataclass


@dataclass(frozen=True)
class SendCommand:
    request_id: str
    recipient: str
    reply_to: str
    message: str


@dataclass(frozen=True)
class Receipt:
    request_id: str
    recipient: str
    status: str
    message_id: str


class DeliveryError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


class DefinitelyRejected(Exception):
    """Transport positively knows this submission was not accepted."""


class SubmissionUnknown(Exception):
    """Transport cannot determine whether the server accepted the submission."""
