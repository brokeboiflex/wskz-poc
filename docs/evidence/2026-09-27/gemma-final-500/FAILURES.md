# Gemma failures

Full requests, raw responses and expected labels are also saved separately under `failures/NNN/` for debugging.

## Case 086: human_resources/recruitment-task/resolved_postscript

Expected: human_resources; actual: other; category: wrong_route.

[Full request](failures/086/request.json) | [Raw response](failures/086/raw-response.txt) | [Case and expected label](failures/086/case.json)

Input:

Otrzymałam zadanie rekrutacyjne polegające na przygotowaniu analizy sprzedaży. W instrukcji nie wskazano, czy prezentacja ma być po polsku, czy po angielsku. Zanim rozpocznę pracę, proszę o doprecyzowanie oczekiwań oraz potwierdzenie terminu przekazania rozwiązania osobie oceniającej kandydatów.

PS. Wczorajsza przerwa w dostępie do serwera plików została usunięta. Wszystkie zespoły potwierdziły poprawne działanie usługi. Ta dopisana informacja nie jest nową prośbą.

Raw response:

```json
{
  "id": "chatcmpl-894",
  "object": "chat.completion",
  "created": 1790518853,
  "model": "gemma4:e2b",
  "system_fingerprint": "fp_ollama",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "",
        "tool_calls": [
          {
            "id": "ngsXnKkYE2xFslYIeBLwubvVIP8Sbyvq",
            "index": 0,
            "type": "function",
            "function": {
              "name": "send_department_email",
              "arguments": "{\"department\":\"other\"}"
            }
          }
        ]
      },
      "finish_reason": "tool_calls"
    }
  ],
  "usage": {
    "prompt_tokens": 665,
    "prompt_tokens_details": {
      "cached_tokens": 607
    },
    "completion_tokens": 17,
    "total_tokens": 682
  }
}
```

## Case 113: payroll/parental-leave/base

Expected: payroll; actual: human_resources; category: wrong_route.

[Full request](failures/113/request.json) | [Raw response](failures/113/raw-response.txt) | [Case and expected label](failures/113/case.json)

Input:

Planuję rozpocząć urlop rodzicielski po zakończeniu obecnej nieobecności. Chciałbym uporządkować terminy i komplet dokumentów wymaganych przez pracodawcę. Proszę o informację, jaki wniosek należy złożyć, gdzie go przekazać i w jaki sposób potwierdzić przyjęcie dokumentacji.

Chcemy z drugim rodzicem wcześniej ustalić podział opieki i podać pracodawcom spójne terminy. Nie przesądzam jeszcze o ostatecznych datach, ponieważ potrzebuję najpierw sprawdzić, jak je prawidłowo zapisać we wniosku i jakie potwierdzenia należy dołączyć.

Czy mogę otrzymać listę wymaganych dokumentów oraz formularz stosowany w naszej firmie? Zależy mi również na informacji, gdzie odnotowane zostanie przyjęcie wniosku i w jaki sposób później otrzymam potwierdzenie okresu nieobecności. Dokumenty z danymi rodzinnymi przekażę dopiero przez wskazany kanał. Chciałbym uniknąć wysyłania kilku niepełnych wersji i przygotować komplet do jednorazowego sprawdzenia.

Raw response:

```json
{
  "id": "chatcmpl-100",
  "object": "chat.completion",
  "created": 1790518906,
  "model": "gemma4:e2b",
  "system_fingerprint": "fp_ollama",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "",
        "tool_calls": [
          {
            "id": "qpxfYvZHZjJf8ATr7i1OKS3oFmurB1R8",
            "index": 0,
            "type": "function",
            "function": {
              "name": "send_department_email",
              "arguments": "{\"department\":\"human_resources\"}"
            }
          }
        ]
      },
      "finish_reason": "tool_calls"
    }
  ],
  "usage": {
    "prompt_tokens": 775,
    "prompt_tokens_details": {
      "cached_tokens": 526
    },
    "completion_tokens": 19,
    "total_tokens": 794
  }
}
```

## Case 117: payroll/occasional-leave/base

Expected: payroll; actual: human_resources; category: wrong_route.

