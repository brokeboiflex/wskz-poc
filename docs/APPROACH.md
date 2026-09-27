# Zatwierdzone podejście, wykonanie i wznowienie

Gemma work accepted as complete. Gemma is now the default; Qwen weights removed and all PoC containers stopped. [Delivered work, cleanup, validation and restart](GEMMA_COMPLETION.md). Historical checkpoints below describe their original runtime.

Final Gemma500 evaluation completed 2026-09-27: **493/500 correct (98.6%), 7 wrong routes, 0 missing/invalid native calls**. All500 first attempts, no retries or mail. Previous score471/500;27 old failures fixed,2 remain,5 new regressions. All raw responses and seven failure bundles saved; offline audit passed and1866 prior hashes unchanged. Synthetic regression evidence, not held-out/general application acceptance. [Results, failures and repeat procedure](evidence/2026-09-27/gemma-final-500/README.md). No further run is implicit.

Laya fine-tuning approved 2026-09-27; resource preflight blocked by steady-state
OOM and checkpoint disk budget. No trained model or full dataset/test result.
[Approved method](LAYA_GENERALIZATION_APPROACH.md),
[evidence and resume conditions](../training/laya-routing/README.md).

Latest repair (2026-09-27): **Ollama0.34.4-poc.tool-choice.2 is applied**. Generic native `tool_choice` transport now works; existing `MODEL_TOOL_CHOICE=required` is enabled and approved guidance is deployed. All8 saved missing-call cases pass on the first required request, including434; auto still reproduces434. Qwen, streaming, named, none and plain-text controls pass;81 application regressions and backend tests/vet pass. No full500 rerun or mail. Unsupported rendered required/none fails explicitly; API/mailer SMTP readiness remains blocked by pre-existing absent Mailpit. [Evidence, commands and rollback](evidence/2026-09-27/ollama-tool-choice/README.md).

Previous prompt/diagnosis checkpoint (2026-09-27): added a minimal generic `<guidance>` block only. Focused23-case check:18 correct native routes,2 wrong routes,3 missing calls;81 regression tests pass. Raw tokens reproduce case434 missing the opening tool marker; native `tool_choice=required` corrects that case, but Ollama ignores the field. The other four original missing-call cases did not reproduce in isolation, so their precise trigger remains unresolved. No backend repair or full500 rerun. Source prompt not redeployed to the API container. [Evidence and repeat procedure](evidence/2026-09-27/gemma-guidance-diagnosis/README.md).

Completed full Gemma check (2026-09-27 local time): **471/500 correct (94.2%)**, 24 wrong routes and 5 missing native calls. All 29 failures retain full requests and raw responses, plus individual debug bundles. All 77 manual review gates and offline audits pass. The earlier 147 outcomes reproduce exactly. No retries, tuning, tool execution or mail. Previous evidence, generic agent and Compose are unchanged. This is synthetic model transport/routing evidence, not full application acceptance.
[Results, failures and repeat procedure](evidence/2026-09-26/gemma-patched-500/README.md). No further run is implicit.

Latest completed check: the user reauthorized the147-case failed set after the
Gemma repair. Gemma146/147 correct with one missing native call; Qwen133/147,
14 wrong routes and no protocol errors. Both audits pass; no retries, email or
full500 run. Historical checkpoints remain unchanged. See
[approach and results](evidence/2026-09-26/failed-cases-patched/README.md).
Older stopped-run statements below describe earlier checkpoints.

Najnowsza zatwierdzona naprawa backendu została wdrożona lokalnie:
[OLLAMA_GEMMA_TOOL_FIX.md](OLLAMA_GEMMA_TOOL_FIX.md).
Ollama0.34.4 z natywnym dekodowaniem narzędzi Gemmy, bez zmiany agenta.
Wyniki i granice dowodów: [raport](evidence/2026-09-26/ollama-gemma-fix/REPORT.md).
Benchmark pozostaje zatrzymany.

Poprzednia diagnoza integracji Gemma z 26.09.2026:
[podejście](evidence/2026-09-26/gemma-integration-audit/APPROACH.md),
[raport](evidence/2026-09-26/gemma-integration-audit/REPORT.md).
Trzy pojedyncze generacje przez OpenAI-compatible API wyizolowały pomijanie
natywnych ograniczeń nazw narzędzi w Ollama oraz osobny problem zachowania
tokenów specjalnych w silniku natywnym. Bez zmian aplikacji, poprawek źródeł
backendu, ponowień ani wznowienia benchmarku. Proces diagnostyczny zatrzymany.

