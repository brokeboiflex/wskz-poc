# Laya: przygotowanie treningu WSKZ

Nowy test regresji na tych samych500 co Gemma ukończony: Laya epoka1 **432/500 (86,4%)**, Gemma493/500 (98,6%);0 błędów protokołu obu. Wybrano epokę1 wyłącznie po walidacji. Bez treningu i ponowień; kontenery zatrzymane. Raport i procedura: `training/laya-routing/runs/laya-gemma-same500/README.md` względem katalogu PoC. Wcześniejsze stwierdzenie o niewykonanym starym benchmarku jest historyczne.

Walidacja epoki2 dokończona na wyraźne polecenie użytkownika: **443/500 (88,6%)**, macro-F1 0,882589. Epoka1:447/500 (89,4%). Wznowiono tylko przypadki386–499, bez ponowień wcześniejszych. Bez kolejnego treningu, krytyka i dodatkowych testów. Kontenery zatrzymane, wagi zachowane. Końcowy test i stary benchmark niewykonane. Wcześniejsze przerwanie walidacji było błędną interpretacją polecenia użytkownika.

Poniżej historia wcześniejszych etapów.

Status27.09.2026: **pełny korpus zaakceptowany, epoka1 zakończona, trening epoki2 działa**
w `wskz-laya-train-epoch2`. Dane2000/500/500 są zamrożone; pełny audyt leksykalny
zaliczony,3000 wejść bez obcięć. Walidacja epoki1:447/500 (89,4%), macroF1 .893358,0 błędów protokołu.
Nie otwarto końcowego testu ani starego benchmarku.
Podejście: [MANUAL_AUTHORING_APPROACH.md](MANUAL_AUTHORING_APPROACH.md).
2500 tekstów ma niezależny przegląd,500 przegląd autora zgodnie z poleceniem
użytkownika „Nie odpalaj juz krytyka”. Nie uruchamiać dalszego krytyka.

Plan600 rodzin/60grup przeszedł audyt po wymianie13 kolizji.
Ostateczny hash: `561b082828ec7b8219d29d9adc2bdeac6cac59ad49e3f256d401800391510b99`.
Wersje planu i negatywne raporty zachowano w `source/history/`.

Zatwierdzone autorstwo lokalnej Gemmy wykonano w małych obserwowanych próbach.
18 odpowiedzi v1-v6/pilota jest zapisanych i audytowanych, ale nie tworzy
zaakceptowanego korpusu: występowała zmiana zadania, brak prawdziwych cytatów,
ogólne historie i powtórzenia. Cały materiał wyłączono z treningu. Dowody:
`generation/evidence-audit-20260927.json`, szczegóły w
[DATA_GENERATION_PROPOSAL.md](DATA_GENERATION_PROPOSAL.md). Serwer autora zatrzymany.

Użytkownik zatwierdził ręczne autorstwo i natychmiastowy trening po kontroli
słowami „Tak potem od razu trenuj”. Obowiązuje
[MANUAL_AUTHORING_APPROACH.md](MANUAL_AUTHORING_APPROACH.md). Teksty i raporty z hashami są kompletne; zakres niezależności opisuje akceptacja.
Źródła: `source/authored/`, przeglądy: `source/authored-reviews/`, odrzucone
wersje: `source/authored-history/`. Stan odczytuje `collect_authored.py --status`.
Pełny audyt: `source/collection-audit.json`; akceptacja: `data/acceptance.json`.
Trening i checkpointy: `work/run-20260927/`.

Trener nie przyjmuje danych bez przeglądu z hashami. Audyt pilnuje rodzin
oraz szerszych grup40/10/10. Raport ewaluacji uwzględnia korelację wariantów
i bootstrap całych rodzin oraz grup, z ograniczeniami syntetycznego testu.

## Wykonane pomiary

| Próba                       | Zakończone kroki AdamW | Wynik                                                                  |
| --------------------------- | ---------------------: | ---------------------------------------------------------------------- |
| `preflight-20260927`        |                      0 | OOM przy pierwszej aktualizacji, po 16 backward                        |
| `preflight-serial-20260927` |                      1 | Pierwszy krok ukończony, bramka dysku nie przeszła                     |
| `preflight-steady-20260927` |                      1 | OOM podczas drugiego kroku, po pierwszym microbatchu                   |
| `preflight-freed-20260927`  |                      1 | OOM przy drugiej aktualizacji, limit 7200 MiB                          |
| `preflight-12g-20260927`    |                      2 | Dwa pełne kroki i bramka dysku zaliczone, limit 10 GiB                 |
| `checkpoint-probe-20260927` |                      2 | Pełny zapis/odczyt Laya i AdamW oraz eksport zgodne tensor po tensorze |

