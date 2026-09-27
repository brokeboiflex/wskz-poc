# Comparison failures

## qwen: payroll/unpaid-leave/base

Expected: payroll; actual: human_resources; category: wrong_route.

Input:

Potrzebuję dwóch tygodni wolnego z powodów osobistych, ale nie chcę wykorzystywać urlopu wypoczynkowego. Chciałabym dowiedzieć się, jak złożyć wniosek o urlop bezpłatny i jakie dane powinien zawierać. Proszę również wskazać, z kim potwierdzić formalny okres takiej nieobecności.

Raw response:

```json
{
  "id": "chatcmpl-317",
  "object": "chat.completion",
  "created": 1790457157,
  "model": "qwen3:4b-instruct-2507-q4_K_M",
  "system_fingerprint": "fp_ollama",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "",
        "tool_calls": [
          {
            "id": "JmmHIJ0sxkwz75pdy8KOzrQyHADI9qEe",
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
    "prompt_tokens": 585,
    "prompt_tokens_details": {
      "cached_tokens": 486
    },
    "completion_tokens": 22,
    "total_tokens": 607
  }
}
```

## qwen: help_desk/slow-laptop/base

Expected: help_desk; actual: it; category: wrong_route.

Input:

Od kilku dni mój laptop bardzo wolno otwiera programy, nawet zanim połączę się z firmowymi zasobami. Wentylator pracuje głośno, a ponowne uruchomienie pomaga tylko na chwilę. Proszę sprawdzić stan tego urządzenia; pozostałe stanowiska w zespole nie mają podobnych objawów.

Raw response:

```json
{
  "id": "chatcmpl-568",
  "object": "chat.completion",
  "created": 1790457446,
  "model": "qwen3:4b-instruct-2507-q4_K_M",
  "system_fingerprint": "fp_ollama",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "",
        "tool_calls": [
          {
            "id": "Gt6vOZh90MOn9hNtioGuDNISVLnpkbgi",
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
    "prompt_tokens": 575,
    "prompt_tokens_details": {
      "cached_tokens": 486
    },
    "completion_tokens": 21,
    "total_tokens": 596
  }
}
```

## qwen: other/museum/quoted_history

Expected: other; actual: human_resources; category: wrong_route.

Input:

Dzień dobry, poniżej przesyłam aktualną wiadomość.

Wybieram się z rodziną do muzeum techniki i chciałbym wcześniej przygotować dzieci do zwiedzania. Jakie pytania można zadawać przy oglądaniu dawnych maszyn, żeby zainteresować je historią wynalazków?

> Archiwalna korespondencja, sprawa zakończona:
> Mój wcześniejszy wniosek o urlop został już poprawnie rozliczony. Nie potrzebuję żadnych dalszych zmian w saldzie ani dokumentacji.

Cytat pozostawiam dla ciągłości korespondencji. Nie wznawiam starego zgłoszenia.

Raw response:

```json
{
  "id": "chatcmpl-662",
  "object": "chat.completion",
  "created": 1790457723,
  "model": "qwen3:4b-instruct-2507-q4_K_M",
  "system_fingerprint": "fp_ollama",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "",
        "tool_calls": [
          {
            "id": "Qcb558GtTaeKNmO8ehiKkFTVjYKhrcKC",
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
    "prompt_tokens": 665,
    "prompt_tokens_details": {
      "cached_tokens": 486
    },
    "completion_tokens": 22,
    "total_tokens": 687
  }
}
```

## qwen: other/press-request/base

Expected: other; actual: human_resources; category: wrong_route.

Input:

Przygotowuję artykuł o lokalnych przedsiębiorstwach i chciałabym uzyskać zgodę na krótką rozmowę o historii Państwa firmy. Czy można skontaktować mnie z osobą uprawnioną do wypowiedzi dla mediów? Mogę wcześniej przesłać zakres pytań i uzgodnić termin autoryzacji wypowiedzi.

