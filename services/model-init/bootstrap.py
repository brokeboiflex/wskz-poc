"""One-shot, resumable model initialization; never invokes the mailer."""

import json
import os
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def request(url, payload=None, *, key="", timeout=30):
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    body = json.dumps(payload).encode() if payload is not None else None
    with urlopen(Request(url, data=body, headers=headers), timeout=timeout) as response:
        return json.load(response)


def probe_error(result):
    try:
        choice = result["choices"][0]
        if choice.get("finish_reason") == "length":
            return "readiness tool call was truncated"
        calls = choice["message"].get("tool_calls") or []
        if len(calls) != 1 or calls[0]["function"]["name"] != "readiness_probe":
            return "model did not produce a native tool call"
        args = json.loads(calls[0]["function"]["arguments"])
        if not isinstance(args, dict) or set(args) != {"ready"} or args["ready"] is not True:
            return "invalid readiness tool arguments"
    except (ValueError, KeyError, TypeError, IndexError):
        return "invalid readiness response"
    return None


def initialize():
    base = os.environ.get("OPENAI_BASE_URL", "http://ollama:11434/v1").rstrip("/")
    model = os.environ.get("OPENAI_MODEL", "gemma4:e2b")
    key = os.environ.get("OPENAI_API_KEY", "ollama")
    mode = os.environ.get("MODEL_BOOTSTRAP", "ollama")
    if mode not in {"ollama", "external"}:
        raise ValueError("MODEL_BOOTSTRAP must be ollama or external")
    if mode == "ollama":
        # Same wire options as the API; no LangChain dependency across services.
        token_field = os.environ.get("MODEL_TOKEN_LIMIT_FIELD", "max_tokens")
        if token_field not in {"max_tokens", "max_completion_tokens"}:
            raise ValueError("invalid MODEL_TOKEN_LIMIT_FIELD")
        options = {token_field: int(os.environ.get("MODEL_MAX_TOKENS", "1024"))}
        for env, field, default, convert in (
            ("MODEL_REASONING_EFFORT", "reasoning_effort", "none", str),
            ("MODEL_TEMPERATURE", "temperature", "0", float),
            ("MODEL_TOP_P", "top_p", "0.8", float),
        ):
            value = os.environ.get(env, default)
            if value:
                options[field] = convert(value)
        choice = os.environ.get("MODEL_TOOL_CHOICE", "required")
        if choice not in {"", "auto", "required", "named"}:
            raise ValueError("invalid MODEL_TOOL_CHOICE")
        if choice:
            options["tool_choice"] = (
                {"type": "function", "function": {"name": "readiness_probe"}}
                if choice == "named"
                else choice
            )
        native = os.environ.get("OLLAMA_BASE_URL", "http://ollama:11434").rstrip("/")
        models = request(native + "/api/tags")["models"]
        if not any(item["name"] == model for item in models):
            print("Downloading configured Ollama model; cached layers are reused.", flush=True)
            result = request(native + "/api/pull", {"model": model, "stream": False}, timeout=1800)
            if result.get("status") != "success":
                raise RuntimeError("model pull did not succeed")
        print("Warming the model and checking native tool calling (no email).", flush=True)
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "Use the provided tool once. No prose."},
                {"role": "user", "content": "Call readiness_probe with ready=true."},
            ],
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "readiness_probe",
                        "description": "Report that inference is ready.",
                        "parameters": {
                            "type": "object",
                            "properties": {"ready": {"type": "boolean"}},
                            "required": ["ready"],
                            "additionalProperties": False,
                        },
                    },
                }
            ],
            **options,
            "stream": False,
        }
        probe_deadline = time.monotonic() + 600
        result = request(base + "/chat/completions", payload, key=key, timeout=600)
        if time.monotonic() >= probe_deadline:
            raise RuntimeError("readiness probe timed out")
        reason = probe_error(result)
        if reason:
            raise RuntimeError(reason)
    deadline = time.monotonic() + 1200
    while time.monotonic() < deadline:
        try:
            models = request(base + "/models", key=key, timeout=10)
            if any(item["id"] == model for item in models["data"]):
                print("Selected model endpoint is ready.", flush=True)
                return
        except HTTPError as exc:
            if exc.code in {401, 403}:
                raise RuntimeError("model endpoint rejected authentication") from None
        except (URLError, TimeoutError, ValueError, KeyError):
            pass
        time.sleep(3)
    raise RuntimeError("selected model did not become available within 20 minutes")


if __name__ == "__main__":
    initialize()