Użytkownik zatwierdził realizację 25.09.2026 („Ok […] Dajesz”), doprecyzowując
oddzielne kontenery, luźne powiązania mikroserwisów, Service Layer Pattern w Pythonie
oraz świeżego agenta krytyka po implementacji. Zgoda obejmuje implementację,
pobranie publicznych zależności/wag i testy z syntetycznymi mailami w Mailpit.
Nie obejmuje wysyłki zewnętrznej, wykorzystania sekretów innych projektów ani
usuwania cudzych danych. Przed wznowieniem przeczytać ten dokument.

## Wejście i wynik

Wejście: treść zadania rekrutacyjnego i wskazany stos Python/LangChain, wymagana
Ollama, wymienne endpointy OpenAI-compatible i dodatkowa Laya.
Wynik: cały ten samodzielny katalog, zawierający Compose, serwisy, env examples,
README, kontrakty, testy oraz raport weryfikacji. Projekt nie zależy od Resumera.

Architektura i polityka: [README.md](../README.md), kontrakty: [CONTRACTS.md](CONTRACTS.md).
Status dowodów: [VERIFICATION.md](VERIFICATION.md). Zasady dla agenta: [AGENTS.md](../AGENTS.md).
Najnowsze zatwierdzone debugowanie obserwowane przez OpenAI-compatible API:
[OBSERVED_DEBUGGING.md](OBSERVED_DEBUGGING.md). Benchmark pozostaje zatrzymany;
każdy pojedynczy przypadek wymaga odczytu skorelowanych śladów przed kolejnym.
Pomiar CPU i RAM podczas tego samego testu syntetycznego:
[RESOURCE_MEASUREMENT.md](RESOURCE_MEASUREMENT.md).

Zatwierdzony syntetyczny benchmark 500 wiadomości po polsku, źródła scenariuszy,
walidacja i komendy uruchomienia: [BENCHMARK_APPROACH.md](BENCHMARK_APPROACH.md).
To 250 rodzin scenariuszy w dwóch wariantach, po 100 wiadomości na dział.

## Implementacja

1. Router: FastAPI → RoutingService → port RoutingAgent i port DeliveryGateway.
   Adapter używa LangChain `create_agent`, ChatOpenAI i StructuredTool.
   Jeden middleware waliduje wywołanie przed wysyłką; `return_direct` kończy
   agenta po narzędziu. Brak własnej pętli, korekcyjnych ponowień lub inferencji
   po wysyłce. Nie ponawiamy mailera po błędzie.
2. Mailer: osobne API → DeliveryService → własny rejestr SQLite i SMTP.
   Trwała rezerwacja z UUID i hashem payloadu przed wywołaniem SMTP. Statusy
   submitted/failed/unknown, bez automatycznych ponowień.
3. Ollama: osobny kontener, przypięta0.34.4 z poprawkami backendu opisanymi
   w OLLAMA_GEMMA_TOOL_FIX.md.
   Model-init sprawdza/pobiera wagi i wykonuje jeden neutralny tool call
   gotowości bez wysyłki. Nie zmienia szablonu ani wag modelu.
4. Laya: osobne kontenery adaptera protokołu i silnika. Adapter przekłada jedno
   narzędzie z argumentem enum na typed choice. Silnik korzysta z publicznego SDK
   `Router.predict(..., model="multilingual", max_len=8192)` i preloadu modelu.
   Własny cienki host zapewnia jawny budżet, którego domyślny serwer upstream nie
   przekazuje w wywołaniu predict. Zachowany format `/v1/systemone`.
   Korekta zatwierdzona 25.09: enum opisuje działy, nie adresy; standardowe
   description i anyOf przekazują pytanie i opis każdej kategorii. Router mapuje wynik
   modelu na adres dopiero po walidacji. Szczegóły wykonania, manifest wag,
   pomiar tokenów i wznowienie: [LAYA_TUNING_APPROACH.md](LAYA_TUNING_APPROACH.md).
   Trening wag z tego dokumentu pozostaje odrębną, niewykonaną propozycją.