Artykuł będzie dotyczył zmian, jakie zaszły w dzielnicy w ciągu ostatnich kilkunastu lat. Interesuje mnie historia powstania firmy, jej związek z okolicą i wspomnienia osób, które pamiętają pierwszą siedzibę. Nie potrzebuję danych finansowych ani informacji o konkretnych pracownikach.

Rozmowa może odbyć się telefonicznie lub osobiście, w dogodnym dla rozmówcy terminie. Przewiduję około dwudziestu minut i wcześniej prześlę listę zagadnień. Jeśli firma dysponuje archiwalnym zdjęciem budynku przeznaczonym do publikacji, chętnie uzgodnię również możliwość jego wykorzystania z odpowiednim podpisem. Proszę przekazać zapytanie osobie, która może reprezentować firmę w kontakcie z redakcją.

Raw response:

```json
{
  "id": "chatcmpl-321",
  "object": "chat.completion",
  "created": 1790457831,
  "model": "qwen3:4b-instruct-2507-q4_K_M",
  "system_fingerprint": "fp_ollama",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "",
        "tool_calls": [
          {
            "id": "FiMxKKAEZ4ZzKv392EBaIHumFy9aNFlx",
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
    "prompt_tokens": 800,
    "prompt_tokens_details": {
      "cached_tokens": 486
    },
    "completion_tokens": 22,
    "total_tokens": 822
  }
}
```

## qwen: other/unknown-reference/resolved_preface

Expected: other; actual: payroll; category: wrong_route.

Input:

Najpierw potwierdzenie zamknięcia poprzedniego wątku: Mój wcześniejszy wniosek o urlop został już poprawnie rozliczony. Nie potrzebuję żadnych dalszych zmian w saldzie ani dokumentacji.

Osobna, aktualna wiadomość:
Wracam do tego, o czym rozmawialiśmy ostatnio. Czy udało się już ustalić rozwiązanie i można przejść do kolejnego etapu? Dajcie znać, bo czekam na odpowiedź.

Raw response:

```json
{
  "id": "chatcmpl-314",
  "object": "chat.completion",
  "created": 1790457853,
  "model": "qwen3:4b-instruct-2507-q4_K_M",
  "system_fingerprint": "fp_ollama",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "",
        "tool_calls": [
          {
            "id": "8PB1M4cEiK2EKS7NGYI5Nw4B8anjD8XU",
            "index": 0,
            "type": "function",
            "function": {
              "name": "send_department_email",
              "arguments": "{\"department\":\"payroll\"}"
            }
          }
        ]
      },
      "finish_reason": "tool_calls"
    }
  ],
  "usage": {
    "prompt_tokens": 620,
    "prompt_tokens_details": {
      "cached_tokens": 486
    },
    "completion_tokens": 22,
    "total_tokens": 642
  }
}
```

## qwen: other/vague-urgent/base

Expected: other; actual: help_desk; category: wrong_route.

Input:

To bardzo pilne!!! Sytuacja od rana jest taka sama. Ktoś może się wreszcie tym zająć? Potrzebuję odpowiedzi jeszcze dzisiaj.

Raw response:

```json
{
  "id": "chatcmpl-340",
  "object": "chat.completion",
  "created": 1790457873,
  "model": "qwen3:4b-instruct-2507-q4_K_M",
  "system_fingerprint": "fp_ollama",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "",
        "tool_calls": [
          {
            "id": "92LWVevb4nu8JPF0PoPkoIs0uqVv70Oi",
            "index": 0,
            "type": "function",
            "function": {
              "name": "send_department_email",
              "arguments": "{\"department\":\"help_desk\"}"
            }
          }
        ]
      },
      "finish_reason": "tool_calls"
    }
  ],
  "usage": {
    "prompt_tokens": 532,
    "prompt_tokens_details": {
      "cached_tokens": 486
    },
    "completion_tokens": 23,
    "total_tokens": 555
  }
}
```

## qwen: other/vague-urgent/resolved_postscript

Expected: other; actual: help_desk; category: wrong_route.

