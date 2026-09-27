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
Zwróć wyłącznie obiekt JSON z pięcioma polami: short, context, resolved_history, quotation, informal. Pola short, context, resolved_history i informal zawierają teksty. Pole quotation ma dwa pola: quote (dosłowne słowa rozmówcy) oraz message (dalsza wypowiedź autora).
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
Każda wiadomość będzie czytana OSOBNO, bez scenariusza i pozostałych wariantów. Nawet krótka i potoczna musi zawierać fakty pozwalające rozpoznać konkretną sprawę. Nie usuwaj dziedziny sprawy przy skracaniu.
Wszystkie osoby i szczegóły są fikcyjne. Nie umieszczaj prawdziwych adresów, danych kontaktowych ani sekretów.
"""


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def new_json(path, value):
    with path.open("x") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def request_for(family, policy, index):
    forms = {
        "short": "Jedno krótkie zdanie, 6-18 słów.",
        "context": "Trzy zdania: konkretna sytuacja, jej skutek i aktualna prośba. 25-45 słów.",
        "resolved_history": "Trzy zdania. Najpierw inna wcześniejsza sprawa wyraźnie JUŻ ROZWIĄZANA, następnie aktualna sytuacja ze scenariusza i prośba. 30-55 słów. Nie proś ponownie o rozwiązanie starej sprawy.",
        "quotation": "Wstaw dosłowny krótki cytat w cudzysłowie (np. słowa rozmówcy lub treść powiadomienia), następnie opisz aktualny zamiar ze scenariusza. 25-45 słów.",
        "informal": "Potoczna wiadomość do współpracownika, skróty lub drobna literówka, 10-25 słów.",
    }
    schema = {
        "type": "object",
        "properties": {
            key: {"type": "string", "description": value} for key, value in forms.items()
        },
        "required": list(STYLES),
        "additionalProperties": False,
    }
    schema["properties"]["quotation"] = {
        "type": "object",
        "description": forms["quotation"],
        "properties": {
            "quote": {
                "type": "string",
                "description": "Dosłowne słowa rozmówcy lub powiadomienia, bez cudzysłowu.",
            },
            "message": {
                "type": "string",
                "description": "Aktualny zamiar autora po przytoczonym cytacie.",
            },
        },
        "required": ["quote", "message"],
        "additionalProperties": False,
    }
    content = {
        "znaczenie_dzialow": policy["criteria"],
        "docelowe_znaczenie": policy["criteria"][family["label"]],
        "scenariusz": family["scenario"],
        "najwazniejsze": "Każdy z pięciu tekstów musi samodzielnie zawierać rodzaj sprawy ze scenariusza. Nie wolno pozostawić ogólnej rozmowy, zmiany, problemu, spotkania itp. bez podania czego dotyczy. Nie odsyłaj do poprzedniej wiadomości. Styl informal ma być potoczny, ale kompletny znaczeniowo.",
        "obowiazkowe_formy": forms,
        "kontrola": "Sprawdź przed odpowiedzią: historia ma zakończoną dawną sprawę; quotation zawiera rzeczywisty cytat; wszystkie teksty zachowują scenariusz. Przy scenariuszu bez informacji lub bez prośby zachowaj ten brak, zamiast dopisywać zadanie.",
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
    if set(payload) != set(STYLES):
        raise ValueError("Exactly five messages required")
    quotation = payload["quotation"]
    if (
        not isinstance(quotation, dict)
        or set(quotation) != {"quote", "message"}
        or any(not isinstance(value, str) or not value.strip() for value in quotation.values())
    ):
        raise ValueError("Quotation requires authored quote and current message")
    payload["quotation"] = f"„{quotation['quote']}” {quotation['message']}"
    texts = []
    for style in STYLES:
        message = payload[style]
        if not isinstance(message, str) or not message.strip() or len(message) > 2000:
            raise ValueError("Empty/oversized message")
        if any(label in message.lower() for label in ("human_resources", "help_desk", "payroll")):
            raise ValueError("Internal label leaked into message")
        texts.append(message)
    if len({text.casefold().strip() for text in texts}) != 5:
        raise ValueError("Duplicate variants")
    return {"messages": [{"style": style, "message": payload[style]} for style in STYLES]}


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
    parser.add_argument("--start-index", type=int, default=0)
    args = parser.parse_args()
    if not 0 <= args.start_index < 600:
        raise ValueError("Invalid explicit starting family")
    plan = json.loads(args.plan.read_text())
    policy = json.loads(args.policy.read_text())
    proof = json.loads(args.proof.read_text())
    review_path = args.plan.with_name("scenarios-review.json")
    plan_review = json.loads(review_path.read_text())
    if plan_review.get("approved_for_generation") is not True or plan_review["plan_sha256"] != sha(
        args.plan
    ):
        raise ValueError("Independent review of the exact scenario plan is required")
    exclusion_path = args.plan.with_name("exclusion-scenario-review-v3.json")
    exclusion_review = json.loads(exclusion_path.read_text())
    if exclusion_review.get("approved_for_generation") is not True or exclusion_review.get(
        "plan_sha256"
    ) != sha(args.plan):
        raise ValueError("Independent exclusion review of the exact plan is required")
    runtime_proof_path = args.proof.with_name("runtime-proof.json")
    runtime_proof = json.loads(runtime_proof_path.read_text())
    if plan["policy_sha256"] != sha(args.policy) or len(plan["families"]) != 600:
        raise ValueError("Frozen scenario plan/policy mismatch")
    if proof["model"] != MODEL or proof.get("layers_verified") is not True:
        raise ValueError("Verified local model assets are required")
    contract = {
        "start_index": args.start_index,
        "plan_sha256": sha(args.plan),
        "policy_sha256": sha(args.policy),
        "proof_sha256": sha(args.proof),
        "plan_review_sha256": sha(review_path),
        "exclusion_review_sha256": sha(exclusion_path),
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
        (args.output / "generator-source.py").write_bytes(Path(__file__).read_bytes())
    if json.loads(path.read_text()) != contract:
        raise ValueError("Generation contract changed; do not silently resume")
    families = plan["families"]
    for index in range(args.start_index, len(families)):
        family = families[index]
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
            print(
                json.dumps(
                    {
                        "accepted_families": index - args.start_index,
                        "next_index": index,
                        "next": family,
                    }
                )
            )
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
    print(json.dumps({"complete": True, "accepted_families": 600 - args.start_index}))


if __name__ == "__main__":
    main()
