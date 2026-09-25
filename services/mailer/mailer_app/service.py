from .domain import DefinitelyRejected, DeliveryError, Receipt, SendCommand, SubmissionUnknown
from .ports import DeliveryRepository, MailTransport


class DeliveryService:
    def __init__(
        self, repository: DeliveryRepository, transport: MailTransport, allowed: frozenset[str]
    ):
        self.repository = repository
        self.transport = transport
        self.allowed = allowed

    def send(self, command: SendCommand) -> Receipt:
        if command.recipient not in self.allowed:
            raise DeliveryError("recipient_not_allowed")
        try:
            created, receipt = self.repository.reserve(command)
        except DeliveryError:
            raise
        except Exception as exc:
            # No transport call has happened. Never turn a failed reservation into a send.
            raise DeliveryError("mailer_unavailable") from exc
        if not created:
            if receipt.status == "submitted":
                return receipt
            codes = {
                "sending": "delivery_in_progress",
                "failed": "delivery_failed",
                "unknown": "delivery_unknown",
            }
            raise DeliveryError(codes[receipt.status])
        try:
            self.transport.send(command, receipt.message_id)
        except DefinitelyRejected as exc:
            self._record_failure(command.request_id, "failed")
            raise DeliveryError("delivery_failed") from exc
        except SubmissionUnknown as exc:
            self._record_failure(command.request_id, "unknown")
            raise DeliveryError("delivery_unknown") from exc
        except Exception as exc:
            self._record_failure(command.request_id, "unknown")
            raise DeliveryError("delivery_unknown") from exc
        try:
            return self.repository.finish(command.request_id, "submitted")
        except Exception as exc:
            # SMTP accepted but durable acknowledgement failed. Never resubmit.
            raise DeliveryError("delivery_unknown") from exc

    def status(self, request_id: str) -> Receipt | None:
        try:
            return self.repository.get(request_id)
        except Exception as exc:
            raise DeliveryError("mailer_unavailable") from exc

    def _record_failure(self, request_id: str, status: str) -> None:
        try:
            self.repository.finish(request_id, status)
        except Exception as exc:
            # The durable record may remain `sending`; restart recovery makes it unknown.
            raise DeliveryError("delivery_unknown") from exc

    def ready(self) -> bool:
        return self.repository.ready() and self.transport.ready()
