"""Capture Ollama's render-only debug endpoint; never generates tokens."""

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
label, endpoint, source = sys.argv[1:]
request = json.loads(Path(source).read_text())
for message in request["messages"]:
    for call in message.get("tool_calls", []):
        args = call["function"]["arguments"]
        if isinstance(args, str):
            call["function"]["arguments"] = json.loads(args)
body = {
    "model": request["model"],
    "messages": request["messages"],
    "tools": request.get("tools", []),
    "stream": False,
    "think": False,
    "_debug_render_only": True,
}
out = HERE / label
out.mkdir(exist_ok=False)
(out / "request.json").write_text(json.dumps(body, ensure_ascii=False, indent=2))
code = """import json,sys,httpx
r=httpx.post(sys.argv[1],json=json.load(sys.stdin),timeout=180)
print(json.dumps({'status':r.status_code,'body':r.json()},ensure_ascii=False))
"""
result = subprocess.run(
    ["docker", "compose", "exec", "-T", "api", "python", "-c", code, endpoint],
    cwd=HERE.parents[3],
    input=json.dumps(body),
    text=True,
    capture_output=True,
    check=True,
)
(out / "response.json").write_text(result.stdout)
response = json.loads(result.stdout)
assert response["status"] == 200, response
rendered = response["body"]["_debug_info"]["rendered_template"]
(out / "prompt.txt").write_text(rendered)
print(rendered)
