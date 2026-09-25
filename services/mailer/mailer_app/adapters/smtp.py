import smtplib
from email.message import EmailMessage
from email.utils import formatdate

from ..domain import DefinitelyRejected, SendCommand, SubmissionUnknown


class SmtpTransport:
    """SMTP submission to the isolated test sink; no automatic retries."""

    def __init__(self, host: str, port: int, sender: str, timeout: float):
        self.host, self.port, self.sender, self.timeout = host, port, sender, timeout

    def send(self, command: SendCommand, message_id: str) -> None:
        message = EmailMessage()
        message["From"] = self.sender
        message["To"] = command.recipient
        message["Reply-To"] = command.reply_to
        message["Subject"] = f"Zgłoszenie {command.request_id}"
        message["Date"] = formatdate(localtime=False)
        message["Message-ID"] = message_id
        message["X-Request-ID"] = command.request_id
        message.set_content(command.message)
        try:
            smtp = smtplib.SMTP(self.host, self.port, timeout=self.timeout)
        except (OSError, smtplib.SMTPException) as exc:
            raise DefinitelyRejected() from exc
        try:
            refused = smtp.send_message(
                message, from_addr=self.sender, to_addrs=[command.recipient]
            )
            if refused:
                raise DefinitelyRejected()
        except (
            smtplib.SMTPRecipientsRefused,
            smtplib.SMTPSenderRefused,
            smtplib.SMTPDataError,
            smtplib.SMTPNotSupportedError,
        ) as exc:
            raise DefinitelyRejected() from exc
        except (OSError, smtplib.SMTPException) as exc:
            raise SubmissionUnknown() from exc
        finally:
            # QUIT failures must not overwrite successful DATA acceptance.
            smtp.close()

    def ready(self) -> bool:
        try:
            smtp = smtplib.SMTP(self.host, self.port, timeout=min(self.timeout, 3))
            try:
                return smtp.noop()[0] == 250
            finally:
                smtp.close()
        except (OSError, smtplib.SMTPException):
            return False
