# Niezależny przegląd implementacji

## Benchmark 500 przypadków - 25.09.2026

Niezależny krytyk przeczytał wszystkie 250 scenariuszy źródłowych i porównał je
z bieżącą polityką działów. Nie znalazł jednoznacznie błędnej etykiety, ale wskazał
sztuczne komentarze tłumaczące brak kontekstu, nadmierne wykluczanie innych działów
i zbyt jednolitą długość wiadomości. Poprawiono te miejsca i rozbudowano 50
scenariuszy o konkretne szczegóły.

W drugim przeglądzie skontrolował warianty historyczne wszystkich 50 scenariuszy
`other`, poprawione dłuższe wiadomości, reguły składania par, oddzielenie odpowiedzi
wzorcowej od requestu, Dockerfile i ścieżkę `--cases`. Samodzielnie uruchomił
walidator odtworzenia oraz 12 testów benchmarku: PASS. Sprawdzony SHA-256:
`bd3cf10bc628dc0c27349201b443ef95a9b11112b272573766d323c547f5cd0e`.

Wniosek: brak pozostałego blokera poprawności dla kontrolowanego benchmarku
syntetycznego. Ograniczenia: 250 skorelowanych par, sztucznie równy udział działów,
pięć powtarzanych szablonów historii z jawnym zamknięciem poprzedniego tematu.
**Nie uruchomiono modeli na tych 500 przypadkach.** Przegląd i testy kodu nie
potwierdzają trafności modelu ani skuteczności na rzeczywistej skrzynce.

Podejście, komendy i checkpoint: [BENCHMARK_APPROACH.md](BENCHMARK_APPROACH.md).

## Korekta semantycznego routingu - 25.09.2026

Świeży niezależny krytyk przeczytał diff routera, adaptera, testów i dokumentacji
oraz uruchomił testy hosta: **85 passed**. Potwierdził wybór `department` przez
model i mapowanie na adres dopiero po walidacji, wykonanie rzeczywistego narzędzia
LangChain oraz brak słów kluczowych decydujących za model. Nie znalazł nowego
blokera w kodzie ani osłabienia kontroli argumentów i pojedynczej wysyłki.

Wskazano nieaktualne opisy `recipient` w kontrakcie i konieczność wyjaśnienia
zastępowania system promptu przez krótkie `x-choice.instructions`. Dokumenty
poprawiono i poddano ponownej kontroli. Krytyk odczytał finalny
[JSONL Laya](evidence/2026-09-25/laya-semantic-pl.jsonl) i potwierdził **13/15**,
run `67d6297c76ab`, błędy tylko dla komputera i historii Rzymu (oba → IT).
Sprawdził także zgodność rewizji/SHA wag i arytmetykę manifestu tokenizacji:
37 tokenów pytania + 123 tokeny opcji + 5 markerów = 165/256.
Metadane `config.training` w manifeście pochodzą z checkpointu upstream,
nie z treningu w tym projekcie; dopisano to jawnie w pliku dowodowym.

Korekta architektoniczna jest potwierdzona. **Trafność Laya nadal nie spełnia
akceptacji 15/15.** Nie jest to niezależny benchmark ani dowód odporności na
prompt injection. W chwili drugiego przeglądu nowy E2E Ollamy nadal trwał;
jego finalny wynik potwierdzono w dodatkowym odczycie po zakończeniu wykonania:
[JSONL Ollamy](evidence/2026-09-25/ollama-semantic.jsonl), run `f0bb73ae3db9`,
wszystkie przypadki 1-15 `passed=true`. Krytyk potwierdził zgodność README
i aktualnej części VERIFICATION z dowodami.

## Aktualizacja po testach runtime - 25.09.2026

Świeży krytyk sprawdził rzeczywisty diff Compose i Dockerfile Laya, kod testu
`verification/e2e.py`, raport `VERIFICATION.md`, log 68 zaliczonych testów
kontenerowych, log przebudowy Laya oraz oba pełne logi E2E. Pliki
[Ollama JSONL](evidence/2026-09-25/ollama.jsonl) i
[Laya JSONL](evidence/2026-09-25/laya.jsonl) są zgodne rekord po rekordzie z logami
wykonania; niezależnie przeliczono wyniki i czasy.

