# Zatwierdzone autorstwo i natychmiastowy trening Laya

Użytkownik zatwierdził zmianę słowami „Tak potem od razu trenuj”. Root redaguje
wiadomości według sprawdzonej próbki15 tekstów; niezależny krytyk kontroluje
wierność, etykiety i przecieki. Nie pytać ponownie o tę zgodę ani o rozpoczęcie
treningu po zaliczeniu kontroli. Nie korzystać z odrzuconych tekstów Gemmy.

Obowiązują pozostałe ustalenia z `../../docs/LAYA_GENERALIZATION_APPROACH.md`
i `RUNBOOK.md`:600 rodzin/60grup,2000/500/500, seed42, zamrożony planSHA
561b082828ec7b8219d29d9adc2bdeac6cac59ad49e3f256d401800391510b99.
Stare500 i15smoke wyłącznie jako wykluczenia i końcowa regresja, nigdy jako
źródło treści, etykiet treningowych lub wyboru modelu. Teksty autorskie,
syntetyczne; pięć skorelowanych wariantów nie jest pięcioma niezależnymi
scenariuszami. Zachować short/context/resolved_history/quotation/informal,
samodzielny kontekst i dokładną aktualną intencję. Zróżnicować zakończone
sprawy oraz naturalne formy, nie mnożyć szablonów ani podmian nazw.

## Wejście, wynik i komendy

`source/authored/*.txt`: ręcznie napisane bloki, identyfikator rodziny w pierwszej
linii, następnie dokładnie pięć pełnych wiadomości, pusty wiersz między blokami.
`collect_authored.py` tylko parsuje teksty i przypina hashe; nie generuje,
nie parafrazuje i nie dopisuje treści. Wynik `source/accepted-authored.jsonl`
i `source/collection-audit.json`. Pełny build dopiero po wszystkich600 rodzinach.

Z katalogu PoC:

```sh
.venv/bin/python training/laya-routing/collect_authored.py
.venv/bin/python training/laya-routing/prepare_data.py build
```

Audyt leksykalny wszystkich3000 wiadomości wobec wykluczeń i innych splitów,
niezależny przegląd semantyczny każdej partii i końcowa akceptacja związana
hashami poprzedzają `data/acceptance.json`. Odrzucone wersje zachować w historii;
nie poprawiać według wyników Laya. Do czasu zaakceptowania danych ich nazwa
accepted-authored oznacza jedynie kompletny zapis źródłowy, nie zgodę na trening.

## Trening i wznowienie

CPU/FP32, microbatch1, akumulacja16, AdamW encoder2.5e-5/head1e-4, weight decay.01,
clip1, seed42, maksymalnie4epoki/8h treningu, early stopping2epoki bez poprawy.
Trener dostaje tylko train, politykę, akceptację i bazowe wagi read-only.
Walidacja przez lokalne Chat Completions po każdej epoce; wybór macroF1,
accuracy, wcześniejsza epoka. Test nie jest montowany w trainerze. Komendy
kontenerów, checkpointu i serwowania są w `RUNBOOK.md`.

Po akceptacji danych od razu uruchomić trening. Zapisywać logi i atomowy
checkpoint; wznowienie `--resume` sprawdza wszystkie hashe i RNG. Nie zmieniać
kodu/danych podczas runu. Po wyborze zamrozić wagi/politykę i wykonać końcowe
new500+old500 dla bazy i kandydata. Kontrole błędów i co10 przypadków zachowane;
bez retry, SMTP, podmiany Gemmy i trenowania według końcowych błędów.
