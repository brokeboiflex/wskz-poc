# Zatwierdzone podejście, wykonanie i wznowienie

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
Pomiar CPU i RAM podczas tego samego testu syntetycznego:
[RESOURCE_MEASUREMENT.md](RESOURCE_MEASUREMENT.md).

Zatwierdzony syntetyczny benchmark 500 wiadomości po polsku, źródła scenariuszy,
walidacja i komendy uruchomienia: [BENCHMARK_APPROACH.md](BENCHMARK_APPROACH.md).
To 250 rodzin scenariuszy w dwóch wariantach, po 100 wiadomości na dział.

## Implementacja

1. Router: FastAPI → RoutingService → port RoutingAgent i port DeliveryGateway.
   Adapter LangChain używa ChatOpenAI i rzeczywistego StructuredTool. Odrzuca brak,
   nadmiar i błędne argumenty tool calla. Wysyłka kończy wykonanie agenta.
2. Mailer: osobne API → DeliveryService → własny rejestr SQLite i SMTP.
   Trwała rezerwacja z UUID i hashem payloadu przed wywołaniem SMTP. Statusy
   submitted/failed/unknown, bez automatycznych ponowień.
3. Ollama: osobny kontener. Model-init sprawdza/pobiera wagi i wykonuje neutralny
   tool call gotowości bez jakiejkolwiek wysyłki.
4. Laya: osobne kontenery adaptera protokołu i silnika. Adapter przekłada jedno
   narzędzie z argumentem enum na typed choice. Silnik korzysta z publicznego SDK
   `Router.predict(..., model="multilingual", max_len=8192)` i preloadu modelu.
   Własny cienki host zapewnia jawny budżet, którego domyślny serwer upstream nie
   przekazuje w wywołaniu predict. Zachowany format `/v1/systemone`.
   Korekta zatwierdzona 25.09: enum opisuje działy, nie adresy; `x-choice`
   przekazuje krótkie pytanie i opis każdej kategorii. Router mapuje wynik
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
