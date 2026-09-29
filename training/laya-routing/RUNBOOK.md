# Laya: stan wykonania i wznowienie

Nowy test regresji na tych samych500 co Gemma ukończony: Laya epoka1 **432/500 (86,4%)**, Gemma493/500 (98,6%);0 błędów protokołu obu. Wybrano epokę1 wyłącznie po walidacji. Bez treningu i ponowień; kontenery zatrzymane. Raport i procedura: `training/laya-routing/runs/laya-gemma-same500/README.md` względem katalogu PoC. Wcześniejsze stwierdzenie o niewykonanym starym benchmarku jest historyczne.

Walidacja epoki2 dokończona na wyraźne polecenie użytkownika: **443/500 (88,6%)**, macro-F1 0,882589. Epoka1:447/500 (89,4%). Wznowiono tylko przypadki386–499, bez ponowień wcześniejszych. Bez kolejnego treningu, krytyka i dodatkowych testów. Kontenery zatrzymane, wagi zachowane. Końcowy test i stary benchmark niewykonane. Wcześniejsze przerwanie walidacji było błędną interpretacją polecenia użytkownika.

Poniżej historia wcześniejszych etapów.

27.09.2026. **Epoka1 zakończona; trening epoki2 wznowiony w `wskz-laya-train-epoch2`.**
Walidacja1:447/500, macroF1 .893358,0 błędów protokołu. Selektor:kontynuuj.
Pełny korpus2000/500/500 zaakceptowany; tokenizacja3000 wiadomości bez obcięć.
2500 tekstów ma niezależny przegląd,500 przegląd autora. Zgodnie z ostatnim
poleceniem użytkownika nie uruchamiać kolejnego krytyka. Końcowy test pozostaje przed nami.
Najpierw przeczytać [ustalenia treningu w README](../../README.md#trening-laya).
[Zmiana autorstwa na Gemmę](DATA_GENERATION_PROPOSAL.md) jest zatwierdzona
przez „Ok do it”; małe próby autora nie spełniły kryteriów i zostały zakończone.
Wszystkie18 odpowiedzi zachowano. Nie wznawiać ich automatycznie. Użytkownik
zatwierdził ręczną redakcję i trening po kontroli: „Tak potem od razu trenuj”.
Obowiązuje [MANUAL_AUTHORING_APPROACH.md](MANUAL_AUTHORING_APPROACH.md).
Plan600 rodzin/60grup i pełne dane są zamrożone w `data/`.
`collect_authored.py --status` podaje liczbę rodzin i partie bez aktualnego
pozytywnego przeglądu. Kolektor kopiuje treści dosłownie, wymaga wszystkich
600 rodzin i pełnego audytu leksykalnego. Builder ponownie sprawdza źródła,
przeglądy, politykę i kod kolektora; manifest przypina też audyt kolekcji.

Audyt dotychczasowych prób: `audit_generation.py` (zapisany wynik w
`generation/evidence-audit-20260927.json`; nie nadpisywać przy ponownym audycie).

## Wykonane kontrole

Polecenia z `poc/message-router`:

```sh
.venv/bin/python -m unittest discover -s training/laya-routing -p test_training_pipeline.py
.venv/bin/python -m unittest discover -s training/laya-routing -p test_data_guard.py
.venv/bin/ruff check training/laya-routing
.venv/bin/ruff format --check training/laya-routing
docker run --rm --network none \
  --mount type=bind,source="$PWD/training/laya-routing",target=/work,readonly \
  --entrypoint python sha256:4d0ffa68273f122a8bb1db1a14d1503b7cca218c91d05c4970ede69601107989 \
  /work/test_exact_resume.py
```

Wynik: 12 testów pipeline i 10 kontroli danych zaliczonych. Prawdziwy PyTorch
w przypiętym obrazie potwierdza bitową zgodność wag i AdamW po czterech
aktualizacjach małej sieci z dropout, z przerwą po drugiej. To test mechanizmu,
nie dowód pamięci potrzebnej do wznowienia pełnej Laya. Sprawdzono także realne
`CompletionRequest`/`parse_choice` adaptera: `evaluate.make_request` zachowuje
dokładnie pytanie, kolejność i opisy z `policy.json`, bez inferencji.

Niezależny krytyk po poprawkach nie znalazł dalszego blokującego defektu
źródłowego. Poprawiono przerwanie zapisu checkpointu, odzyskanie eksportu,
tożsamość upstreamu adaptera, ponowny audyt dowodów, selektor walidacyjny,
rezerwę dysku oraz wersje bibliotek. To nie zastępuje kontroli live.

## Dane robocze

- `source/plan.json`: wcześniejszy przydział identyfikatorów. Nie wystarcza
  jako plan rodzin semantycznych.
- `drafts/initial-human-resources/`: zachowane 90 niezatwierdzonych rodzin,
  450 wiadomości; przeniesiono trzy pliki ze `source/` bez zmieniania treści.
- Przegląd pierwszych 60 odrzucił podział: 023/053 zawierają feedback
  rekrutacyjny między train/validation, 003/015 poniżanie między train/test,
  a 014 odtwarza powrót po przerwie zarezerwowany w preflight dla train.
- `data/acceptance.json` zawiera `ready_for_training=true`, zakres przeglądów
  i hashe danych, polityki, źródeł oraz audytów. Ograniczenia syntetycznego
  korpusu i brak niezależnego przeglądu ostatnich500 tekstów są jawne.

## Przygotowany kod i granice

`train.py` wykonuje jedną epokę i zatrzymuje się do walidacji. Czyta tylko
train, politykę, bazowe aktywa i akceptację. FP32 CPU, efektywny batch16,
maksymalnie cztery epoki i osiem godzin forward/backward/aktualizacji.
Limit sprawdzany jest na granicy batcha; I/O i walidacja nie są wliczane.

`checkpoint.py`: zapis generacji `state-<uuid>.pt`, fsync, atomowy pointer
`latest.json` z SHA, następnie usunięcie tylko poprzednio wskazanej generacji.
Obce pliki i osierocone zapisy po przerwaniu pozostają. Zapis co20 aktualizacji
i na granicach etapów. Przerwanie przed zapisem może wymagać odtworzenia
do19 aktualizacji. Gdy zapis narusza rezerwę4GiB, pozostaje poprzedni checkpoint.

`--resume` odtwarza wagi, optimizer, RNG Python/NumPy/Torch, kolejność, pozycję,
epokę i czas. Scheduler jest `None`. Sprawdza hashe danych/polityki/kodu/
akceptacji/modelu i wersje bibliotek. Faza `completing_export` pozwala dokończyć
eksport przed wymaganiem walidacji. Nie zmieniać kodu podczas runu.

`serve_checkpoint.py` używa prawdziwego SDK za istniejącym runtime.
`serve_adapter.py` dodaje diagnostykę do istniejącego adaptera. Jego
`/health/checkpoint` pyta ten sam klient upstream, który wykonuje klasyfikację.
Wagi, tokenizer i konfiguracja są sprawdzane hashami; CPU AMP zabronione.
Nie zmieniono produkcyjnego Compose ani Gemmy.

`evaluate.py`: tylko lokalne Chat Completions, jedna próba, pełne requesty
i surowe odpowiedzi. Po błędzie lub10 przypadkach wymaga rzeczywistego
przeglądu i notatki. Nie automatyzować `review`. Niejasna rozpoczęta próba
blokuje wznowienie. Wyniki są ponownie sprawdzane z requestami, odpowiedziami,
parsingiem, hashami i etykietami. Błędy protokołu pozostają w mianowniku.
Finalne testy wymagają osobnego freeze.

`select_checkpoint.py`: wyłącznie kompletna, audytowana walidacja500.
Wybór macro-F1, accuracy, wcześniejsza epoka; patience2, maksymalnie4 epoki.
Trener sprawdza decyzję i hashe wcześniejszych raportów. Nie tworzyć ręcznie
`decision.json`, nie wybierać według testu.

## Uruchomiony trening i wznowienie

Dokładny argv i ID kontenera: `runs/wskz-laya-train-epoch1/`.
Tylko train jest montowany do trenera, wszystkie wejścia read-only.

```sh
.venv/bin/python training/laya-routing/run_training.py --name wskz-laya-train-epoch1
```

Nie powtarzać startu. Log zdarzeń i checkpoint są w `work/run-20260927/`.
Po ukończonej i audytowanej walidacji oraz decyzji selektora wznowić kolejną
epokę z nową nazwą kontenera i `--resume`. Najpierw zatrzymać wyłącznie
kontenery ewaluacji tego zadania; launcher odmawia konkurencji zasobów.

## Pełnowymiarowy zapis i odczyt

Przed treningiem docelowym `preflight.py --steps 2 --verify-checkpoint`
sprawdza zapis rzeczywistego modelu i AdamW, zwolnienie obiektów, odczyt mmap
i odtworzenie świeżego modelu/optimizera oraz eksport safetensors. Porównuje
SHA-256 każdego tensora, nie wynik jakości. Używa tych samych16 przykładów
train i zasobów; wyeksportowane wagi są tylko artefaktem próby technicznej.
Serwer generowania Gemmy jest na ten czas zatrzymany. Komenda z PoC:

```sh
docker stop wskz-laya-data-gemma
docker run --name wskz-laya-checkpoint-probe --network none --memory 10g --memory-swap 10g \
  --mount source=message-router_laya-models,target=/models,readonly \
  --mount type=bind,source="$PWD/training/laya-routing",target=/work \
  --env HF_HUB_OFFLINE=1 --env TRANSFORMERS_OFFLINE=1 \
  --entrypoint python sha256:4d0ffa68273f122a8bb1db1a14d1503b7cca218c91d05c4970ede69601107989 \
  -u /work/preflight.py --steps 2 --verify-checkpoint \
  --model /models/hub/models--convaiinnovations--laya/snapshots/55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851/multilingual \
  --output /work/runs/checkpoint-probe-20260927
```

Zachować stdout i stan kontenera; odczyt wyników nie jest kolejną inferencją.
Nie wznowić w istniejącym katalogu ani nie używać wag próby jako kandydata.
Po ukończeniu `docker start wskz-laya-data-gemma` przywraca ten sam serwer
z zachowaniem przypiętego ID; dalsze generowanie zależy od akceptacji danych.

Wynik próby checkpointu: zaliczony, exit0, bezOOM.32 backward i2 aktualizacje,
checkpoint3,861,535,435 bajtów, eksport1,287,653,720 bajtów, wszystkie tensory
modelu i AdamW identyczne po odczycie, eksport zgodny z checkpointem.
Peak RSS8.34GiB w limicie10GiB. Dowody: `runs/checkpoint-probe-20260927/`.
To test serializacji na danych zasobowych, nie kandydat ani wynik benchmarku.

## Izolowane serwowanie wyeksportowanej epoki

Po treningu zapis `base_assets` z `work/run-20260927/contract.json` należy
utrwalić jako osobny `base-assets.json`. Runtime dostaje wyłącznie eksport
wskazanej epoki, ten manifest i kod serwera, bez danych testowych. Obraz
adaptera: `sha256:37701ba29c1d2f7c2f2bb31ae307ee21b77642216f3931f16355456fd7506e5b`.
Serwer główny Gemmy pozostaje nietknięty; tymczasowy serwer autora danych
musi być zatrzymany na czas treningu/ewaluacji Laya.

Przed uruchomieniem utrwalić konkretny katalog epoki i SHA wag. Utworzyć
sieć `wskz-laya-evaluation` jako Docker internal. Runtime w tej sieci,
limit10GiB, przypięty obraz Laya, read-only wolumen bazowy `/models`,
read-only eksport `/checkpoint`, `/code/serve_checkpoint.py`,
`/runtime-source/runtime.py` z `services/laya-runtime/runtime.py` i manifest.
Env: `CHECKPOINT_PATH=/checkpoint`, `CHECKPOINT_SHA256=<SHA>`,
`BASE_ASSETS_MANIFEST=/inputs/base-assets.json`, `LAYA_CPU_AMP=0`,
`HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, `PYTHONPATH=/code`.
Komenda: `uvicorn serve_checkpoint:app --host 0.0.0.0 --port 8000
--workers 1 --no-access-log`.

Adapter w tej samej sieci dostaje `/code/serve_adapter.py`,
`PYTHONPATH=/code:/app`, `LAYA_BASE_URL=http://<nazwa-runtime>:8000`,
`LAYA_MODEL=multilingual`; udostępnia tylko `127.0.0.1:18091:8000`.
Komenda: `uvicorn serve_adapter:app --host 0.0.0.0 --port 8000
--workers 1 --no-access-log`. Evaluator sprawdza wagę przez
`/health/checkpoint` adaptera, które pyta dokładnie ten sam upstream co
rzeczywiste decyzje. Przed oceną mała kontrola wyłącznie na train.
Dokładne wykonane polecenia/kontenery zapisać przy run, nie przedstawiać
powyższej przygotowanej procedury jako wykonanego testu live.

## Aktualne launchery i zamrożenie wyniku

`run_training.py` zapisuje dokładne polecenie i ID kontenera w `runs/<name>/`.
`run_runtime.py` zapisuje oba polecenia, ID kontenerów i manifest bazowych aktywów.
Te launchery nie uruchamiają ani nie akceptują bramek ewaluacji.
Po zakończeniu epoki1:

```sh
.venv/bin/python training/laya-routing/run_runtime.py --epoch 1 --name wskz-laya-eval-epoch1
```

Sprawdzić `/health/checkpoint` na `http://127.0.0.1:18091`, zgodność SHA z
`export/epoch-1/provenance.json` oraz pojedynczą kontrolę API na danych train.
Runner `evaluate.py run` wymaga `--input data/validation.jsonl`, `--policy policy.json`,
`--output work/run-20260927/validation-1`, `--weights-sha256 <SHA>` i
`--split validation` (ścieżki względem `training/laya-routing/`). Po każdej
bramce przeczytać wyniki i surowe odpowiedzi, następnie wywołać `review`
z tymi samymi argumentami i konkretnym `--note`. Po500 wykonać `report`.
Nie automatyzować akceptacji przeglądów i nie ponawiać prób.

```sh
.venv/bin/python training/laya-routing/select_checkpoint.py \
  --run training/laya-routing/work/run-20260927 \
  --validation training/laya-routing/data/validation.jsonl \
  --policy training/laya-routing/policy.json \
  --approval training/laya-routing/data/acceptance.json --epoch 1
```

Przy `stop=false` zatrzymać wyłącznie kontenery `wskz-laya-eval-epoch1-adapter`
i `wskz-laya-eval-epoch1-runtime`, następnie uruchomić `run_training.py`
z `--name wskz-laya-train-epoch2 --resume`. Powtarzać według zamrożonego
warunku zatrzymania. Zachować wszystkie poprzednie kontenery/logi/eksporty.

Po `stop=true`:

```sh
.venv/bin/python training/laya-routing/freeze_selected.py
```

Skrypt ponownie audytuje komplet walidacji i przeglądów, sprawdza wybrane wagi,
politykę i hashe obu testów, zapisuje wyłącznie nowy `work/run-20260927/final-freeze.json`.
Nie otwiera treści testu. Finalny runner wymaga `--freeze` z tym plikiem.
Dla wybranej epoki i bazy (`run_runtime.py --base --name wskz-laya-eval-base`)
wykonać osobno `data/test.jsonl --split test` oraz
`verification/benchmark/cases-500.json --split regression`, raz na każde wagi.
Każdy przebieg ma osobny katalog dowodów. Zatrzymać runtime między wariantami.
Nie dopasowywać modelu według ujawnionych błędów końcowych.

## Kontrola live po pierwszej epoce

Epoka1 ukończona exit0, bezOOM; wagi SHA
`1b69c0e79d45ee9decac6bc0840985652448b8c28af59a30ecdf7f04628098a8`.
Kontrola train przez API poprawna. Walidacja500:447 poprawnych,53 pomyłki,
0 błędów protokołu; wszystkie bramki faktycznie obejrzane przez root, bez krytyka.
Surowe requesty/odpowiedzi, przeglądy, metryki i decyzja w
`work/run-20260927/validation-1/`; logi runtime w `runs/wskz-laya-eval-epoch1/`.

Docker nie publikuje portów sieci internal-only. Adapter podłączono dodatkowo
do bridge wejściowego; opublikowany port pozostaje wyłącznie127.0.0.1:18091.
Runtime modelu pozostaje tylko w sieci internal. Dokładna komenda jest zapisana
w `ingress-command.json` i uwzględniona w launcherze. To naprawa dostępu localhost,
bez zmiany modelu, wejść, danych ani ścieżki klasyfikacji.

`observed_eval.py --session <session.json>` daje zwięzły widok kolejnej bramki:
liczby zgodnych/błędnych tras, rzeczywiste argumenty ostatniej surowej odpowiedzi,
a dla każdego błędu pełną wiadomość i odpowiedź. Całe surowe dowody pozostają
zapisane. Wznowienie wymaga jawnego `--note` od operatora po obejrzeniu wyniku;
skrypt nie podejmuje decyzji przeglądu samodzielnie. `--report` po ostatniej bramce
uruchamia pełny audyt oryginalnego evaluatora. Zamrożony evaluator bez zmian.

## Dokończenie walidacji epoki2

Wznowiono istniejące kontenery przez `docker start wskz-laya-eval-epoch2-runtime wskz-laya-eval-epoch2-adapter`. Sprawdzono `/health/checkpoint`: SHA `992a2a7bd5efb93f97921752b88f2a45c19ce2ec0c12bd69f0b28f7cbbfd3a5f`. Użyto niezmienionego `observed_eval.py --session training/laya-routing/runs/wskz-laya-eval-epoch2/session.json --note <rzeczywisty przegląd>` po każdej bramce, na końcu `--report`. Audyt500 zaliczony. Dane, polityka i wagi bez zmian; brak ponowień. Dowody: `work/run-20260927/validation-2/metrics.json`. Po raporcie oba kontenery zatrzymano przez `docker stop`. Nie wznawiać treningu ani uruchamiać kolejnych testów.