5. Publiczny endpoint modelu i wybór modelu są konfigurowane wyłącznie env.
   Ollama pozostaje w Compose również dla dostawców alternatywnych, ale nie pobiera
   wtedy wag. Laya uruchamiana jest profilem. Mailpit zawsze przechwytuje pocztę.

UMC pozostaje opcjonalną przyszłą implementacją kontraktu mailera, zgodnie z
zaakceptowanym zakresem początkowo bez UMC.

## Warunki i komendy

Docker Engine z Compose >=2.24, dostęp do rejestrów publicznych i wag, wolne porty
8000/8025, zalecane początkowo 8 GB RAM dla Dockera i miejsce na modele. Pierwszy
start obejmuje pobieranie. Brak gotowości ma skutkować błędem, nie atrapą.

Wszystkie poniższe komendy wykonuje się w głównym katalogu tego PoC:

```sh
docker compose config --quiet
docker compose --env-file .env.laya-example config --quiet
docker compose --env-file .env.openrouter-example config --quiet
docker compose up -d
docker compose ps -a
docker compose logs --tail 100 model-init api mailer
docker compose --profile test run --build --rm tests
docker compose --profile test run --build --rm e2e
```

Po zmianie dostawcy stosować odpowiedni `--env-file` we wszystkich poleceniach.
OpenRouter wymaga własnego klucza w ignorowanym `.env`. Nie czytać sekretów innych
projektów. `.env.example` wylicza wszystkie konfigurowalne parametry Compose.

Test E2E używa 15 przypadków z `verification/cases.json`, zwraca JSONL z wynikami
oraz czasem każdej operacji, odczytuje surowe MIME z Mailpit i kontroluje adres,
Reply-To, Message-ID, korelację i treść. Każdy przebieg tworzy nowe syntetyczne
wiadomości. Nie usuwa wiadomości. Wynik niezerowy oznacza niespełnienie kryterium.

## Kontrole lokalne

```sh
python3.12 -m venv .venv
.venv/bin/python -m ensurepip
.venv/bin/python -m pip install -r services/router/requirements.txt -r tests/requirements.txt
.venv/bin/ruff check services tests verification
.venv/bin/ruff format --check services tests verification
.venv/bin/pytest -q
```

Te testy obejmują warstwy domeny i usług, rzeczywiste narzędzie LangChain,
kontrolery ASGI, adaptery HTTP z kontrolowanymi odpowiedziami, MIME, rejestr
idempotencji, współbieżność, utratę potwierdzeń i granice importów usług.
Nie zastępują E2E z modelem i SMTP.

W sesji implementacyjnej terminal nie miał dostępu do sieci ani gniazda Docker.
Do testów hosta użyto zainstalowanego Python 3.12 i dostępnych lokalnie pakietów
z cache uv. Utworzono odrębne środowisko `.venv`, bez modyfikowania globalnych
pakietów. Cache metadata skopiowano do `/private/tmp/message-router-uv-cache`;
rozpakowane publiczne pakiety z cache odtworzono jako pliki wheel w
`/private/tmp/message-router-wheelhouse`, zachowując METADATA/WHEEL/RECORD.
Instalacja była offline:

```sh
uv pip install --offline --no-index \
  --find-links /private/tmp/message-router-wheelhouse \
  --cache-dir /private/tmp/message-router-uv-cache \
  --python .venv/bin/python \
  -r /private/tmp/message-router-host-requirements.txt
```

Host requirements obejmowały `services/router/requirements.txt` bez niedostępnego
`langchain-openai` oraz `tests/requirements.txt`. Odpowiedni test wire klienta
OpenAI jest jawnie pomijany, jeśli brak paczki; standardowy obraz testowy instaluje
pełen zestaw. To ograniczenie dowodów, a nie alternatywna implementacja runtime.
Po uzyskaniu dostępu do normalnych instalacji użyć kanonicznych komend powyżej.

## Wznowienie testów 25.09.2026

Na polecenie „Przetestuj wskz-poc, potem commit and push” wznowiono ten sam
zestaw testów. Sieć i Docker Engine są dostępne. Uzupełniono `pip` przez
`ensurepip` i zainstalowano pełne requirements w istniejącym `.venv`.

Pomocnik `docker-credential-desktop get` zatrzymywał pobieranie publicznych
obrazów. Do tych samych poleceń Compose użyto tymczasowej konfiguracji klienta
z pustym `auths`, bez zmiany konfiguracji użytkownika i bez kopiowania sekretów:

