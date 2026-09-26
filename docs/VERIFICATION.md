# Stan weryfikacji

## Najnowsza diagnoza obserwowana

Bez zmiany modelu/promptu wykonano cztery oddzielnie obserwowane zgłoszenia
oraz trzy sondy tokenów przez standardowe OpenAI Chat Completions (bez wysyłki).
Zapisano pełne requesty, surowe odpowiedzi, wynik LangChain i MIME.
Model mylił etykietę działu z nazwą funkcji: `help_desk` lub `payroll` zamiast
`send_department_email`. Parser serwera ukrywał takie wywołanie jako pustą
odpowiedź. Osobno odtworzono poprawne wywołanie ze złym działem.
Kontrola zakończyła się poprawnym HR; dwa wysłane maile przeszły niezależne
kontrole MIME, dwa odrzucone zgłoszenia nie wysłały maili. Jedna sonda urlopu
nie odtworzyła błędu; zachowano oba wyniki. To diagnoza, nie naprawa trafności.
46 testów instrumentacji/SDK/routera zaliczonych; trace po odczycie wyłączony.
Dowody: [observed-debug/README.md](evidence/2026-09-25/observed-debug/README.md).

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

Data: 25.09.2026. **Po korekcie semantycznej Laya: 13/15, nadal FAIL akceptacji.**
Model wybiera dział na podstawie treści i opisów; adres ustala aplikacja.
Nie trenowano wag. Poprzedni pomiar Laya 6/15 pozostaje poniżej jako historia.

Późniejszy [pomiar CPU i RAM](RESOURCE_MEASUREMENT.md) powtórzył ten sam zestaw:
Laya 13/15, Ollama 13/15 (błędne przypadki 3 i 6). Wcześniejsze 15/15 Ollamy
pozostaje prawdziwym wynikiem tamtego przebiegu, ale nie dowodzi powtarzalnie
bezbłędnego routingu. Dowody nowych przebiegów i pomiarów zasobów są w
`docs/evidence/2026-09-25/resources/`.

## Aktualny wynik: wspólny agent bez heurystyk dostawcy

Na polecenie po świeżym przeglądzie usunięto dwie pozostałe zależności:
heurystykę licznika tokenów Ollamy oraz prywatne x-choice w schemacie każdego
requestu. Agent używa standardowego JSON Schema z opisami alternatyw anyOf;
adapter Laya przekłada je na identyczne pytanie i kryteria typed choice.
Nie dodano nowego proxy, patchowania SDK ani przełączników nazw dostawców w agencie.

- **120/120 testów na hoście i w przebudowanym kontenerze.** Obejmują dwa
  endpointy konfigurowane wyłącznie env przez rzeczywisty SDK, poprawne wywołanie
  przy osiągniętym limicie tokenów oraz dokładną zgodność wejścia Laya.
- **Ollama: 5/5 live smoke**, run `0f9c08ddffc3`.
- **Laya: 4/5 poprawnych działów, 5/5 dostarczonych wiadomości**, run `ab7b125923ec`.
  „Nie działa mi komputer.” trafiło do IT zamiast help desku. Ten sam błąd jest
  zapisany w starszych `laya-semantic-pl.jsonl` i `resources/laya-e2e.jsonl`.
  Nie zmieniano polityki ani wag, aby dopasować wynik testu.
- Odczyt MIME wszystkich **10** wiadomości potwierdził oryginalny tekst, Reply-To,
  adres zgodny z decyzją modelu, Message-ID, korelację i brak duplikatów.
- Render-only na rzeczywistej Ollamie potwierdził zachowanie opisów, anyOf i enum
  w stockowym szablonie. Nie uruchamiało to inferencji ani wysyłki.
- Świeży krytyk nie znalazł blokera; niezależnie zaliczył **101 testów** i potwierdził,
  że anyOf jest standardowym JSON Schema, a nie przemianowaną prywatną strukturą.

