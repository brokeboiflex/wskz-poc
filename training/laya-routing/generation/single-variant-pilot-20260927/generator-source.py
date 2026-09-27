"""One observed authoring pilot: simpler single-message request, no classification/evaluation."""

import json
import time
import urllib.request
from pathlib import Path

from generate_data import ENDPOINT, MODEL, new_json, sha

ROOT = Path(__file__).parent
output = ROOT / "generation/single-variant-pilot-20260927"
output.mkdir(exist_ok=False)
plan_path = ROOT / "source/scenarios.json"
family = json.loads(plan_path.read_text())["families"][6]
policy = json.loads((ROOT / "policy.json").read_text())
system = """Napisz jedną naturalną wiadomość po polsku dotyczącą podanej sprawy. Zachowaj dokładnie rodzaj zadania i fakty ze scenariusza. Nie dodawaj innych aktywnych spraw. Każda wiadomość jest samodzielna. Nie wymieniaj nazwy docelowego działu. Zwróć tylko treść wiadomości, bez komentarza, analizy i podpisu. Wszystkie szczegóły są fikcyjne."""
request = {
    "model": MODEL,
    "messages": [
        {
            "role": "system",
            "content": system
            + "\nZnaczenie kategorii do kontroli zakresu: "
            + json.dumps(policy["criteria"], ensure_ascii=False),
        },
        {
            "role": "user",
            "content": "Sprawa: "
            + family["scenario"]
            + "\nForma: trzy zdania, 25-45 słów. Krótko opisz sytuację i poproś o wykonanie dokładnie tego zadania. Występujesz jako organizator rekrutacji.",
        },
    ],
    "temperature": 0.3,
    "top_p": 0.9,
    "seed": 48,
    "reasoning_effort": "none",
    "max_tokens": 300,
    "stream": False,
}
new_json(output / "request.json", request)
new_json(
    output / "attempt.json",
    {
        "family": family,
        "plan_sha256": sha(plan_path),
        "script_sha256": sha(__file__),
        "time": time.time(),
        "training_data": False,
    },
)
(output / "generator-source.py").write_bytes(Path(__file__).read_bytes())
wire = urllib.request.Request(
    ENDPOINT,
    data=json.dumps(request, ensure_ascii=False).encode(),
    headers={"Content-Type": "application/json"},
)
start = time.monotonic()
with urllib.request.urlopen(wire, timeout=180) as response:
    body = response.read().decode()
(output / "response.txt").write_text(body)
result = json.loads(body)
new_json(
    output / "result.json",
    {
        "seconds": time.monotonic() - start,
        "request_sha256": sha(output / "request.json"),
        "response_sha256": sha(output / "response.txt"),
        "finish_reason": result["choices"][0]["finish_reason"],
        "message": result["choices"][0]["message"]["content"],
    },
)
print((output / "result.json").read_text())
