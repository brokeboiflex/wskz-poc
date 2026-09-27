# Konkretna próbka alternatywnego autorstwa

To propozycja zmiany metody, nie dane zatwierdzone do treningu.15 wiadomości
napisał root na podstawie trzech definicji train z zaakceptowanego planu:
`human_resources-001`, `human_resources-006`, `human_resources-009`.
Nie wykorzystano treści ani wyników starego benchmarku. Próbka odpowiada
rodzinom, w których generowanie przez lokalną Gemmę pokazało problemy jakości.
Nie jest to wybór według błędów modelu Laya, którego jeszcze nie oceniono.

Proponowana zmiana: wiadomości redaguje root, niezależny krytyk sprawdza
etykiety, wierność i rozdzielenie rodzin. Zachować dokładnie aktualny plan600
rodzin/60grup,2000/500/500, wszystkie wykluczenia, brak wykorzystania starego500
w treningu i wyborze modelu, CPU/FP32, hiperparametry i walidacyjny wybór epoki.
Po zamrożeniu wag pozostaje jednorazowa końcowa ocena bazy i kandydata.

Plik `families.jsonl` ma jawne `proposal_only:true`, leży poza `source/`
i nie może zostać przyjęty przez aktualny builder/collector. Przed pełnym
ręcznym autorstwem potrzebne jest zatwierdzenie zmiany względem obecnego
podejścia Gemma przez użytkownika. Zachować wszystkie odrzucone odpowiedzi.

Obecny bloker: v1-v6 lokalnej Gemmy nie utrzymały wymaganej wierności intencji
oraz form cytatu/historii. Włączenie thinking i rozbicie rodziny na pojedyncze
zapytania nie usunęły problemu. Nie uruchomiono pełnego treningu ani ewaluacji.