Input:

To bardzo pilne!!! Sytuacja od rana jest taka sama. Ktoś może się wreszcie tym zająć? Potrzebuję odpowiedzi jeszcze dzisiaj.

PS. Komputer został naprawiony i działa poprawnie. Zakończenie tamtego zgłoszenia technicznego zostało potwierdzone. Ta dopisana informacja nie jest nową prośbą.

Raw response:

```json
{
  "id": "chatcmpl-959",
  "object": "chat.completion",
  "created": 1790457903,
  "model": "qwen3:4b-instruct-2507-q4_K_M",
  "system_fingerprint": "fp_ollama",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "",
        "tool_calls": [
          {
            "id": "ZYaOdZXcHIW28XxLshUTSJ4iXepriKBx",
            "index": 0,
            "type": "function",
            "function": {
              "name": "send_department_email",
              "arguments": "{\"department\":\"help_desk\"}"
            }
          }
        ]
      },
      "finish_reason": "tool_calls"
    }
  ],
  "usage": {
    "prompt_tokens": 585,
    "prompt_tokens_details": {
      "cached_tokens": 526
    },
    "completion_tokens": 23,
    "total_tokens": 608
  }
}
```

## qwen: other/unknown-error/base

Expected: other; actual: help_desk; category: wrong_route.

Input:

Coś się nie zgadza, ale trudno mi teraz dokładnie wyjaśnić co. Wczoraj było inaczej. Czy mogę najpierw z kimś porozmawiać i ustalić, od czego zacząć?

Raw response:

```json
{
  "id": "chatcmpl-868",
  "object": "chat.completion",
  "created": 1790457937,
  "model": "qwen3:4b-instruct-2507-q4_K_M",
  "system_fingerprint": "fp_ollama",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "",
        "tool_calls": [
          {
            "id": "H0v2cMSBxHet5FBUoWRRy3Tq8evhTVoC",
            "index": 0,
            "type": "function",
            "function": {
              "name": "send_department_email",
              "arguments": "{\"department\":\"help_desk\"}"
            }
          }
        ]
      },
      "finish_reason": "tool_calls"
    }
  ],
  "usage": {
    "prompt_tokens": 549,
    "prompt_tokens_details": {
      "cached_tokens": 486
    },
    "completion_tokens": 23,
    "total_tokens": 572
  }
}
```

## qwen: other/unknown-error/forwarded_history

Expected: other; actual: it; category: wrong_route.

Input:

Przekazuję nową wiadomość w ramach tej samej korespondencji:

Coś się nie zgadza, ale trudno mi teraz dokładnie wyjaśnić co. Wczoraj było inaczej. Czy mogę najpierw z kimś porozmawiać i ustalić, od czego zacząć?

--- Przekazany stary wątek: ZAMKNIĘTY ---
Awaria firmowej sieci została usunięta. Nie występują już żadne objawy i nie ma potrzeby dalszej interwencji.
--- Koniec archiwum ---
Proszę nie otwierać ponownie sprawy opisanej w archiwum.

Raw response:

```json
{
  "id": "chatcmpl-778",
  "object": "chat.completion",
  "created": 1790457961,
  "model": "qwen3:4b-instruct-2507-q4_K_M",
  "system_fingerprint": "fp_ollama",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "",
        "tool_calls": [
          {
            "id": "xktlwvoM4Ve1v6MBnzL1fSehAD1cNEdQ",
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
    "prompt_tokens": 653,
    "prompt_tokens_details": {
      "cached_tokens": 486
    },
    "completion_tokens": 21,
    "total_tokens": 674
  }
}
```

## qwen: other/fragment/conversation_history

Expected: other; actual: it; category: wrong_route.

Input:

Historia wcześniejszej rozmowy:
Ja: Awaria firmowej sieci została usunięta. Nie występują już żadne objawy i nie ma potrzeby dalszej interwencji.
Odpowiedź: Dziękujemy za potwierdzenie zakończenia tamtej sprawy.

