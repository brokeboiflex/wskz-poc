# Laya dla WSKZ: dostrojenie bez uczenia pod benchmark

Nowy test regresji na tych samych500 co Gemma ukończony: Laya epoka1 **432/500 (86,4%)**, Gemma493/500 (98,6%);0 błędów protokołu obu. Wybrano epokę1 wyłącznie po walidacji. Bez treningu i ponowień; kontenery zatrzymane. Raport i procedura: `training/laya-routing/runs/laya-gemma-same500/README.md` względem katalogu PoC. Wcześniejsze stwierdzenie o niewykonanym starym benchmarku jest historyczne.

Walidacja epoki2 dokończona na wyraźne polecenie użytkownika: **443/500 (88,6%)**, macro-F1 0,882589. Epoka1:447/500 (89,4%). Wznowiono tylko przypadki386–499, bez ponowień wcześniejszych. Bez kolejnego treningu, krytyka i dodatkowych testów. Kontenery zatrzymane, wagi zachowane. Końcowy test i stary benchmark niewykonane. Wcześniejsze przerwanie walidacji było błędną interpretacją polecenia użytkownika.

Poniżej historia wcześniejszych etapów.

Status27.09.2026: **pełne3000 wiadomości zaakceptowane, epoka2 uruchomiona po walidacji1:447/500**.
Dane2000/500/500 zamrożone, audyt leksykalny i tokenizacja bez obcięć zaliczone.
2500 tekstów przeglądnięto niezależnie,500 przez autora zgodnie z późniejszym
poleceniem użytkownika oszczędzania tokenów i nieuruchamiania krytyka.
Obowiązuje [zatwierdzona metoda z korektą użytkownika](../training/laya-routing/MANUAL_AUTHORING_APPROACH.md).
Odrzucone próby Gemmy i wcześniejszy draft nie weszły do treningu.
[Raport](../training/laya-routing/README.md), [komendy](../training/laya-routing/RUNBOOK.md).
Polecenie użytkownika: dostosować
Laya do prawidłowej klasyfikacji 500 przypadków bez overfittingu. Dokument
uszczegóławia niewykonaną propozycję z [LAYA_TUNING_APPROACH.md](LAYA_TUNING_APPROACH.md).
Nie stanowi potwierdzenia wykonania ani obietnicy wyniku 500/500.

## Ustalenia z odczytu

- Gemma: 471/500, 24 błędne działy i 5 brakujących natywnych wywołań.
  [Dowody](evidence/2026-09-26/gemma-patched-500/README.md).
- Laya: wagi nie były trenowane; historyczna regresja po poprawie integracji
  wyniosła 13/15. Nie ma tutaj potwierdzonego pełnego wyniku Laya na 500.
- Runtime: `laya==0.3.20`, jawne `multilingual`, CPU, `max_len=8192`.
  Zapisana rewizja bundle: `55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851`,
  podkatalog `multilingual`, SHA-256 wag:
  `9d628fd971b700382ac6f65920a86f149777b2e748e0c955fb3b19695aa8f204`.
  Przed uruchomieniem sprawdzić rzeczywiście dostępny snapshot i image digest.
- Laya otrzymuje pytanie i opisy opcji ze schematu, a nie pełny `SYSTEM_PROMPT`.
  Nie zakładać, że dopisanie zasad w prompcie Gemmy zmienia wejście klasyfikatora.
- Host: Apple M4, 24 GiB RAM, około 12 GiB wolnego dysku podczas odczytu.
  Nie sprawdzono jeszcze dostępnej pamięci Docker ani czasu forward/backward.

## Zabezpieczenie przed przeciekiem

1. Zamrozić istniejące 500 wiadomości (250 rodzin), oryginalne 15 smoke cases,
   politykę, tokenizer, wersje bibliotek i bazowe wagi. Hash starego benchmarku:
   `bd3cf10bc628dc0c27349201b443ef95a9b11112b272573766d323c547f5cd0e`.
2. Nie używać tych wiadomości, ich parafraz, uzasadnień, błędów Gemmy ani
   przewidywań do tworzenia przykładów treningowych, wyboru hiperparametrów,
   promptu, checkpointu, progów czy reguł. Bez lookupów, reguł pod konkretne
   przypadki, podmieniania etykiet i przekazywania modelowi identyfikatorów.
