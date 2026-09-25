"""Real ChatOpenAI serialization against controlled HTTP responses, not a live model."""

import json

import httpx
import pytest
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import StructuredTool
from router_app.adapters.agent import SendArguments
from router_app.config import Settings
from router_app.main import build_model

langchain_openai = pytest.importorskip(
    "langchain_openai",
    reason="LangChain OpenAI package unavailable in offline host cache; run container tests",
)


async def test_real_chatopenai_sends_tools_and_parses_native_tool_calls():
    seen = []

    def handle(request):
        seen.append(request)
        body = json.loads(request.content)
        assert request.url.path == "/v1/chat/completions"
        assert body["tools"][0]["function"]["name"] == "send_department_email"
        assert "department" in body["tools"][0]["function"]["parameters"]["properties"]
        prop = body["tools"][0]["function"]["parameters"]["properties"]["department"]
        criteria = {item["enum"][0]: item["description"] for item in prop["anyOf"]}
        assert "Urlopy" in criteria["payroll"]
        assert "x-choice" not in json.dumps(body)
        assert "@" not in json.dumps(body["tools"])
        return httpx.Response(
            200,
            json={
                "id": "chatcmpl-test",
                "object": "chat.completion",
                "created": 1,
                "model": "test",
                "choices": [
                    {
                        "index": 0,
                        "finish_reason": "tool_calls",
                        "message": {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": "call_test",
                                    "type": "function",
                                    "function": {
                                        "name": "send_department_email",
                                        "arguments": '{"department":"payroll"}',
                                    },
                                }
                            ],
                        },
                    }
                ],
            },
        )

    async def send(department: str):
        """Send email."""
        return "ok"

    tool = StructuredTool.from_function(
        coroutine=send,
        name="send_department_email",
        args_schema=SendArguments.model_json_schema(),
    )
    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        model = build_model(
            Settings(
                openai_model="test", openai_base_url="http://model/v1", openai_api_key="synthetic"
            ),
            client,
        )
        result = await model.bind_tools([tool]).ainvoke(
            [SystemMessage("route"), HumanMessage("urlop")]
        )
    assert result.tool_calls[0]["args"] == {"department": "payroll"}
    assert len(seen) == 1
    body = json.loads(seen[0].content)
    assert body["max_tokens"] == 1024
    assert "max_completion_tokens" not in body
    assert body["reasoning_effort"] == "none"
    assert body["temperature"] == 0.7
    assert body["top_p"] == 0.8
    assert "extra_body" not in body


async def test_real_chatopenai_payload_is_accepted_by_laya_adapter():
    from laya_adapter.main import create_app
    from laya_adapter.service import ChoiceService
    from router_app.adapters.agent import LangChainRoutingAgent
    from router_app.domain import Delivery, Message
    from router_app.service import RoutingService

    class Engine:
        async def ready(self):
            return True

        async def choose(self, choice):
            from router_app.adapters.agent import DECISION_INSTRUCTIONS, DEPARTMENT_CRITERIA

            assert choice.instructions == DECISION_INSTRUCTIONS
            assert (
                dict(zip(choice.options, choice.descriptions, strict=True)) == DEPARTMENT_CRITERIA
            )
            assert "@" not in str(choice)
            assert choice.state == "Proszę o urlop."
            return "payroll"

    class Mailer:
        def __init__(self):
            self.calls = []

        async def ready(self):
            return True

        async def send(self, request_id, recipient, message):
            self.calls.append((recipient.value, message.email, message.message))
            return Delivery(request_id, recipient.value, "submitted", "<id@test>")

    app = create_app(ChoiceService(Engine()))
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            base_url="http://laya/v1/", transport=httpx.ASGITransport(app=app)
        ) as client:
            model = build_model(
                Settings(
                    openai_model="laya-multilingual",
                    openai_base_url="http://laya/v1",
                    openai_api_key="synthetic",
                    model_reasoning_effort="",
                    model_temperature="",
                    model_top_p="",
                ),
                client,
            )
            mailer = Mailer()
            service = RoutingService(
                LangChainRoutingAgent(model, client, "laya-multilingual", tool_choice="required"),
                mailer,
            )
            assert await service.ready()
            receipt = await service.route(Message("jan@example.com", "Proszę o urlop."))
    assert receipt.status == "submitted"
    assert mailer.calls == [("kadry@example.com", "jan@example.com", "Proszę o urlop.")]


@pytest.mark.parametrize("token_field", ["max_tokens", "max_completion_tokens"])
async def test_provider_options_can_be_omitted_and_token_field_selected(token_field):
    seen = []

    def handle(request):
        seen.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "id": "test",
                "object": "chat.completion",
                "created": 1,
                "model": "test",
                "choices": [
                    {
                        "index": 0,
                        "finish_reason": "stop",
                        "message": {"role": "assistant", "content": "test"},
                    }
                ],
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        model = build_model(
            Settings(
                openai_base_url="http://model/v1",
                openai_api_key="synthetic",
                model_token_limit_field=token_field,
                model_max_tokens=384,
                model_reasoning_effort="",
                model_temperature="",
                model_top_p="",
            ),
            client,
        )
        await model.ainvoke("test")
    assert seen[0][token_field] == 384
    other = {"max_tokens", "max_completion_tokens"} - {token_field}
    assert not other.intersection(seen[0])
    assert not {"reasoning_effort", "temperature", "top_p"}.intersection(seen[0])


