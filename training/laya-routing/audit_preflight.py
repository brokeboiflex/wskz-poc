"""Read-only evidence audit: no model imports, HTTP, or training."""

import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root = Path(__file__).parent
    summaries = []
    for name in ("preflight-20260927", "preflight-serial-20260927", "preflight-steady-20260927"):
        run = root / "runs" / name
        records = [json.loads(line) for line in (run / "events.jsonl").read_text().splitlines()]
        container = json.loads((run / "container-state.json").read_text())
        inputs = records[0]
        assert inputs["event"] == "inputs"
        assert inputs["train_sha256"] == sha(root / "preflight-train.jsonl")
        assert inputs["policy_sha256"] == sha(root / "policy.json")
        result = (
            json.loads((run / "result.json").read_text())
            if (run / "result.json").exists()
            else None
        )
        if result:
            assert result["script_sha256"] == sha(run / "preflight-source.py")
            assert result["trained_weights_saved"] is False
            assert result["production_changed"] is False
        state = container["state"]
        assert state["Status"] == "exited" and not state["Running"]
        assert state["ExitCode"] == (137 if state["OOMKilled"] else 0)
        steps = [r for r in records if r["event"] == "optimizer_step"]
        microbatches = [r for r in records if r["event"] == "train_microbatch"]
        source_files = [run / "preflight-source.py"]
        if (run / "optimizer-source.py").exists():
            source_files.append(run / "optimizer-source.py")
        summaries.append(
            {
                "run": name,
                "oom_killed": state["OOMKilled"],
                "exit_code": state["ExitCode"],
                "completed_optimizer_steps": len(steps),
                "completed_microbatches": len(microbatches),
                "last_event": records[-1]["event"],
                "memory_limit_bytes": container["memory"],
                "max_recorded_rss_bytes": max(r.get("peak_rss_bytes", 0) for r in records),
                "disk_gate_passed": result["disk_gate_passed"] if result else None,
                "sources": {p.name: sha(p) for p in source_files},
            }
        )
    assert [r["completed_optimizer_steps"] for r in summaries] == [0, 1, 1]
    assert [r["oom_killed"] for r in summaries] == [True, False, True]
    print(
        json.dumps(
            {
                "evidence_audit_passed": True,
                "training_ready": False,
                "reason": "Steady-state OOM and failed disk budget",
                "runs": summaries,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
