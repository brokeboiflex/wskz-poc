import json

import httpx
import pytest
from fastapi.testclient import TestClient
from laya_adapter.domain import Choice
from laya_adapter.engine import HttpDecisionEngine
from laya_adapter.main import create_app
from laya_adapter.service import ChoiceService


class Engine:
    def __init__(self, selected="billing"):
        self.selected, self.calls = selected, []

    async def ready(self):
        return True

    async def choose(self, choice):
        self.calls.append(choice)
        return self.selected


def payload():
    return {
        "model": "laya-multilingual",
        "messages": [
            {"role": "system", "content": "Select the responsible team."},
            {"role": "user", "content": "Duplicate payment"},
        ],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "select_team",
                    "description": "Choose a team",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "team": {
                                "type": "string",
                                "enum": ["billing", "support"],
                                "description": "billing for invoices, support for bugs",
                            }
                        },
                        "required": ["team"],
                    },
                },
            }
        ],
    }


def test_adapter_translates_real_engine_decision_without_business_policy():
    engine = Engine()
    with TestClient(create_app(ChoiceService(engine))) as client:
        assert client.get("/v1/models").json()["data"][0]["id"] == "laya-multilingual"
        response = client.post("/v1/chat/completions", json=payload())
        assert response.status_code == 200
    call = response.json()["choices"][0]["message"]["tool_calls"][0]
    assert call["function"]["name"] == "select_team"
    assert json.loads(call["function"]["arguments"]) == {"team": "billing"}
    assert len(engine.calls) == 1
    assert engine.calls[0].state == "Duplicate payment"
    assert "billing for invoices" in engine.calls[0].instructions


@pytest.mark.parametrize(
    "change,status",
    [
        ({"model": "unknown"}, 404),
        ({"stream": True}, 422),
        ({"tools": []}, 422),
        ({"messages": [{"role": "assistant", "content": "sent"}]}, 422),
        ({"temperature": 0.5}, 422),
        ({"messages": [{"role": "user", "content": "a"}, {"role": "user", "content": "b"}]}, 400),
        ({"messages": [{"role": "user", "content": "😀" * 3000}]}, 413),
    ],
)
def test_adapter_rejects_unsupported_contracts(change, status):
    engine = Engine()
    with TestClient(create_app(ChoiceService(engine))) as client:
        response = client.post("/v1/chat/completions", json={**payload(), **change})
    assert response.status_code == status
    assert engine.calls == []


def test_adapter_rejects_malformed_schema_without_inference():
    body = payload()
    body["tools"][0]["function"]["parameters"]["properties"]["extra"] = {"type": "string"}
    engine = Engine()
    with TestClient(create_app(ChoiceService(engine))) as client:
        assert client.post("/v1/chat/completions", json=body).status_code == 400
    assert not engine.calls


@pytest.mark.parametrize("properties", [42, ["wrong"], {"team": "wrong"}])
def test_invalid_json_schema_returns_client_error(properties):
    body = payload()
    body["tools"][0]["function"]["parameters"]["properties"] = properties
    engine = Engine()
    with TestClient(create_app(ChoiceService(engine))) as client:
        assert client.post("/v1/chat/completions", json=body).status_code == 400
    assert not engine.calls


def test_adapter_never_invents_a_choice_when_engine_is_wrong():
    with TestClient(create_app(ChoiceService(Engine("evil")))) as client:
        response = client.post("/v1/chat/completions", json=payload())
    assert response.status_code == 502
    assert "tool_calls" not in response.text


async def test_jev_http_contract():
    def handle(request):
        assert request.url.path == "/v1/systemone"
        assert json.loads(request.content) == {
            "model": "multilingual",
            "state": "test",
            "questions": {
                "selection": {
                    "type": "choice",
                    "instructions": "pick",
                    "criteria": {"a": "a", "b": "b"},
                }
            },
        }
        return httpx.Response(200, json={"answers": {"selection": {"choice": "b"}}})

    async with httpx.AsyncClient(
        base_url="http://laya/", transport=httpx.MockTransport(handle)
    ) as client:
        assert (
            await HttpDecisionEngine(client, "multilingual").choose(
                Choice("test", "pick", ("a", "b"))
            )
            == "b"
        )


def test_runtime_uses_injected_predictor_and_enforces_context_bound():
    from runtime import InferenceService
    from runtime import create_app as create_runtime

    class Predictor:
        def predict(self, state, questions):
            return {"answers": {"selection": {"choice": "b"}}}

    body = {
        "state": "hello",
        "questions": {
            "selection": {
                "type": "choice",
                "instructions": "pick",
                "criteria": {"a": "a", "b": "b"},
            }
        },
    }
    with TestClient(create_runtime(InferenceService(Predictor()))) as client:
        assert client.get("/health/ready").status_code == 200
        assert (
            client.post("/v1/systemone", json=body).json()["answers"]["selection"]["choice"] == "b"
        )
        assert client.post("/v1/systemone", json={**body, "state": "😀" * 3000}).status_code == 413
