from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage
from router_app.adapters.agent import DEPARTMENT_CRITERIA, LangChainRoutingAgent
from router_app.adapters.mailer import HttpDeliveryGateway
from router_app.domain import Delivery, Department, Message, RoutingError
from router_app.main import create_app
from router_app.service import RoutingService


class Model:
    def __init__(self, response):
        self.response = response
        self.tools = []
        self.messages = []

    def bind_tools(self, tools, **kwargs):
        self.tools = tools
        return self

    async def ainvoke(self, messages):
        self.messages = messages
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


class Mailer:
    def __init__(self, failure=None):
        self.commands = []
        self.failure = failure

    async def ready(self):
        return True

    async def send(self, request_id, recipient, message):
        self.commands.append((request_id, recipient, message))
        if self.failure:
            raise self.failure
        return Delivery(request_id, recipient.value, "submitted", f"<{request_id}@test>")


def call(department="payroll", **extra):
    return {
        "name": "send_department_email",
        "args": {"department": department, **extra},
        "id": "call_1",
        "type": "tool_call",
    }


@pytest.fixture
def health_client():
    async def handler(request):
        return httpx.Response(200, json={"data": [{"id": "test-model"}]})

    return httpx.AsyncClient(base_url="http://model/v1/", transport=httpx.MockTransport(handler))


async def test_native_tool_execution_preserves_original_context(health_client):
    model = Model(AIMessage(content="", tool_calls=[call()]))
    mailer = Mailer()
    service = RoutingService(LangChainRoutingAgent(model, health_client, "test-model"), mailer)
    message = Message("jan.nowak@example.com", "  Proszę o urlop.\nDziękuję.  ")
    receipt = await service.route(message)
    assert receipt.status == "submitted"
    assert mailer.commands == [(receipt.request_id, Department.PAYROLL, message)]
    assert model.tools[0].name == "send_department_email"
    schema = model.tools[0].args_schema
    assert set(schema["properties"]) == {"department"}
    assert set(schema["properties"]["department"]["enum"]) == set(DEPARTMENT_CRITERIA)
    assert "@" not in str(schema) + model.tools[0].description + str(model.messages)
    assert len(model.messages) == 2
    assert message.email not in str(model.messages)


@pytest.mark.parametrize(
    "department,recipient",
    [
        ("human_resources", Department.HR),
        ("payroll", Department.PAYROLL),
        ("help_desk", Department.HELP_DESK),
        ("it", Department.IT),
        ("other", Department.OTHER),
    ],
)
async def test_model_department_is_mapped_to_its_mailbox(health_client, department, recipient):
    model = Model(AIMessage(content="", tool_calls=[call(department)]))
    mailer = Mailer()
    service = RoutingService(LangChainRoutingAgent(model, health_client, "test-model"), mailer)
    message = Message("sender@example.com", "Treść do interpretacji przez model.")
    receipt = await service.route(message)
    assert receipt.recipient == recipient.value
    assert mailer.commands == [(receipt.request_id, recipient, message)]


@pytest.mark.parametrize(
    "response",
    [
        AIMessage(content="Email sent successfully"),
        AIMessage(content='{"recipient":"kadry@example.com"}'),
        AIMessage(content="", tool_calls=[call(), {**call(), "id": "call_2"}]),
        AIMessage(content="", tool_calls=[{**call(), "name": "unregistered_tool"}]),
        AIMessage(content="", tool_calls=[call("attacker@evil.example")]),
        AIMessage(content="", tool_calls=[call("kadry@example.com")]),
        AIMessage(content="", tool_calls=[call(recipient="it@example.com")]),
        AIMessage(content="", tool_calls=[call(reply_to="attacker@evil.example")]),
        AIMessage(
            content="",
            invalid_tool_calls=[
                {"name": "send_department_email", "args": "{", "id": "bad", "error": "invalid"}
            ],
        ),
    ],
)
async def test_no_delivery_without_one_valid_native_tool_call(health_client, response):
    mailer = Mailer()
    service = RoutingService(
        LangChainRoutingAgent(Model(response), health_client, "test-model"), mailer
    )
    with pytest.raises(RoutingError, match="invalid_tool_call") as err:
        await service.route(Message("jan@example.com", "test"))
    assert err.value.request_id
    assert mailer.commands == []


async def test_provider_failure_does_not_route_to_other(health_client):
    mailer = Mailer()
    service = RoutingService(
        LangChainRoutingAgent(Model(RuntimeError("secret")), health_client, "test-model"), mailer
    )
    with pytest.raises(RoutingError, match="model_unavailable"):
        await service.route(Message("jan@example.com", "test"))
    assert not mailer.commands


async def test_transport_failure_cannot_be_reported_as_success(health_client):
    model = Model(AIMessage(content="sent", tool_calls=[call()]))
    mailer = Mailer(RoutingError("delivery_unknown"))
    service = RoutingService(LangChainRoutingAgent(model, health_client, "test-model"), mailer)
    with pytest.raises(RoutingError, match="delivery_unknown"):
        await service.route(Message("jan@example.com", "test"))
    assert len(mailer.commands) == 1


@pytest.mark.parametrize(
    "body",
    [
        {"email": "broken", "message": "test"},
        {"email": "jan@example.com\r\nBcc: evil@example.com", "message": "test"},
        {"email": "jan@example.com", "message": " \n"},
        {"email": "jan@example.com", "message": "x" * 4001},
        {"email": "jan@example.com", "message": "test", "recipient": "it@example.com"},
        {"email": "jan@example.com", "message": "test", "department": "it"},
    ],
)
def test_http_validation_precedes_application_execution(health_client, body):
    mailer = Mailer()
    service = RoutingService(
        LangChainRoutingAgent(Model(AIMessage(content="")), health_client, "test-model"), mailer
    )
    with TestClient(create_app(service)) as client:
        assert client.post("/api/v1/messages", json=body).status_code == 422
    assert not mailer.commands