[Full request](failures/117/request.json) | [Raw response](failures/117/raw-response.txt) | [Case and expected label](failures/117/case.json)

Input:

W przyszłym tygodniu biorę ślub i chciałbym skorzystać z przysługującego z tego tytułu wolnego. Nie wiem, jaki rodzaj wniosku wybrać ani kiedy przedstawić potwierdzenie zdarzenia. Proszę o wskazanie wymaganych formalności i sposobu ujęcia tych dni w ewidencji czasu pracy.

Raw response:

```json
{
  "id": "chatcmpl-378",
  "object": "chat.completion",
  "created": 1790518913,
  "model": "gemma4:e2b",
  "system_fingerprint": "fp_ollama",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "",
        "tool_calls": [
          {
            "id": "P4oei3WAlN4xUbTStuU7pz8ztHv9VeIC",
            "index": 0,
            "type": "function",
            "function": {
              "name": "send_department_email",
              "arguments": "{\"department\":\"human_resources\"}"
            }
          }
        ]
      },
      "finish_reason": "tool_calls"
    }
  ],
  "usage": {
    "prompt_tokens": 599,
    "prompt_tokens_details": {
      "cached_tokens": 527
    },
    "completion_tokens": 19,
    "total_tokens": 618
  }
}
```

## Case 147: payroll/employment-certificate/base

Expected: payroll; actual: other; category: wrong_route.

[Full request](failures/147/request.json) | [Raw response](failures/147/raw-response.txt) | [Case and expected label](failures/147/case.json)

Input:

Bank poprosił mnie o aktualne zaświadczenie potwierdzające zatrudnienie w naszej firmie. Formularz wymaga podpisu pracodawcy i wskazania rodzaju umowy. Proszę o informację, komu przekazać druk i ile czasu zajmuje przygotowanie takiego dokumentu do odbioru.

Instytucja wymaga swojego formularza, na którym znajdują się pola dotyczące daty zatrudnienia, rodzaju umowy oraz potwierdzenia, że stosunek pracy nadal trwa. Nie wystarczy jej skan samej umowy. Dokument ma być podpisany przez upoważnioną osobę, a ja nie wiem, czy potrzebny jest oryginał formularza, czy wystarczy jego elektroniczna wersja.

Termin uzupełnienia wniosku mija w przyszły czwartek. Mogę odebrać dokument osobiście, jeśli będzie to szybsze. Proszę dać znać, jakie dane identyfikujące pracownika przekazać przez właściwy kanał i czy na druku powinienem sam uzupełnić jakąś część przed dostarczeniem. Zależy mi na uniknięciu konieczności ponownego wystawiania zaświadczenia.

Raw response:

```json
{
  "id": "chatcmpl-516",
  "object": "chat.completion",
  "created": 1790518967,
  "model": "gemma4:e2b",
  "system_fingerprint": "fp_ollama",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "",
        "tool_calls": [
          {
            "id": "WVMKUBkqzC4nNIZUwVkKboKDd0laaWKU",
            "index": 0,
            "type": "function",
            "function": {
              "name": "send_department_email",
              "arguments": "{\"department\":\"other\"}"
            }
          }
        ]
      },
      "finish_reason": "tool_calls"
    }
  ],
  "usage": {
    "prompt_tokens": 777,
    "prompt_tokens_details": {
      "cached_tokens": 526
    },
    "completion_tokens": 17,
    "total_tokens": 794
  }
}
```

## Case 174: payroll/employment-history/resolved_preface

Expected: payroll; actual: human_resources; category: wrong_route.

[Full request](failures/174/request.json) | [Raw response](failures/174/raw-response.txt) | [Case and expected label](failures/174/case.json)

Input:

Najpierw potwierdzenie zamknięcia poprzedniego wątku: Termin mojej rozmowy rozwojowej został już uzgodniony. Organizator potwierdził spotkanie i ten wątek jest zakończony.

Osobna, aktualna wiadomość:
Odnalazłam świadectwo pracy od poprzedniego pracodawcy, którego nie przekazałam przy zatrudnieniu. Może ono mieć znaczenie dla naliczenia mojego wymiaru urlopu. Proszę wskazać sposób uzupełnienia dokumentacji i zweryfikować, czy po jego uwzględnieniu zmieni się dostępny limit.

