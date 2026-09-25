"""Build/check a frozen synthetic corpus without network access or model inference."""

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parent
RECIPIENTS = {
    "human_resources": "human-resources@example.com",
    "payroll": "kadry@example.com",
    "help_desk": "help-desk@example.com",
    "it": "it@example.com",
    "other": "other@example.com",
}

# Closed side issues intentionally differ from the current scenario's department.
# They must never introduce a second unresolved request or a suggested destination.
CLOSED = {
    "human_resources": [
        "W poprzednim wątku wyjaśniono różnicę na moim pasku wynagrodzenia. "
        "Poprawne rozliczenie jest już dostępne, a sprawa została zamknięta.",
        "Wcześniej nie działał monitor na moim biurku. Urządzenie zostało wymienione, "
        "obraz jest poprawny i tamto zgłoszenie zostało zamknięte.",
        "Wczorajsza przerwa w dostępie do serwera plików została usunięta. "
        "Wszystkie zespoły potwierdziły poprawne działanie usługi.",
        "Zamówione wcześniej zaświadczenie o zarobkach zostało już wystawione "
        "i odebrane. Nie wymaga korekty ani dodatkowego działania.",
    ],
    "payroll": [
        "Termin mojej rozmowy rozwojowej został już uzgodniony. "
        "Organizator potwierdził spotkanie i ten wątek jest zakończony.",
        "Hasło do konta zostało wczoraj zresetowane i logowanie działa. "
        "Rozwiązanie problemu i zamknięcie zgłoszenia zostały potwierdzone.",
        "Awaria sieci w całym biurze została usunięta. "
        "Łączność jest stabilna i nie potrzebujemy dalszej interwencji w tej sprawie.",
        "Zapisy na warsztat komunikacji są zakończone. Miejsce jest potwierdzone "
        "i materiały przekazane; nie potrzeba już pomocy organizacyjnej.",
    ],
    "help_desk": [
        "Rozliczenie mojej wypłaty zostało sprawdzone i jest prawidłowe. "
        "Wyjaśnienie jest już dostępne, więc tamta sprawa jest zakończona.",
        "Spotkanie z mentorem zostało już zaplanowane i odbyło się zgodnie z ustaleniami. "
        "Nie potrzebuję kolejnej rozmowy dotyczącej jego organizacji.",
        "Przerwa w działaniu centralnego serwera została usunięta. "
        "Monitoring i pozostałe zespoły potwierdzają, że usługi działają poprawnie.",
        "Kopia umowy została odebrana, a zgodność dokumentu potwierdzona. "
        "Nie trzeba niczego uzupełniać w zakończonej sprawie dokumentacji zatrudnienia.",
    ],
    "it": [
        "Stary problem z myszą przy moim biurku rozwiązano przez wymianę urządzenia. "
        "Nowa mysz działa i nie wymaga dalszego sprawdzania.",
        "Pomyłka w moim saldzie urlopu została wyjaśniona. "
        "W ewidencji są już prawidłowe dane, a poprzednie zgłoszenie jest zamknięte.",
        "Warsztat dla nowych liderów zakończył się w ubiegłym tygodniu. "
        "Materiały są już przekazane i nie potrzeba pomocy przy jego organizacji.",
        "Lokalny problem z drukowaniem mojego dokumentu został rozwiązany. "
        "Wydruk odebrano i nie ma potrzeby ponawiania tamtego zgłoszenia.",
    ],
    "other": [
        "Mój wcześniejszy wniosek o urlop został już poprawnie rozliczony. "
        "Nie potrzebuję żadnych dalszych zmian w saldzie ani dokumentacji.",
        "Komputer został naprawiony i działa poprawnie. "
        "Zakończenie tamtego zgłoszenia technicznego zostało potwierdzone.",
        "Udział w szkoleniu został już potwierdzony i przekazano komplet informacji. "
        "Tamta sprawa organizacyjna jest zamknięta.",
        "Awaria firmowej sieci została usunięta. "
        "Nie występują już żadne objawy i nie ma potrzeby dalszej interwencji.",
    ],
}

STYLES = (
    "quoted_history",
    "resolved_preface",
    "resolved_postscript",
    "conversation_history",
    "forwarded_history",
)


def contextualize(message, closed, style):
    if style == "quoted_history":
        return (
            f"Dzień dobry, poniżej przesyłam aktualną wiadomość.\n\n{message}\n\n"
            f"> Archiwalna korespondencja, sprawa zakończona:\n> {closed}\n\n"
            "Cytat pozostawiam dla ciągłości korespondencji. Nie wznawiam starego zgłoszenia."
        )
    if style == "resolved_preface":
        return (
            f"Najpierw potwierdzenie zamknięcia poprzedniego wątku: {closed}\n\n"
            f"Osobna, aktualna wiadomość:\n{message}"
        )
    if style == "resolved_postscript":
        return f"{message}\n\nPS. {closed} Ta dopisana informacja nie jest nową prośbą."
    if style == "conversation_history":
        return (
            "Historia wcześniejszej rozmowy:\n"
            f"Ja: {closed}\n"
            "Odpowiedź: Dziękujemy za potwierdzenie zakończenia tamtej sprawy.\n\n"
            f"Moja obecna wiadomość dotyczy osobnej kwestii:\n{message}"
        )
    return (
        f"Przekazuję nową wiadomość w ramach tej samej korespondencji:\n\n{message}\n\n"
        f"--- Przekazany stary wątek: ZAMKNIĘTY ---\n{closed}\n"
        "--- Koniec archiwum ---\n"
        "Proszę nie otwierać ponownie sprawy opisanej w archiwum."
    )


