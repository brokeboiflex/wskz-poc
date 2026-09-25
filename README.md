# Inteligentny router wiadomości

PoC mikroserwisów: Python, FastAPI, LangChain, lokalna Ollama i Mailpit.
Agent analizuje wiadomość i wykonuje narzędzie wysyłkowe przez native function
calling. Osobny serwis pocztowy przekazuje oryginalną treść przez SMTP do Mailpit,
ustawiając `Reply-To` na adres z requestu.

## Uruchomienie

Wymagania: Docker Engine / Docker Desktop z Compose **2.24 lub nowszym**, internet
przy pierwszym pobraniu obrazów i wag, wolne porty 8000 i 8025. Przeznacz na początek
8 GB RAM dla Dockera i zapas miejsca na obrazy oraz modele; jest to zalecenie
startowe, nie zmierzony minimalny próg. Domyślna konfiguracja używa CPU, także
w Docker Desktop na Apple Silicon. Nie wymaga Pythona ani klucza API na hoście.

Z głównego katalogu tego projektu:

```sh
docker compose up -d
```

Nie trzeba tworzyć `.env`. Compose buduje obrazy, uruchamia Ollamę i Mailpit,
pobiera `qwen3:1.7b`, rozgrzewa model i sprawdza rzeczywiste tool calling bez wysyłki
maila. API startuje po pomyślnej inicjalizacji i gotowości mailera. Pierwszy start
może potrwać kilka minut lub dłużej, zależnie od internetu i CPU. Kolejne starty
wykorzystują zachowane wagi. Błąd inicjalizacji blokuje start API.

- Swagger: <http://localhost:8000/api/v1/docs>
- OpenAPI: <http://localhost:8000/api/v1/openapi.json>
- Mailpit: <http://localhost:8025>
- Gotowość: <http://localhost:8000/health/ready>

```sh
curl --fail-with-body http://localhost:8000/api/v1/messages \
  -H 'Content-Type: application/json' \
  -d '{"email":"jan.nowak@example.com","message":"Chciałbym zgłosić urlop na jutro"}'
```

Przykładowy kształt odpowiedzi (identyfikatory są generowane dla requestu):

```json
{
  "request_id": "e19f7b8a-1d0b-4a54-9f7c-cb0674fa5950",
  "recipient": "kadry@example.com",
  "status": "submitted",
  "message_id": "<e19f7b8a-1d0b-4a54-9f7c-cb0674fa5950@message-router.local>"
}
```

`submitted` oznacza akceptację SMTP, nie przeczytanie wiadomości przez człowieka.
W domyślnym środowisku odbiorcą SMTP jest Mailpit. Nie ma połączenia z produkcyjną
skrzynką ani dostarczania maili na zewnętrzne adresy.

## Architektura i Service Layer Pattern

```mermaid
flowchart LR
    User[Klient HTTP] --> API[Router API / Python]
    API --> LLM[Ollama / Chat Completions]
    LLM -->|native tool call| API
    API -->|narzędzie: HTTP /internal/v1/deliveries| Mailer[Mailer / Python]
    Mailer --> Ledger[(Prywatny rejestr SQLite)]
    Mailer -->|SMTP| Mailpit[Mailpit]
    API -. alternatywny base URL .-> Adapter[Laya adapter / Python]
    Adapter -->|HTTP /v1/systemone| Laya[Laya runtime / Python]
    API -. alternatywny base URL .-> Cloud[OpenRouter]
```

| Kontener       | Odpowiedzialność                                                    |
| -------------- | ------------------------------------------------------------------- |
| `api`          | Publiczny endpoint, agent LangChain, wybór działu i wywołanie toola |
| `mailer`       | Niezależne API wysyłki, MIME, SMTP, własny trwały rejestr zleceń    |
| `mailpit`      | Przechwytywanie wiadomości oraz panel i API do ich kontroli         |
| `ollama`       | Lokalny model przez protokół OpenAI Chat Completions                |
| `model-init`   | Jednorazowe pobranie, rozgrzanie i kontrola dostępności modelu      |
| `laya-adapter` | Opcjonalna translacja typowanej decyzji na `tool_calls`             |
| `laya-runtime` | Opcjonalny silnik Laya, bez zależności od routingu i poczty         |

Router, mailer i adapter mają osobne obrazy, zależności, konfigurację i kontrakty
HTTP. Nie importują kodu sąsiada i nie współdzielą bazy. Mailer nie zna modelu,
a router nie zna SMTP ani bazy mailera. Sieć `smtp` jest wewnętrzna i niedostępna
routerowi; porty SMTP, mailera i modeli nie są publikowane na hoście. Połączenie
z dostawcą modelu jest jedyną zależnością routera wymagającą wyjścia do internetu.
Mailpit ma dodatkową sieć `mailpit-ui`, dzięki której Docker publikuje panel na
`127.0.0.1:8025`. Sama sieć `internal` nie zapewnia publikacji portu na hoście.
Port SMTP pozostaje niepublikowany, a mailer korzysta z wewnętrznej sieci `smtp`.

W każdej aplikacji biznesowej:

1. **Kontroler HTTP** waliduje DTO, wywołuje usługę i mapuje odpowiedź/błąd.
2. **Service layer** realizuje przypadek użycia przez porty (`Protocol`).
3. **Domena** zawiera wartości i błędy, bez FastAPI, LangChain czy SMTP.
4. **Adaptery** implementują komunikację z modelem, HTTP mailera, SMTP i SQLite.
5. **Composition root** (`main.py`) tworzy zależności w lifecycle aplikacji.

Agent jest celowo ograniczony do jednej decyzji i jednej czynności końcowej.
`ChatOpenAI.bind_tools()` przekazuje rzeczywisty schemat narzędzia do modelu.
Adapter sprawdza `AIMessage.tool_calls`, waliduje pojedyncze wywołanie i uruchamia
zarejestrowane narzędzie LangChain przez `StructuredTool.ainvoke()`.
Tekst „wysłano” ani JSON w zwykłej odpowiedzi nie powoduje wysyłki. Po potwierdzeniu
SMTP nie ma kolejnej inferencji, która mogłaby wywołać ponowną wysyłkę lub zmienić
wynik na błąd. Brak poprawnego wywołania narzędzia daje HTTP 502.

## Zasady routingu

Zadanie nie precyzuje granicy między HR i kadrami ani help deskiem i IT. Dlatego
przyjęto następujący jawny podział, zapisany w polityce routera:

| Dział                         | Typ sprawy                                                             |
| ----------------------------- | ---------------------------------------------------------------------- |
| `human-resources@example.com` | Rekrutacja, szkolenia, rozwój, relacje pracownicze                     |
| `kadry@example.com`           | Urlopy, płace, czas pracy, dokumenty zatrudnienia                      |
| `help-desk@example.com`       | Pomoc pojedynczemu użytkownikowi: komputer, drukarka, hasło            |
| `it@example.com`              | Infrastruktura, serwery, awarie sieci/systemów, cyberbezpieczeństwo    |
| `other@example.com`           | Nierozpoznany temat, treść niezwiązana z działami lub niewystarczająca |

Fallback jest decyzją semantyczną. Awaria modelu nie jest zamieniana na wysyłkę do
`other`. Dla kilku tematów agent ma wybrać główną prośbę. Nie deklarujemy idealnej
trafności małego modelu: mierzy ją zestaw akceptacyjny w `verification/cases.json`.

## Dostawcy przez env

Klient routera pozostaje ten sam. Zmieniają się `OPENAI_BASE_URL`, `OPENAI_API_KEY`,
`OPENAI_MODEL` oraz sposób inicjalizacji i profil potrzebnych kontenerów.
Obsługiwany jest tekstowy Chat Completions z function calling. Nie każdy model
oferowany przez dostawcę obsługuje tools. Rozszerzenia Responses API, multimodalność
i specyficzne parametry reasoning nie są częścią wspólnego kontraktu.

Przykłady nie zawierają sekretów:

```sh
# Ollama; równoważne domyślnemu uruchomieniu.
docker compose --env-file .env.ollama-example up -d

# Laya: uruchamia dodatkowo silnik i adapter, bez pobierania wag Ollamy.
docker compose --env-file .env.laya-example up -d
```

Dla OpenRouter skopiuj `.env.openrouter-example` do ignorowanego `.env`, wpisz
własny klucz i wybierz dostępny model obsługujący tools, następnie:

```sh
docker compose up -d
```

Ollama pozostaje uruchomiona także przy dostawcy zewnętrznym, ale bez pobierania
niepotrzebnych wag. Przy przełączaniu wariantu zachowaj ten sam plik env we
wszystkich komendach. Aby zatrzymać poprzedni wariant przed zmianą, użyj
`docker compose --env-file <poprzedni-plik> down` bez `--volumes`; dane pozostaną.
Po zmianie kodu użyj `up -d --build`. `.env.example` opisuje pełną konfigurację.

### Różnica wariantu Laya

Laya jest rzeczywistym modelem typowanych decyzji, nie modelem generującym natywne
wywołania funkcji. Adapter przyjmuje dokładnie jedno narzędzie z jednym argumentem
`string enum`, przekazuje opcje i instrukcje przez HTTP do Laya, a odpowiedź
`choice` opakowuje w `tool_calls`. Sam nie zna adresów działów i nie klasyfikuje
słowami kluczowymi. Nie ma dostępu do mailera.

Silnik ładuje checkpoint `multilingual` przed zgłoszeniem gotowości. Cienki host
wykorzystuje publiczne `Router.predict(..., max_len=8192)` i format
`/v1/systemone`. Jawny limit chroni przed użyciem domyślnych 1024 tokenów serwera
upstream. Adapter przyjmuje do 7000 bajtów łącznej treści, instrukcji i opcji;
nadmiar jest odrzucany, a nie obcinany. To dodatkowy wariant porównawczy.
**Ścieżką spełniającą wymaganie lokalnego LLM z natywnym function calling jest Ollama.**