3. Stary benchmark był wielokrotnie analizowany podczas rozwoju systemu.
   Raportować go jako znaną regresję. Nie nazywać go dziewiczym testem,
   nawet gdy żadna z jego wiadomości nie wejdzie do treningu wag.
4. Przygotować nowy syntetyczny korpus wyłącznie na podstawie znaczenia pięciu
   działów: 2000 wiadomości train, 500 validation, 500 test. Zbalansować działy.
   Najpierw przydzielić rodziny scenariuszy i konstrukcje wiadomości do splitów;
   wszystkie warianty jednej rodziny pozostają razem. Seed podziału: 42.
   Nie tworzyć zbioru przez samo mnożenie szablonów lub zamianę nazw.
5. Uwzględnić różne prośby, negacje, cytaty, historię, niepełne informacje,
   literówki i konkurujące tematy. Etykiety wynikają z polityki, nie z odpowiedzi
   Gemmy. Korpus autorski, bez płatnych API i dostępu do rzeczywistych skrzynek.
6. Sprawdzić duplikaty po normalizacji, podobieństwo fragmentów oraz pokrewieństwo
   scenariuszy między splitami i starym benchmarkiem. Audyt przecieku ma odrzucać
   zanieczyszczone nowe przykłady, nie podpowiadać poprawek według błędów modelu.
   Zapisać przegląd etykiet i wszystkie wykluczenia przed treningiem.
7. Oddzielić autorskie dane testowe i ich etykiety od procesu treningowego;
   zamontować tylko train/validation. Nowy test ujawnić po zamrożeniu modelu.
   To test syntetyczny o ograniczonej niezależności autorstwa, nie dowód jakości
   na rzeczywistej korespondencji WSKZ ani dowód całkowitego braku overfittingu.

## Wykonanie po zatwierdzeniu

1. Przygotować skrypty w `training/laya-routing/`, utrwalić dokładne CLI i wersje
   w tym dokumencie przed ich uruchomieniem. Najpierw testy offline: izolacja
   etykiet, grupowanie rodzin, duplikaty, odmowa użycia starego testu w treningu,
   zgodność tokenizacji trening/serwowanie i wznowienie bez utraty stanu.
2. Sprawdzić tokenizację obecnych pytań/opcji oraz kompletną ścieżkę adaptera.
   Ewentualne doprecyzowanie opisów może wyrażać wyłącznie istniejącą politykę;
   wybrać je na nowych train/validation. Utrwalić je przed końcowymi testami.
3. Wykorzystać lokalny obraz/runtime i istniejące wagi; bez płatnego GPU,
   publikacji na Hub i nadpisywania modelu bazowego. Offline trening może
   wywoływać PyTorch bezpośrednio. Ewaluacja decyzji pozostaje przez
   OpenAI-compatible Chat Completions i istniejący adapter Laya.
4. Najpierw krótki pomiar forward/backward na train: CPU w osobnym kontenerze,
   FP32, microbatch 1, efektywny batch 16 przez akumulację. Zmierzyć RAM,
   wolne miejsce, czas kroku i oszacować cały przebieg. Nie obiecywać czasu.
   Limit tej propozycji: 8 godzin treningu, co najmniej 4 GiB wolnego dysku.
   Zatrzymać z checkpointem przy limicie; nie usuwać cudzych plików ani nie
   przechodzić samowolnie na płatne/zewnętrzne środowisko.
5. Dostosować natywną głowicę choice i encoder multilingual przez nadzorowaną
   cross-entropy. To świadoma adaptacja referencji RLCD+CE do pięciu twardych
   etykiet, a nie kopia notebooka CUDA/DDP. AdamW, LR encoder 2.5e-5,
   head 1e-4, weight decay 0.01, clipping 1.0, seed 42, maksymalnie 4 epoki,
   gradient checkpointing. Bez przeszukiwania wielu konfiguracji na testach.
   Długość wejścia ustalić z tokenizacji train/validation z jawnym audytem
   obcięć; nie ukrywać utraty treści, zachować zgodność z runtime.
6. Wybierać checkpoint wyłącznie po macro-F1 validation; przy remisie accuracy,
   następnie wcześniejsza epoka. Early stopping po dwóch epokach bez poprawy.
   Zapisać wszystkie epoki, metryki i decyzje wyboru, również niekorzystne.
   Nie kalibrować pewności w tym etapie: temperatura nie naprawia argmax.