```sh
task_docker_host=$(docker context inspect --format '{{.Endpoints.docker.Host}}')
task_docker_config=$(mktemp -d /tmp/wskz-docker-config.XXXXXX)
printf '%s\n' '{"auths":{},"cliPluginsExtraDirs":["/Users/mini/.docker/cli-plugins"]}' > "$task_docker_config/config.json"
export DOCKER_CONFIG="$task_docker_config"
export DOCKER_HOST="$task_docker_host"
docker compose up -d --build
docker compose --profile test run --build --rm tests
docker compose --profile test run --build --rm e2e
```

Ścieżka `cliPluginsExtraDirs` dotyczy tego hosta macOS. Na innym hoście użyć
katalogu zawierającego jego pluginy Compose/Buildx. Przy sprawnym pomocniku
poświadczeń nie potrzeba tych zmiennych. Po zakończeniu w danej powłoce wykonać
`unset DOCKER_CONFIG DOCKER_HOST`. Wolumeny i obrazy nadal należą do tego samego
daemonu i projektu Compose `message-router`. Wyniki i ograniczenia bieżącego
przebiegu są w [VERIFICATION.md](VERIFICATION.md).

Po starcie sprawdzić również publikowane porty z hosta (test wewnątrz Compose
nie wykrywa braku publikacji panelu Mailpit):

```sh
curl --fail http://127.0.0.1:8000/health/ready
curl --fail -o /dev/null http://127.0.0.1:8000/api/v1/docs
curl --fail -o /dev/null http://127.0.0.1:8025/
```

Naprawy znalezione podczas testów nie zmieniają modelu, zbioru przypadków ani
ścieżki agent → mailer → SMTP. Mailpit ma dodatkowy bridge `mailpit-ui` do
publikacji panelu, a obraz Laya jawny `TORCHINDUCTOR_CACHE_DIR=/tmp/torchinductor`,
żeby PyTorch nie szukał nazwy użytkownika dla numerycznego UID 10001.

Końcowy checkpoint: kontenery zatrzymane (`docker compose stop`), wolumeny
zachowane. Wyniki E2E w `docs/evidence/2026-09-25/`. Przed kolejnym uruchomieniem
uwzględnić otwartą niestabilność sondy tool calling Ollamy i niezaliczoną trafność
Laya opisaną w raporcie. Nie zastępować nieudanej sondy deklaracją gotowości.

## Checkpoint, awarie i wznowienie

- Sprawdzić `git status`, zachować wcześniejsze pliki użytkownika, przeczytać
  README i raport VERIFICATION. Nie restartować innych projektów Compose.
- Sprawdzić `docker info`. `permission denied` w tej sesji oznacza ograniczenie
  sandboxa; nie wyciągać z niego wniosku, że daemon na hoście nie działa.
- Po przerwaniu pobierania zachować wolumen `ollama-models` lub `laya-models`.
  Ponowić model-init i sprawdzić kod wyjścia, następnie uruchomić całe środowisko.
- Po zmianie kodu budować przez `docker compose up -d --build`.
- Po niejednoznacznej wysyłce sprawdzić `request_id` w Mailpit i wewnętrznym API
  mailera. Nie powtarzać automatycznie publicznego POST ani operacji SMTP.
- Nie używać `down --volumes` do zwykłego wznowienia; usuwa dane i wagi.
- Uruchomić pełny kontenerowy E2E dla Ollamy, następnie dla Laya. Dopiero faktyczne
  wyniki pozwalają określić trafność oraz czas działania.
- Po istotnych poprawkach wykonać odpowiednie regresje i odświeżyć raport krytyka.

## Referencje użyte przed implementacją

- https://docs.langchain.com/oss/python/langchain/tools
- https://docs.langchain.com/oss/python/integrations/chat/openai
- https://docs.ollama.com/api/openai-compatibility
- https://docs.docker.com/compose/how-tos/startup-order/
- https://mailpit.axllent.org/docs/api-v1/
- https://github.com/NandhaKishorM/laya
- https://raw.githubusercontent.com/NandhaKishorM/laya/main/laya/serve.py
- https://raw.githubusercontent.com/NandhaKishorM/laya/main/laya/router.py

