"""Compact operator view; review advances only with an explicit operator note."""

import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", type=Path, required=True)
    parser.add_argument("--note")
    parser.add_argument("--report", action="store_true")
    args = parser.parse_args()
    session = json.loads(args.session.read_text())
    root = Path(__file__).resolve().parent
    common = []
    for key, value in session.items():
        common += ["--" + key, str(value)]
    prefix = [sys.executable, str(root / "evaluate.py")]
    if args.note:
        subprocess.run(prefix + ["review", *common, "--note", args.note], check=True)
    output = Path(session["output"])
    before = len(list(output.glob("*.result.json"))) if output.exists() else 0
    result = subprocess.run(
        prefix + ["report" if args.report else "run", *common],
        text=True,
        capture_output=True,
    )
    if result.returncode:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        raise SystemExit(result.returncode)
    if args.report:
        report = json.loads(result.stdout)
        print(json.dumps({k: report[k] for k in ("count", "accuracy", "macro_f1")}))
        return
    files = sorted(output.glob("*.result.json"))
    routes = Counter()
    for path in files[before:]:
        row = json.loads(path.read_text())
        routes[f"{row['expected']}->{row['predicted']}"] += 1
        if not row["correct"]:
            print(json.dumps({k: row[k] for k in ("id", "expected", "predicted", "error")}))
            print(row["message"])
            print(path.with_name(path.name.replace(".result.json", ".response.txt")).read_text())
    if files:
        last = files[-1]
        if json.loads(last.read_text())["correct"]:
            raw = json.loads(
                last.with_name(last.name.replace(".result.json", ".response.txt")).read_text()
            )
            choice = raw["choices"][0]
            print(
                "Raw last call:",
                choice["finish_reason"],
                choice["message"]["tool_calls"][0]["function"],
            )
    print(json.dumps({"range": [before, len(files) - 1], "routes": routes}))


if __name__ == "__main__":
    main()
