import smtplib
from email import policy
from email.parser import BytesParser

import httpx
from langchain_core.messages import AIMessage
from mailer_app.adapters.repository import SqliteDeliveryRepository
from mailer_app.adapters.smtp import SmtpTransport
from mailer_app.main import create_app as create_mailer
from mailer_app.service import DeliveryService
from router_app.adapters.agent import LangChainRoutingAgent
from router_app.adapters.mailer import HttpDeliveryGateway
from router_app.main import create_app as create_router
from router_app.service import RoutingService


async def test_http_request_tool_call_http_mailer_and_mime_contract(tmp_path, monkeypatch):
    """Real app/service/adapter chain, controlled inference and SMTP boundaries."""
    captured = []

    class SMTP:
        def __init__(self, *args, **kwargs):
            pass

        def send_message(self, message, **kwargs):
            captured.append(message.as_bytes(policy=policy.SMTP))
            return {}

        def close(self):
            pass

    class Model:
        def bind_tools(self, tools):
            assert tools[0].name == "send_department_email"
            return self

        async def ainvoke(self, messages):
            return AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "send_department_email",
                        "args": {"recipient": "it@example.com"},
                        "id": "call_it",
                        "type": "tool_call",
                    }
                ],
            )

    monkeypatch.setattr(smtplib, "SMTP", SMTP)
    mailer = create_mailer(
        DeliveryService(
            SqliteDeliveryRepository(str(tmp_path / "private.sqlite3")),
            SmtpTransport("mailpit", 1025, "router@example.com", 15),
            frozenset({"it@example.com"}),
        ),
        token="integration-token",
    )
    async with mailer.router.lifespan_context(mailer):
        async with httpx.AsyncClient(
            base_url="http://mailer/",
            transport=httpx.ASGITransport(app=mailer),
            headers={"Authorization": "Bearer integration-token"},
        ) as delivery_client:
            router = create_router(
                RoutingService(
                    LangChainRoutingAgent(Model(), delivery_client, "unused-health"),
                    HttpDeliveryGateway(delivery_client),
                )
            )
            async with router.router.lifespan_context(router):
                async with httpx.AsyncClient(
                    base_url="http://router/", transport=httpx.ASGITransport(app=router)
                ) as client:
                    response = await client.post(
                        "/api/v1/messages",
                        json={
                            "email": "jan.nowak@example.com",
                            "message": "Serwer nie działa.\nPilna awaria.",
                        },
                    )
            assert response.status_code == 200
            receipt = response.json()
            saved = await delivery_client.get(f"/internal/v1/deliveries/{receipt['request_id']}")
            assert saved.json() == receipt
    assert len(captured) == 1
    mime = BytesParser(policy=policy.default).parsebytes(captured[0])
    assert str(mime["Reply-To"]) == "jan.nowak@example.com"
    assert str(mime["To"]) == "it@example.com"
    assert str(mime["Message-ID"]) == receipt["message_id"]
    assert str(mime["X-Request-ID"]) == receipt["request_id"]
    assert mime.get_content().replace("\r\n", "\n") == "Serwer nie działa.\nPilna awaria.\n"