@pytest.mark.parametrize(
    "finish,arguments,reason",
    [
        ("length", '{"department":"payroll"}', "truncated"),
        ("tool_calls", '{"department":', "malformed_arguments"),
        ("tool_calls", '{"department":"secret-invalid-value"}', "invalid_arguments"),
        ("stop", None, "missing_call"),
    ],
)
async def test_real_wire_rejections_never_send_or_log_content(finish, arguments, reason, caplog):
    from router_app.adapters.agent import LangChainRoutingAgent
    from router_app.domain import Message, RoutingError

    def handle(request):
        message = {"role": "assistant", "content": "secret-response"}
        if arguments is not None:
            message["tool_calls"] = [
                {
                    "id": "call_test",
                    "type": "function",
                    "function": {
                        "name": "send_department_email",
                        "arguments": arguments,
                    },
                }
            ]
        return httpx.Response(
            200,
            json={
                "id": "test",
                "object": "chat.completion",
                "created": 1,
                "model": "test",
                "choices": [{"index": 0, "finish_reason": finish, "message": message}],
            },
        )

    class NoDelivery:
        async def send(self, *args):
            pytest.fail("invalid model output initiated delivery")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        model = build_model(
            Settings(openai_base_url="http://model/v1", openai_api_key="synthetic"), client
        )
        agent = LangChainRoutingAgent(model, client, "test")
        with pytest.raises(RoutingError, match="invalid_tool_call"):
            await agent.run(
                "correlation-test", Message("secret@example.com", "secret-input"), NoDelivery()
            )
    assert f"reason={reason}" in caplog.text
    assert "request_id=correlation-test" in caplog.text
    assert "secret" not in caplog.text


@pytest.mark.parametrize("tool_choice", ["", "auto", "required", "named"])
@pytest.mark.parametrize(
    "base,model_name,token_field",
    [
        ("https://first-provider.example/v1", "model-a", "max_tokens"),
        ("https://second-provider.example/api/v1", "model-b", "max_completion_tokens"),
    ],
)
async def test_same_agent_switches_providers_by_env_only(
    monkeypatch, base, model_name, token_field, tool_choice
):
    from router_app.adapters.agent import LangChainRoutingAgent
    from router_app.domain import Delivery, Message

    for key, value in {
        "OPENAI_BASE_URL": base,
        "OPENAI_MODEL": model_name,
        "OPENAI_API_KEY": "test-key",
        "MODEL_TOKEN_LIMIT_FIELD": token_field,
        "MODEL_MAX_TOKENS": "384",
        "MODEL_REASONING_EFFORT": "",
        "MODEL_TEMPERATURE": "",
        "MODEL_TOP_P": "",
        "MODEL_TOOL_CHOICE": tool_choice,
    }.items():
        monkeypatch.setenv(key, value)
    requests, deliveries = [], []

    def handle(request):
        requests.append(request)
        body = json.loads(request.content)
        assert str(request.url) == base + "/chat/completions"
        assert body["model"] == model_name
        assert request.headers["Authorization"] == "Bearer test-key"
        assert body[token_field] == 384
        assert not {"reasoning_effort", "temperature", "top_p"}.intersection(body)
        assert "x-choice" not in json.dumps(body)
        if tool_choice == "named":
            assert body["tool_choice"] == {
                "type": "function",
                "function": {"name": "send_department_email"},
            }
        elif tool_choice:
            assert body["tool_choice"] == tool_choice
        else:
            assert "tool_choice" not in body
        prop = body["tools"][0]["function"]["parameters"]["properties"]["department"]
        assert set(prop) <= {"type", "enum", "description", "anyOf", "title"}
        assert {item["enum"][0] for item in prop["anyOf"]} == set(prop["enum"])
        return httpx.Response(
            200,
            json={
                "id": "test",
                "object": "chat.completion",
                "created": 1,
                "model": model_name,
                "usage": {"prompt_tokens": 30, "completion_tokens": 384, "total_tokens": 414},
                "choices": [
                    {
                        "index": 0,
                        "finish_reason": "tool_calls",
                        "message": {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": "call_test",
                                    "type": "function",
                                    "function": {
                                        "name": "send_department_email",
                                        "arguments": '{"department":"payroll"}',
                                    },
                                }
                            ],
                        },
                    }
                ],
            },
        )

    class Mailer:
        async def send(self, request_id, recipient, message):
            deliveries.append((recipient.value, message))
            return Delivery(request_id, recipient.value, "submitted", "<id@test>")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        settings = Settings()
        agent = LangChainRoutingAgent(
            build_model(settings, client),
            client,
            settings.openai_model,
            tool_choice=settings.model_tool_choice,
        )
        message = Message("sender@example.com", "Proszę o urlop.")
        receipt = await agent.run("test-request", message, Mailer())
    assert receipt.status == "submitted"
    assert len(requests) == 1
    assert deliveries == [("kadry@example.com", message)]
