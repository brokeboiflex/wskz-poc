# Stan weryfikacji

Data: 25.09.2026. Implementacja i niezależny przegląd zakończone. Pełny odbiór
uruchomieniowy pozostaje zablokowany przez ograniczenia środowiska.

- Konfiguracja Compose: PASS dla domyślnej Ollamy, `.env.laya-example` i `.env.openrouter-example`.
- Testy Python 3.12: **66 passed, 1 skipped**. Pominięty został moduł `test_openai_wire.py` (dwa scenariusze wymagające niedostępnego w cache `langchain-openai`). Testowy obraz instaluje tę paczkę i powinien uruchomić cały moduł. Jeden warning dotyczy przestarzałego aliasu AnyIO w Starlette TestClient.
- `ruff check services tests verification`: PASS. `ruff format --check services tests verification`: PASS.
- Kontrakt wewnętrzny: test przechodzi przez rzeczywiste kontrolery ASGI routera i mailera, Service Layer, narzędzie LangChain, HTTP gateway, SQLite oraz budowanie MIME. Na granicach modelu i SMTP używa kontrolowanych odpowiedzi; nie jest rzeczywistą inferencją ani przechwyceniem sieciowego SMTP.
- Testy trwałości: duplikat, konflikt payloadu, współbieżna rezerwacja, utrata odpowiedzi SMTP, awaria zapisu przed/po SMTP, restart niedokończonego zlecenia. Wszystkie PASS.
- Testy inicjalizacji: istniejący/brakujący model, brak pobierania i płatnej inferencji dla zewnętrznego dostawcy, brak native tool calla, błąd autoryzacji i ograniczony czas oczekiwania. Wszystkie PASS.
- Build obrazów i uruchomienie: niewykonane. Sandbox terminala odmawia dostępu do gniazda Docker (`permission denied`), mimo autoryzacji użytkownika. Nie oznacza to, że Docker na hoście jest wyłączony.
- Pobranie wag, rzeczywista klasyfikacja, przechwycenie SMTP: niewykonane w tej sesji.
- OpenRouter: niewykonane, nie dostarczono klucza dla tego projektu.
- Laya: zweryfikowano oficjalne SDK/HTTP źródłowo; trafność i wydajność wymagają rzeczywistego modelu.
- Niezależny krytyk: [CRITIC.md](CRITIC.md). Potwierdził strukturę mikroserwisów, Service Layer i rzeczywiste wykonywanie narzędzia. Wskazane błędy walidacji schematu Laya oraz mapowania awarii SQLite poprawiono i sprawdzono ponownie. Krytyk uruchomił 65 testów; późniejszy dodatkowy test integracji ASGI podniósł wynik głównego przebiegu do 66.

Testy z kontrolowanymi odpowiedziami zależności nie są dowodem działania modelu
ani całego Compose. DoD pozostaje niepotwierdzone do przejścia kontenerowego E2E.

## Kryteria odbioru

| Kryterium                           | Implementacja / lokalny dowód                                    | Brakująca kontrola                                   |
| ----------------------------------- | ---------------------------------------------------------------- | ---------------------------------------------------- |
| Start jednym poleceniem             | Compose poprawny dla wszystkich env, init i zależności gotowości | Rzeczywisty build i `docker compose up -d`           |
| Swagger `/api/v1/docs`              | PASS przez rzeczywisty kontroler ASGI                            | HTTP opublikowanego kontenera                        |
| README                              | Obecny w katalogu głównym samodzielnego projektu                 | Brak                                                 |
| Agent i native tool calling         | Schemat tools i rzeczywisty StructuredTool sprawdzone lokalnie   | Pełny ChatOpenAI oraz rzeczywista Ollama             |
| Poprawny dział                      | Polityka, zamknięta lista i 15 przypadków odbioru                | Trafność rzeczywistego modelu, bez deklaracji wyniku |
| Wiadomość w Mailpit                 | Konfiguracja transportu i skrypt kontroli raw MIME               | Rzeczywisty SMTP i panel Mailpit                     |
| Reply-To                            | PASS dla MIME i integracji aplikacji z kontrolowanym SMTP        | Raw MIME z Mailpit po rzeczywistej wysyłce           |
| Oddzielne kontenery / Service Layer | PASS testów granic importów i niezależnego krytyka               | Brak potwierdzonej wady architektury                 |

## Komendy brakującej weryfikacji

```sh
docker compose up -d --build
docker compose --profile test run --build --rm tests
docker compose --profile test run --build --rm e2e
docker compose --env-file .env.laya-example up -d --build
docker compose --env-file .env.laya-example --profile test run --build --rm e2e
```

Przed zmianą wariantu zatrzymać poprzedni zgodnie z README, zachowując wolumeny.
Nie przenosić statusów PASS z testów jednostkowych na brakujące wiersze E2E.
