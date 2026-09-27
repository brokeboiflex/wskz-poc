"""Observed family authoring: five simple Chat Completions, then mandatory family review."""

import argparse
import hashlib
import json
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

MODEL = "gemma4:e2b"
ENDPOINT = "http://127.0.0.1:18092/v1/chat/completions"
STYLES = ("short", "context", "resolved_history", "quotation", "informal")
FORMS = (
    "Jedno krótkie zdanie, 6-18 słów. Nazwij konkretne zadanie i jego dziedzinę.",
    "Trzy naturalne zdania, 25-45 słów: sytuacja, jej znaczenie i prośba o wykonanie dokładnie zadania ze scenariusza.",
    "30-55 słów. Najpierw wspomnij konkretny DAWNY problem, różny od bieżącego zadania, oraz wyraźnie powiedz jak został już rozwiązany. Potem poproś o aktualne zadanie ze scenariusza. Dawna sprawa jest zakończona i nie wymaga działania. Unikaj ogólnika 'wcześniej omówiliśmy kwestie'.",
    "25-45 słów. Przytocz krótkie cudze słowa w cudzysłowie jako tło sprawy, następnie sformułuj własną aktualną prośbę. Cytat i prośba mają różne brzmienie. Zachowaj dokładnie zadanie ze scenariusza.",
    "Potoczna wiadomość do współpracownika, 10-25 słów, może zawierać skrót lub drobną literówkę. Zachowaj samodzielny pełny kontekst sprawy i konkretne zadanie.",
)
SYSTEM = """Napisz jedną naturalną wiadomość po polsku z prośbą o załatwienie podanej sprawy.
Zachowaj dokładnie aktualne zadanie ze scenariusza. Warunki opisane jako spełnione nie są nowym zadaniem.
Zaadresuj prośbę do osoby mającej ją obsłużyć. Nie odpowiadaj na nią, nie pisz zaproszenia do kandydata i nie zmieniaj rekrutacji na szkolenie.
Nie dodawaj zadań, które wynikają tylko z ogólnego opisu kategorii. Każda wiadomość jest samodzielna.
Nie wymieniaj docelowego działu, etykiety ani klasyfikacji. Zwróć wyłącznie treść wiadomości, bez tytułu, podpisu i komentarza.
Jeśli scenariusz celowo nie zawiera prośby lub informacji, zachowaj ten brak zamiast dopisywać zadanie.
Osoby i szczegóły fikcyjne, bez prawdziwych kontaktów i sekretów.
"""


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def new_json(path, value):
    with path.open("x") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def request_for(family, policy, index, variant):
    return {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": SYSTEM
                + "\nZnaczenie kategorii wyłącznie do kontroli granic: "
                + json.dumps(policy["criteria"], ensure_ascii=False),
            },
            {
                "role": "user",
                "content": "Bieżące zadanie: "
                + family["scenario"]
                + "\nForma wypowiedzi: "
                + FORMS[variant],
            },
        ],
        "temperature": 0.3,
        "top_p": 0.9,
        "seed": 42 + 5 * index + variant,
        "reasoning_effort": "none",
        "max_tokens": 300,
        "stream": False,
    }


def parse(body):
    choices = json.loads(body)["choices"]
    if len(choices) != 1 or choices[0]["finish_reason"] != "stop":
        raise ValueError("Generation did not finish normally")
    message = choices[0]["message"]["content"]
    if not isinstance(message, str) or not message.strip() or len(message) > 2000:
        raise ValueError("Empty/oversized message")
    if any(label in message.lower() for label in ("human_resources", "help_desk", "payroll")):
        raise ValueError("Internal label leaked")
    return message


