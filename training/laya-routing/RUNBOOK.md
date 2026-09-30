# Trening Laya

Polecenia uruchamiaj z głównego katalogu repozytorium. Trening działa na CPU
w FP32, bez dostępu do sieci. Wymaga lokalnych wag Laya multilingual,
tokenizera oraz środowiska z PyTorch, Laya, Transformers, NumPy i safetensors.

## Przygotowanie

`train.py` sprawdza sumę kontrolną bazowych wag, dane, politykę i metadane
akceptacji. Przy wznowieniu sprawdza również kod i wersje bibliotek.
Dane wejściowe to `data/train.jsonl`, `policy.json` i `data/acceptance.json`.
Zbiorów validation i test nie montuje się do kontenera trenera.

Launchery są skonfigurowane dla konkretnego lokalnego środowiska:

- wolumen modeli: `message-router_laya-models`;
- snapshot: `55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851/multilingual`
  w `hub/models--convaiinnovations--laya/snapshots/`;
- obraz treningowy: `sha256:4d0ffa68273f122a8bb1db1a14d1503b7cca218c91d05c4970ede69601107989`;
- katalog roboczy: `training/laya-routing/work/run-20260927`;
- limit kontenera: 10 GiB RAM, bez dodatkowego swapu.

Sam klon repozytorium nie zapewnia tych lokalnych zasobów. Przed użyciem
launcherów sprawdź ich dostępność oraz konfigurację `run_training.py` i
`run_runtime.py`. Oba launchery odmawiają startu, jeśli działa dowolny inny
kontener. Zmiana `--name` zmienia nazwę kontenera, nie katalog checkpointów.
Nowy eksperyment wymaga osobnego katalogu roboczego; istniejący wznawia się
przez `--resume`.

Trener wymaga miejsca na checkpoint, jego atomowy zapis, eksport wag oraz
4 GiB rezerwy dysku. Pamięć Dockera musi pomieścić kontener i narzut środowiska.

## Parametry

| Parametr | Wartość |
| --- | --- |
| Precyzja / urządzenie | FP32 / CPU |
| Microbatch / efektywny batch | 1 / 16 |
| Optimizer | AdamW |
| Learning rate encoder / head | 2,5e-5 / 1e-4 |
| Weight decay | 0,01 |
| Gradient clipping | 1 |
| Scheduler | Brak |
| Seed | 42 |
| Maksymalna liczba epok | 4 |
| Limit czasu obliczeń treningowych | 8 godzin |
| Zapis checkpointu | Co 20 aktualizacji i na granicach etapów |

Jedno wywołanie trenera wykonuje jedną epokę, po której wymagana jest walidacja.
Limit czasu nie obejmuje I/O ani walidacji.

## Uruchomienie

W przygotowanym środowisku lokalnym:

```sh
python training/laya-routing/run_training.py --name laya-train-epoch1
```

Bez launchera można wskazać ścieżki jawnie w środowisku z zależnościami modelu:

```sh
python training/laya-routing/train.py \
  --base /path/to/multilingual \
  --train training/laya-routing/data/train.jsonl \
  --policy training/laya-routing/policy.json \
  --approval training/laya-routing/data/acceptance.json \
  --run /path/to/new-run
```

Checkpoint zawiera wagi, optimizer, RNG, kolejność i pozycję danych, epokę
oraz czas treningu. `--resume` odtwarza ten stan; zmiana kontraktu powoduje
odmowę wznowienia. Eksport epoki znajduje się w `export/epoch-N/` katalogu run.

## Walidacja i wybór checkpointu

Po zakończeniu treningu uruchom runtime eksportowanej epoki:

```sh
python training/laya-routing/run_runtime.py --epoch 1 --name laya-eval-epoch1
curl --fail http://127.0.0.1:18091/health/checkpoint
```

Launcher runtime korzysta z tego samego stałego katalogu roboczego co launcher
treningu. Dla własnego katalogu run należy dostosować ścieżkę runtime.
SHA wag musi zgadzać się z `export/epoch-1/provenance.json`.

```sh
python training/laya-routing/evaluate.py run \
  --input training/laya-routing/data/validation.jsonl \
  --policy training/laya-routing/policy.json \
  --output training/laya-routing/work/run-20260927/validation-1 \
  --weights-sha256 <SHA_WAG> \
  --split validation
```

Evaluator zatrzymuje się po błędzie lub partii 10 przypadków. Po sprawdzeniu
odpowiedzi użyj komendy `review` z tymi samymi argumentami i `--note`
opisującym wynik kontroli, następnie kontynuuj `run`. Po pełnym zbiorze użyj
`report`. Niejasna rozpoczęta próba blokuje wznowienie; błędy protokołu liczą
się do wyniku. Każda wiadomość ma jedną próbę.

```sh
python training/laya-routing/select_checkpoint.py \
  --run training/laya-routing/work/run-20260927 \
  --validation training/laya-routing/data/validation.jsonl \
  --policy training/laya-routing/policy.json \
  --approval training/laya-routing/data/acceptance.json --epoch 1
```

Selektor wymaga kompletnej walidacji. Porównuje macro-F1, następnie accuracy,
a przy remisie wybiera wcześniejszą epokę. Patience wynosi 2, limit to 4 epoki.
Przy decyzji `stop=false` zatrzymaj runtime i adapter przed następną epoką:

```sh
docker stop laya-eval-epoch1-adapter laya-eval-epoch1-runtime
python training/laya-routing/run_training.py --name laya-train-epoch2 --resume
```

Dla kolejnej epoki zmień numer eksportu, katalog walidacji i argument `--epoch`.

## Końcowa ocena

Po decyzji `stop=true` utrwal wybór:

```sh
python training/laya-routing/freeze_selected.py
```

Skrypt korzysta z `work/run-20260927` i zapisuje `final-freeze.json`.
Końcową ocenę wykonuje `evaluate.py` na `data/test.jsonl`, z `--split test`
i `--freeze` wskazującym ten plik. Każdy oceniany model wymaga osobnego katalogu
wyników. Wynik testowy nie służy do wyboru checkpointu ani dostrajania modelu.
