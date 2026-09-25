> Aktualizacja po przeglądzie neutralności dostawcy: sekcje poniżej dokumentują
> historyczną korektę x-choice. Aktualny kontrakt używa standardowych description
> i anyOf; adapter zachowuje identyczne pytanie i kryteria. Zobacz
> [CONTRACTS.md](CONTRACTS.md) i [TOOL_WIRING.md](TOOL_WIRING.md).

# Korekta integracji Laya i propozycja dostrojenia wag

Status 25.09.2026: użytkownik poleceniem „Dobra popraw to” zatwierdził korektę
semantycznej decyzji na podstawie treści wiadomości. Wykonano zmianę integracji
i testy lokalne. Nie rozpoczęto treningu wag ani generowania zbioru treningowego.

## Wykonany zakres i wynik

- Model wybiera `department`, a aplikacja mapuje tę decyzję na e-mail. Pole
  `email` publicznego requestu jest kontaktem nadawcy (Reply-To), nie odbiorcą.
- Polityka routera przekazuje krótkie pytanie i osobne opisy kategorii przez
  `x-choice` w schemacie narzędzia. Ogólny adapter tłumaczy je na `criteria`
  Laya; nie otrzymuje mapy adresów i nie zawiera reguł słów kluczowych.
- Schemat przekazywany do StructuredTool jest słownikiem JSON Schema,
  ponieważ konwersja klasy Pydantic w LangChain usuwała dodatkowe metadane.
  Walidacja Pydantic przed rzeczywistym wykonaniem narzędzia pozostaje obowiązkowa.
- Ten sam zestaw 15 znanych wiadomości: wcześniej 6/15, angielskie opisy 9/15,
  polskie opisy 13/15. Wariant polski pozostaje aktualną konfiguracją.
  Błędy: komputer oraz historia Rzymu → IT. To korekta integracji i porównanie
  na znanej regresji, nie niezależny test generalizacji ani fine-tuning.
- Testy hosta i kontenera: 85 passed. Dowody:
  [raport](VERIFICATION.md), [wynik polski](evidence/2026-09-25/laya-semantic-pl.jsonl),
  [manifest modelu i tokenizacji](evidence/2026-09-25/laya-semantic-model.json).
- Regresja Ollamy po zmianie schematu: 15/15, run `f0bb73ae3db9`.
  Jej inicjalizator przeszedł sondę tool calling w tym przebiegu.
- SDK 0.3.20, bundle `convaiinnovations/laya`, rewizja
  `55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851`, podkatalog `multilingual`.
  SHA-256 wag: `9d628fd971b700382ac6f65920a86f149777b2e748e0c955fb3b19695aa8f204`.
  Pytanie: 37 tokenów, opcje: 22/26/27/26/22, razem z markerami 165/256.
  Żadna opcja nie przekracza limitu 48 tokenów. Wagi nie zostały zmienione.

## Odtworzenie korekty i checkpoint

Warunki, publiczne zależności, obejście zawieszonego pomocnika Docker i zachowanie
wolumenów: [APPROACH.md](APPROACH.md). Komendy w katalogu głównym PoC:

```sh
.venv/bin/ruff check services tests verification
.venv/bin/ruff format --check services tests verification
.venv/bin/pytest -q
docker compose --env-file .env.laya-example build api laya-adapter tests
docker compose --env-file .env.laya-example up -d --no-build
docker compose --profile test run --no-deps --rm tests
docker compose --env-file .env.laya-example --profile test run --no-deps --rm e2e
# Regresja domyślnego dostawcy po zakończeniu testu Laya:
docker compose --env-file .env.ollama-example up -d --no-build
docker compose --env-file .env.laya-example stop laya-adapter laya-runtime
docker compose --env-file .env.ollama-example --profile test run --no-deps --rm e2e
docker compose --env-file .env.ollama-example stop
```

`--no-build` korzysta z wcześniej zbudowanego runtime Laya. Przy nowej instalacji
najpierw wykonać pełny build z APPROACH. Wejścia: `verification/cases.json` i
polityka w `services/router/router_app/adapters/agent.py`. E2E wypisuje JSONL i
tworzy syntetyczne maile w Mailpit. Kod 1 dla wyniku 13/15 jest oczekiwanym
sygnałem niespełnienia kryterium; nie zmieniać oczekiwanych adresów.
Nie nadpisywać historycznych dowodów przy wznowieniu. Zachować wolumeny i bazowe
wagi. Dalszy trening z poniższej propozycji wymaga osobnego przygotowania i
potwierdzenia rzeczywistego sposobu wykonania; w tym zadaniu go nie uruchomiono.

Pomiar tokenów wykonano tokenizerem z tego samego snapshotu, bez pobierania
nowego modelu. Powtórzenie podczas działania kontenera:

```sh
PYTHONPATH=services/router .venv/bin/python - <<'PY' > /tmp/wskz-laya-choice.json
import json
from router_app.adapters.agent import DEPARTMENT_CRITERIA, DECISION_INSTRUCTIONS
print(json.dumps({'criteria': DEPARTMENT_CRITERIA, 'instructions': DECISION_INSTRUCTIONS}))
PY
docker compose --env-file .env.laya-example exec -T laya-runtime python -c '
import json, sys
from pathlib import Path
from transformers import AutoTokenizer
p = Path("/models/hub/models--convaiinnovations--laya/snapshots/55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851/multilingual")
tok = AutoTokenizer.from_pretrained(str(p / "tokenizer"), local_files_only=True)
policy = json.load(sys.stdin)
count = lambda s: len(tok(s, add_special_tokens=False)["input_ids"])
question = count("choice question: " + policy["instructions"])
options = {k: count(" " + k + ": " + v) for k, v in policy["criteria"].items()}
print({"question_tokens": question, "option_tokens": options,
       "head_tokens_with_markers": question + sum(options.values()) + len(options)})
' < /tmp/wskz-laya-choice.json
```