7. Po zamrożeniu wag, pytań i opcji wykonać jednokrotnie nowy test 500 oraz
   stary benchmark 500 dla bazy i wybranego kandydata. Zachować pełne requesty
   i odpowiedzi wszystkich przypadków, nie tylko błędów. Model widzi tylko
   wiadomość i kontrakt kategorii, bez gold, rationale i ID benchmarku.
8. Zachować obserwowany tryb: inspekcja każdego błędu przed następnym requestem
   i przegląd co 10 przypadków; żadnego automatycznego akceptowania bramek,
   retries, maili czy wykonywania narzędzia wysyłki. To ewaluacja klasyfikacji
   i adaptera, nie test rzeczywistej dostawy SMTP.
9. Raport: accuracy, macro-F1, recall działów, macierz pomyłek, błędy protokołu,
   wynik według rodzin, opóźnienia oraz różnica względem bazy. Wyniki starego
   i nowego testu osobno. Jeżeli nie ma 500/500, podać rzeczywisty wynik.
   Nie wracać do dostrajania według końcowych błędów i nie przedstawiać
   wielokrotnie używanego testu jako niezależnego. Dalsza iteracja potrzebuje
   nowego protokołu i świeżego testu. Nie podmieniać działającej Gemmy.

## Artefakty i wznowienie

Docelowy katalog: `training/laya-routing/`; duże wagi poza Git.
Wymagane artefakty: `data/{train,validation,test}.jsonl`, `data/manifest.json`,
`data/leakage-audit.json`, konfiguracja z hashami, skrypty przygotowania,
treningu, eksportu, ewaluacji i audytu, `runs/<run-id>/` z metrykami i logami.
Pełny korpus istnieje, trening jest uruchomiony. Dokładny bieżący stan,
ograniczenia i wznowienie opisuje runbook.
Skrypty pomiaru zasobów i audytu danych opisano poniżej.

Pełny checkpoint: model, optimizer, scheduler, RNG, epoka, kolejność danych,
pozycja i liczba kroków. Zapisywać atomowo na granicy kroku optymalizatora.
Wznowienie sprawdza hashe danych, konfiguracji, kodu i modelu; odmawia przy
rozbieżności. Przed wznowieniem przeczytać ten dokument i log ostatniego kroku.
Wagi najlepszego modelu przechować osobno od pełnego stanu wznowienia.
Ocenić miejsce także na tymczasowy plik podczas atomowego zapisu.

Runner ewaluacji zapisuje identyfikator rozpoczętej próby przed requestem,
wynik i przegląd po nim. Przy wznowieniu pomija ukończone przypadki i blokuje
niejasną próbę do inspekcji; nie powtarza jej po cichu. Każdy wynik dotyczy
konkretnego snapshotu. Nie logować sekretów. Powtórzyć porównanie eksportu
z checkpointem na validation, zanim zostanie otwarty końcowy test.

## Uruchomienie pomiaru zasobów, 27.09.2026

Przygotowano `training/laya-routing/preflight.py`, nie pełny trainer. Wejście:
16 jawnie treningowych, nowo napisanych scenariuszy w `preflight-train.jsonl`
oraz kopia aktualnego pytania/opcji `policy.json`. Te rodziny rezerwuje się dla
train, nigdy dla validation/test. Nie jest to jeszcze korpus 2000/500/500.
Przed wejściem do pełnego train przykłady wymagają audytu przecieku.

Pierwsze pomiary wykonywały jeden przejściowy krok AdamW (16 microbatchy),
aktualny skrypt domyślnie sprawdza dwa kroki. Zapisuje każde
wejście, logits, loss, czas i szczyt RSS. Nie eksportuje zmienionych wag.
Wolumen bazowy jest read-only, sieć wyłączona. Limit kontenera 6500 MiB
pozostawia zasoby dla istniejących usług. Rzeczywisty Docker ma 7.75 GiB RAM.
Skrypt sprawdza hash wag, brak obcięcia wejścia/opcji i dokładną liczbę bajtów
tensorów checkpointu. Budżet dysku obejmuje latest, zapis atomowy, best FP32
oraz 4 GiB rezerwy. Osobno raportuje estymację czasu bez walidacji i I/O.

Historyczna komenda pierwszego pomiaru z katalogu PoC (kod tej wersji zachowany
w `runs/preflight-20260927/preflight-source.py`; aktualny skrypt jest nowszy):