**Domyślna Ollama zaliczyła 15/15 przypadków. Laya zaliczyła 6/15 i nie spełnia
kryterium poprawnego routingu.** Historyczna luka G1 jest zamknięta dla Ollamy,
a pomijane wcześniej testy kontraktu T1 wykonano w pełnym zestawie 68 testów.
Nie znaleziono nowej regresji w dwóch minimalnych poprawkach uruchomieniowych.
Panel Mailpit został dodatkowo sprawdzony niezależnie z hosta: HTTP 200.
SMTP pozostaje niepublikowany, a sieci `smtp` i `app` pozostają wewnętrzne.
Jawny cache PyTorch korzysta z zapisywalnego `/tmp`; przebudowa i rzeczywisty
przebieg Laya potwierdzają wykonanie inferencji po wcześniejszej awarii preloadu.

Pozostałe ograniczenia odbioru:

- Laya błędnie skierowała przypadki 1, 2, 3, 4, 5, 9, 11, 12 i 14. Wszystkie
  przeszły potwierdzenie `submitted` i odczyt MIME, ale te dziewięć zakończyło
  test na odbiorcy. Nie potwierdzono dla nich dalszych asercji Reply-To,
  Message-ID, korelacji i treści. Szybsza inferencja nie oznacza zaliczenia testu.
- Niezawodność startu pozostaje niepotwierdzona. Po wcześniejszym błędzie
  `model-init` bez zachowanego szczegółowego logu, końcowe przywracanie domyślnej
  konfiguracji ponownie zakończyło się błędem sondy gotowości:
  `model did not produce a native tool call`. Zachowano
  [dowód awarii](evidence/2026-09-25/bootstrap-failure.txt). Cztery kolejne sondy
  na rozgrzanym modelu i jedna po jego wyładowaniu zwróciły poprawne natywne
  wywołanie; krytyk sprawdził ich surowe odpowiedzi. Nie zachowano jednak surowej
  odpowiedzi z błędnego wywołania. Przyczyna pozostaje nieustalona, a problem
  uruchomieniowy pozostaje otwarty mimo udanych ponowień i E2E.
- Wynik Ollamy dotyczy jednego przebiegu 15 syntetycznych wiadomości w Mailpit.
  Nie certyfikuje ogólnej trafności, odporności na prompt injection ani
  produkcyjnego dostarczania poczty. OpenRouter nadal nie został wykonany.

Raport weryfikacji poprawnie rozdziela sprawny runtime Laya od niezaliczonej
trafności i ujawnia okresowy błąd startu Ollamy. Nie znaleziono materialnej
sprzeczności z zachowanymi dowodami. Całego PoC nie należy opisywać jako
bezwarunkowo gotowego: pozostają niezaliczony routing Laya i niestabilny start.

## Historyczny przegląd przed udostępnieniem Dockera i sieci

Poniższy raport zachowano jako zapis pierwszego przeglądu. Jego informacje
o niewykonanych buildach, E2E i pominiętych testach zastępuje aktualizacja wyżej.

Data: 25.09.2026. Krytyk sprawdził rzeczywisty kod wszystkich usług, Compose,
Dockerfile, wymagania, przykłady env, kontrakty i testy. Opisy README nie zostały
potraktowane jako dowód wykonania. Raport dotyczy samodzielnego PoC, nie wymaga
rozbudowy do systemu produkcyjnego.

## Werdykt

Struktura realizuje uzgodniony cel: osobne kontenery i protokoły, brak wspólnej
bazy aplikacji, niezależny mailer oraz Service Layer Pattern. Ścieżka routera
korzysta z prawdziwego narzędzia LangChain i odrzuca zwykły tekst modelu jako
potwierdzenie wykonania. Nie znalazłem potrzeby zmiany architektury ani dodania UMC.

