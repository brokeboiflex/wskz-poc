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

## Laya adapter i engine

Adapter obsługuje podzbiór powyższego protokołu: jeden tekst użytkownika, opcjonalny
system prompt, jedno narzędzie i jeden wymagany argument string enum. Odrzuca
streaming, multimodalność, historię wykonanych narzędzi, nieznane modele i
nieobsługiwane pola. Nazwa narzędzia i wartości enum pochodzą z requestu, bez
wbudowanej polityki działów. Maksymalnie 7000 bajtów kontekstu decyzji.

Opcjonalne rozszerzenie schematu argumentu `x-choice` zawiera `instructions`
(niepuste pytanie, do 1000 znaków) i `criteria` (mapa każdej wartości enum na
niepusty opis, do 500 znaków na opis). Adapter przekazuje je do silnika w
kolejności enum. Brak lub nadmiar opcji, puste opisy albo wadliwa struktura
zwracają HTTP 400 przed inferencją. Opisy wliczają się w limit bajtów.
Bez rozszerzenia adapter zachowuje wcześniejszy format ogólny: instrukcje z
promptu i schematu, a tekst opcji jako jej opis. Router korzysta z `x-choice`,
aby Laya dostała krótkie pytanie klasyfikacyjne zamiast instrukcji wykonania toola.
Rozszerzenie definiuje właściciel narzędzia; adapter nie zawiera polityki poczty.

Engine przyjmuje `POST /v1/systemone`, z `model: multilingual`, `state` oraz jednym
elementem `questions`: typ `choice`, instrukcje i `criteria` jako mapa opcji.
Zwraca SDK Laya `answers.<question>.choice`. Wykorzystuje model o budżecie 8192
tokenów. Surowy budżet bajtów jest konserwatywną granicą wejścia, nie statystyką
tokenizacji. Brak odpowiedzi, wynik poza opcjami lub błąd modelu daje 502 adaptera.
SDK ma ponadto osobny limit pytania i opcji: 256 tokenów dla tego checkpointu
oraz 48 tokenów na opis opcji z jej etykietą. Aktualna polityka routera mieści
się w tych limitach: 165 tokenów z markerami; najdłuższa opcja ma 27 tokenów.