def audit_family(directory, family, index, policy):
    result = json.loads((directory / "result.json").read_text())
    attempt = json.loads((directory / "attempt.json").read_text())
    if attempt["index"] != index or attempt["family"] != family:
        raise ValueError("Family identity mismatch")
    messages, error, records = [], None, []
    for variant, style in enumerate(STYLES):
        request = directory / f"{variant}.request.json"
        response = directory / f"{variant}.response.txt"
        record_path = directory / f"{variant}.result.json"
        if not record_path.exists():
            error = f"Incomplete variant {variant}"
            break
        record = json.loads(record_path.read_text())
        if (
            json.loads(request.read_text()) != request_for(family, policy, index, variant)
            or record["request_sha256"] != sha(request)
            or record["response_sha256"] != sha(response)
        ):
            raise ValueError("Generation evidence chain mismatch")
        records.append({"variant": variant, "result_sha256": sha(record_path)})
        try:
            if record["http_status"] != 200:
                raise ValueError(f"HTTP {record['http_status']}")
            message = parse(response.read_text())
            if record.get("message") != message or record.get("parse_error"):
                raise ValueError("Saved message differs from raw generation")
            messages.append({"style": style, "message": message})
        except (ValueError, KeyError, TypeError, IndexError) as exc:
            error = str(exc)
            if record.get("parse_error") != error:
                raise ValueError("Saved parse failure differs") from exc
            break
    if error is None and len({row["message"].casefold().strip() for row in messages}) != 5:
        error = "Duplicate variants"
    if (
        result.get("parse_error") != error
        or result["messages"] != messages
        or result["variants"] != records
    ):
        raise ValueError("Family summary differs from raw variants")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("step", "review", "status"))
    for name in ("plan", "policy", "proof", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--decision", choices=("accept", "reject"))
    parser.add_argument("--note")
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text())
    policy = json.loads(args.policy.read_text())
    proof = json.loads(args.proof.read_text())
    plan_review = args.plan.with_name("scenarios-review.json")
    exclusion_review = args.plan.with_name("exclusion-scenario-review-v3.json")
    for path in (plan_review, exclusion_review):
        review = json.loads(path.read_text())
        if review.get("approved_for_generation") is not True or review["plan_sha256"] != sha(
            args.plan
        ):
            raise ValueError("Independent plan/exclusion review required")
    if (
        plan["policy_sha256"] != sha(args.policy)
        or len(plan["families"]) != 600
        or proof.get("layers_verified") is not True
        or proof["model"] != MODEL
    ):
        raise ValueError("Plan/policy/model provisioning differs")
    runtime_path = args.proof.with_name("runtime-proof.json")
    runtime = json.loads(runtime_path.read_text())
    contract = {
        "plan_sha256": sha(args.plan),
        "policy_sha256": sha(args.policy),
        "proof_sha256": sha(args.proof),
        "runtime_sha256": sha(runtime_path),
        "plan_review_sha256": sha(plan_review),
        "exclusion_review_sha256": sha(exclusion_review),
        "generator_sha256": sha(__file__),
        "endpoint": ENDPOINT,
        "model": MODEL,
        "requests_per_observed_family": 5,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    contract_path = args.output / "contract.json"
    if not contract_path.exists():
        new_json(contract_path, contract)
        (args.output / "generator-source.py").write_bytes(Path(__file__).read_bytes())
    if json.loads(contract_path.read_text()) != contract:
        raise ValueError("Generation contract changed")
    for index, family in enumerate(plan["families"]):
        directory = args.output / f"{index:03d}"
        result_path, review_path = directory / "result.json", directory / "review.json"
        result = audit_family(directory, family, index, policy) if result_path.exists() else None
        if review_path.exists():
            review = json.loads(review_path.read_text())
            if review["result_sha256"] != sha(result_path):
                raise ValueError("Reviewed result changed")
            if review["decision"] != "accept":
                print(
                    json.dumps({"blocked_rejection": index, "review": review}, ensure_ascii=False)
                )
                return
            continue
        if result_path.exists():
            if args.command == "review":
                if not args.decision or not args.note or len(args.note.strip()) < 30:
                    raise ValueError("Explicit substantive review required")
                if args.decision == "accept" and result.get("parse_error"):
                    raise ValueError("Cannot accept malformed/incomplete generation")
                new_json(
                    review_path,
                    {
                        "decision": args.decision,
                        "note": args.note,
                        "result_sha256": sha(result_path),
                        "time": time.time(),
                    },
                )
                print(json.dumps({"reviewed": index, "decision": args.decision}))
                return
            print(
                json.dumps(
                    {"review_required": index, "family": family, "result": result},
                    ensure_ascii=False,
                )
            )
            return
        if args.command != "step":
            print(json.dumps({"accepted_families": index, "next": family}, ensure_ascii=False))
            return
        if directory.exists():
            raise ValueError("Unresolved prior attempt; no automatic retry")
        live = json.loads(
            subprocess.check_output(["docker", "inspect", "wskz-laya-data-gemma"], text=True)
        )[0]
        if (
            not live["State"]["Running"]
            or live["Id"] != runtime["container_id"]
            or live["Image"] != proof["server_image"]
            or not any(
                m.get("Name") == "message-router_ollama-models"
                and m["Destination"] == "/root/.ollama"
                and m["RW"] is False
                for m in live["Mounts"]
            )
            or live["NetworkSettings"]["Ports"].get("11434/tcp")
            != [{"HostIp": "127.0.0.1", "HostPort": "18092"}]
        ):
            raise ValueError("Live server differs from verified provisioning")
        directory.mkdir()
        new_json(
            directory / "attempt.json", {"index": index, "family": family, "time": time.time()}
        )
        messages, records, error = [], [], None
        for variant, style in enumerate(STYLES):
            payload = request_for(family, policy, index, variant)
            request_path = directory / f"{variant}.request.json"
            response_path = directory / f"{variant}.response.txt"
            new_json(request_path, payload)
            start = time.monotonic()
            wire = urllib.request.Request(
                ENDPOINT,
                data=json.dumps(payload, ensure_ascii=False).encode(),
                headers={"Content-Type": "application/json"},
            )
            try:
                with urllib.request.urlopen(wire, timeout=180) as response:
                    status, body = response.status, response.read().decode()
            except urllib.error.HTTPError as exc:
                status, body = exc.code, exc.read().decode()
            except (OSError, TimeoutError) as exc:
                new_json(
                    directory / f"{variant}.transport-error.json",
                    {"type": type(exc).__name__, "message": str(exc)},
                )
                raise
            response_path.write_text(body)
            record = {
                "http_status": status,
                "seconds": time.monotonic() - start,
                "request_sha256": sha(request_path),
                "response_sha256": sha(response_path),
            }
            try:
                if status != 200:
                    raise ValueError(f"HTTP {status}")
                record["message"] = parse(body)
                messages.append({"style": style, "message": record["message"]})
            except (ValueError, KeyError, TypeError, IndexError) as exc:
                error = record["parse_error"] = str(exc)
            record_path = directory / f"{variant}.result.json"
            new_json(record_path, record)
            records.append({"variant": variant, "result_sha256": sha(record_path)})
            if error:
                break
        if error is None and len({row["message"].strip().casefold() for row in messages}) != 5:
            error = "Duplicate variants"
        result = {"messages": messages, "variants": records, "parse_error": error}
        new_json(result_path, result)
        audit_family(directory, family, index, policy)
        print(
            json.dumps(
                {"review_required": index, "family": family, "result": result}, ensure_ascii=False
            ),
            flush=True,
        )
        return
    print(json.dumps({"complete": True, "accepted_families": 600}))


if __name__ == "__main__":
    main()
