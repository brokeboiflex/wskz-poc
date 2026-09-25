# Stan weryfikacji

Data: 25.09.2026. **Po korekcie semantycznej Laya: 13/15, nadal FAIL akceptacji.**
Model wybiera dział na podstawie treści i opisów; adres ustala aplikacja.
Nie trenowano wag. Poprzedni pomiar Laya 6/15 pozostaje poniżej jako historia.

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