**Nie można jeszcze odebrać PoC jako działającego po `docker compose up -d`.**
Build obrazów, inicjalizacja rzeczywistego modelu i przejście HTTP -> model ->
narzędzie -> SMTP -> Mailpit pozostają niewykonane. Jest to luka dowodowa,
nie stwierdzenie, że Compose lub wybrany model są uszkodzone.

## Ustalenia według wagi

### G1 - blokada odbioru: brak rzeczywistego E2E

- Lokalizacja: `docker-compose.yml:22-117`, `services/model-init/bootstrap.py:26-66`,
  `verification/e2e.py:51-98`, `tests/test_openai_wire.py:11-14`.
- Lokalny zestaw testów podstawia odpowiedzi modelu i transportu SMTP. Potwierdza
  reguły wykonywania, walidację, tworzenie MIME i idempotencję, ale nie dostępność
  obrazów, poprawną instalację pełnego stosu ani to, że `qwen3:1.7b` wybiera
  wymagane działy przez natywne `tool_calls`.
- Test rzeczywistego klienta ChatOpenAI jest pomijany na tym hoście, bo paczka
  `langchain-openai` nie jest dostępna w środowisku offline. Import klienta w
  normalnym lifespan API nie został wykonany przez testy z wstrzykniętą usługą.
- Wymagana kontrola przed oddaniem jako gotowe: build/start w dozwolonym środowisku
  Docker, kontenerowe testy bez pominięcia ChatOpenAI i 15/15 wyników E2E dla Ollamy
  z przechwyconym MIME. Wariant Laya wymaga osobnego rzeczywistego przebiegu.
  OpenRouter można pozostawić oznaczony jako niewykonany bez klucza użytkownika.
- Ograniczenia gniazda Docker i sieci tej sesji są rzeczywistym blokerem wykonania;
  krytyk ich nie obchodził i nie utożsamia ich z wyłączonym daemonem hosta.

### P2 - zamknięte: mapowanie błędów rejestru mailera

- Lokalizacja poprawki: `services/mailer/mailer_app/service.py:16-22`, `:34-60`.
- Błąd `repository.reserve()` oraz błąd `repository.finish()` podczas obsługi
  odrzucenia lub niepewnego wyniku SMTP wychodzi jako nieobsłużony wyjątek.
  Odtworzono przez rzeczywisty kontroler ASGI: `sqlite3.OperationalError` podczas
  rezerwacji oraz po `SubmissionUnknown` zwracają HTTP 500 `Internal Server Error`,
  bez umówionego JSON `code`.
- To narusza kontrakt niezależnego serwisu i gubi rozróżnienie wyniku wysyłki.
  Publiczny gateway routera zachowuje się konserwatywnie i mapuje takie 500 na
  `delivery_unknown`; nie znaleziono automatycznej ponownej wysyłki.
- Poprawiono podczas przeglądu. Ponowienie obu kontroli ASGI daje teraz HTTP 502
  i odpowiednio `mailer_unavailable` / `delivery_unknown`. Kod zachowuje jawne
  `DeliveryError`, a awaria rezerwacji nie uruchamia SMTP. Nowe regresje sprawdzają
  zero wywołań przy błędzie rezerwacji i dokładnie jedno przy błędzie późniejszego
  zapisu oraz zachowanie rezerwacji `sending`. Istniejący test restartu potwierdza
  przejście takich rezerwacji w `unknown`. Nie dodano retry.

### T1 - test zgodności ChatOpenAI z adapterem Laya dodany, wykonanie zablokowane

- Lokalizacja: `tests/test_openai_wire.py:17-76`, `tests/test_laya.py:26-60`,
  `services/router/router_app/main.py:42-52`.
- Początkowo jeden test dostawał gotową odpowiedź OpenAI z MockTransport, a drugi
  ręcznie składał request adaptera. Nie sprawdzały wspólnie serializacji ChatOpenAI
  i restrykcyjnego DTO adaptera, które zabrania nieznanych pól.