Przełączenie wykonano `.env.laya-example`, a potem przywrócono `.env.ollama-example`.
Domyślne kontenery są zdrowe; opcjonalna Laya została zatrzymana. OpenRouter
sprawdzono na poziomie konfiguracji/wire, bez prawdziwego zewnętrznego klucza
lub płatnej inferencji. Zgodność każdego zewnętrznego dostawcy nie jest dowiedziona:
wymagane są Chat Completions z tool calling, użyte standardowe pola schematu
oraz `/models` z wybranym ID. Licznik tokenów nie zastępuje finish_reason.

Dowody: `docs/evidence/2026-09-25/generic-agent/`: `container-tests.txt`,
`ollama-smoke.jsonl`, `laya-smoke.jsonl`, `mime-audit.json`, `rendered-schema.json`.
Read-only kontrola MIME: `audit_smoke.py`. Pierwsze podejście do Laya zakończyło
się przed pierwszym POST, ponieważ API jeszcze się uruchamiało; zapisano
`laya-preflight-exit.txt`. Właściwy przebieg użył Compose `--wait`.
Benchmark 500 przypadków pozostał zatrzymany. Komendy: [TOOL_WIRING.md](TOOL_WIRING.md).

## Wcześniejsza naprawa integracji Qwen/Ollama

**Finalny kod: 116/116 testów na hoście i w przebudowanym kontenerze; 5/5
rzeczywistych zgłoszeń smoke.** API, Swagger i panel Mailpit są dostępne.
Ollama 0.13.5 uruchomiła model i zaliczyła pojedynczą sondę native tool calling.
To weryfikacja integracji, nie pomiar ogólnej trafności modelu.

Potwierdzono w rzeczywistym prompcie regresję Ollama #14601: wersja 0.17.7
renderowała definicję narzędzia jako strukturę Go zamiast JSON. Compose używa
teraz 0.13.5 sprzed regresji; produkcyjne narzędzie na stockowym szablonie
renderuje się jako poprawny JSON z zachowaną nazwą, opisami, wymaganym polem
i enum. Przywrócony manifest modelu jest identyczny z oryginalnym, wraz z wagami.
Usunięto naprawianie szablonu w bootstrapie i własną pętlę korekt. LangChain
`create_agent` zarządza inferencją i wykonaniem terminalnego narzędzia.

Smoke wybrał pierwszy przypadek każdego działu z istniejącego 15-elementowego
zestawu: urlop, komputer, serwer, rekrutacja, przepis kulinarny. Każde zgłoszenie
sprawdzono przez HTTP, model, mailer i rzeczywisty SMTP do Mailpit: odbiorcę,
Reply-To, Message-ID, korelację, oryginalną treść i brak duplikatu. Wszystkie
przeszły bez korekcyjnych ponowień. Run ID: `d8d91b7be2bb`.

Dowody w `docs/evidence/2026-09-25/tool-wiring/`:

- `agent-factory-tests.txt`: 116 zaliczonych testów kontenerowych.
- `bootstrap-0.13.5.txt`, `rendered-prompt-0.13.5-stock.json`,
  `model-manifest-stock.json`: działający runtime, stockowy szablon i model.
- `focused-smoke-cases.json`, `focused-smoke.jsonl`, `focused-smoke-exit.txt`:
  dokładne wejścia, per-case wyniki i kod wyjścia 0.
- `agent-factory-api.txt`, `agent-factory-containers.jsonl`: logi i stan kontenerów.

Świeży niezależny krytyk nie znalazł blokującego błędu w kodzie; samodzielnie
zaliczył 79 testów obejmujących agenta, realną serializację SDK, kontrakty,
mailer, bootstrap i granice warstw. Przypomniał, że ponowny publiczny POST
tworzy nowy identyfikator i może wysłać drugi mail; deduplikacja wewnętrznego
mailera nie jest deduplikacją publicznych requestów. [Raport](CRITIC.md).

