"""Read-only audit of preserved authoring attempts; does not generate or accept data."""

import importlib.util
import json
from pathlib import Path

from generate_data import sha

ROOT = Path(__file__).parent
policy_path = ROOT / "policy.json"
policy = json.loads(policy_path.read_text())
plans = {sha(path): path for path in (ROOT / "source").rglob("scenarios.json")}
runs = []
responses = 0
for index, run in enumerate(sorted((ROOT / "generation").glob("gemma-*/"))):
    contract = json.loads((run / "contract.json").read_text())
    code = run / "generator-source.py"
    assert sha(code) == contract["generator_sha256"]
    assert sha(policy_path) == contract["policy_sha256"]
    plan_path = plans[contract["plan_sha256"]]
    families = json.loads(plan_path.read_text())["families"]
    spec = importlib.util.spec_from_file_location(f"generation_audit_{index}", code)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    reviewed = []
    for directory in sorted(run.iterdir()):
        if not directory.is_dir() or not directory.name.isdigit():
            continue
        family_index = int(directory.name)
        module.audit_family(directory, families[family_index], family_index, policy)
        review = json.loads((directory / "review.json").read_text())
        assert review["result_sha256"] == sha(directory / "result.json")
        reviewed.append(
            {
                "index": family_index,
                "decision": review["decision"],
                "review_sha256": sha(directory / "review.json"),
            }
        )
    count = len(list(run.rglob("*response.txt")))
    responses += count
    runs.append(
        {
            "run": run.name,
            "contract_sha256": sha(run / "contract.json"),
            "plan": str(plan_path.relative_to(ROOT)),
            "responses": count,
            "reviews": reviewed,
            "accepted_for_training": False,
        }
    )
pilot = ROOT / "generation/single-variant-pilot-20260927"
result = json.loads((pilot / "result.json").read_text())
assert result["request_sha256"] == sha(pilot / "request.json")
assert result["response_sha256"] == sha(pilot / "response.txt")
raw = json.loads((pilot / "response.txt").read_text())["choices"][0]
assert result["message"] == raw["message"]["content"]
assert result["finish_reason"] == raw["finish_reason"]
attempt = json.loads((pilot / "attempt.json").read_text())
assert attempt["script_sha256"] == sha(pilot / "generator-source.py")
responses += 1
report = {
    "passed": True,
    "authoring_responses": responses,
    "runs": runs,
    "pilot": {
        "path": str(pilot.relative_to(ROOT)),
        "result_sha256": sha(pilot / "result.json"),
        "accepted_for_training": False,
    },
    "training_ready": False,
    "reason": "Authorship quality rejected; separate reviewed manual proposal awaits method approval. No trained candidate or final evaluation.",
}
output = ROOT / "generation/evidence-audit-20260927.json"
with output.open("x") as handle:
    json.dump(report, handle, ensure_ascii=False, indent=2)
    handle.write("\n")
print(json.dumps({"passed": True, "authoring_responses": responses, "training_ready": False}))