- Dodano `test_real_chatopenai_payload_is_accepted_by_laya_adapter`
  (`tests/test_openai_wire.py:79`): rzeczywisty ChatOpenAI z limitem/timeoutem jak
  w composition root, rzeczywista aplikacja adaptera ASGI, wstrzyknięty
  DecisionEngine, router i kontrola jednego wywołania portu mailera.
- Krytyk przeczytał test, ale nie potwierdza jego przejścia: cały moduł pozostaje
  pominięty z powodu brakującego `langchain-openai`. Uruchomić go w kontenerowym
  zestawie testowym. Nawet wtedy będzie dowodem kontraktu, nie działania modelu Laya.

## Potwierdzone zalety i granice zakresu

- Router, mailer i adapter mają własne moduły domeny, portów, usług i composition
  roots. Usługi zależą od portów, bez importowania frameworków czy adapterów.
  Build contexts aplikacji nie obejmują kodu sąsiada. Jedynie kontener testowy
  zawiera wszystkie usługi w celu testowania.
- Mailer posiada własny wolumen SQLite. Router nie czyta go i nie zna SMTP;
  komunikacja odbywa się przez wersjonowany HTTP. Mailpit ma osobny wolumen.
- Model otrzymuje schemat z dokładnie pięcioma adresami. Narzędzie nie pozwala
  zmienić treści ani Reply-To, a mailer ponownie weryfikuje odbiorcę. Oryginalna
  treść i adres pochodzą z requestu, nie z odpowiedzi modelu.
- `StructuredTool.ainvoke()` jest faktycznie wykonywane po walidacji pojedynczego
  `AIMessage.tool_calls`; nie jest to parsowanie JSON z tekstu ani fikcyjna
  deklaracja wysłania. Zakończenie po akcji wysyłkowej jest właściwe dla tego PoC.
- Rezerwacja SQLite poprzedza SMTP, nieznane wyniki nie są ponawiane, a restart
  przekształca pozostawione `sending` w `unknown`. Brak deduplikacji ponownych
  publicznych POST jest jawnie opisany i nie został uznany za rozszerzenie zakresu.
- Swagger ma wymaganą ścieżkę. Compose zawiera warunki gotowości i jednorazowy
  init pobierający model. Poprawna konfiguracja nie dowodzi rzeczywistego startu.
- Klient routera jest wspólny dla wszystkich wariantów. Laya jest jawnie
  dodatkowym typed-choice adapterem, a nie natywnym function calling LLM.
  Nie udaje spełnienia tego wymagania przez lokalny LLM.
- Brak publicznego auth, limitów ruchu, HA i UMC jest zgodny z ustalonym zakresem
  lokalnego PoC. Nie zalecam ich dodawania w celu zamknięcia tego przeglądu.

## Wykonane kontrole

- `pytest -q`: **65 passed, 1 skipped**, jeden warning zależności Starlette/AnyIO.
- `ruff check services tests verification`: PASS.
- `ruff format --check services tests verification`: PASS, 36 plików.
- `docker compose config --quiet`: PASS dla domyślnej Ollamy, env Laya i OpenRouter.
- Odtworzenie awarii rejestru przez kontroler ASGI: początkowo 500, po poprawce
  oba opisane przypadki dają 502 z właściwym kodem.
- Walidacja niepoprawnych `schema.properties` w adapterze Laya: `null`, lista i
  `{"recipient": null}` dają już 400. Tę lukę znaleziono i poprawiono podczas
  przeglądu; ponowna kontrola potwierdziła poprawkę.