Raw response:

```json
{
  "id": "chatcmpl-497",
  "object": "chat.completion",
  "created": 1790519018,
  "model": "gemma4:e2b",
  "system_fingerprint": "fp_ollama",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "",
        "tool_calls": [
          {
            "id": "mXw1qeMuehvQ0Nwc5XChXSP7pCA99FVy",
            "index": 0,
            "type": "function",
            "function": {
              "name": "send_department_email",
              "arguments": "{\"department\":\"human_resources\"}"
            }
          }
        ]
      },
      "finish_reason": "tool_calls"
    }
  ],
  "usage": {
    "prompt_tokens": 662,
    "prompt_tokens_details": {
      "cached_tokens": 526
    },
    "completion_tokens": 19,
    "total_tokens": 681
  }
}
```

## Case 287: help_desk/local-backup-restore/base

Expected: help_desk; actual: other; category: wrong_route.

[Full request](failures/287/request.json) | [Raw response](failures/287/raw-response.txt) | [Case and expected label](failures/287/case.json)

Input:

Przez pomyłkę nadpisałam własny arkusz roboczy pustą wersją. Zauważyłam to dopiero po zamknięciu programu, więc cofnięcie ostatniej operacji już nie działa. Czy można sprawdzić historię wersji lub kopię mojego pliku, żeby odzyskać wczorajszą zawartość bez naruszania pozostałych dokumentów?

Pamiętam nazwę pliku i folder, w którym pracowałam. Ostatnia poprawna wersja była otwierana wczoraj po południu. Od zauważenia pomyłki nie zapisuję już kolejnych zmian, żeby nie utrudniać przywrócenia właściwej zawartości.

Raw response:

```json
{
  "id": "chatcmpl-993",
  "object": "chat.completion",
  "created": 1790519227,
  "model": "gemma4:e2b",
  "system_fingerprint": "fp_ollama",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "",
        "tool_calls": [
          {
            "id": "QfuA4yFYqA01SqVkdzVnLIWiyrsvr7O1",
            "index": 0,
            "type": "function",
            "function": {
              "name": "send_department_email",
              "arguments": "{\"department\":\"other\"}"
            }
          }
        ]
      },
      "finish_reason": "tool_calls"
    }
  ],
  "usage": {
    "prompt_tokens": 681,
    "prompt_tokens_details": {
      "cached_tokens": 526
    },
    "completion_tokens": 17,
    "total_tokens": 698
  }
}
```

## Case 472: other/missing-attachment/quoted_history

Expected: other; actual: it; category: wrong_route.

[Full request](failures/472/request.json) | [Raw response](failures/472/raw-response.txt) | [Case and expected label](failures/472/case.json)

Input:

Dzień dobry, poniżej przesyłam aktualną wiadomość.

Dzień dobry, proszę sprawdzić sprawę opisaną w załączniku i przekazać mi informację o dalszych krokach.

[Brak załączników]

> Archiwalna korespondencja, sprawa zakończona:
> Awaria firmowej sieci została usunięta. Nie występują już żadne objawy i nie ma potrzeby dalszej interwencji.

Cytat pozostawiam dla ciągłości korespondencji. Nie wznawiam starego zgłoszenia.

Raw response:

```json
{
  "id": "chatcmpl-108",
  "object": "chat.completion",
  "created": 1790519558,
  "model": "gemma4:e2b",
  "system_fingerprint": "fp_ollama",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "",
        "tool_calls": [
          {
            "id": "rh8H9cVY8Wuigx6KYQsqpkCpqrqqLNcm",
            "index": 0,
            "type": "function",
            "function": {
              "name": "send_department_email",
              "arguments": "{\"department\":\"it\"}"
            }
          }
        ]
      },
      "finish_reason": "tool_calls"
    }
  ],
  "usage": {
    "prompt_tokens": 656,
    "prompt_tokens_details": {
      "cached_tokens": 530
    },
    "completion_tokens": 17,
    "total_tokens": 673
  }
}
```