```sh
.venv/bin/ruff check training/laya-routing
.venv/bin/ruff format --check training/laya-routing
docker run --name wskz-laya-training-preflight --network none --memory 6500m --memory-swap 6500m \
  --mount source=message-router_laya-models,target=/models,readonly \
  --mount type=bind,source="$PWD/training/laya-routing",target=/work \
  --env HF_HUB_OFFLINE=1 --env TRANSFORMERS_OFFLINE=1 \
  --entrypoint python sha256:4d0ffa68273f122a8bb1db1a14d1503b7cca218c91d05c4970ede69601107989 \
  -u /work/preflight.py \
  --model /models/hub/models--convaiinnovations--laya/snapshots/55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851/multilingual \
  --output /work/runs/preflight-20260927
```

Nie powtarzać tej komendy w istniejącym katalogu; skrypt odmawia nadpisania.
Po przerwaniu zachować `events.jsonl` i stan kontenera. Probe nie ma checkpointu
wag do wznowienia: jest jednorazowym pomiarem przed pełnym treningiem.
Zachować `docker inspect` (stan/limit/obraz, bez env) i log jako dowód.

Pierwszy probe zakończony OOM (exit 137) po 16 backward, przed ukończeniem
AdamW; nie zapisał wag. Zachowano kod, log i stan kontenera w katalogu run.
Kolejny probe stosuje ten sam AdamW FP32, batch, gradient clipping i LR,
ale wykonuje niezależne aktualizacje parametrów kolejno i zwalnia już użyte
gradienty. `test_optimizer.py` porównuje bitowo wagi i stany optymalizatora
z PyTorch AdamW po czterech krokach, także po serializacji/wznowieniu.
To optymalizacja pamięci implementacji, bez zmiany algorytmu treningu.

```sh
docker run --rm --network none \
  --mount type=bind,source="$PWD/training/laya-routing",target=/work,readonly \
  --entrypoint python sha256:4d0ffa68273f122a8bb1db1a14d1503b7cca218c91d05c4970ede69601107989 \
  /work/test_optimizer.py
```

Drugie uruchomienie preflight: ta sama komenda i limity co powyżej,
z nazwą kontenera `wskz-laya-training-preflight-serial` oraz
`--output /work/runs/preflight-serial-20260927`. Nie nadpisywać pierwszej próby.

Trzeci pomiar sprawdza dwa pełne kroki (drugi z już obecnymi stanami AdamW):
aktualny `preflight.py --steps 2`, ta sama komenda/limity z nazwą kontenera
`wskz-laya-training-preflight-steady` i
`--output /work/runs/preflight-steady-20260927`. Poprzednie pomiary używały
jednego kroku i są zachowane wraz z ówczesnym kodem. Nie są dowodem wykonalności
pełnego treningu. Serial run ma negatywną bramkę dysku; trzeci pomiar nie zapisuje
wag, jedynie sprawdza drugi niezależny warunek zasobów.

Kontrola danych offline nie uruchamia modelu ani nie ujawnia tekstów benchmarku:

```sh
.venv/bin/python -m unittest discover -s training/laya-routing -p test_data_guard.py
.venv/bin/python training/laya-routing/data_guard.py \
  --input training/laya-routing/preflight-train.jsonl \
  --benchmark verification/benchmark/cases-500.json --smoke verification/cases.json \
  --preflight-only --output training/laya-routing/runs/preflight-data-audit.json
```

Po przypięciu również hash smoke wykonano ponowny audyt offline do
`runs/preflight-data-audit-pinned.json`, zachowując pierwszy raport.
Nie uruchamiało to modelu. Końcowy audyt dowodów:

```sh
.venv/bin/python training/laya-routing/audit_preflight.py
```

Tryb pełnego korpusu nie przyjmuje brakujących rekordów ani naruszenia balansu.
Tryb preflight sprawdza tylko 16 rekordów train. Screening obejmuje normalizację,
duplikaty, grupy scenariuszy i nakładanie trigramów; nie zastępuje przeglądu
semantycznego. Nie generuje przykładów z tekstu benchmarku.

## Przeczytane referencje

## Wznowienie po zwolnieniu zasobów, 27.09.2026

