# Laya: przygotowanie treningu WSKZ

Status 27.09.2026: **pełny trening zablokowany przez zasoby**. Nie ma dostrojonych
wag, pełnego nowego korpusu 2000/500/500 ani nowej ewaluacji 500 przypadków.
Zatwierdzone podejście: [LAYA_GENERALIZATION_APPROACH.md](../../docs/LAYA_GENERALIZATION_APPROACH.md).

## Wykonane pomiary

| Próba                       | Zakończone kroki AdamW | Wynik                                                |
| --------------------------- | ---------------------: | ---------------------------------------------------- |
| `preflight-20260927`        |                      0 | OOM przy pierwszej aktualizacji, po 16 backward      |
| `preflight-serial-20260927` |                      1 | Pierwszy krok ukończony, bramka dysku nie przeszła   |
| `preflight-steady-20260927` |                      1 | OOM podczas drugiego kroku, po pierwszym microbatchu |

Wszystkie próby: ten sam model multilingual, FP32, CPU, efektywny batch 16,
gradient checkpointing, 16 autorskich przykładów wyłącznie train. Wagi zmieniały
się jedynie w pamięci procesu i nie zostały wyeksportowane. To pomiar treningu,
nie wynik jakości klasyfikacji. Logity w logach pochodzą z trybu train/dropout.

Ostatnia próba miała limit 6500 MiB (6.35 GiB); Docker ma 7.75 GiB łącznie.
Pierwszy krok nie jest dowodem wystarczającej pamięci: podczas drugiego
gradienty współistnieją z utworzonymi już momentami AdamW. Nie zwiększano
globalnej pamięci Docker ani nie restartowano usług użytkownika.

W pełnym checkpointcie same tensory zajmują 3 861 321 396 bajtów. Latest,
atomowy zapis następnego, best FP32 i rezerwa 4 GiB wymagają co najmniej
13 305 246 080 bajtów (12.39 GiB), przed narzutem plików. Podczas udanej próby
dostępne było 12 300 775 424 bajtów (11.46 GiB). Brakuje około 0.94 GiB,
a dostępne miejsce w kolejnych odczytach jeszcze spadło. Nie pomijano rezerwy.

Warunki następnej próby: więcej pamięci dla izolowanego treningu oraz większy
budżet wolnego dysku. Przydział 10-12 GiB RAM Docker i co najmniej 15 GiB wolnego
dysku to proponowany zapas do ponownego pomiaru, **nie zweryfikowana gwarancja**.
Zmiana globalnego limitu Docker wymaga restartu i dotknęłaby też inne usługi;
nie wykonano jej w ramach tego pomiaru. Alternatywny backend lub inny sposób
treningu wymaga zatwierdzenia zmiany podejścia.

## Kod, audyt i granice

- `optimizer.py` aktualizuje parametry kolejno i zwalnia zużyte gradienty.
  Test porównuje bitowo wagi oraz stany z AdamW po czterech krokach i wznowieniu.
  Dotyczy skonfigurowanego AdamW bez dodatkowych hooków/schedulera na wywołanie.
  Usuwa pierwszy pik pamięci, lecz nie rozwiązuje OOM przy kolejnym backward.
- `data_guard.py` sprawdza oba zamrożone hashe, duplikaty, podział rodzin i
  podobieństwo leksykalne; pełny tryb wymaga dokładnie 2000/500/500 i balansu.
  Dziewięć testów sprawdza istotne odmowy oraz ograniczenia audytu.
- 16 nowych przykładów przeszło screening leksykalny względem 515 wykluczonych
  wiadomości. Nie potwierdza to niezależności semantycznej. Przed pełnym
  treningiem potrzebny jest przegląd związany z hashami korpusu. Te przykłady
  nie mogą stać się wzorcem stylistycznym całego zbioru.
- `policy.json` zachowuje aktualne pytanie i kryteria, bez dostrajania opisów
  do benchmarku. Tokenizacja: pytanie 37 tokenów, opcje 22/26/27/26/22;
  241-259 tokenów na całe wejście probe, bez obcięć.
- Niezależny krytyk wskazał potrzebę drugiego kroku, pełnego utrwalenia kodu
  i przypięcia również hash smoke corpus. Te uwagi uwzględniono.

Komendy oraz nazwy kontenerów są w podejściu. Kontenery pomiarowe zakończyły
pracę; nie działa żaden proces treningu. Logi, wersje kodu i oczyszczony stan
kontenerów pozostają w `runs/`. Nie nadpisywać ich przy wznowieniu.

Audyt dowodów offline z katalogu PoC:

```sh
.venv/bin/python training/laya-routing/audit_preflight.py
```

Raport audytu może potwierdzić kompletność zapisanych dowodów, podczas gdy
`training_ready` pozostaje `false`. Brak raportu ukończenia przy OOM nie jest
traktowany jako poprawne zakończenie. Nie uruchamiać pełnego treningu, dopóki
próba ciągłej pracy i budżet checkpointów nie przejdą.