Przeczytano również oficjalny [kod Router Laya](https://raw.githubusercontent.com/NandhaKishorM/laya/main/laya/router.py),
[serwer Laya](https://raw.githubusercontent.com/NandhaKishorM/laya/main/laya/serve.py)
oraz [dokumentację kolejności startu Compose](https://docs.docker.com/compose/how-tos/startup-order/).
SDK rzeczywiście udostępnia jawny parametr `max_len`; odczyt źródła nie zastępuje
uruchomienia przypiętej wersji pakietu i rzeczywistego checkpointu.

Raport należy odświeżyć po wykonaniu brakujących kontroli.

## Finalne uproszczenie integracji Ollama/LangChain, 25.09.2026

Świeży agent krytyk przeczytał finalny kod i zainstalowane źródła LangChain,
nie tylko opis zmian. Samodzielnie zaliczył 79 testów hosta. Nie znalazł
blokującego błędu. Potwierdził, że `create_agent` zarządza bindingiem, inferencją
i wykonaniem toola, a `return_direct` kończy graf bez ponownej inferencji.
Middleware odrzuca błędne, wielokrotne i ucięte wywołania przed wysyłką.
Błędy mailera propagują bez ponowień. Zachowano oryginalną treść i Reply-To,
mapowanie działów oraz niezależność warstw i serwisów.

Ograniczenie wskazane przez krytyka: deduplikacja wewnętrznego mailera dotyczy
tego samego ID; drugi publiczny POST tworzy nowe ID i może wysłać kolejny mail.
Krytyk nie wykonywał inferencji ani operacji Docker. Osobne kontrole prowadzącego
po jego przeglądzie potwierdziły stockowy szablon na 0.13.5, 116 testów w
kontenerze i 5/5 zgłoszeń smoke. Benchmark 500 przypadków pozostaje zatrzymany.

## Świeży przegląd neutralności po poprawkach

Poprzedni dodatkowy przegląd ocenił neutralność jako PARTIAL: agent nadal miał
heurystykę zużycia tokenów Ollamy i wysyłał prywatne x-choice do wszystkich
dostawców. Obie uwagi zostały naprawione na polecenie użytkownika.

Nowy niezależny krytyk przeczytał kod po zmianach i zaliczył 101 testów. Nie
znalazł blokera w zakresie naprawy. Potwierdził brak heurystyki licznika tokenów,
standardowy JSON Schema anyOf z opisanymi singleton enums, zachowanie wejścia
Laya, właściwe użycie create_agent i brak ponowień wysyłki. Walidacja dokładnie
jednego narzędzia, mapowanie dozwolonego działu i zachowanie oryginalnego maila
pozostają regułami biznesowymi, a nie wyjątkami konkretnego modelu.

Krytyk nie uruchamiał inferencji ani Dockera. Ograniczenie dowodów: kontrolowane
odpowiedzi HTTP potwierdzają przenośność klienta, nie zgodność każdego dostawcy.
Prowadzący osobno sprawdził oba rzeczywiste lokalne warianty i opisał wyniki
5/5 Ollamy oraz 4/5 Laya w VERIFICATION.md.

## Routing-policy revision, 2026-09-25

Fresh agent routing_policy_critic inspected the changed application, env/Compose
wiring, real SDK tests, installed LangChain source and the Laya schema contract.
No concrete defect found: middleware override reaches bind_tools, named choice
serializes correctly, and Laya's input is unchanged. No provider branch, retry
or repair was added. Critic ran no tests/inference and explicitly did not certify
model accuracy. Parent observed four public cases: two pass, two still fail;
details in evidence/2026-09-25/routing-policy/README.md.

## Env-only model comparison, 2026-09-25

Fresh model_comparison_critic independently inspected qwen4b-instruct/ artifacts,
prior routing-policy/ requests, application/manifest hashes and live Mailpit.
No evidence blocker: four correct calls/deliveries; only model changed on the
wire; all four MIME bodies, recipients, Reply-To and correlations confirmed.
Four selected cases do not establish general accuracy; model package changes
weights and stock template. No inference/tests/mutations by the critic.

## Stopped-run forensic review, 2026-09-26

Fresh fluke_evidence_critic recomputed all 190 saved outcomes independently from
corpus, raw wire, SDK and MIME. It found no score inflation/direct label leakage
and confirmed four identical-input repeated successes. It highlighted two-class
coverage, 95 correlated pairs, prior corpus exposure and unmeasured repeatability.
The parent's separate complete-log and live-mail audit found no hidden attempts
or duplicate deliveries. No model calls or mail were made during review.

Earlier runner critic recommendations were incorporated into the final partial
auditor: expected label and boolean/derived score consistency, category total
conservation, all trace correlations and explicit partial-run status.