Początkowy build po pobraniu obrazu zatrzymał się na błędzie I/O containerd,
gdy host miał 214 MiB wolnego miejsca. Użytkownik zwolnił miejsce; po wznowieniu
build i wszystkie powyższe kontrole przeszły. Kontenery pozostawiono uruchomione.

Benchmark 500 przypadków **zatrzymano na polecenie użytkownika** i nie wznowiono.
Nie ma wyniku końcowego. `template-patch-partial.jsonl` opisuje przerwaną, starszą
implementację z retry i patchowaniem, nie finalny kod. Historyczne 121 testów
również dotyczą tej usuniętej implementacji. Źródła i komendy:
[TOOL_WIRING.md](TOOL_WIRING.md).

## Utworzenie benchmarku syntetycznego 500 wiadomości (wcześniejszy checkpoint)

Zbudowano [zbiór 500 przypadków](../verification/benchmark/cases-500.json), po 100
na dział, z 250 scenariuszy w dwóch wariantach. Etykiety przypisano podczas
pisania scenariuszy; żaden z ocenianych modeli nie ustalał odpowiedzi wzorcowych.
Mediana: 61 słów, zakres: 16–176 słów. Zbiór jest syntetyczny i kontrolowany,
nie stanowi reprezentatywnej próbki rzeczywistej korespondencji.

- Host i przebudowany kontener testowy: **97 passed** (12 nowych kontroli).
- Walidacja źródeł, liczby, balansu, unikalności, par i SHA-256: PASS.
- Deterministyczne odtworzenie w obrazie E2E jako UID 10001: PASS.
- `--cases` wybiera zbiór; wyniki zawierają ID przypadku/rodziny i SHA-256.
- API otrzymuje tylko nadawcę i treść, bez etykiet i uzasadnień.
- Niezależny przegląd zakończony bez pozostałego blokera dla tego zakresu.
- **W chwili utworzenia zbioru nie wykonano inferencji 500 wiadomości.** Historyczne wyniki
  13/15 i 15/15 dotyczą wyłącznie poprzedniego zestawu 15 krótkich wiadomości.

Sposób odtworzenia, ograniczenia i checkpoint:
[BENCHMARK_APPROACH.md](BENCHMARK_APPROACH.md). Manifest:
[manifest.json](../verification/benchmark/manifest.json).

## Korekta semantycznej klasyfikacji

- Host: **85 passed**, bez pominięć, jeden warning Starlette/AnyIO.
  Zbudowany kontener testowy: **85 passed**, bez warningów. Ruff lint: PASS.
- Rzeczywisty klient ChatOpenAI zachowuje `x-choice` i dostarcza opisy do adaptera.
  Testy obejmują pięć mapowań dział → adres, odmowę podanego adresu lub dodatkowych
  argumentów, wadliwe opisy, limity oraz ogólność adaptera bez polityki poczty.
- [Angielskie opisy](evidence/2026-09-25/laya-semantic.jsonl): **9/15**,
  run `60b464aeb04b`. Następnie sprawdzono opisy po polsku, zgodnie z językiem wejścia.
- [Aktualne polskie opisy](evidence/2026-09-25/laya-semantic-pl.jsonl): **13/15**,
  run `67d6297c76ab`, E2E exit 1. Przypadek 4 (komputer) i 15 (historia Rzymu)
  trafiły do IT zamiast help desku i other. Pozostałe przypadki przechodzą wszystkie
  asercje surowego MIME, Reply-To, Message-ID, korelacji i oryginalnej treści.
  Błędne przypadki kończą kontrolę na odbiorcy MIME.
- Publiczne health API i Mailpit z hosta: HTTP 200.
- [Ollama po zmianie schematu](evidence/2026-09-25/ollama-semantic.jsonl):
  **15/15**, run `f0bb73ae3db9`, E2E exit 0. Inicjalizator w tym przebiegu
  przeszedł prawdziwą sondę native tool calling i dopuścił start API.
  Nie zmieniano jego kodu; wcześniejsza okresowa awaria nadal nie ma ustalonej
  przyczyny. Nowy poprawny start nie oznacza usunięcia tej niestabilności.
