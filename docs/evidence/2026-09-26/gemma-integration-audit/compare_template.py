"""Offline comparison of Google's template and captured Ollama rendering."""

import difflib
import hashlib
import json
from pathlib import Path

import jinja2

HERE = Path(__file__).resolve().parent
PREVIOUS = HERE.parent / "failed-cases-comparison"
request = json.loads((PREVIOUS / "gemma-token-request.json").read_text())
env = jinja2.Environment(trim_blocks=True, lstrip_blocks=True)
template = env.from_string((HERE / "google-chat-template.jinja").read_text())
rendered = template.render(
    messages=request["messages"],
    tools=request["tools"],
    bos_token="<bos>",
    eos_token="<eos>",
    enable_thinking=False,
    add_generation_prompt=True,
)
actual = (PREVIOUS / "gemma-rendered-prompt.txt").read_text()
diff = "".join(
    difflib.unified_diff(
        actual.splitlines(keepends=True),
        rendered.splitlines(keepends=True),
        fromfile="ollama-v0.34.4",
        tofile="google-official",
    )
)
metadata = json.loads((HERE / "google-model-metadata.json").read_text())
result = {
    "google_revision": metadata["sha"],
    "jinja_version": jinja2.__version__,
    "identical": rendered == actual,
    "google_characters": len(rendered),
    "ollama_characters": len(actual),
    "google_sha256": hashlib.sha256(rendered.encode()).hexdigest(),
    "ollama_sha256": hashlib.sha256(actual.encode()).hexdigest(),
}
for name, text in {
    "google-rendered-prompt.txt": rendered,
    "template.diff": diff,
    "template-comparison.json": json.dumps(result, indent=2) + "\n",
}.items():
    with (HERE / name).open("x") as output:
        output.write(text)
print(json.dumps(result, indent=2))
print(diff)
