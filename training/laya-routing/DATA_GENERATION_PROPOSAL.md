# Zatwierdzone przygotowanie danych przez lokalną Gemmę

Status: podejście Gemma zatwierdzone przez „Ok do it” i wykonane w małych
próbach. Autor nie spełnił kryteriów; wszystkie18 odpowiedzi zachowano,
audyt pochodzenia przeszedł, korpus niezaakceptowany. Serwer zatrzymany.
[Sprawdzona propozycja ręcznej redakcji](drafts/manual-fallback-proposal/README.md)
czeka na zgodę na zmianę metody. Nie rozpoczynać jej bez odpowiedzi użytkownika.
Zmiana autorstwa może być wykonywana bez kolejnych pytań o tę samą zgodę.
Dotychczasowy szkic 90 rodzin jest niezatwierdzony i nie może wejść do treningu.
Niezależny przegląd pierwszych 60 wykazał pokrewne scenariusze między splitami.
Nie powstały ani nie zostały ocenione wagi treningu docelowego.

## Zakres

Zachować bazowy model Laya, FP32/CPU, hiperparametry, budżet 8 godzin,
2000/500/500 przykładów, wyłączenie starych 515 wiadomości oraz jednorazową
końcową ewaluację. Zmienić wyłącznie przygotowanie tekstów: lokalna Gemma
tworzy warianty na podstawie przygotowanych i zamrożonych scenariuszy.
Root nie generuje całego korpusu ręcznie. Żadnego płatnego API.

## Kolejność i zabezpieczenia

1. Przed generowaniem opisać grupy semantyczne i scenariusze. Przydzielić
   całe grupy do train/validation/test z zachowaniem balansu działów; kolejne
   warianty, aktorzy i parafrazy nie tworzą niezależnych grup.
2. Zamrozić plan z hashami. Nie przyjmować samego losowania numerów jako
   dowodu niezależności. Dotychczasowe szkice zachować jako odrzucone źródło.
3. Użyć istniejącej lokalnej Gemmy przez `/v1/chat/completions`. Uruchomić
   tylko Ollama, bez routera, mailera i SMTP. Żadne wiadomości nie są wysyłane.
4. Wejście generatora: opisy pięciu działów, jedna zatwierdzona rodzina,
   wymagania dotyczące pięciu różnych form wypowiedzi. Nie przekazywać starego
   benchmarku, jego etykiet, błędów, wyników, promptu Gemmy ani przykładów.
5. Każdy request i surową odpowiedź zapisać wraz z hashem modelu i planu.
   Warianty: krótka prośba, kontekstowa wiadomość, historia zakończonego
   problemu z aktualnym zadaniem, cytat i główna prośba, naturalne skróty lub
   literówki. Bez dodawania identyfikatorów/etykiet do wiadomości.
6. Etykieta wynika ze scenariusza i polityki, nie z klasyfikacji Gemmy.
   Przegląd redakcyjny potwierdza poprawność każdej wiadomości. Wadliwa rodzina
   zatrzymuje przebieg; zachować odrzucenie. Nie automatycznie akceptować
   odpowiedzi ani ponawiać żądania bez inspekcji.
7. Audyt leksykalny i niezależny przegląd semantyczny wykluczają podobieństwa
   między splitami i ze starym benchmarkiem oraz 16 rodzinami preflight.
   Stare teksty służą tylko wykluczaniu przecieku, nie generowaniu poprawek.
8. Test zamrozić przed treningiem, nie montować w trainerze. Raportować
   zależność od syntetycznego autora i korelację wariantów; to nie rzeczywiste
   zgłoszenia i nie dowód doskonałej generalizacji.

## Wznowienie i dowody

Generator zapisuje stan rozpoczętej rodziny przed HTTP i pełną odpowiedź
przed parsowaniem. Przy wznowieniu pomija ukończone rodziny, odmawia zmiany
planu/modelu/promptu i blokuje niejasne, rozpoczęte próby do przeglądu.
Katalog docelowy: `generation/<run-id>/`. Skrypt `generate_data.py` i komendy
poniżej powstały przed wykonaniem. Sekrety nie mogą wejść do logów.

## Zamrożony plan i uruchomienie