Wszystkie próby: ten sam model multilingual, FP32, CPU, efektywny batch 16,
gradient checkpointing,16 autorskich przykładów wyłącznie train. Pierwsze pięć
prób zmieniało wagi tylko w pamięci. Szósta zapisała techniczny checkpoint
i eksport do kontroli serializacji; nie jest kandydatem treningu docelowego. To pomiar treningu,
nie wynik jakości klasyfikacji. Logity w logach pochodzą z trybu train/dropout.

Pierwsze trzy próby miały limit 6500 MiB (6.35 GiB); Docker miał 7.75 GiB łącznie.
Pierwszy krok nie jest dowodem wystarczającej pamięci: podczas drugiego
gradienty współistnieją z utworzonymi już momentami AdamW. Nie zwiększano
globalnej pamięci Docker podczas tych pierwszych prób.

Po zwolnieniu zasobów przez użytkownika zwiększono pamięć Docker Desktop z
8 do 12 GiB, przy zatrzymanych kontenerach. Ostatnia próba wykonała 32 backward
i dwie aktualizacje; peak RSS 7 741 759 488 bajtów. Wolne miejsce:
111 715 196 928 bajtów. To dowód wykonalności na długościach probe, nie gwarancja
całego treningu ani wynik klasyfikacji. Pełny korpus przejdzie audyt tokenizacji.

W pełnym checkpointcie same tensory zajmują 3 861 321 396 bajtów. Latest,
atomowy zapis następnego, best FP32 i rezerwa 4 GiB wymagają co najmniej
13 305 246 080 bajtów (12.39 GiB), przed narzutem plików. Podczas historycznej
próby `serial` dostępne było tylko 12 300 775 424 bajtów (11.46 GiB).
Brakowało około 0.94 GiB. Ten brak został usunięty przed ostatnią próbą.

Historyczne warunki następnej próby: więcej pamięci dla izolowanego treningu oraz większy
budżet wolnego dysku. Przydział 10-12 GiB RAM Docker i co najmniej 15 GiB wolnego
dysku to proponowany zapas do ponownego pomiaru, **nie zweryfikowana gwarancja**.
Zmiana globalnego limitu Docker wymaga restartu i dotknęłaby też inne usługi;
nie wykonano jej w ramach pierwszych trzech pomiarów. Alternatywny backend lub inny sposób
treningu wymaga zatwierdzenia zmiany podejścia.

## Kod, audyt i granice

- `optimizer.py` aktualizuje parametry kolejno i zwalnia zużyte gradienty.
  Test porównuje bitowo wagi oraz stany z AdamW po czterech krokach i wznowieniu.
  Dotyczy skonfigurowanego AdamW bez dodatkowych hooków/schedulera na wywołanie.
  Usuwa pierwszy pik pamięci; kolejne próby wykazały również potrzebę większej pamięci Docker.
- `data_guard.py` sprawdza oba zamrożone hashe, duplikaty, podział rodzin i
  podobieństwo leksykalne; pełny tryb wymaga dokładnie 2000/500/500 i balansu.
  Dziesięć testów sprawdza istotne odmowy oraz ograniczenia audytu.
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
pracę; właściwy trening działa w osobnym kontenerze. Logi, wersje kodu i oczyszczony stan
kontenerów pozostają w `runs/`. Nie nadpisywać ich przy wznowieniu.

Audyt dowodów offline z katalogu PoC:

```sh
.venv/bin/python training/laya-routing/audit_preflight.py
```

Aktualny audyt obejmuje wszystkie pięć prób. `resource_probe_passed=true`,
jego historyczne `training_ready=false` dotyczy czasu przed akceptacją danych.
Osobna szósta próba potwierdziła rzeczywisty save/reload Laya, AdamW i eksportu,
exit0, bezOOM, peak RSS8.34GiB; surowe dowody są w jej katalogu run. Dawny raport `runs/evidence-audit.json` zachowuje
wynik pierwszych trzech prób; nowy wynik zapisano osobno w
`runs/evidence-audit-resources-passed.json`. [Pełne komendy i braki](RUNBOOK.md).