Użytkownik: „Ok powinieneś miec potrzebne zasoby wolne”. Dysk: około 104 GiB
wolnego, Docker nadal 7.75 GiB RAM, ale bez uruchomionych innych kontenerów.
Ta sama metoda CPU/FP32 i niezmieniony preflight, limit 7200 MiB zamiast
6500 MiB; bez zmiany globalnej konfiguracji Docker. Historia prób pozostaje.

```sh
docker run --name wskz-laya-training-preflight-freed --network none --memory 7200m --memory-swap 7200m \
  --mount source=message-router_laya-models,target=/models,readonly \
  --mount type=bind,source="$PWD/training/laya-routing",target=/work \
  --env HF_HUB_OFFLINE=1 --env TRANSFORMERS_OFFLINE=1 \
  --entrypoint python sha256:4d0ffa68273f122a8bb1db1a14d1503b7cca218c91d05c4970ede69601107989 \
  -u /work/preflight.py --steps 2 \
  --model /models/hub/models--convaiinnovations--laya/snapshots/55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851/multilingual \
  --output /work/runs/preflight-freed-20260927
```

### Źródła

Próba `preflight-freed-20260927` przy 7200 MiB nadal OOM po wszystkich 32
backward, przed ukończeniem drugiej aktualizacji. Dysk ma już ponad 100 GiB.
Ponieważ wszystkie kontenery są zatrzymane, w Docker Desktop Resources >
Advanced ustawiono do zastosowania Memory limit 12 GB (12288 MiB), wcześniej
8 GB (8192 MiB), a następnie Apply & restart. Innych ustawień nie zmieniać.
Rollback przy braku potrzeby większej pamięci: ten sam suwak na 8 GB i restart
przy zatrzymanych kontenerach. To zwiększenie dostępnych zasobów tego samego
treningu CPU/FP32, bez zmiany algorytmu, modelu ani danych.

Po odczycie `docker info --format '{{.MemTotal}}'` nowa próba stosuje tę samą
komendę z `--memory 10g --memory-swap 10g`, nazwą
`wskz-laya-training-preflight-12g` i `--output /work/runs/preflight-12g-20260927`.

## Przygotowanie korpusu

600 rodzin, 120 na dział, po pięć osobno napisanych wiadomości. Najpierw
`prepare_data.py plan` przydziela identyfikatory rodzin do splitów (seed 42),
80/20/20 rodzin na dział. Dopiero potem powstają teksty źródłowe w `source/`.
Warianty mogą zmieniać zwięzłość, narrację, historię i sposób sformułowania
prośby; nie są mechanicznym generatorem zamiany nazw. Powiązania semantyczne
między rodzinami trzeba ocenić przed akceptacją podziału.

To 2000/500/500 wiadomości, ale tylko 400/100/100 rodzin. Raport i przedziały
ufności muszą uwzględniać tę zależność. Test ma ograniczoną niezależność
autorstwa. Szesnaście przykładów zasobowych nie jest automatycznie dodawane
do korpusu i nie może przeniknąć do validation/test.

Komendy z PoC (bez inferencji):

```sh
.venv/bin/python training/laya-routing/prepare_data.py plan
.venv/bin/python training/laya-routing/prepare_data.py build
```

Build odmawia brakujących rodzin, niewłaściwej liczby wariantów, zmian splitów
i nadpisania istniejącego kompletu danych. Po build wymagany jest audyt
przecieku i przegląd semantyczny przed treningiem. Pierwotne ręczne autorstwo
zastąpiła zatwierdzona lokalna Gemma, według zamrożonego `source/scenarios.json`.
Nie odczytywać błędów starego benchmarku przy tworzeniu danych.

### Referencje

- [Oficjalny notebook Laya](https://github.com/NandhaKishorM/laya/blob/main/notebooks/laya_finetune_typed_decisions_2xT4_kaggle.ipynb):
  build_sequence, build_model, maski opcji, trening RLCD+CE, eksport tokenizer/
  encoder/config. CUDA/NCCL i angielski checkpoint wymagają jawnej adaptacji.
- [Model multilingual](https://huggingface.co/convaiinnovations/laya-multilingual).
- Lokalna implementacja `services/laya-runtime/runtime.py`, adapter
  `services/laya-adapter/laya_adapter/engine.py` i polityka
  `services/router/router_app/adapters/agent.py`.
- [Zamrożony benchmark i granice dowodów](BENCHMARK_APPROACH.md).
