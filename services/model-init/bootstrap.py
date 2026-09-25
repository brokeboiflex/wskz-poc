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


def initialize():
    base = os.environ.get("OPENAI_BASE_URL", "http://ollama:11434/v1").rstrip("/")
    model = os.environ.get("OPENAI_MODEL", "qwen3:1.7b")
    key = os.environ.get("OPENAI_API_KEY", "ollama")
    mode = os.environ.get("MODEL_BOOTSTRAP", "ollama")
    if mode not in {"ollama", "external"}:
        raise ValueError("MODEL_BOOTSTRAP must be ollama or external")
    if mode == "ollama":
        native = os.environ.get("OLLAMA_BASE_URL", "http://ollama:11434").rstrip("/")
        models = request(native + "/api/tags")["models"]
        if not any(item["name"] == model for item in models):
            print("Downloading configured Ollama model; cached layers are reused.", flush=True)
            result = request(native + "/api/pull", {"model": model, "stream": False}, timeout=1800)
            if result.get("status") != "success":
                raise RuntimeError("model pull did not succeed")
        print("Warming the model and checking native tool calling (no email).", flush=True)
        result = request(
            base + "/chat/completions",
            {
                "model": model,
                "messages": [
                    {"role": "user", "content": "Call readiness_probe with ready=true. /no_think"}
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
                            },
                        },
                    }
                ],
                "max_tokens": 256,
                "stream": False,
            },
            key=key,
            timeout=600,
        )
        calls = result["choices"][0]["message"].get("tool_calls", [])
        if len(calls) != 1 or calls[0]["function"]["name"] != "readiness_probe":
            raise RuntimeError("model did not produce a native tool call")
        if json.loads(calls[0]["function"]["arguments"]).get("ready") is not True:
            raise RuntimeError("invalid readiness tool arguments")
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