W rzeczywistym teście z 25.09.2026 Ollama uzyskała **15/15**, a Laya **6/15**
poprawnych wyników. Laya uruchamia się i wysyła wiadomości do Mailpit, lecz nie
spełnia kryterium trafności routingu. Wyniki i granice dowodów:
[raport weryfikacji](docs/VERIFICATION.md).
Podczas testów wystąpiły też okresowe błędy sondy tool calling w inicjalizatorze
Ollamy, blokujące start API. Ich przyczyna pozostaje nieustalona; udany przebieg
E2E nie stanowi potwierdzenia niezawodności każdego startu.

## Błędy, potwierdzenia i dane

- HTTP 422: niepoprawny e-mail, pusta wiadomość, ponad 4000 znaków lub nadmiarowe pola.
- HTTP 502 z `code` i `request_id`: awaria modelu, błędne tool calling lub niepotwierdzona wysyłka.
- Model wybiera wyłącznie odbiorcę z enum. Reply-To i treść pochodzą z requestu,
  From z konfiguracji mailera. Dodatkowe argumenty narzędzia są odrzucane.
- Mailer sprawdza swoją listę dopuszczonych odbiorców i token połączenia usługowego.
  Domyślny token jest publiczną wartością PoC, a port mailera pozostaje wewnętrzny.
- Każdy request ma UUID, przekazywany do mailera jako klucz zlecenia i nagłówek
  `X-Request-ID`. Mailer zapisuje rezerwację przed SMTP. Ten sam UUID i payload
  zwracają wcześniejsze potwierdzenie, inny payload daje konflikt.
- `failed` oznacza znane odrzucenie, `unknown` brak pewnego potwierdzenia.
  Po restarcie niedokończone `sending` przechodzi w `unknown`. Nie ma automatycznego
  ponawiania niepewnych operacji. Mailer pracuje jako **jedna instancja na wolumen**.
- Awaria zapisu rezerwacji daje `mailer_unavailable` przed jakąkolwiek próbą SMTP.
  Awaria utrwalenia wyniku po wywołaniu transportu daje `delivery_unknown`.
- Ponowne wysłanie publicznego POST tworzy nowe zgłoszenie. Nie jest deduplikowane
  między requestami. Nie ponawiaj go bez sprawdzenia Mailpit po błędzie niepewnej wysyłki.
- Status zlecenia jest dostępny przez chronione, wewnętrzne
  `GET /internal/v1/deliveries/{request_id}`. Treść i adres nadawcy nie trafiają do
  logów aplikacji. Rejestr mailera przechowuje hash payloadu i potwierdzenia,
  a pełne wiadomości przechowuje Mailpit.

To PoC, bez publicznego uwierzytelniania, limitów ruchu, HA ani produkcyjnego MTA.
Lokalne porty są ograniczone do loopback. Unified Mail Core nie jest wymagany ani
dołączony: ewentualny adapter z jego outboxem może zastąpić mailer za tym samym
kontraktem, ale status `queued` nie może udawać `submitted`.

## Testy i diagnostyka

```sh
# Konfiguracja nie wymaga działającego daemonu.
docker compose config --quiet

# Testy jednostkowe, kontraktowe i granic architektury, bez dostępu do sieci w runtime.
docker compose --profile test run --build --rm tests

# Prawdziwy model + HTTP + SMTP + Mailpit, 15 wiadomości po polsku.
docker compose --profile test run --build --rm e2e

# Ta sama weryfikacja dla Laya.
docker compose --env-file .env.laya-example --profile test run --build --rm e2e

docker compose ps -a
docker compose logs --tail 100 model-init api mailer
```

Test E2E kontroluje Swagger, adres docelowy, surowy MIME, Reply-To, Message-ID,
korelację i treść każdego maila. Kończy się błędem, jeśli którykolwiek przypadek
nie przejdzie. Nie kasuje istniejących wiadomości; każde uruchomienie dodaje nowy
zestaw syntetyczny. Wynik wypisuje jako JSONL, wraz z opóźnieniami.

Przy nieudanym pobraniu zachowaj wolumen i ponów `docker compose up -d model-init`.
Po naprawie inicjalizacji uruchom `docker compose up -d`. Błąd klucza, nieistniejący
model, brak native tool calling i timeout inicjalizacji mają pozostać widocznymi
błędami. Nie podmieniaj modelu na atrapę w celu uzyskania zielonego healthchecka.

Stan faktycznie wykonanych kontroli i ograniczenia: [VERIFICATION.md](docs/VERIFICATION.md).
Odtwarzalne podejście i wznowienie: [APPROACH.md](docs/APPROACH.md).
Kontrakty usług: [CONTRACTS.md](docs/CONTRACTS.md).

## Referencje

- [LangChain tools](https://docs.langchain.com/oss/python/langchain/tools)
- [ChatOpenAI i tool calling](https://docs.langchain.com/oss/python/integrations/chat/openai)
- [Ollama OpenAI compatibility](https://docs.ollama.com/api/openai-compatibility)
- [Gotowość zależności Compose](https://docs.docker.com/compose/how-tos/startup-order/)
- [Mailpit API](https://mailpit.axllent.org/docs/api-v1/)
- [Laya, SDK i granice modelu](https://github.com/NandhaKishorM/laya)
