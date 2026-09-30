# Trening klasyfikatora Laya

Katalog zawiera kod dostrajania modelu Laya multilingual do klasyfikacji
polskich wiadomości do pięciu działów. Model otrzymuje treść wiadomości,
pytanie i opisy klas z `policy.json`. Nie otrzymuje adresów e-mail ani etykiety
wzorcowej jako części wejścia.

## Dataset

Syntetyczny korpus zawiera 3000 wiadomości, 600 rodzin scenariuszy i 60 grup
semantycznych. Każda rodzina ma pięć wariantów. Rodziny i grupy są rozdzielone
między zbiory; seed podziału wynosi 42.

| Zbiór | Wiadomości | Rodziny | Grupy | Wiadomości na klasę |
| --- | ---: | ---: | ---: | ---: |
| `data/train.jsonl` | 2000 | 400 | 40 | 400 |
| `data/validation.jsonl` | 500 | 100 | 10 | 100 |
| `data/test.jsonl` | 500 | 100 | 10 | 100 |

Klasy: `human_resources`, `payroll`, `help_desk`, `it`, `other`.
Definicje klas znajdują się w `policy.json`, a liczebności i sumy kontrolne
w `data/manifest.json`. `data/acceptance.json` zawiera metadane wymagane przez
trener. Powiązane warianty wiadomości nie stanowią niezależnych próbek.

Trening korzysta wyłącznie z `train`. Walidacja służy do wyboru checkpointu,
a `test` do końcowej oceny. Zbiory `verification/cases.json` i
`verification/benchmark/cases-500.json` są oddzielnymi korpusami regresji;
nie służą do treningu ani wyboru checkpointu. Dane syntetyczne nie zastępują
oceny na rzeczywistej korespondencji.

## Trening

Instrukcję przygotowania środowiska, uruchomienia, walidacji i wznowienia
zawiera [RUNBOOK.md](RUNBOOK.md).

Podstawowe skrypty:

- `train.py`: trening jednej epoki oraz zapis checkpointu i eksportu wag.
- `evaluate.py`: ocena modelu przez Chat Completions.
- `select_checkpoint.py`: wybór checkpointu na podstawie walidacji.
- `freeze_selected.py`: utrwalenie wybranego modelu przed końcową oceną.
- `run_training.py`, `run_runtime.py`: launchery kontenerów lokalnego środowiska.

Domyślny profil Compose `laya` używa modelu bazowego. Dostrojone wagi wymagają
osobnego uruchomienia runtime; nie są częścią repozytorium.
