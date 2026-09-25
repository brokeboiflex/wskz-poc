# Kontrakty usług v1

Usługi nie dzielą bibliotek domenowych ani bazy. Zgodność weryfikują testy
kontraktowe. Zmiana niekompatybilna wymaga nowej wersji ścieżki API.

## Router publiczny

`POST /api/v1/messages`, JSON:

```json
{
  "email": "jan.nowak@example.com",
  "message": "Chciałbym zgłosić urlop na jutro"
}
```

Email walidowany składniowo. Message: 1-4000 znaków, nie same białe znaki.
Pozostałe pola są zabronione. HTTP 200 zawiera `request_id`, `recipient`,
`status: submitted` i `message_id`. HTTP 422 oznacza błąd wejścia. HTTP 502 zawiera
`code` i `request_id`; nie upoważnia do automatycznego ponowienia POST.

`/health/live` sprawdza proces. `/health/ready` sprawdza dostępność skonfigurowanego
modelu przez `/v1/models` i gotowość mailera. Błędy skutkują 503. Gotowość nie jest
pomiarem trafności modelu. Swagger jest pod `/api/v1/docs`.

## Mailer wewnętrzny

`POST /internal/v1/deliveries`, nagłówek `Authorization: Bearer <MAILER_TOKEN>`:

```json
{
  "request_id": "e19f7b8a-1d0b-4a54-9f7c-cb0674fa5950",
  "recipient": "kadry@example.com",
  "reply_to": "jan.nowak@example.com",
  "message": "Chciałbym zgłosić urlop na jutro"
}
```

`request_id`: UUID i trwały klucz idempotencji w obrębie mailera. Odbiorca musi
być na skonfigurowanej liście. From i Subject należą do serwisu. SMTP envelope
zawiera wyłącznie jednego wskazanego odbiorcę. Nie ma parametrów CC/BCC.

HTTP 200: `request_id`, `recipient`, `status: submitted`, `message_id`.
HTTP 401: brak/poprawność tokenu. HTTP 422: walidacja lub `recipient_not_allowed`.
HTTP 409: `idempotency_conflict` albo `delivery_in_progress`.
HTTP 502: `delivery_failed`, `delivery_unknown` lub `mailer_unavailable` (np. brak
możliwości zapisania rezerwacji przed SMTP). Awaria zapisu statusu po próbie SMTP
daje `delivery_unknown`. Nie wolno traktować błędu rejestru jako potwierdzenia wysyłki.

`GET /internal/v1/deliveries/{request_id}` wymaga tego samego tokenu. Zwraca
`sending`, `submitted`, `failed` lub `unknown`; 404, gdy brak zlecenia.
Nie jest publicznym endpointem routera i nie zwraca oryginalnej treści.

## Model OpenAI-compatible

`GET /v1/models`: `data[]` z `id`. `POST /v1/chat/completions`: tekstowe messages,
model, tools i limit odpowiedzi. Odpowiedź musi zawierać dokładnie jedno poprawne
`choices[0].message.tool_calls[]`. Nazwa: `send_department_email`.
Jedyny argument: `department` z enum `human_resources`, `payroll`, `help_desk`,
`it`, `other`. Model dostaje treść i opisy działów. Router mapuje zatwierdzony
wybór na adres odbiorcy; adresy docelowe nie są kategoriami modelu. Zwykła treść nie jest
interpretowana jako wywołanie narzędzia. Nie wysyłamy danych uwierzytelniających
mailera ani adresu Reply-To do modelu.

Ustawienia `MODEL_REASONING_EFFORT`, `MODEL_TEMPERATURE` i `MODEL_TOP_P` są
opcjonalne; puste wartości pomijają pola w requestach. `MODEL_TOKEN_LIMIT_FIELD`
wybiera `max_tokens` lub `max_completion_tokens`. Domyślny wariant Ollama używa
`max_tokens`, `reasoning_effort=none`, temperatury 0.7 i top_p 0.8.
Gotowość wymaga `GET /models` z dokładnym ID wybranego modelu. Zewnętrzny
endpoint musi obsługiwać Chat Completions, tool calling i użyte standardowe
schema; sam zgodny URL nie gwarantuje pełnej zgodności dostawcy.

LangChain `create_agent` wykonuje jedno wywołanie modelu z limitem
`MODEL_TIMEOUT_SECONDS`, walidację middleware i terminalne narzędzie wysyłki.
Błędny native tool call daje `invalid_tool_call` bez wywołania mailera;
timeout lub błąd dostawcy daje `model_unavailable`. Jawne zakończenie
`finish_reason=length` jest odrzucane; samo zużycie limitu tokenów nie oznacza błędu. Nie ma korekcyjnych ponowień
modelu, kolejnej inferencji po wysyłce ani automatycznego ponowienia mailera.

## Laya adapter i engine

Adapter obsługuje podzbiór powyższego protokołu: jeden tekst użytkownika, opcjonalny
system prompt, jedno narzędzie i jeden wymagany argument string enum. Odrzuca
streaming, multimodalność, historię wykonanych narzędzi, nieznane modele i
nieobsługiwane pola. Nazwa narzędzia i wartości enum pochodzą z requestu, bez
wbudowanej polityki działów. Maksymalnie 7000 bajtów kontekstu decyzji.

Opisane opcje używają standardowego JSON Schema: argument zawiera string enum
oraz `anyOf` z jedną alternatywą na wartość. Każda alternatywa ma `type: string`,
jednoelementowe `enum` i `description`. Opis samego argumentu jest pytaniem
(do 1000 znaków), a opisy alternatyw kryteriami (do 500 znaków). Adapter mapuje
je na pytanie i kryteria Laya w kolejności głównego enum. Brak lub nadmiar opcji,
duplikaty i błędne opisy dają HTTP 400 przed inferencją. Opisy wliczają się w
limit bajtów. Zwykły enum bez anyOf nadal używa instrukcji z promptu i schematu,
a tekst opcji jako jej opisu. Nie ma prywatnego rozszerzenia x-choice ani
wbudowanej polityki działów w adapterze.

Engine przyjmuje `POST /v1/systemone`, z `model: multilingual`, `state` oraz jednym
elementem `questions`: typ `choice`, instrukcje i `criteria` jako mapa opcji.
Zwraca SDK Laya `answers.<question>.choice`. Wykorzystuje model o budżecie 8192
tokenów. Surowy budżet bajtów jest konserwatywną granicą wejścia, nie statystyką
tokenizacji. Brak odpowiedzi, wynik poza opcjami lub błąd modelu daje 502 adaptera.
SDK ma ponadto osobny limit pytania i opcji: 256 tokenów dla tego checkpointu
oraz 48 tokenów na opis opcji z jej etykietą. Aktualna polityka routera mieści
się w tych limitach: 165 tokenów z markerami; najdłuższa opcja ma 27 tokenów.

Opcjonalne `MODEL_TOOL_CHOICE`: puste pomija pole; `auto` i `required` wysyłane są
bez zmian, `named` wskazuje nazwę jedynego narzędzia przez ChatOpenAI. LangChain
wiąże narzędzie podczas `create_agent`, z ustawieniem przekazanym przez
`ModelRequest.override`. Laya akceptuje `auto`/`required`; jej przykład env używa
`required`. Obecna Ollama ignoruje wybór, dlatego jej przykład pomija pole.
Brak wsparcia u dostawcy nie uruchamia fallbacku ani ponowienia. Bootstrap nadal
sprawdza ogólną gotowość tool calling, nie egzekwowanie named tool_choice.