## Punkt wyjścia

Projekt używa `laya==0.3.20` i jawnie wybiera `multilingual` przy preloadzie
i każdej predykcji, na CPU z `max_len=8192`. To rodzina Laya Multilingual,
mmBERT-base z głowicą decyzyjną, około 322 mln parametrów. Domyślna mapa SDK
wskazuje repozytorium `convaiinnovations/laya`, podkatalog `multilingual`;
model ma też osobne repo `convaiinnovations/laya-multilingual`.

Wynik pierwotnego E2E: 6/15. Adapter przekazywał `criteria` jako mapę
adres → ten sam adres; opisy działów znajdują się w długich instrukcjach.
Oficjalny przykład przekazuje opis znaczenia każdej opcji bezpośrednio w
`criteria`. Ta różnica uzasadniła korektę integracji; nie dowodzi, że wyjaśniała
wszystkie błędne decyzje pierwotnego modelu.

## Proponowany zakres wykonania

1. Ustalić i zapisać rewizję SDK, wag oraz ich sumy kontrolne. Sprawdzić
   tokenizację instrukcji i opcji, także osobny budżet głowicy modelu.
2. Wprowadzić opisowe kryteria przekazywane ze schematu narzędzia, zachowując
   adapter niezależny od polityki działów. Porównać ten sam model przed i po
   zmianie formatu. Ten etap nie zmienia wag.
3. Przygotować oznaczony zbiór polskich wiadomości dla pięciu działów, w tym
   przypadki graniczne kadry/HR oraz help desk/IT. Początkowo 1000 odrębnych
   przykładów, po 200 na dział; syntetyczne pochodzenie jawnie oznaczone.
   Grupować parafrazy i wspólne scenariusze w jednym podzbiorze, usuwać duplikaty.
   Podział według grup: train 70%, validation 15%, test 15%, seed 42.
   Dotychczasowe 15 znanych przypadków zostaje osobną regresją, nie niezależnym
   testem generalizacji. Nie pobierać rzeczywistych skrzynek ani płatnych API.
4. Przygotować adaptację oficjalnej pętli RLCD i cross-entropy do checkpointu
   multilingual oraz własnych etykiet. Punkt startowy: 4 epoki, AdamW,
   LR encoder 2.5e-5, LR head 1e-4, weight decay 0.01, gradient clipping 1.0,
   gradient checkpointing. Microbatch dobrać po pomiarze pamięci bez zmiany
   efektywnego batch size. Nie obiecywać czasu ani możliwości treningu, dopóki
   test forward/backward na dostępnym sprzęcie tego nie potwierdzi.
5. Najlepszą epokę wybierać wyłącznie na validation. Kalibrację temperatury
   wykonywać na danych niewykorzystanych do aktualizacji wag. Temperatura
   kalibruje pewność; wspólna dodatnia skala logitów nie zmienia argmax kategorii.
6. Porównać bazowy model, poprawiony format i dostrojone wagi: accuracy,
   macro-F1, macierz pomyłek, recall każdego działu, opóźnienia. Końcowy test
   wykorzystać po zamknięciu wyboru modelu. Następnie wykonać E2E przez Mailpit.

## Warunki, artefakty i wznowienie

- Trening wymaga osobnego środowiska z PyTorch i zgodnymi zależnościami Laya.
  Notebook referencyjny używa CUDA/NCCL i 2×T4; nie uruchomi się bez adaptacji
  na samym macOS/CPU. Nie rezerwować płatnego GPU ani nie wysyłać danych do
  zewnętrznego środowiska bez osobnego wskazania/autoryzacji użytkownika.
- Przed wykonaniem utrwalić w tym dokumencie rzeczywiste przygotowane skrypty
  i komendy dla dostępnego sprzętu. Nie ma jeszcze skryptu treningowego w PoC;
  komendy notebooka nie są gotowym poleceniem dla tego projektu.
- Dane, manifest splitów i metryki: `training/laya-routing/` (do utworzenia).
  Duże wagi pozostają poza Git, z manifestem sum kontrolnych i pochodzenia.
- Checkpoint ma zawierać model, optimizer, scheduler, RNG, epokę i pozycję
  w danych. Notebook zapisuje wagi po epokach, ale nie pełny stan wznowienia;
  pełne wznowienie wymaga uzupełnienia implementacji.
- Nowy model zapisać osobno. Nie nadpisywać bazowych wag i nie publikować na Hub.
  Przy braku poprawy zachować raport, a model bazowy pozostawić dostępny.

## Przeczytane referencje

- [Model i architektura](https://huggingface.co/convaiinnovations/laya-multilingual)
- [Router i domyślna mapa modeli](https://github.com/NandhaKishorM/laya/blob/main/laya/router.py)
- [Oficjalny przykład opisowych criteria](https://github.com/NandhaKishorM/laya#quickstart)
- [Oficjalny notebook treningowy](https://github.com/NandhaKishorM/laya/blob/main/notebooks/laya_finetune_typed_decisions_2xT4_kaggle.ipynb)
