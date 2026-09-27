"""One observed OpenAI-compatible diagnostic, no tool execution or retries."""

import datetime
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
label, endpoint, source = sys.argv[1:]
attempt = HERE / label
attempt.mkdir(exist_ok=False)
request = json.loads(Path(source).read_text())
(attempt / "request.json").write_text(json.dumps(request, ensure_ascii=False, indent=2))
(attempt / "metadata.json").write_text(
    json.dumps(
        {
            "endpoint": endpoint,
            "started_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "source": str(Path(source).resolve()),
            "retries": 0,
            "tool_execution": False,
        },
        indent=2,
    )
)
code = """import json,sys,httpx
request=json.load(sys.stdin)
response=httpx.post(sys.argv[1],json=request,timeout=180)
print(json.dumps({'status':response.status_code,'body':response.text},ensure_ascii=False))
"""
result = subprocess.run(
    ["docker", "compose", "exec", "-T", "api", "python", "-c", code, endpoint],
    input=json.dumps(request),
    text=True,
    capture_output=True,
    cwd=ROOT,
)
(attempt / "transport.stdout").write_text(result.stdout)
(attempt / "transport.stderr").write_text(result.stderr)
summary = {"transport_exit": result.returncode}
if result.returncode == 0:
    transport = json.loads(result.stdout)
    body = json.loads(transport["body"])
    (attempt / "response.json").write_text(json.dumps(body, ensure_ascii=False, indent=2))
    summary["http_status"] = transport["status"]
    if body.get("choices"):
        choice = body["choices"][0]
        summary["message"] = choice["message"]
        summary["finish_reason"] = choice.get("finish_reason")
        summary["usage"] = body.get("usage")
        tokens = (choice.get("logprobs") or {}).get("content", [])
        generated = "".join(t["token"] for t in tokens)
        (attempt / "generated-tokens.txt").write_text(generated)
        summary["generated_tokens"] = generated
    else:
        summary["error"] = body
(attempt / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
print(json.dumps(summary, ensure_ascii=False, indent=2))