`scenario_groups.py` definiuje60 grup semantycznych, po10 konkretnych rodzin.
Na dział przypada8 grup train,2 validation,2 test. Każda rodzina otrzyma5
wariantów. Niezależny przegląd wskazał3 powtórzenia podstawowej prośby między
splitami; zastąpiono je przed zamrożeniem scenariuszami odczytu kodów kreskowych,
automatycznej jasności, GPS i napisów w wideo. Krytyk potwierdził usunięcie
tych powtórzeń i prawidłowe przypisanie16 scenariuszy preflight do train.
To akceptacja definicji, nie jeszcze wygenerowanych wiadomości.

`freeze_scenarios.py` zachowuje pierwotny przydział identyfikatorów seed42
i zapisuje `source/scenarios.json` wraz z hashami. Wykonano go po przeglądzie.
Nowy test ma100 konkretnych rodzin, ale tylko10 szerszych grup semantycznych;
raport musi podawać oba poziomy zależności.

Weryfikacja z katalogu PoC, bez inferencji:

```sh
docker run --rm --network none \
  --mount source=message-router_ollama-models,target=/models,readonly \
  --mount type=bind,source="$PWD/training/laya-routing",target=/work \
  --entrypoint python sha256:4d0ffa68273f122a8bb1db1a14d1503b7cca218c91d05c4970ede69601107989 \
  /work/verify_gemma_assets.py --models /models --output /work/generation/model-proof.json
```

Osobny serwer tej samej Gemmy, bez API routera, mailera i bootstrapu:

```sh
docker run -d --name wskz-laya-data-gemma --memory 10g --memory-swap 10g \
  --mount source=message-router_ollama-models,target=/root/.ollama,readonly \
  --publish 127.0.0.1:18092:11434 \
  --env OLLAMA_HOST=0.0.0.0:11434 --env OLLAMA_NUM_PARALLEL=1 \
  --env OLLAMA_CONTEXT_LENGTH=4096 --env OLLAMA_KEEP_ALIVE=30m \
  sha256:f3d9e1f71a3f6d54ac426206726a3f18b412eece49445cb6230bf60da52119b9 serve
```

Jedna rodzina na wywołanie, następnie odczyt jej pięciu tekstów i osobny przegląd:

```sh
.venv/bin/python training/laya-routing/generate_data.py step \
  --plan training/laya-routing/source/scenarios.json \
  --policy training/laya-routing/policy.json \
  --proof training/laya-routing/generation/model-proof.json \
  --output training/laya-routing/generation/gemma-20260927
```

Po rzeczywistej inspekcji ten sam zestaw parametrów z `review --decision accept`
lub `reject --note '<konkretna notatka>'` (polecenie pozostaje `review`, a reject
jest wartością `--decision`). Nie automatyzować akceptacji. `status` nie uruchamia
inferencji. Rejection lub nierozstrzygnięta próba blokuje dalszy przebieg.
Żadne żądanie nie jest automatycznie ponawiane. Zachować odpowiedzi odrzucone.