- [Snapshot i pomiar tokenizacji](evidence/2026-09-25/laya-semantic-model.json):
  SDK 0.3.20, `multilingual`, encoder `jhu-clsp/mmBERT-base`. Pytanie i opcje
  zajmują 165/256 tokenów, najdłuższa opcja 27/48. Opisy nie są obcinane.
- Te same 15 znanych przypadków służyło do porównania formatów. Nie wykonano
  niezależnego testu generalizacji ani certyfikacji odporności na prompt injection.
  Korekta protokołu jest potwierdzona; pełna trafność modelu pozostaje otwarta.

Sposób wykonania i wznowienie: [LAYA_TUNING_APPROACH.md](LAYA_TUNING_APPROACH.md).
Końcowa kontrola Ruff lint/format, Prettier zmienionych dokumentów, `pip check`
i konfiguracji Compose trzech wariantów: PASS. Kontenery zatrzymano po testach,
zachowując wolumeny modeli, rejestru i syntetycznych wiadomości.

## Historyczny przebieg przed korektą semantyczną

Rzeczywiste testy kontenerowe zostały wykonane po udostępnieniu Dockera i sieci.
**Domyślna Ollama: 15/15 E2E. Dodatkowa Laya: 6/15, FAIL.**

## Środowisko i wyniki

Docker Engine 29.6.1, Compose 5.2.0, Linux ARM64 w Docker Desktop na macOS,
10 CPU i około 7,75 GiB RAM przydzielonego Dockerowi. Inferencja CPU, bez GPU.
Wyłącznie syntetyczne wiadomości z `verification/cases.json`, poczta w Mailpit.

| Kontrola                                                        | Wynik                                                  |
| --------------------------------------------------------------- | ------------------------------------------------------ |
| Compose: domyślna Ollama, env Laya, env OpenRouter              | PASS                                                   |
| Ruff lint i formatowanie                                        | PASS, 37 plików Python                                 |
| Python 3.12 na hoście, pełne requirements                       | 68 passed, bez pominięć; jeden warning Starlette/AnyIO |
| Świeżo zbudowany kontener testowy                               | 68 passed, bez pominięć i warningów                    |
| `pip check` środowiska hosta                                    | PASS                                                   |
| Build routera, mailera, inicjalizatora, adaptera i runtime Laya | PASS                                                   |
| Gotowość API, Swagger i panel Mailpit przez porty hosta         | HTTP 200 po poprawce sieci Mailpit                     |
| Ollama `qwen3:1.7b`, native tool calling, HTTP → SMTP → Mailpit | 15/15 PASS                                             |
| Laya `multilingual`, adapter, HTTP → SMTP → Mailpit             | 6/15 PASS, 9 błędnych działów; proces E2E exit 1       |
| OpenRouter                                                      | Niewykonane, brak klucza dla projektu                  |

Pełny zestaw 68 testów obejmuje oba wcześniej pomijane scenariusze rzeczywistego
klienta ChatOpenAI, kontrolery ASGI, wykonanie narzędzia LangChain, kontrakt Laya,
MIME, SQLite, idempotencję, współbieżność, niepewne potwierdzenia SMTP, awarie
zapisu i granice architektury. Zależności modelu i SMTP w tych testach są
kontrolowane; rzeczywistą inferencję i SMTP potwierdzają osobne przebiegi E2E.

## Dowody E2E

- [Ollama JSONL](evidence/2026-09-25/ollama.jsonl), run `96db7c88b2f6`:
  **15/15**. Wszystkie pięć działów. Każdy przypadek sprawdził adres docelowy,
  Reply-To, Message-ID, X-Request-ID i niezmienioną treść surowego MIME w Mailpit.
  Czas jednego żądania: minimum 11,365 s, mediana 14,633 s, maksimum 51,437 s;
  łącznie 276,057 s. Czasy obejmują także odbiór i kontrolę MIME, bez pobierania wag.