Wersje bezpośrednich zależności zapisano w requirements każdego serwisu; obrazy
mają jawne tagi. Zależności przechodnie nie mają jeszcze kompletnego lockfile,
a checkpointy modeli są identyfikowane tagiem/nazwą, nie niezmiennym hashem.

## Korekta integracji tool calling, 25.09.2026

Na polecenie użytkownika „Full access now. Fix it” wznowiono testy Dockera.
Potwierdzono regresję serwera Ollama i zmianę pola tokenów przez ChatOpenAI.
Po uwagach o nadmiernej złożoności usunięto pętlę korekt i naprawianie szablonu
w bootstrapie. Używamy `create_agent` oraz Ollamy 0.13.5 sprzed regresji.
Zgodnie z poleceniem użytkownika benchmark 500 przypadków zatrzymano i nie
wznawiamy go. Dalsza weryfikacja to testy kodu/kontraktów i mały smoke test.
Źródła, komendy oraz checkpoint: [TOOL_WIRING.md](TOOL_WIRING.md).

## Uogólnienie agenta po przeglądzie

Na polecenie „So fix it and test” usunięto specyficzną dla Ollamy heurystykę
licznika tokenów i prywatne rozszerzenie x-choice. Standardowy JSON Schema
opisuje teraz każdą opcję, a wyłącznie adapter Laya tłumaczy go na typed choice.
Walidujemy jawne ucięcie i poprawność pojedynczego wywołania, bez heurystyk modelu.
Weryfikacja: testy kodu/kontraktów, pięć istniejących przypadków smoke dla Ollamy,
przełączenie env na Laya i te same pięć przypadków, powrót do Ollamy. Bez
wznowienia benchmarku 500, treningu lub zewnętrznych płatnych wywołań.
Dowody: `docs/evidence/2026-09-25/generic-agent/`.

## Latest checkpoint: stopped by user

The reauthorized run was stopped on the user's explicit instruction. Run
`2279baae02cc` has 241 completed records: 176 correct routes, 52 wrong departments,
and 13 HTTP 502 `invalid_tool_call` responses. All 13 matching API log reasons
are `missing_call`, not malformed JSON or invalid arguments. Of the 100 HR
messages, 41 went to help desk. These are partial, class-ordered results, not a
500-case accuracy score. No full-run MIME audit was performed. An in-flight
request at cancellation may finish independently; do not replay it automatically.
The E2E container was stopped (exit 137); results and API logs were preserved in
`docs/evidence/2026-09-25/ollama-500-generic/`. Do not resume without a new explicit
request. No model, prompt, schema or corpus changes were made during this run.

## Routing-policy replay checkpoint

The approved prompt/tool-choice change and four individual observed replays are
complete. See [evidence](evidence/2026-09-25/routing-policy/README.md): two public
cases succeeded, two remain missing calls. One metadata-only replay reproduced
function-name confusion. Repeat commands and checkpoint rules remain in
OBSERVED_DEBUGGING.md; do not resume the stopped benchmark.

## Model comparison checkpoint

User approved an env-only model comparison with logs. Four observed cases on
qwen3:4b-instruct-2507-q4_K_M passed with unchanged application code; candidate
remains active with tracing off, repository defaults unchanged. Reproduction,
artifacts and limitations: [model comparison](evidence/2026-09-25/qwen4b-instruct/README.md).
Follow OBSERVED_DEBUGGING.md; no bulk benchmark resume.

## Latest checkpoint: testing stopped at 190, evidence audit complete

User stopped testing and requested a no-fluke check. No further model inference
was run. Full logs and all 190 live MIME agree with 190 actual successful calls,
but only HR 100/payroll 90 (95 pairs) were covered, with previous corpus exposure.
Commands, read-only repeat audit and limitations:
[FORENSIC_REVIEW.md](evidence/2026-09-25/qwen4b-500/FORENSIC_REVIEW.md).
Do not resume testing without a new request.

## Resume authorized, 2026-09-26

User requested commit, push and remaining cases. Resume the same observed method
at case 191 using `run.py --resume-after-190`; preserve cases 1-190, no replay.
The explicit flag validates the frozen prefix and refuses an existing resume
marker or case-191 artifacts. Keep per-case audits, failure/ten-case review gates
and unchanged model settings. Preserve first-segment logs separately, then join
API logs for the full audit. Save logs before disabling tracing. Commit and push
the implementation checkpoint, then completed evidence.

