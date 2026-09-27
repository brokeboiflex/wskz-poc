"""One observed local Gemma request at a time, with explicit review and resumable evidence."""

import argparse
import hashlib
import json
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

STYLES = ("short", "context", "resolved_history", "quotation", "informal")
MODEL = "gemma4:e2b"
ENDPOINT = "http://127.0.0.1:18092/v1/chat/completions"
SYSTEM = """Piszesz syntetyczne wiadomości po polsku do badania klasyfikacji zgłoszeń.
Nie klasyfikujesz istniejących wiadomości. Tworzysz nowe teksty na podstawie jednej definicji scenariusza.
Zwróć wyłącznie obiekt JSON messages z dokładnie pięcioma obiektami style/message.
Każdy tekst ma wyrażać ten sam główny zamiar ze scenariusza, ale własnymi słowami i z innym naturalnym kontekstem.
Nie zmieniaj rodzaju sprawy, nie dodawaj nowej aktywnej prośby do innego działu.
Nie ujawniaj etykiety, nazwy docelowego działu, numeru scenariusza ani wskazówki dla klasyfikatora w wiadomości.
Nie pisz uzasadnienia poprawnej odpowiedzi. Nie używaj szablonu z podmienionymi nazwami.
Warianty w kolejności:
short: krótka naturalna prośba, 6-18 słów;
context: prośba z konkretnym kontekstem, 20-40 słów;
resolved_history: zakończony wcześniejszy problem jako tło, wyraźna aktualna sprawa ze scenariusza, 25-50 słów;
quotation: krótki cytat lub przekazana informacja i aktualny zamiar, 25-50 słów;
informal: naturalne skróty lub drobna literówka, 10-25 słów.
Jeśli scenariusz oznacza brak prośby lub brak informacji, zachowaj ten brak; nie wymyślaj konkretnego zadania tylko po to, by wydłużyć tekst.
Nie powtarzaj mechanicznie zwrotu 'nie chodzi o'. Używaj różnych zdań, nie jednego schematu.
Wszystkie osoby i szczegóły są fikcyjne. Nie umieszczaj prawdziwych adresów, danych kontaktowych ani sekretów.
"""


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def new_json(path, value):
    with path.open("x") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def request_for(family, policy, index):
    schema = {
        "type": "object",
        "properties": {
            "messages": {
                "type": "array",
                "minItems": 5,
                "maxItems": 5,
                "items": {
                    "type": "object",
                    "properties": {
                        "style": {"type": "string", "enum": list(STYLES)},
                        "message": {"type": "string"},
                    },
                    "required": ["style", "message"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["messages"],
        "additionalProperties": False,
    }
    content = {
        "znaczenie_dzialow": policy["criteria"],
        "docelowe_znaczenie": policy["criteria"][family["label"]],
        "scenariusz": family["scenario"],
    }
    return {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": json.dumps(content, ensure_ascii=False)},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": "authored_messages", "strict": True, "schema": schema},
        },
        "temperature": 0.7,
        "top_p": 0.9,
        "seed": 42 + index,
        "reasoning_effort": "none",
        "max_tokens": 1000,
        "stream": False,
    }


def parse(body):
    response = json.loads(body)
    choices = response["choices"]
    if len(choices) != 1 or choices[0]["finish_reason"] != "stop":
        raise ValueError("Generation did not finish normally")
    payload = json.loads(choices[0]["message"]["content"])
    if set(payload) != {"messages"} or len(payload["messages"]) != 5:
        raise ValueError("Exactly five messages required")
    texts = []
    for style, row in zip(STYLES, payload["messages"], strict=True):
        if set(row) != {"style", "message"} or row["style"] != style:
            raise ValueError("Unexpected style or fields")
        message = row["message"]
        if not isinstance(message, str) or not message.strip() or len(message) > 2000:
            raise ValueError("Empty/oversized message")
        if any(label in message.lower() for label in ("human_resources", "help_desk", "payroll")):
            raise ValueError("Internal label leaked into message")
        texts.append(message)
    if len({text.casefold().strip() for text in texts}) != 5:
        raise ValueError("Duplicate variants")
    return payload


def audit_family(directory, family, index, policy):
    result = json.loads((directory / "result.json").read_text())
    request = directory / "request.json"
    response = directory / "response.txt"
    attempt = json.loads((directory / "attempt.json").read_text())
    if (
        json.loads(request.read_text()) != request_for(family, policy, index)
        or result["request_sha256"] != sha(request)
        or result["response_sha256"] != sha(response)
        or attempt["index"] != index
        or attempt["family"] != family
    ):
        raise ValueError("Generation evidence chain mismatch")
    payload, error = None, None
    try:
        if result["http_status"] != 200:
            raise ValueError(f"HTTP {result['http_status']}")
        payload = parse(response.read_text())
    except (ValueError, KeyError, TypeError, IndexError) as exc:
        error = str(exc)
    if result.get("parse_error") != error or result.get("messages") != (
        payload["messages"] if payload else None
    ):
        raise ValueError("Saved messages differ from raw generation")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("step", "review", "status"))
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--proof", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--decision", choices=("accept", "reject"))
    parser.add_argument("--note")
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text())
    policy = json.loads(args.policy.read_text())
    proof = json.loads(args.proof.read_text())
    review_path = args.plan.with_name("scenarios-review.json")
    plan_review = json.loads(review_path.read_text())
    if plan_review.get("approved_for_generation") is not True or plan_review["plan_sha256"] != sha(
        args.plan
    ):
        raise ValueError("Independent review of the exact scenario plan is required")
    runtime_proof_path = args.proof.with_name("runtime-proof.json")
    runtime_proof = json.loads(runtime_proof_path.read_text())
    if plan["policy_sha256"] != sha(args.policy) or len(plan["families"]) != 600:
        raise ValueError("Frozen scenario plan/policy mismatch")
    if proof["model"] != MODEL or proof.get("layers_verified") is not True:
        raise ValueError("Verified local model assets are required")
    contract = {
        "plan_sha256": sha(args.plan),
        "policy_sha256": sha(args.policy),
        "proof_sha256": sha(args.proof),
        "plan_review_sha256": sha(review_path),
        "runtime_proof_sha256": sha(runtime_proof_path),
        "generator_sha256": sha(__file__),
        "endpoint": ENDPOINT,
        "model": MODEL,
        "system_sha256": hashlib.sha256(SYSTEM.encode()).hexdigest(),
    }
    args.output.mkdir(parents=True, exist_ok=True)
    path = args.output / "contract.json"
    if not path.exists():
        new_json(path, contract)
    if json.loads(path.read_text()) != contract:
        raise ValueError("Generation contract changed; do not silently resume")
    families = plan["families"]
    for index, family in enumerate(families):
        directory = args.output / f"{index:03d}"
        result_path = directory / "result.json"
        review_path = directory / "review.json"
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
                if args.decision is None or not args.note or len(args.note.strip()) < 30:
                    raise ValueError("Explicit substantive review required")
                if args.decision == "accept" and result.get("parse_error"):
                    raise ValueError("Cannot accept malformed generation")
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
            print(json.dumps({"accepted_families": index, "next": family}))
            return
        if directory.exists():
            raise ValueError("Unresolved prior attempt; no automatic retry")
        live = json.loads(
            subprocess.check_output(["docker", "inspect", "wskz-laya-data-gemma"], text=True)
        )[0]
        if (
            not live["State"]["Running"]
            or live["Id"] != runtime_proof["container_id"]
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
            raise ValueError("Live Gemma server does not match verified model provisioning")
        directory.mkdir()
        request = request_for(family, policy, index)
        new_json(directory / "request.json", request)
        new_json(
            directory / "attempt.json", {"index": index, "family": family, "time": time.time()}
        )
        start = time.monotonic()
        wire = urllib.request.Request(
            ENDPOINT,
            data=json.dumps(request, ensure_ascii=False).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(wire, timeout=300) as response:
                status, body = response.status, response.read().decode()
        except urllib.error.HTTPError as exc:
            status, body = exc.code, exc.read().decode()
        except (OSError, TimeoutError) as exc:
            new_json(
                directory / "transport-error.json",
                {"type": type(exc).__name__, "message": str(exc)},
            )
            raise
        with (directory / "response.txt").open("x") as handle:
            handle.write(body)
        result = {
            "http_status": status,
            "seconds": time.monotonic() - start,
            "response_sha256": sha(directory / "response.txt"),
            "request_sha256": sha(directory / "request.json"),
        }
        try:
            if status != 200:
                raise ValueError(f"HTTP {status}")
            result.update(parse(body))
        except (ValueError, KeyError, TypeError, IndexError) as exc:
            result["parse_error"] = str(exc)
        new_json(result_path, result)
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
