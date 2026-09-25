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