- [Laya JSONL](evidence/2026-09-25/laya.jsonl), run `2f68d753ba8d`:
  **6/15**. Błędne przypadki: 1, 2, 3, 4, 5, 9, 11, 12 i 14. Na przykład prośba
  o urlop trafiła do help desku zamiast kadr. Wszystkie żądania zwróciły
  `submitted` i miały wiadomość w Mailpit, ale dziewięć zakończyło kontrolę na
  błędnym odbiorcy MIME; dalsze asercje tych dziewięciu nie zostały wykonane.
  Minimum 0,221 s, mediana 0,231 s, maksimum 0,298 s. Krótszy czas nie rekompensuje
  niezaliczonej trafności. Nie zmieniano przypadków, oczekiwanych adresów, promptu
  ani modeli, żeby uzyskać wynik pozytywny.

To pojedyncze przebiegi na 15 przypadkach, nie benchmark ogólnej skuteczności,
obciążenia ani odporności na prompt injection. Laya pozostaje wariantem
porównawczym i nie spełnia aktualnego kryterium routingu.

## Poprawione błędy uruchomieniowe

1. **Brak panelu Mailpit na hoście.** Kontener był podłączony wyłącznie do
   `smtp: internal`. Docker zapisywał żądane powiązanie portu, ale
   `NetworkSettings.Ports` nie zawierało publikacji, a połączenie z portem 8025
   było odrzucane. Dodano osobny bridge `mailpit-ui`; SMTP pozostaje niepublikowany,
   a jego sieć nadal wewnętrzna. Ponowna kontrola z hosta: HTTP 200.
2. **Laya nie ładowała modelu.** Pierwotna przyczyna to `KeyError: getpwuid(): uid
not found: 10001` w wyznaczaniu domyślnego cache PyTorch; ponowny import ujawniał
   wtórny błąd rejestracji artefaktu `precompile`. Jawny
   `TORCHINDUCTOR_CACHE_DIR=/tmp/torchinductor` korzysta z zapisywalnego tmpfs.
   Po przebudowie przechodzą importy PyTorch/Transformers, preload rzeczywistych
   wag, gotowość kontenera i pełne wykonanie zestawu E2E. Trafność pozostaje FAIL.

