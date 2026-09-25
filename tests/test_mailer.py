import smtplib
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from email import policy
from email.parser import BytesParser
from threading import Event
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from mailer_app.adapters.repository import SqliteDeliveryRepository
from mailer_app.adapters.smtp import SmtpTransport
from mailer_app.domain import DefinitelyRejected, DeliveryError, SendCommand, SubmissionUnknown
from mailer_app.main import create_app
from mailer_app.service import DeliveryService


class Transport:
    def __init__(self, failure=None):
        self.calls = []
        self.failure = failure

    def send(self, command, message_id):
        self.calls.append((command, message_id))
        if self.failure:
            raise self.failure

    def ready(self):
        return True


@pytest.fixture
def command():
    return SendCommand(
        str(uuid4()), "kadry@example.com", "jan.nowak@example.com", "Proszę o urlop.\nDziękuję."
    )


@pytest.fixture
def repository(tmp_path):
    return SqliteDeliveryRepository(str(tmp_path / "ledger.sqlite3"))


def service(repository, transport):
    return DeliveryService(repository, transport, frozenset({"kadry@example.com"}))


def test_duplicate_delivery_is_submitted_once(repository, command):
    transport = Transport()
    application = service(repository, transport)
    first = application.send(command)
    second = application.send(command)
    assert first == second
    assert first.status == "submitted"
    assert len(transport.calls) == 1


def test_reusing_key_with_other_payload_fails(repository, command):
    application = service(repository, Transport())
    application.send(command)
    with pytest.raises(DeliveryError, match="idempotency_conflict"):
        application.send(replace(command, message="another message"))


@pytest.mark.parametrize(
    "error,status,code",
    [
        (DefinitelyRejected(), "failed", "delivery_failed"),
        (SubmissionUnknown(), "unknown", "delivery_unknown"),
        (RuntimeError(), "unknown", "delivery_unknown"),
    ],
)
def test_failures_persist_and_are_never_resent(repository, command, error, status, code):
    transport = Transport(error)
    application = service(repository, transport)
    for _ in range(2):
        with pytest.raises(DeliveryError, match=code):
            application.send(command)
    assert repository.get(command.request_id).status == status
    assert len(transport.calls) == 1


def test_crash_recovery_never_resubmits_unacknowledged_attempt(repository, command):
    repository.reserve(command)
    reopened = SqliteDeliveryRepository(repository.path)
    assert reopened.get(command.request_id).status == "unknown"
    transport = Transport()
    with pytest.raises(DeliveryError, match="delivery_unknown"):
        service(reopened, transport).send(command)
    assert not transport.calls


def test_concurrent_duplicate_cannot_race_the_transport(repository, command):
    entered, release = Event(), Event()

    class BlockingTransport(Transport):
        def send(self, command, message_id):
            super().send(command, message_id)
            entered.set()
            assert release.wait(5)

    transport = BlockingTransport()
    application = service(repository, transport)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(application.send, command)
        assert entered.wait(5)
        try:
            with pytest.raises(DeliveryError, match="delivery_in_progress"):
                application.send(command)
        finally:
            release.set()
        assert first.result().status == "submitted"
    assert len(transport.calls) == 1


def test_disallowed_recipient_never_reaches_transport(repository, command):
    transport = Transport()
    with pytest.raises(DeliveryError, match="recipient_not_allowed"):
        service(repository, transport).send(replace(command, recipient="evil@example.com"))
    assert not transport.calls
    assert repository.get(command.request_id) is None


def test_smtp_builds_real_mime_reply_to_and_original_body(monkeypatch, command):
    captured = {}

    class SMTP:
        def __init__(self, host, port, timeout):
            captured["connection"] = (host, port, timeout)

        def send_message(self, message, from_addr, to_addrs):
            captured["raw"] = message.as_bytes(policy=policy.SMTP)
            captured["envelope"] = (from_addr, to_addrs)
            return {}

        def close(self):
            captured["closed"] = True

    monkeypatch.setattr(smtplib, "SMTP", SMTP)
    SmtpTransport("mailpit", 1025, "router@example.com", 15).send(command, "<id@test>")
    parsed = BytesParser(policy=policy.default).parsebytes(captured["raw"])
    assert str(parsed["Reply-To"]) == command.reply_to
    assert str(parsed["To"]) == command.recipient
    assert str(parsed["From"]) == "router@example.com"
    assert parsed["Message-ID"] == "<id@test>"
    assert parsed["X-Request-ID"] == command.request_id
    assert parsed.get_content().replace("\r\n", "\n").removesuffix("\n") == command.message
    assert captured["envelope"] == ("router@example.com", [command.recipient])
    assert captured["closed"]


@pytest.mark.parametrize(
    "error,expected",
    [
        (smtplib.SMTPDataError(550, b"rejected"), DefinitelyRejected),
        (smtplib.SMTPServerDisconnected("lost after DATA"), SubmissionUnknown),
        (TimeoutError(), SubmissionUnknown),
    ],
)
def test_smtp_classifies_negative_ack_vs_lost_ack(monkeypatch, command, error, expected):
    class SMTP:
        def __init__(self, *args, **kwargs):
            pass

        def send_message(self, *args, **kwargs):
            raise error

        def close(self):
            pass

    monkeypatch.setattr(smtplib, "SMTP", SMTP)
    with pytest.raises(expected):
        SmtpTransport("mailpit", 1025, "router@example.com", 15).send(command, "<id@test>")


def test_internal_auth_validation_and_status(repository, command):
    transport = Transport()
    from dataclasses import asdict

    with TestClient(create_app(service(repository, transport), token="test-token")) as client:
        assert client.post("/internal/v1/deliveries", json=asdict(command)).status_code == 401
        headers = {"Authorization": "Bearer test-token"}
        assert (
            client.post(
                "/internal/v1/deliveries", headers=headers, json=asdict(command)
            ).status_code
            == 200
        )
        assert (
            client.get(f"/internal/v1/deliveries/{command.request_id}", headers=headers).json()[
                "status"
            ]
            == "submitted"
        )
        assert (
            client.post(
                "/internal/v1/deliveries",
                headers=headers,
                json={**asdict(command), "reply_to": "jan@example.com\r\nBcc: evil@example.com"},
            ).status_code
            == 422
        )
    assert len(transport.calls) == 1


def test_failed_reservation_returns_typed_error_and_never_sends(repository, command, monkeypatch):
    def broken(_command):
        raise OSError("disk unavailable")

    monkeypatch.setattr(repository, "reserve", broken)
    transport = Transport()
    with pytest.raises(DeliveryError, match="mailer_unavailable"):
        service(repository, transport).send(command)
    assert not transport.calls


@pytest.mark.parametrize("transport_error", [None, DefinitelyRejected(), SubmissionUnknown()])
def test_failed_persistence_after_transport_returns_unknown(
    repository, command, monkeypatch, transport_error
):
    def broken(request_id, status):
        raise OSError("disk unavailable")

    monkeypatch.setattr(repository, "finish", broken)
    transport = Transport(transport_error)
    with pytest.raises(DeliveryError, match="delivery_unknown"):
        service(repository, transport).send(command)
    assert len(transport.calls) == 1
    assert repository.get(command.request_id).status == "sending"
