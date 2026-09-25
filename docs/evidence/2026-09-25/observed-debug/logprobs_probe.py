"""One observed OpenAI-compatible request; records tokens and never executes tools."""

import json
import os
import time
from pathlib import Path

import httpx
from router_app.config import Settings

settings = Settings()
payload = json.loads(Path("/tmp/observed-wire-request.json").read_text())
# Standard OpenAI diagnostic metadata, not a different inference endpoint/client.
payload["logprobs"] = True
payload["top_logprobs"] = int(os.environ.get("DIAGNOSTIC_TOP_LOGPROBS", "0"))
started = time.perf_counter()
response = httpx.post(
    settings.openai_base_url.rstrip("/") + "/chat/completions",
    headers={"Authorization": "Bearer " + settings.openai_api_key.get_secret_value()},
    json=payload,
    timeout=settings.model_timeout_seconds,
)
print(
    json.dumps(
        {
            "request": payload,
            "status": response.status_code,
            "seconds": round(time.perf_counter() - started, 3),
            "raw_response": response.text,
        },
        ensure_ascii=False,
    ),
    flush=True,
)
response.raise_for_status()
