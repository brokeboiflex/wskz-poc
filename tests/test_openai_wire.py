"""Real ChatOpenAI serialization against controlled HTTP responses, not a live model."""

import json

import httpx
import pytest
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import StructuredTool
from router_app.adapters.agent import SendArguments

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
        assert "recipient" in body["tools"][0]["function"]["parameters"]["properties"]
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
                                        "arguments": '{"recipient":"kadry@example.com"}',
                                    },
                                }
                            ],
                        },
                    }
                ],
            },
        )

    async def send(recipient: str):
        """Send email."""
        return "ok"

    tool = StructuredTool.from_function(
        coroutine=send, name="send_department_email", args_schema=SendArguments
    )
    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        model = langchain_openai.ChatOpenAI(
            model="test",
            base_url="http://model/v1",
            api_key="synthetic",
            http_async_client=client,
            use_responses_api=False,
            max_retries=0,
        )
        result = await model.bind_tools([tool]).ainvoke(
            [SystemMessage("route"), HumanMessage("urlop")]
        )
    assert result.tool_calls[0]["args"] == {"recipient": "kadry@example.com"}
    assert len(seen) == 1


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
            assert "kadry@example.com" in choice.options
            assert choice.state == "Proszę o urlop."
            return "kadry@example.com"

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
            model = langchain_openai.ChatOpenAI(
                model="laya-multilingual",
                base_url="http://laya/v1",
                api_key="synthetic",
                http_async_client=client,
                use_responses_api=False,
                max_retries=0,
                max_tokens=1024,
                timeout=180,
            )
            mailer = Mailer()
            service = RoutingService(
                LangChainRoutingAgent(model, client, "laya-multilingual"), mailer
            )
            assert await service.ready()
            receipt = await service.route(Message("jan@example.com", "Proszę o urlop."))
    assert receipt.status == "submitted"
    assert mailer.calls == [("kadry@example.com", "jan@example.com", "Proszę o urlop.")]