def build_cases():
    cases = []
    scenarios = set()
    expected_files = {f"{department}.txt" for department in RECIPIENTS}
    if {path.name for path in (ROOT / "scenarios").glob("*.txt")} != expected_files:
        raise ValueError("unexpected or missing scenario source file")
    for department, recipient in RECIPIENTS.items():
        lines = (ROOT / "scenarios" / f"{department}.txt").read_text().splitlines()
        if len(lines) != 50:
            raise ValueError(f"{department}: expected 50 scenarios, got {len(lines)}")
        for index, line in enumerate(lines):
            slug, rationale, message = line.split(" | ", 2)
            message = message.replace("\\n", "\n")
            if not re.fullmatch(r"[a-z][a-z0-9-]+", slug) or not rationale.strip():
                raise ValueError(f"invalid source metadata: {department}/{slug}")
            scenario = f"{department}/{slug}"
            if scenario in scenarios:
                raise ValueError(f"duplicate scenario: {scenario}")
            scenarios.add(scenario)
            style = STYLES[index % len(STYLES)]
            closed = CLOSED[department][index % len(CLOSED[department])]
            for variant, body in (
                ("base", message),
                (style, contextualize(message, closed, style)),
            ):
                cases.append(
                    {
                        "id": f"{scenario}/{variant}",
                        "scenario_id": scenario,
                        "variant": variant,
                        "language": "pl",
                        "department": department,
                        "recipient": recipient,
                        "rationale": rationale,
                        "message": body,
                    }
                )
    return cases


def validate(cases):
    if len(cases) != 500:
        raise ValueError("expected exactly 500 cases")
    if Counter(case["department"] for case in cases) != dict.fromkeys(RECIPIENTS, 100):
        raise ValueError("unbalanced departments")
    ids = {case["id"] for case in cases}
    texts = {" ".join(case["message"].casefold().split()) for case in cases}
    if len(ids) != 500 or len(texts) != 500:
        raise ValueError("duplicate IDs or normalized messages")
    pairs = Counter(case["scenario_id"] for case in cases)
    if len(pairs) != 250 or set(pairs.values()) != {2}:
        raise ValueError("invalid scenario pairs")
    for case in cases:
        if case["recipient"] != RECIPIENTS[case["department"]]:
            raise ValueError(f"label mismatch: {case['id']}")
        body = case["message"]
        if not 1 <= len(body) <= 4000:
            raise ValueError(f"outside API length limit: {case['id']}")
        # Reserve ample space below the adapter's 7000-byte choice payload budget.
        if len(body.encode()) > 5000:
            raise ValueError(f"insufficient adapter metadata headroom: {case['id']}")
        if any(address in body for address in RECIPIENTS.values()):
            raise ValueError(f"leaked answer address: {case['id']}")


def serialize(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def length_stats(values):
    return {"min": min(values), "median": median(values), "max": max(values)}


def report(cases, payload):
    sources = {}
    for path in sorted((ROOT / "scenarios").glob("*.txt")):
        sources[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return {
        "dataset": "wskz-synthetic-pl-500-v1",
        "provenance": "synthetic, authored by Codex; no imported customer emails",
        "intended_use": "evaluation only; paired cases are not independent observations",
        "cases": len(cases),
        "scenario_families": len({case["scenario_id"] for case in cases}),
        "sha256": hashlib.sha256(payload.encode()).hexdigest(),
        "source_sha256": sources,
        "departments": dict(Counter(case["department"] for case in cases)),
        "variants": dict(Counter(case["variant"] for case in cases)),
        "characters": length_stats([len(case["message"]) for case in cases]),
        "words_whitespace": length_stats([len(case["message"].split()) for case in cases]),
        "utf8_bytes": length_stats([len(case["message"].encode()) for case in cases]),
        "model_evaluation": "not run",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="compare without writing")
    args = parser.parse_args()
    cases = build_cases()
    validate(cases)
    payload = serialize(cases)
    summary = report(cases, payload)
    for filename, content in (
        ("cases-500.json", payload),
        ("manifest.json", serialize(summary)),
    ):
        path = ROOT / filename
        if args.check:
            if not path.exists() or path.read_text() != content:
                raise SystemExit(f"{filename} differs; review source and regenerate intentionally")
        else:
            path.write_text(content)
    print(serialize(summary), end="")


if __name__ == "__main__":
    main()