def test_swagger_openapi_and_success_response(health_client):
    service = RoutingService(
        LangChainRoutingAgent(
            Model(AIMessage(content="", tool_calls=[call()])), health_client, "test-model"
        ),
        Mailer(),
    )
    with TestClient(create_app(service)) as client:
        assert client.get("/api/v1/docs").status_code == 200
        schema = client.get("/api/v1/openapi.json").json()
        assert "/api/v1/messages" in schema["paths"]
        assert client.get("/health/ready").status_code == 200
        response = client.post(
            "/api/v1/messages", json={"email": "jan@example.com", "message": "urlop"}
        )
        assert response.status_code == 200
        assert response.json()["recipient"] == "kadry@example.com"


async def test_http_mailer_contract_and_exact_context():
    request_id = str(uuid4())

    async def handler(request):
        import json

        body = json.loads(request.content)
        assert request.url.path == "/internal/v1/deliveries"
        assert body == {
            "request_id": request_id,
            "recipient": "it@example.com",
            "reply_to": "jan@example.com",
            "message": "  awaria\n",
        }
        return httpx.Response(
            200,
            json={
                "request_id": request_id,
                "recipient": body["recipient"],
                "status": "submitted",
                "message_id": "<id@test>",
            },
        )

    async with httpx.AsyncClient(
        base_url="http://mailer/", transport=httpx.MockTransport(handler)
    ) as client:
        receipt = await HttpDeliveryGateway(client).send(
            request_id, Department.IT, Message("jan@example.com", "  awaria\n")
        )
    assert receipt.status == "submitted"


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(502, json={"code": "delivery_unknown"}),
        httpx.Response(200, json={"status": "submitted"}),
        httpx.Response(
            200,
            json={
                "request_id": "wrong",
                "recipient": "it@example.com",
                "status": "submitted",
                "message_id": "x",
            },
        ),
    ],
)
async def test_mailer_unconfirmed_or_mismatched_receipt_rejected(response):
    async with httpx.AsyncClient(
        base_url="http://mailer/", transport=httpx.MockTransport(lambda _: response)
    ) as client:
        with pytest.raises(RoutingError):
            await HttpDeliveryGateway(client).send(
                str(uuid4()), Department.IT, Message("jan@example.com", "test")
            )


async def test_mailer_timeout_not_retried():
    calls = []

    def handler(request):
        calls.append(request)
        raise httpx.ReadTimeout("response lost")

    async with httpx.AsyncClient(
        base_url="http://mailer/", transport=httpx.MockTransport(handler)
    ) as client:
        with pytest.raises(RoutingError, match="delivery_unknown"):
            await HttpDeliveryGateway(client).send(
                str(uuid4()), Department.IT, Message("jan@example.com", "test")
            )
    assert len(calls) == 1


async def test_invalid_arguments_fail_without_regeneration(health_client):
    class Once(Model):
        async def ainvoke(self, messages):
            assert not self.messages, "unexpected corrective retry"
            return await super().ainvoke(messages)

    model = Once(AIMessage(content="private text", tool_calls=[call(message="private args")]))
    mailer = Mailer()
    agent = LangChainRoutingAgent(model, health_client, "test")
    with pytest.raises(RoutingError, match="invalid_tool_call"):
        await agent.run("test-id", Message("sender@example.com", "urlop"), mailer)
    assert not mailer.commands


async def test_complete_call_at_token_limit_is_accepted(health_client, caplog):
    response = AIMessage(
        content="",
        tool_calls=[call()],
        response_metadata={"finish_reason": "tool_calls"},
        usage_metadata={"input_tokens": 50, "output_tokens": 384, "total_tokens": 434},
    )
    mailer = Mailer()
    agent = LangChainRoutingAgent(Model(response), health_client, "test")
    receipt = await agent.run("budget-test", Message("sender@example.com", "urlop"), mailer)
    assert receipt.status == "submitted"
    assert len(mailer.commands) == 1
    assert "reason=truncated" not in caplog.text


async def test_model_timeout_prevents_delivery(health_client):
    import asyncio

    class SlowModel(Model):
        attempts = 0

        async def ainvoke(self, messages):
            self.attempts += 1
            await asyncio.sleep(1)
            return AIMessage(content="no tool")

    mailer = Mailer()
    model = SlowModel(None)
    agent = LangChainRoutingAgent(model, health_client, "test", timeout=0.11)
    with pytest.raises(RoutingError, match="model_unavailable"):
        await agent.run("timeout-test", Message("sender@example.com", "urlop"), mailer)
    assert model.attempts == 1
    assert not mailer.commands


async def test_delivery_failure_does_not_restart_the_model_loop(health_client):
    class Once(Model):
        async def ainvoke(self, messages):
            assert not self.messages, "model called again after delivery attempted"
            return await super().ainvoke(messages)

    mailer = Mailer(RoutingError("delivery_unknown"))
    agent = LangChainRoutingAgent(
        Once(AIMessage(content="", tool_calls=[call()])), health_client, "test"
    )
    with pytest.raises(RoutingError, match="delivery_unknown"):
        await agent.run("delivery-test", Message("sender@example.com", "urlop"), mailer)
    assert len(mailer.commands) == 1