Moja obecna wiadomość dotyczy osobnej kwestii:
Dzień dobry, w nawiązaniu do kwestii związanej z tym, że w ubiegłym tygodniu miało zostać ustalone

Raw response:

```json
{
  "id": "chatcmpl-307",
  "object": "chat.completion",
  "created": 1790458010,
  "model": "qwen3:4b-instruct-2507-q4_K_M",
  "system_fingerprint": "fp_ollama",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "",
        "tool_calls": [
          {
            "id": "FIiUI9dWxXfTpHa36ivr2g4XFXgB2l6V",
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
    "prompt_tokens": 618,
    "prompt_tokens_details": {
      "cached_tokens": 486
    },
    "completion_tokens": 21,
    "total_tokens": 639
  }
}
```

## qwen: other/unknown-number/forwarded_history

Expected: other; actual: payroll; category: wrong_route.

Input:

Przekazuję nową wiadomość w ramach tej samej korespondencji:

Cześć, co z numerem 4827? Mam tylko taki zapis w notesie. Możecie sprawdzić i dać znać?

--- Przekazany stary wątek: ZAMKNIĘTY ---
Mój wcześniejszy wniosek o urlop został już poprawnie rozliczony. Nie potrzebuję żadnych dalszych zmian w saldzie ani dokumentacji.
--- Koniec archiwum ---
Proszę nie otwierać ponownie sprawy opisanej w archiwum.

Raw response:

```json
{
  "id": "chatcmpl-35",
  "object": "chat.completion",
  "created": 1790458069,
  "model": "qwen3:4b-instruct-2507-q4_K_M",
  "system_fingerprint": "fp_ollama",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "",
        "tool_calls": [
          {
            "id": "hZm6N0GGGFZ5qEI60VAeVCSmJfKaR8Cs",
            "index": 0,
            "type": "function",
            "function": {
              "name": "send_department_email",
              "arguments": "{\"department\":\"payroll\"}"
            }
          }
        ]
      },
      "finish_reason": "tool_calls"
    }
  ],
  "usage": {
    "prompt_tokens": 638,
    "prompt_tokens_details": {
      "cached_tokens": 486
    },
    "completion_tokens": 22,
    "total_tokens": 660
  }
}
```

## qwen: other/undefined-document/quoted_history

Expected: other; actual: help_desk; category: wrong_route.

Input:

Dzień dobry, poniżej przesyłam aktualną wiadomość.

Potrzebuję poprawionej wersji tego dokumentu, który ostatnio omawialiśmy. Możecie podesłać? Nie pamiętam nazwy, chodzi o ten drugi.

> Archiwalna korespondencja, sprawa zakończona:
> Komputer został naprawiony i działa poprawnie. Zakończenie tamtego zgłoszenia technicznego zostało potwierdzone.

Cytat pozostawiam dla ciągłości korespondencji. Nie wznawiam starego zgłoszenia.

Raw response:

```json
{
  "id": "chatcmpl-730",
  "object": "chat.completion",
  "created": 1790458097,
  "model": "qwen3:4b-instruct-2507-q4_K_M",
  "system_fingerprint": "fp_ollama",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "",
        "tool_calls": [
          {
            "id": "NT4d6GMAOZaNZYy1btwmAC6hUFZZxWsw",
            "index": 0,
            "type": "function",
            "function": {
              "name": "send_department_email",
              "arguments": "{\"department\":\"help_desk\"}"
            }
          }
        ]
      },
      "finish_reason": "tool_calls"
    }
  ],
  "usage": {
    "prompt_tokens": 640,
    "prompt_tokens_details": {
      "cached_tokens": 486
    },
    "completion_tokens": 23,
    "total_tokens": 663
  }
}
```

## qwen: other/unspecified-approval/base

Expected: other; actual: human_resources; category: wrong_route.

Input:

Czy jest już zgoda? Miała być odpowiedź do piątku, a nadal czekam. Bez tego nie ruszę dalej.

Raw response:

```json
{
  "id": "chatcmpl-735",
  "object": "chat.completion",
  "created": 1790458129,
  "model": "qwen3:4b-instruct-2507-q4_K_M",
  "system_fingerprint": "fp_ollama",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "",
        "tool_calls": [
          {
            "id": "cXTTpGubfS6BHvYSZhPlawBSyXyJoERl",
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
    "prompt_tokens": 525,
    "prompt_tokens_details": {
      "cached_tokens": 486
    },
    "completion_tokens": 22,
    "total_tokens": 547
  }
}
```

## qwen: other/unknown-change/conversation_history

Expected: other; actual: payroll; category: wrong_route.

Input:

Historia wcześniejszej rozmowy:
Ja: Mój wcześniejszy wniosek o urlop został już poprawnie rozliczony. Nie potrzebuję żadnych dalszych zmian w saldzie ani dokumentacji.
Odpowiedź: Dziękujemy za potwierdzenie zakończenia tamtej sprawy.

Moja obecna wiadomość dotyczy osobnej kwestii:
Trzeba poprawić ten zapis, dalej jest stara wersja. Pisałem o tym wcześniej. Możecie to zmienić i potwierdzić?

Raw response:

```json
{
  "id": "chatcmpl-43",
  "object": "chat.completion",
  "created": 1790458151,
  "model": "qwen3:4b-instruct-2507-q4_K_M",
  "system_fingerprint": "fp_ollama",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "",
        "tool_calls": [
          {
            "id": "v9Uw6laJL3FDtBQvvjSDJsQkfNwYw8eO",
            "index": 0,
            "type": "function",
            "function": {
              "name": "send_department_email",
              "arguments": "{\"department\":\"payroll\"}"
            }
          }
        ]
      },
      "finish_reason": "tool_calls"
    }
  ],
  "usage": {
    "prompt_tokens": 629,
    "prompt_tokens_details": {
      "cached_tokens": 486
    },
    "completion_tokens": 22,
    "total_tokens": 651
  }
}
```

## gemma: other/private-purchase/resolved_preface

Expected: other; actual: None; category: protocol_error.

Input:

Najpierw potwierdzenie zamknięcia poprzedniego wątku: Mój wcześniejszy wniosek o urlop został już poprawnie rozliczony. Nie potrzebuję żadnych dalszych zmian w saldzie ani dokumentacji.

Osobna, aktualna wiadomość:
Kupiłam w sklepie internetowym czajnik do domu i otrzymałam model w innym kolorze niż zamówiony. Chciałabym napisać do sprzedawcy prośbę o wymianę. Czy możecie pomóc ułożyć taką wiadomość? Zakup był prywatny i nie ma związku z firmowym wyposażeniem.

Na potwierdzeniu zamówienia mam właściwy wariant, a etykieta pudełka wskazuje inny. Samo urządzenie wygląda na nieużywane i nie zostało jeszcze uruchomione. Mam zdjęcia przesyłki, numer zamówienia oraz wiadomość od sklepu potwierdzającą zakup.

Chciałabym poprosić o wymianę na zamówiony kolor, a nie o zwrot pieniędzy. Nie wiem, czy w pierwszej wiadomości opisywać wszystko szczegółowo, czy wystarczy krótka informacja i zdjęcia. Zależy mi na spokojnym tonie, bo być może to zwykła pomyłka podczas pakowania. Pomóżcie ułożyć jasną wiadomość do sprzedawcy z prośbą o wskazanie sposobu wymiany i o informację, jak przygotować paczkę do odbioru.

Raw response:

```json
{
  "id": "chatcmpl-539",
  "object": "chat.completion",
  "created": 1790458559,
  "model": "gemma4:e2b",
  "system_fingerprint": "fp_ollama",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "send_department_email{department:<|\"|>other<|\"|>}"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 732,
    "prompt_tokens_details": {
      "cached_tokens": 417
    },
    "completion_tokens": 13,
    "total_tokens": 745
  }
}
```