## Latest checkpoint: stopped at 400

User stopped testing to inspect failures. No further inference. Results: 375 correct,
6 wrong routes, 19 upstream missing calls; 381 live MIME audits passed. See
`docs/evidence/2026-09-25/qwen4b-500/FAILURE_REVIEW.md` (path from repository root).

## Approved Ollama backport

User approved PR17284 backport and focused observed verification. Follow
`docs/OLLAMA_BACKPORT.md` (repository root). Bulk testing remains stopped.

## Temperature and schema diagnostic, 2026-09-26

User requested temperature reduction and simpler schema, superseding EXAONE.
Observed four transport-only requests: temperature0 alone still invalid on394;
removing anyOf gives3/3 valid calls,2/3 correct departments. No production schema
change or mail. Approach/evidence: docs/evidence/2026-09-26/simple-schema/README.md
(path from repository root). Bulk benchmark remains stopped.

## English minimal-schema diagnostic

User approved testing the English prompt/minimal schema with failure-only records.
Three observed cases394,235,393 passed native call and route checks at temperature0.
Zero failures; no mail or production changes. Details and repeat approach:
`docs/evidence/2026-09-26/english-minimal/README.md` (repository-root path).

## Completed English minimal-schema evaluation, 2026-09-26

User authorized all 500 cases with failure-only records. Completed unchanged
Qwen3 4B / patched Ollama / temperature 0: 353 correct, 109 wrong routes,
38 missing native calls. All missing calls were in the other category and
returned ordinary text with finish_reason=stop, not native tool_calls.
This is transport-only evidence: no emails or application schema changes.
All 147 failures and 182 review gates passed the offline consistency audit;
successful raw responses were intentionally not retained. No further run is
implicit. Approach, exact prompt/schema, failure report and audit command:
`docs/evidence/2026-09-26/english-minimal-500/README.md` (repository-root path).

## Missing-call policy correction, 2026-09-26

The user requested fixing missing calls and explaining the500 failures.
Read `docs/evidence/2026-09-26/routing-policy-fix/README.md` and ANALYSIS.md
(repository-root directory) before resuming. The application system prompt now
requires forwarding every message, explicitly including other, and clarifies
company-specific category boundaries. Schema/Laya criteria and agent code remain
unchanged. Observed minimal-schema diagnostic:15native calls,14correct routes;
case474 remains wrong due to resolved history. Seven former missing calls pass.
81 router/wire/Laya/architecture tests pass. This is a prompt mitigation, not
server-enforced tool calling or a full500 pass. Do not restart the bulk run.

## Frozen failed-case comparison, 2026-09-26

User authorized comparing Qwen and Gemma4 E4B only on the147 previously failed
cases, freezing everything else. Inputs/settings are hashed under
`docs/evidence/2026-09-26/failed-cases-comparison/`. Preflight blocked: current
Ollama0.13.5-poc.17284 rejects Gemma4 with HTTP412 requiring a newer server.
No inference or runtime upgrade occurred. Do not change the frozen backend
implicitly; read that directory README before resuming.

## Isolated newer Ollama candidate, 2026-09-26

User requested investigating/patching newer Ollama. Build-only approach and logs:
`docs/evidence/2026-09-26/ollama-candidate/README.md`. Candidate0.34.4 carries
upstream PR18391 (template JSON) and PR17284 (unparsed output). Main Compose,
running0.13.5 and frozen147-case comparison remain unchanged. These patches
do not enforce tool_choice or establish Gemma inference correctness.

## Gemma E2B comparison stopped and diagnosed, 2026-09-26

The user stopped Gemma at31/147 after31 invalid tool-call names. Qwen completed
133/147 correct routes,14 wrong routes and no protocol errors on the same backend.
No bulk resume. One isolated logprobs replay proved the model itself generated
`call:human_resources{}` despite a correct rendered `send_department_email` schema.
Gemma uses its dedicated rendered completion/parser path; tool definitions are
not enforced as decoding constraints and the parser passes through unknown names.
The two existing generic patches do not cover this path. No repair implemented.
Evidence, reproduction and checkpoint:
[DIAGNOSIS_E2B.md](evidence/2026-09-26/failed-cases-comparison/DIAGNOSIS_E2B.md).