Naprawę sieci wspiera [dokumentacja sieci Compose](https://docs.docker.com/compose/how-tos/networking/).
Niezależny przegląd zmian i ograniczenia: [CRITIC.md](CRITIC.md).

## Przebieg i ograniczenia

- Początkowy pomocnik poświadczeń Docker Desktop blokował pobieranie publicznych
  obrazów. Testy wykonano z tymczasową pustą konfiguracją auth klienta, na tym
  samym daemonie, bez zmiany ustawień użytkownika. Powtórzenie w
  [APPROACH.md](APPROACH.md).
- Pierwszy start Ollamy z pobraniem wag przeszedł. Podczas późniejszej przebudowy
  jeden `model-init` zakończył się kodem 1 bez zachowanego szczegółowego logu.
  Przy powrocie z Laya dwukrotnie odtworzono błąd `model did not produce a native tool call`,
  który prawidłowo zablokował API. Następne cztery sondy na rozgrzanym modelu i
  jedna po jego wyładowaniu przeszły, zwracając prawdziwe `readiness_probe` z
  `ready=true`. Nie odtworzono surowej niepoprawnej odpowiedzi; nie można uznać
  przyczyny za ustaloną ani problemu za naprawiony. **Start Ollamy jest okresowo
  zawodny**, mimo zaliczonego routingu. Nie dodano automatycznego retry ani
  pomijania kontroli tool calling. Ślad błędu:
  [bootstrap-failure.txt](evidence/2026-09-25/bootstrap-failure.txt).
- Start Laya z zachowanymi wagami trwał kilka minut. Diagnostyczny proces z limitem
  30 s pokazał oczekiwanie na handshake TLS do Hugging Face; właściwy kontener
  później osiągnął gotowość. Nie zmieniano transportu ani źródła modeli.
- Modele oraz zależności przechodnie nie mają kompletnego niezmiennego lockfile.
  Nie wykonano testów produkcyjnych, HA ani dostarczania do zewnętrznych skrzynek.
- W pierwotnym przebiegu zachowano wolumeny modeli, rejestru i 30 syntetycznych wiadomości.
- Po tamtych testach zatrzymano kontenery przez `docker compose stop`. Ostatnie
  uruchomienie domyślnego wariantu w pierwotnym przebiegu zablokowała sonda gotowości; nie pozostawiono
  API działającego z pominięciem tej kontroli.

## Powtórzenie

Komendy, wymagania, warianty dostawców i wznowienie bez usuwania danych:
[APPROACH.md](APPROACH.md). Do standardowego uruchomienia nadal służy
`docker compose up -d`. E2E tworzy nowe syntetyczne wiadomości przy każdym
wykonaniu; nie ponawiać niepewnych zgłoszeń produkcyjnych na tej podstawie.

## Routing-policy revision: observed, 2026-09-25

Shortened the function description, added explicit system routing policy and
configurable MODEL_TOOL_CHOICE through existing LangChain middleware. All 77
targeted SDK/router/tracing/Laya tests pass; Ruff and all three Compose examples
validate. Fresh independent read-only critic found no implementation blocker.

Four individually observed public requests on the unchanged qwen3:1.7b backend:
interview and language-training cases routed correctly to HR; harassment and
leave cases still returned HTTP 502 with empty upstream messages. Both successful
deliveries passed MIME/Reply-To checks, both rejected requests produced no mail.
A separate logprobs replay for harassment again generated help_desk as the
function name. The model/backend reliability problem remains. No broad accuracy
claim, external-provider call or new Laya inference; the full benchmark remains
stopped. Evidence and repeat instructions:
[evidence/2026-09-25/routing-policy/README.md](evidence/2026-09-25/routing-policy/README.md).

## Env-only model comparison, 2026-09-25

qwen3:4b-instruct-2507-q4_K_M on the same Ollama 0.13.5 passed all four
individually observed diagnostic cases: interview, language training, harassment
reporting and leave. The previous revised-prompt 1.7B run passed two and returned
missing calls for two. Each new request made exactly one native email-tool call
and produced one captured email with correct recipient, original body and Reply-To.
Only the model field changed in corresponding wire requests; app image/hashes
are unchanged. No code tests rerun because no application change was made.

Public latency: 20.363 s on the first loaded request, then 3.685/4.402/3.962 s.
Ollama container snapshot: 3.514 GiB, CPU only, serving context 4096. This is not
a peak-memory measurement or a balanced accuracy benchmark. No clean bootstrap
or broader corpus check was performed. Candidate active, tracing off, defaults
unchanged. [Logs, MIME, model provenance and commands](evidence/2026-09-25/qwen4b-instruct/README.md).

## Full run stopped; forensic audit, 2026-09-26

The user stopped the 4B run at 190/500. No test process remains and no new
inference was run for the audit. All190 saved raw responses and live captured
emails were independently checked: 100 HR and 90 payroll correct, zero protocol
or MIME failures, no duplicate or unrecorded attempt. Full API logs have 950
correlated events and server logs exactly 190 inference POSTs. The four earlier
4B diagnostic requests also passed again with identical inputs.

This is 95 paired scenarios, only two classes, and a corpus already exposed
during debugging. No claim of broad accuracy or stochastic reliability is
warranted. The fresh critic confirmed real successes without direct label
leakage or scoring inflation. Candidate remains active with tracing off; the
benchmark must not resume implicitly.
[Forensic findings](evidence/2026-09-25/qwen4b-500/FORENSIC_REVIEW.md).

## Latest checkpoint: stopped at 400

User stopped testing to inspect failures. No further inference. Results: 375 correct,
6 wrong routes, 19 upstream missing calls; 381 live MIME audits passed. See
`docs/evidence/2026-09-25/qwen4b-500/FAILURE_REVIEW.md` (path from repository root).
