import asyncio
import json
import logging

import httpx
import pytest
from router_app.adapters.agent import LangChainRoutingAgent
from router_app.config import Settings
from router_app.domain import Message, RoutingError
from router_app.main import build_model
from router_app.model_trace import event_hooks, trace_scope


@pytest.mark.parametrize("enabled", [False, True])
async def test_trace_preserves_wire_and_explains_missing_call(enabled, caplog):
    caplog.set_level(logging.INFO, logger="uvicorn.error.model_trace")
    requests = []
    raw = json.dumps(
        {
            "id": "diagnostic",
            "object": "chat.completion",
            "created": 1,
            "model": "test",
            "choices": [
                {
                    "index": 0,
                    "finish_reason": "stop",
                    "message": {"role": "assistant", "content": "synthetic model prose"},
                }
            ],
        }
    ).encode()

    def handle(request):
        requests.append(request.content.decode())
        assert request.headers["Authorization"] == "Bearer never-log-key"
        return httpx.Response(200, content=raw, headers={"Content-Type": "application/json"})

    class NoDelivery:
        async def send(self, *args):
            pytest.fail("missing call must not send")

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handle), event_hooks=event_hooks(enabled)
    ) as client:
        model = build_model(
            Settings(openai_base_url="http://model/v1", openai_api_key="never-log-key"), client
        )
        agent = LangChainRoutingAgent(model, client, "test", trace=enabled)
        with pytest.raises(RoutingError, match="invalid_tool_call"):
            await agent.run(
                "trace-one", Message("test@example.com", "synthetic input"), NoDelivery()
            )
    records = [
        json.loads(r.message.split("model_trace ", 1)[1])
        for r in caplog.records
        if r.name == "uvicorn.error.model_trace"
    ]
    assert len(requests) == 1
    assert "never-log-key" not in caplog.text
    assert "Authorization" not in caplog.text
    if enabled:
        assert [r["event"] for r in records] == ["request", "response", "parsed", "agent_error"]
        assert {r["request_id"] for r in records} == {"trace-one"}
        assert records[0]["body"] == requests[0]
        assert records[1]["body"] == raw.decode()
        assert records[2]["rejection_reason"] == "missing_call"
        assert records[2]["response"]["content"] == "synthetic model prose"
    else:
        assert records == []
        assert "synthetic input" not in caplog.text
        assert "synthetic model prose" not in caplog.text


async def test_concurrent_trace_scopes_do_not_cross_requests(caplog):
    caplog.set_level(logging.INFO, logger="uvicorn.error.model_trace")

    async def handle(request):
        await asyncio.sleep(0)
        return httpx.Response(200, content=request.content)

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handle), event_hooks=event_hooks(True)
    ) as client:

        async def call(label):
            with trace_scope(label):
                response = await client.post(
                    "http://model/v1/chat/completions?key=hidden-query",
                    content=label,
                    headers={"Authorization": "hidden-auth"},
                )
                assert response.content == label.encode()

        await asyncio.gather(call("alpha"), call("beta"))
        # Context must be reset after the requests, including the no-scope path.
        await client.post("http://model/v1/chat/completions", content="outside")
    records = [json.loads(r.message.split("model_trace ", 1)[1]) for r in caplog.records]
    assert len(records) == 4
    assert all(r["request_id"] == r["body"] for r in records)
    assert "hidden-query" not in caplog.text
    assert "hidden-auth" not in caplog.text
    assert "outside" not in caplog.text
