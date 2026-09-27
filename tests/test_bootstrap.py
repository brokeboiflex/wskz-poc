import importlib.util
from pathlib import Path
from urllib.error import HTTPError

import pytest

PATH = Path(__file__).resolve().parents[1] / "services" / "model-init" / "bootstrap.py"
spec = importlib.util.spec_from_file_location("bootstrap", PATH)
bootstrap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bootstrap)


@pytest.fixture(autouse=True)
def clean_config(monkeypatch):
    monkeypatch.setenv("OPENAI_BASE_URL", "http://model/v1")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://ollama:11434")
    monkeypatch.setenv("MODEL_BOOTSTRAP", "ollama")


@pytest.mark.parametrize("cached", [True, False])
def test_ollama_download_is_conditional_and_tool_probe_has_no_mail(cached, monkeypatch):
    calls = []

    def request(url, payload=None, **kwargs):
        calls.append((url, payload))
        if url.endswith("/api/tags"):
            return {"models": [{"name": "test-model"}] if cached else []}
        if url.endswith("/api/pull"):
            return {"status": "success"}
        if url.endswith("/chat/completions"):
            assert payload["tools"][0]["function"]["name"] == "readiness_probe"
            return {
                "choices": [
                    {
                        "message": {
                            "tool_calls": [
                                {
                                    "function": {
                                        "name": "readiness_probe",
                                        "arguments": '{"ready":true}',
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        return {"data": [{"id": "test-model"}]}

    monkeypatch.setattr(bootstrap, "request", request)
    bootstrap.initialize()
    assert sum(url.endswith("/api/pull") for url, _ in calls) == (0 if cached else 1)
    assert all("mailer" not in url for url, _ in calls)


def test_external_endpoint_does_not_download_local_models_or_make_paid_inference(monkeypatch):
    monkeypatch.setenv("MODEL_BOOTSTRAP", "external")
    calls = []

    def request(url, payload=None, **kwargs):
        calls.append(url)
        assert payload is None
        return {"data": [{"id": "test-model"}]}

    monkeypatch.setattr(bootstrap, "request", request)
    bootstrap.initialize()
    assert calls == ["http://model/v1/models"]


def test_model_without_function_calling_fails_initialization(monkeypatch):
    def request(url, *args, **kwargs):
        if url.endswith("/api/tags"):
            return {"models": [{"name": "test-model"}]}
        return {"choices": [{"message": {"content": "ready"}}]}

    monkeypatch.setattr(bootstrap, "request", request)
    with pytest.raises(RuntimeError, match="native tool call"):
        bootstrap.initialize()


def test_auth_rejection_stops_initialization_without_printing_key(monkeypatch):
    monkeypatch.setenv("MODEL_BOOTSTRAP", "external")

    def request(url, *args, **kwargs):
        raise HTTPError(url, 401, "provider response containing secret", {}, None)

    monkeypatch.setattr(bootstrap, "request", request)
    with pytest.raises(RuntimeError, match="rejected authentication") as error:
        bootstrap.initialize()
    assert "secret" not in str(error.value)


def test_missing_model_has_bounded_readiness_wait(monkeypatch):
    monkeypatch.setenv("MODEL_BOOTSTRAP", "external")
    ticks = iter([0, 0, 1201])
    monkeypatch.setattr(bootstrap.time, "monotonic", lambda: next(ticks))
    monkeypatch.setattr(bootstrap.time, "sleep", lambda _: None)
    monkeypatch.setattr(bootstrap, "request", lambda *a, **k: {"data": []})
    with pytest.raises(RuntimeError, match="20 minutes"):
        bootstrap.initialize()


@pytest.mark.parametrize("omit", [False, True])
def test_bootstrap_and_production_model_use_same_inference_options(monkeypatch, omit):
    import asyncio
    import json

    import httpx
    from router_app.config import Settings
    from router_app.main import build_model

    monkeypatch.setenv("MODEL_MAX_TOKENS", "384")
    monkeypatch.setenv("MODEL_TOKEN_LIMIT_FIELD", "max_tokens")
    monkeypatch.setenv("MODEL_REASONING_EFFORT", "" if omit else "none")
    monkeypatch.setenv("MODEL_TEMPERATURE", "" if omit else "0.7")
    monkeypatch.setenv("MODEL_TOP_P", "" if omit else "0.8")
    bodies = []
    response = {
        "id": "probe",
        "object": "chat.completion",
        "created": 1,
        "model": "test-model",
        "choices": [
            {
                "index": 0,
                "finish_reason": "tool_calls",
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "probe",
                            "type": "function",
                            "function": {"name": "readiness_probe", "arguments": '{"ready":true}'},
                        }
                    ],
                },
            }
        ],
    }

    def request(url, payload=None, **kwargs):
        if url.endswith("/api/tags"):
            return {"models": [{"name": "test-model"}]}
        if url.endswith("/models"):
            return {"data": [{"id": "test-model"}]}
        bodies.append(payload)
        return response

    monkeypatch.setattr(bootstrap, "request", request)
    bootstrap.initialize()

    async def api_request():
        def handle(request):
            bodies.append(json.loads(request.content))
            return httpx.Response(200, json=response)

        async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
            await build_model(Settings(), client).ainvoke("probe")

    asyncio.run(api_request())
    fields = {"max_tokens", "max_completion_tokens", "reasoning_effort", "temperature", "top_p"}
    assert {k: v for k, v in bodies[0].items() if k in fields} == {
        k: v for k, v in bodies[1].items() if k in fields
    }


@pytest.mark.parametrize("finish,expected", [("tool_calls", None), ("length", "truncated")])
def test_bootstrap_uses_finish_reason_not_token_count(finish, expected):
    response = {
        "usage": {"completion_tokens": 1024},
        "choices": [
            {
                "finish_reason": finish,
                "message": {
                    "tool_calls": [
                        {
                            "function": {
                                "name": "readiness_probe",
                                "arguments": '{"ready":true}',
                            }
                        }
                    ]
                },
            }
        ],
    }
    error = bootstrap.probe_error(response)
    assert error is None if expected is None else expected in error


@pytest.mark.parametrize("arguments", ['{"ready":true,"extra":"bad"}', '{"ready":1}', "{"])
def test_bootstrap_never_accepts_extra_or_malformed_arguments(arguments):
    response = {
        "choices": [
            {
                "message": {
                    "tool_calls": [
                        {
                            "function": {
                                "name": "readiness_probe",
                                "arguments": arguments,
                            }
                        }
                    ]
                }
            }
        ]
    }
    assert bootstrap.probe_error(response) is not None


def test_bootstrap_rejected_probe_is_not_retried(monkeypatch):
    probes = []

    def request(url, payload=None, **kwargs):
        if url.endswith("/api/tags"):
            return {"models": [{"name": "test-model"}]}
        probes.append(url)
        return {"choices": [{"message": {"content": "ready"}}]}

    monkeypatch.setattr(bootstrap, "request", request)
    with pytest.raises(RuntimeError, match="native tool call"):
        bootstrap.initialize()
    assert probes == ["http://model/v1/chat/completions"]


def test_bootstrap_does_not_accept_a_valid_response_after_budget(monkeypatch):
    ticks = iter([0, 601])
    monkeypatch.setattr(bootstrap.time, "monotonic", lambda: next(ticks))

    def request(url, *args, **kwargs):
        if url.endswith("/api/tags"):
            return {"models": [{"name": "test-model"}]}
        return {
            "choices": [
                {
                    "message": {
                        "tool_calls": [
                            {
                                "function": {
                                    "name": "readiness_probe",
                                    "arguments": '{"ready":true}',
                                }
                            }
                        ]
                    }
                }
            ]
        }

    monkeypatch.setattr(bootstrap, "request", request)
    with pytest.raises(RuntimeError, match="timed out"):
        bootstrap.initialize()


@pytest.mark.parametrize("choice", ["", "auto", "required", "named"])
def test_bootstrap_forwards_configured_tool_choice(monkeypatch, choice):
    monkeypatch.setenv("MODEL_TOOL_CHOICE", choice)
    bodies = []

    def request(url, payload=None, **kwargs):
        if url.endswith("/api/tags"):
            return {"models": [{"name": "test-model"}]}
        if url.endswith("/models"):
            return {"data": [{"id": "test-model"}]}
        bodies.append(payload)
        return {
            "choices": [
                {
                    "finish_reason": "tool_calls",
                    "message": {
                        "tool_calls": [
                            {"function": {"name": "readiness_probe", "arguments": '{"ready":true}'}}
                        ]
                    },
                }
            ]
        }

    monkeypatch.setattr(bootstrap, "request", request)
    bootstrap.initialize()
    assert len(bodies) == 1
    if choice == "named":
        assert bodies[0]["tool_choice"] == {
            "type": "function",
            "function": {"name": "readiness_probe"},
        }
    elif choice:
        assert bodies[0]["tool_choice"] == choice
    else:
        assert "tool_choice" not in bodies[0]