Parametry generowania: temperature0.7, top_p0.9, seed42+index, max_tokens1000,
reasoning_effort=none, standardowe response_format/json_schema. Nie zmieniać
ich po uruchomieniu bez utrwalenia przyczyny i nowego kontraktu. Referencje:
[Ollama Chat Completions](https://docs.ollama.com/api/openai-compatibility),
[structured outputs](https://docs.ollama.com/capabilities/structured-outputs).

Wymóg potwierdzenia zmiany pochodzi z repozytoryjnej instrukcji:
„Do not substitute or change the method unless the user explicitly instructs
or approves the change.” Zmiana metody tworzenia danych nie jest jeszcze
objęta pierwotnym dokumentem; została teraz osobno zatwierdzona.

## Kontrola pierwszej odpowiedzi

Pierwsza rodzina w `generation/gemma-20260927/000/` została odrzucona:
pięć krótkich parafraz, brak faktycznego cytatu i zakończonej historii. Surowy
wynik, odrzucenie i stary kod zachowano. Korekta techniczna kontraktu v2:
pięć nazwanych pól JSON zamiast tablicy oraz jawne wymagania form w wiadomości
użytkownika i opisach schematu. Ten sam autor, plan, polityka i parametry.
Ręcznie zatwierdzona po inspekcji ponowna próba tej rodziny rozpoczyna osobny
`generation/gemma-v2-20260927/`; polecenia powyżej z tym nowym `--output`.
Nie odczytywano starego benchmarku ani nie trenowano wag.

Druga próba v2 poprawiła kontekst i historię, lecz ponownie pominęła cytat.
Zachowano odrzucenie i kod. Kontrakt v3 wyraża pole quotation jako dwa
autorskie teksty quote/message; parser jedynie dodaje cudzysłów i spację,
bez dopisywania treści. Pozostałe pola i parametry niezmienione. Po inspekcji
ręcznie ponowiono pierwszą rodzinę w `generation/gemma-v3-20260927/`.

Dalsza kontrola v3: rodzinę000 zaakceptowano redakcyjnie (pięć wiadomości),
rodzinę001 odrzucono, ponieważ samodzielny wariant informal zgubił kontekst
rekrutacji. Nie ma jeszcze akceptacji tych danych do treningu. Niezależny
audyt scenariuszy względem wykluczonych starych przypadków jest wykonywany
przed dalszym generowaniem. Wstrzymanie zachowuje wszystkie surowe próby.

Audyt danych i raporty pilnują także szerszych grup semantycznych:40/10/10,
bez przecieku między splitami. Raport ewaluacji dodaje bootstrap rodzin
i szerszych grup (seed42,2000 replik), z ograniczeniem małej liczby grup.
Build przyjmuje wyłącznie kompletny, audytowany plik accepted-gemma.jsonl;
nie zbiera luźnych szkiców źródłowych.

## Korekta samodzielności wiadomości

Przygotowany kontrakt v4 dodaje jawny wymóg zachowania rodzaju sprawy
w KAŻDYM wariancie, także potocznym. Nie dodaje benchmarku do promptu.
Generator zapisuje własny kod razem z kontraktem. Opcjonalny `--start-index N`
pozwala jawnie rozpocząć osobny run od przejrzanej odrzuconej rodziny,
bez ponownego generowania wcześniejszych zaakceptowanych rodzin; numer i seed
pozostają globalne. Nie służy do automatycznych ponowień. Run musi zostać
zapisany w kolektorze i żadna rodzina nie może mieć dwóch przyjętych źródeł.

`collect_generated.py --plan source/scenarios.json --policy policy.json
--run generation/<run> [--run generation/<other-run>]
--output source/accepted-gemma.jsonl` (ścieżki względem katalogu treningu)
sprawdza wszystkie surowe odpowiedzi kodem przypiętym do każdej próby oraz
hashe przeglądów. Dopiero komplet600 przyjętych rodzin może zostać zapisany.
To dowód pochodzenia tekstów, nie samodzielna akceptacja danych do treningu.

## Wykluczenia po niezależnym audycie

Audyt wszystkich600 definicji wskazał13 mocnych kolizji konkretnych sytuacji
ze starym benchmarkiem (11train,1validation,1test);202 pozostałe podobieństwa
są szerszym pokryciem zadań i nie dowodzą kopiowania.13 definicji zastąpiono
przed treningiem na podstawie ogólnej polityki i własnego nowego planu.
Autor nie otrzymał tekstów starych przypadków, jedynie IDs do wykluczenia.
Pierwotny plan/kod/raporty: `source/history/pre-exclusion-20260927/`.
Zmiany: `source/replacements-20260927.json`. Przydział600 rodzin i60 grup
do splitów pozostał identyczny. Nowe definicje wymagają ponownego przeglądu.

Wszystkie dotychczasowe próby v1-v3 są dowodami przygotowania starego planu
i zostają wyłączone z przyszłego korpusu. Po akceptacji nowego hasha należy
uruchomić v4 od indeksu0 w `generation/gemma-v4-20260927/`. Kontrakt
przypina również niezależny `source/exclusion-scenario-review-v3.json`;
generator odmawia braku akceptacji albo innego hasha planu.

Drugi przegląd13 zmian zaakceptował12. Ostatnią definicję payroll-013
zastąpiono jeszcze raz przed generowaniem. Raport v2 pozostaje negatywny
i niezmieniony; odpowiadający mu plan jest zachowany w
`source/history/exclusion-revision-20260927/`. Końcowy plan ma SHA-256
`561b082828ec7b8219d29d9adc2bdeac6cac59ad49e3f256d401800391510b99`;
akceptacja generowania jest osobnym raportem v3, bez zmiany dowodów v2.

## Kontrakt autora v5 po niezależnym przeglądzie próbek

Cały v4 wyłączono: krytyk potwierdził zmianę aktualnej intencji w003/006,
pozorne historie oraz powtarzanie treści cytatu. Wcześniejsze akceptacje
redakcyjne nie są akceptacją danych do treningu; `editorial-audit.json`
utrwala odrzucenie całego run. Wszystkie surowe odpowiedzi pozostają.

Korekta techniczna v5 zachowuje lokalnego autora, pięć wariantów na rodzinę,
plan, politykę, podział i ręczne przeglądy. Włącza dostępne myślenie Gemmy
przez standardowe `reasoning_effort=low` (metadata modelu: false/true, low
mapuje się na true), temperature0.3 i max_tokens3000. Uzasadnienie: jakość
i wierność własnych pierwszych przykładów train, bez wyników klasyfikatora.
System dokładnie rozróżnia aktualne zadanie i spełnione warunki; usuwa
redundantny opis samego docelowego działu. Historia ma trzy osobno napisane
pola: problem, rozwiązanie, bieżąca wiadomość. Parser wyłącznie łączy je
spacjami. Powtórzenie identycznego cytatu jako bieżącej prośby jest błędem.

Dowód dostępnej funkcji: `generation/thinking-proof.json`, wyłącznie odczyt
metadanych, bez inferencji. [Oficjalne mapowanie reasoning_effort](https://docs.ollama.com/api/openai-compatibility).
Nowy run: `generation/gemma-v5-20260927/`, od indeksu0. Najpierw próbka
poddana niezależnej kontroli, dopiero potem dalsze generowanie. Nie zmienia
to hiperparametrów Laya ani kryterium wyboru modelu.

## Mała próba pojedynczej wiadomości

Pierwszy v5 nie przeszedł nawet kontroli struktury: identyczny cytat/prośba
i niewłaściwa historia. Zachowano odrzucenie. Przed kolejnym skalowaniem
`single_variant_pilot.py` sprawdza uproszczenie jednego requestu do jednej
formy wypowiedzi. Nadal ta sama lokalna Gemma, zamrożony scenariusz i polityka,
bez benchmarku i bez treningu. Jedna znana z próby authoring rodzina train
(index6), forma kontekstowa, temperature0.3, top_p0.9, seed48,
reasoning_effort=none, max_tokens300, zwykła treść Chat Completions bez
złożonego JSON. Wszystkie requesty/odpowiedzi zapisane w osobnym katalogu.
To próba techniczna jakości autora, nie jeszcze dane treningowe. Komenda:
`.venv/bin/python training/laya-routing/single_variant_pilot.py`.

## Kontrakt v6: prosta pojedyncza forma w każdym zapytaniu

Pilot pojedynczego tekstu ukończył się w3.49s, zachował zadanie rekrutacyjne,
ale przyjął formę zaproszenia zamiast zgłoszenia. v6 jawnie wymaga prośby
do osoby obsługującej sprawę. Zamiast jednego złożonego JSON powstaje pięć
prostych odpowiedzi Chat Completions, po jednej na styl, w obrębie jednego
obserwowanego scenariusza. Po pięciu odpowiedziach runner zawsze wraca do
ręcznej inspekcji całej rodziny przed następnym scenariuszem. Błąd HTTP,
formatu lub transportu zatrzymuje rodzinę od razu, bez automatycznego retry.
Nie ma automatycznej akceptacji treści. To korekta jednostki zapytania
autora, bez zmiany modelu, danych wejściowych, podziału ani treningu Laya.

`generate_family.py` zapisuje wszystkie pięć osobnych requestów, odpowiedzi
i wyników oraz wspólny wynik/przegląd z hashami. Każdy tekst to dokładna
treść odpowiedzi, bez napraw i dopisywania scenariusza przez parser.
Parametry: temperature0.3, top_p0.9, seed42+5*family_index+variant_index,
reasoning_effort=none, max_tokens300. Kolektor sprawdza dowody kodem zapisanym
w danym run i odmawia runów wykluczonych przez niezależny przegląd redakcyjny.

CLI identyczne jak wcześniej, ale skrypt `generate_family.py`, katalog
`generation/gemma-v6-20260927/`. Najpierw mała próbka i niezależny krytyk.
Wszystkie v1-v5 pozostają wyłączone z korpusu.
