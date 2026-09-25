# Niezależny przegląd implementacji

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
