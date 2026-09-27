"""Authored scenario definitions; no benchmark-derived text, inference or message templates."""

# Whole semantic groups stay in one split. Each line is one specific family.
GROUPS = [
    (
        "human_resources",
        "train",
        "recruitment_process",
        """
Organizacja rozmowy z kandydatem niesłyszącym wymagającym tłumacza migowego.
Uzgodnienie z kandydatem innej daty spotkania kwalifikacyjnego.
Przygotowanie merytorycznych pytań do ustrukturyzowanego wywiadu rekrutacyjnego.
Weryfikacja referencji kandydata za jego zgodą.
Przyjęcie wycofania aplikacji przez kandydata przed zakończeniem naboru.
Informacja o etapie trwającej rekrutacji bez żądania oceny kompetencji.
Organizacja zadania praktycznego dla kandydatów na redaktorów.
Ustalenie składu komisji rekrutacyjnej przy naborze kierownika.
Wyjaśnienie kryteriów preselekcji aplikacji bez historii własnego odrzucenia.
Zaplanowanie naboru po zatwierdzeniu nowego wakatu.
""",
    ),
    (
        "human_resources",
        "train",
        "interpersonal_conflict",
        """
Mediacja po publicznym krytykowaniu i upokarzaniu pracownika.
Interwencja wobec krzyku i zastraszania podwładnych przez przełożonego.
Wyjaśnienie konfliktu o przypisywanie sobie cudzych osiągnięć.
Zatrzymanie rozpowszechniania plotek naruszających godność kolegi.
Odbudowa współpracy dwóch osób odmawiających wspólnej realizacji projektu.
Rozwiązanie sporu między zespołami o sposób dzielenia odpowiedzialności.
Wsparcie osoby izolowanej po zgłoszeniu niewłaściwego traktowania.
Ustalenie granic między życiem prywatnym a zachowaniem współpracowników.
Poufna interwencja po niechcianych komentarzach seksualnych w pracy.
Rozmowa o demonstracyjnym pomijaniu pracownika w ustaleniach zespołu.
""",
    ),
    (
        "human_resources",
        "train",
        "equal_treatment",
        """
Zgłoszenie pomijania starszych pracowników przy ambitnych zadaniach.
Zbadanie odmowy odpowiedzialności zawodowej uzasadnianej płcią.
Interwencja po obraźliwych uwagach o pochodzeniu narodowym.
Rozwiązanie problemu wyśmiewania przekonań religijnych współpracownika.
Wsparcie pracownika dyskryminowanego z powodu niepełnosprawności.
Zgłoszenie nierównego traktowania osoby ze względu na orientację seksualną.
Wyjaśnienie stereotypowych ocen pracowników wychowujących dzieci.
Zbadanie gorszego traktowania osoby po długiej chorobie.
Ustalenie równych możliwości udziału osób zdalnych w życiu zespołu.
Przeciwdziałanie uprzedzeniom dotyczącym akcentu współpracownika.
""",
    ),
    (
        "human_resources",
        "train",
        "individual_development",
        """
Mentor i plan odbudowy kompetencji po powrocie z przerwy zawodowej.
Przygotowanie specjalisty do pierwszej roli kierowniczej.
Plan rozwoju eksperckiego dla osoby niechcącej zarządzać ludźmi.
Doradztwo przy zmianie specjalizacji zawodowej w organizacji.
Ustalenie następnego etapu nauki po warsztatach prezentacji.
Indywidualny coaching wspierający cele zawodowe.
Ocena luk kompetencyjnych przed podjęciem nowej odpowiedzialności.
Plan przygotowania następcy odchodzącego lidera.
Organizacja obserwowania pracy eksperta w celu nauki zawodu.
Uzgodnienie celów rozwojowych podczas powrotu do regularnych obowiązków.
""",
    ),
    (
        "human_resources",
        "train",
        "communication_training",
        """
Warsztat konstruktywnej informacji zwrotnej dla kierowników.
Szkolenie z publicznych wystąpień i prezentowania wyników.
Trening asertywności i wyrażania granic zawodowych.
Kurs mediacji i prowadzenia trudnych rozmów.
Szkolenie komunikacji międzykulturowej międzynarodowego zespołu.
Warsztat jasnego pisania raportów i prostego języka.
Trening negocjowania warunków współpracy z klientem.
Kurs facylitacji i moderowania spotkań zespołowych.
Warsztat reagowania na emocje niezadowolonych klientów.
Szkolenie profesjonalnego prowadzenia rozmów telefonicznych.
""",
    ),
    (
        "human_resources",
        "train",
        "professional_skills_training",
        """
Kurs zaawansowanych arkuszy kalkulacyjnych przy sprawnym programie.
Warsztat podstaw programowania dla analityków.
Szkolenie metod zarządzania projektami.
Kurs języka obcego potrzebnego w obowiązkach zawodowych.
Zajęcia praktyczne z obsługi sprawnej aparatury laboratoryjnej.
Szkolenie czytania wyników finansowych dla kierowników.
Kurs badania potrzeb użytkowników i prowadzenia wywiadów.
Warsztat tworzenia dostępnych dokumentów cyfrowych.
Szkolenie krytycznej analizy danych i wyciągania wniosków.
Nauka przygotowywania materiałów graficznych w działającej aplikacji.
""",
    ),
    (
        "human_resources",
        "train",
        "team_learning",
        """
Organizacja zespołowego ćwiczenia przekazywania instrukcji prostym językiem nowym współpracownikom.
Przygotowanie wewnętrznych ekspertów do roli trenerów.
Organizacja regularnych spotkań wymiany wiedzy między zespołami.
Warsztat delegowania odpowiedzialności i zadań.
Kurs planowania pracy własnej bez pytań o ewidencję godzin.
Szkolenie prowadzących spotkania z równoważenia udziału osób cichych i dominujących.
Szkolenie liderów z przeprowadzania zmiany organizacyjnej.
Warsztat dokumentowania wiedzy i przekazywania jej następcom.
Szkolenie rozpoznawania wypalenia i wspierania dobrostanu pracowników.
Trening technik radzenia sobie z presją zawodową.
""",
    ),
    (
        "human_resources",
        "train",
        "employment_relationship_support",
        """
Doradztwo zawodowe dla osób objętych likwidacją zespołu po formalnym rozliczeniu.
Poufna rozmowa pracownika o trudnościach adaptacji do nowego zespołu.
Wsparcie kierownika w rozmowie z niezadowolonym podwładnym.
Ustalenie kultury doceniania osiągnięć bez naliczania premii.
Wyjaśnienie standardów zachowania i szacunku w relacjach pracowniczych.
Organizacja dobrowolnej rozmowy naprawczej po nieporozumieniu zawodowym.
Pomoc w zgłoszeniu obaw dotyczących atmosfery i bezpieczeństwa psychologicznego.
Uzgodnienie sposobu komunikowania trudnej decyzji personalnej pracownikom.
Wsparcie pracownika odczuwającego zawodowe osamotnienie w organizacji.
Konsultacja przełożonego o budowaniu zdrowych relacji w rozproszonym zespole.
""",
    ),
    (
        "human_resources",
        "validation",
        "recruitment_outreach",
        """
Organizacja stoiska rekrutacyjnego podczas targów pracy na uczelni.
Ustalenie współpracy z biurem karier w pozyskiwaniu kandydatów.
Przygotowanie dnia otwartego dla osób zainteresowanych zatrudnieniem.
Wybór kanałów publikacji ogłoszenia o pracy w małej miejscowości.
Organizacja programu poleceń kandydatów przez pracowników bez wypłaty nagród.
Zaplanowanie kampanii naboru absolwentów szkół zawodowych.
Przygotowanie spotkania informacyjnego o możliwych ścieżkach zatrudnienia.
Koordynacja współpracy z organizatorem lokalnej giełdy pracy.
Zebranie materiałów przedstawiających organizację potencjalnym kandydatom.
Uzgodnienie udziału pracowników jako ambasadorów pracodawcy.
""",
    ),
    (
        "human_resources",
        "validation",
        "training_administration",
        """
Zmiana terminu wcześniej zatwierdzonego szkolenia pracowniczego.
Potwierdzenie miejsca na liście uczestników kursu zawodowego.
Zastępstwo uczestnika w zapisanym zespole szkoleniowym.
Uzyskanie duplikatu certyfikatu ukończenia szkolenia.
Wyjaśnienie zasad zaliczenia zajęć w programie rozwojowym.
Udostępnienie materiałów merytorycznych po szkoleniu bez problemu technicznego.
Uzgodnienie trybu zdalnego lub stacjonarnego zaplanowanego kursu.
Organizacja sali i prowadzącego na potwierdzone zajęcia pracownicze.
Zgłoszenie rezygnacji z udziału w kursie bez rozliczania kosztów.
Ustalenie harmonogramu kolejnej edycji już wybranego programu nauki.
""",
    ),
    (
        "human_resources",
        "test",
        "performance_feedback",
        """
Wyjaśnienie merytorycznej oceny okresowej po zamknięciu cyklu.
Odwołanie od oceny rocznej przypisującej cudze błędy.
Organizacja wieloźródłowego feedbacku360 dla kadry kierowniczej.
Ustalenie standardu oceny kompetencji na różnych stanowiskach.
Zebranie opinii współpracowników do rozmowy oceniającej.
Kalibracja ocen między kierownikami różnych zespołów.
Wyjaśnienie skali stosowanej w formularzu oceny pracowniczej.
Rozdzielenie oceny wyników pracy od osobistej sympatii oceniającego.
Zaplanowanie spotkania omawiającego osiągnięcia minionego roku.
Informacja zwrotna dla odrzuconego kandydata o ocenie jego kompetencji.
""",
    ),
    (
        "human_resources",
        "test",
        "workforce_diagnosis",
        """
Badanie przyczyn wysokiej rotacji pracowników w dziale.
Organizacja anonimowej ankiety satysfakcji zawodowej.
Przeprowadzenie rozmowy o powodach odejścia pracownika.
Analiza zbiorczych potrzeb rozwojowych całej organizacji.
Zbadanie czynników angażujących pracowników w wykonywane zadania.
Przygotowanie mapy kluczowych kompetencji dostępnych w organizacji.
Zebranie opinii zespołów o kulturze organizacyjnej po reorganizacji.
Opracowanie wniosków z ankiety pracowniczej dla kierownictwa.
Diagnoza przyczyn rezygnacji kandydatów z procesu naboru.
Badanie skuteczności programu zatrzymywania specjalistów.
""",
    ),
    (
        "payroll",
        "train",
        "ordinary_leave",
        """
Wyjaśnienie, czy dzień świąteczny w środku zaplanowanego urlopu pomniejsza pulę dni wypoczynku.
Wyjaśnienie przeniesienia niewykorzystanych dni urlopu z poprzedniego roku.
Korekta liczby dni pobranych z puli za zaplanowany wypoczynek.
Zmiana zatwierdzonego terminu urlopu wypoczynkowego w ewidencji.
Anulowanie wniosku urlopowego po rezygnacji z wyjazdu.
Obliczenie proporcjonalnego urlopu przy zatrudnieniu w środku roku.
Wyjaśnienie rozliczenia urlopu osoby pracującej w nierównym rozkładzie godzin.
Potwierdzenie zapisania dnia urlopu na żądanie.
Rozliczenie niewykorzystanego fragmentu urlopu po wcześniejszym odwołaniu pracownika z wypoczynku.
Ustalenie procedury wniosku o urlop bezpłatny.
""",
    ),
    (
        "payroll",
        "train",
        "salary_payments",
        """
Wyjaśnienie braku przelewu miesięcznego wynagrodzenia.
Korekta potrącenia pensji za dzień faktycznie przepracowany.
Sprawdzenie przelewu wynagrodzenia na nieaktualny rachunek pracownika.
Wyjaśnienie rozbieżności między kwotą na pasku a otrzymanym przelewem.
Korekta omyłkowego podwójnego naliczenia potrącenia z pensji.
Ustalenie wypłaty wynagrodzenia za niepełny pierwszy miesiąc.
Wyjaśnienie rozdzielenia jednej wypłaty na dwa przelewy z opisami różnych okresów rozliczeniowych.
Sprawdzenie terminu przelewu wynagrodzenia przed dniem wolnym bankowym.
Otrzymanie czytelnego zestawienia składników ostatniej pensji.
Rozliczenie zwrotu nadpłaconego wynagrodzenia.
""",
    ),
    (
        "payroll",
        "train",
        "time_records",
        """
Poprawienie nieodnotowanego wejścia pracownika do ewidencji czasu.
Wyjaśnienie błędnie wpisanej nieobecności przy pracy zdalnej.
Korekta liczby godzin przy wyjściu prywatnym odpracowanym później.
Zapisanie zatwierdzonej zamiany zmian pomiędzy pracownikami.
Uzgodnienie sposobu ewidencji służbowego szkolenia w godzinach pracy.
Wyjaśnienie rozliczenia czasu podróży służbowej w karcie obecności.
Korekta wpisu obecności dotyczącego niewłaściwego pracownika.
Potwierdzenie rozliczenia przerwy niewliczanej do czasu pracy.
Uzupełnienie ewidencji po przejściu na inny grafik.
Otrzymanie zestawienia przepracowanych godzin za zamknięty miesiąc.
""",
    ),
    (
        "payroll",
        "train",
        "employment_personal_records",
        """
Aktualizacja nazwiska w dokumentacji zatrudnienia po zmianie danych.
Poprawienie adresu zamieszkania w aktach pracownika.
Wydanie zaświadczenia o zatrudnieniu potrzebnego do wynajęcia mieszkania.
Uzupełnienie akt osobowych o brakujące świadectwo ukończenia szkoły.
Uzyskanie kopii podpisanej umowy o pracę.
Korekta literówki w danych osobowych na zaświadczeniu pracowniczym.
Aktualizacja numeru rachunku do wypłat wynagrodzenia.
Wyjaśnienie sposobu odbioru dokumentu zatrudnienia przez upoważnioną osobę.
Potwierdzenie złożenia oświadczenia o danych pracownika.
Ustalenie brakujących dokumentów potrzebnych do założenia akt osobowych.
""",
    ),
    (
        "payroll",
        "train",
        "employment_contract_changes",
        """
Przygotowanie aneksu po zatwierdzonej zmianie wymiaru etatu.
Poprawienie daty rozpoczęcia zatrudnienia w podpisywanej umowie.
Wyjaśnienie formalnego terminu zakończenia umowy próbnej.
Przygotowanie dokumentu przedłużenia zatrudnienia na uzgodnionych warunkach.
Sprostowanie nazwy stanowiska w aneksie do umowy.
Uzyskanie potwierdzenia obowiązującego wymiaru czasu pracy z umowy.
Uzupełnienie podpisu na uzgodnionym dokumencie zatrudnienia.
Zapisanie zatwierdzonej zmiany miejsca wykonywania pracy w dokumentacji.
Wyjaśnienie formalności związanych z przejściem na część etatu.
Sprawdzenie zgodności aneksu z zaakceptowaną datą zmiany warunków.
""",
    ),
    (
        "payroll",
        "train",
        "sickness_absence",
        """
Sprawdzenie odnotowania zwolnienia lekarskiego w kadrowej ewidencji.
Wyjaśnienie naliczenia wynagrodzenia za okres choroby.
Uzupełnienie danych potrzebnych do wypłaty zasiłku chorobowego.
Korekta dat niezdolności do pracy w rozliczeniu nieobecności.
Wyjaśnienie dokumentowania choroby podczas wcześniej zatwierdzonego urlopu.
Sprawdzenie, dlaczego system kadrowy nadal wykazuje zakończone zwolnienie.
Ustalenie formalności po zagranicznym zaświadczeniu o chorobie.
Wyjaśnienie rozliczenia okresu oczekiwania na świadczenie chorobowe.
Przekazanie dokumentów potrzebnych do rozliczenia nieobecności po wypadku.
Wyjaśnienie sposobu skorygowania pominiętego okresu usprawiedliwionej choroby.
""",
    ),
    (
        "payroll",
        "train",
        "payroll_components",
        """
Wyjaśnienie naliczenia zatwierdzonej premii zadaniowej.
Sprawdzenie potrącenia dobrowolnej składki z wynagrodzenia.
Korekta dodatku stażowego po uzupełnieniu dokumentów.
Wyjaśnienie naliczenia wynagrodzenia za dyżur zgodnie z decyzją przełożonego.
Sprawdzenie rozliczenia finansowego zastępstwa na innym stanowisku.
Ustalenie sposobu potrącenia zaliczki pobranej przez pracownika.
Wyjaśnienie kwoty dodatku funkcyjnego na pasku płacowym.
Rozliczenie uzgodnionej nagrody jubileuszowej.
Korekta nieprawidłowo naliczonego świadczenia pracowniczego w pensji.
Wyjaśnienie podziału wypłaty pomiędzy dwa rachunki bankowe pracownika.
""",
    ),
    (
        "payroll",
        "train",
        "employee_tax_documents",
        """
Otrzymanie rocznego dokumentu podatkowego od pracodawcy.
Sprostowanie danych na informacji podatkowej dotyczącej wynagrodzeń.
Złożenie oświadczenia wpływającego na zaliczki podatkowe z pensji.
Wyjaśnienie zmiany zaliczki na podatek na pasku wynagrodzenia.
Potwierdzenie uwzględnienia podwyższonych kosztów uzyskania przychodu pracownika.
Aktualizacja właściwego urzędu skarbowego w danych płacowych.
Wyjaśnienie, gdzie odebrać korektę dokumentu podatkowego pracownika.
Ustalenie formalności cofnięcia wcześniejszego oświadczenia podatkowego.
Sprawdzenie wykazania świadczenia pracowniczego w rocznej informacji podatkowej.
Uzyskanie potwierdzenia przekazania dokumentu podatkowego byłemu pracownikowi.
""",
    ),
    (
        "payroll",
        "validation",
        "family_leave",
        """
Ustalenie dokumentów do urlopu rodzicielskiego po narodzinach dziecka.
Zgłoszenie planowanego urlopu ojcowskiego i jego terminów.
Wyjaśnienie ewidencji dni opieki nad dzieckiem.
Złożenie wniosku o urlop wychowawczy.
Ustalenie formalnego powrotu po urlopie macierzyńskim.
Korekta rozliczenia zwolnienia na opiekę nad chorym dzieckiem.
Wyjaśnienie dokumentowania zwolnienia z powodu siły wyższej w rodzinie.
Ustalenie formalności urlopu opiekuńczego dla członka rodziny.
Zapisanie zatwierdzonego urlopu okolicznościowego po ślubie.
Wyjaśnienie liczby dni wolnych w związku ze zgonem bliskiej osoby.
""",
    ),
    (
        "payroll",
        "validation",
        "overtime_compensation",
        """
Wyjaśnienie wypłaty dodatku za zatwierdzone nadgodziny.
Rozliczenie pracy w niedzielę przez udzielenie dnia wolnego.
Sprawdzenie dodatku za pracę w porze nocnej.
Korekta rozliczenia przekroczenia normy średniotygodniowej.
Zamiana wynagrodzenia za nadgodziny na czas wolny na wniosek pracownika.
Ustalenie daty wypłaty nadgodzin po zamknięciu okresu rozliczeniowego.
Wyjaśnienie sposobu naliczenia dodatku za pracę w święto.
Sprawdzenie rozliczenia dodatkowych godzin przy niepełnym etacie.
Korekta pominiętych nadgodzin zatwierdzonych po zamknięciu listy płac.
Wyjaśnienie bilansu czasu wolnego udzielonego za pracę poza grafikiem.
""",
    ),
    (
        "payroll",
        "test",
        "separation_documents",
        """
Wydanie świadectwa pracy po zakończeniu zatrudnienia.
Sprostowanie błędnej daty na otrzymanym świadectwie pracy.
Ustalenie formalnego obiegu podpisanego wypowiedzenia.
Wyjaśnienie wyliczenia ekwiwalentu za niewykorzystany urlop przy odejściu.
Przygotowanie dokumentu rozwiązania umowy za porozumieniem stron.
Uzyskanie duplikatu świadectwa pracy sprzed kilku lat.
Sprawdzenie rozliczenia ostatniej wypłaty po rozwiązaniu umowy.
Potwierdzenie daty końca okresu wypowiedzenia.
Wyjaśnienie formalności odbioru dokumentacji po ustaniu zatrudnienia.
Korekta informacji o wykorzystanych nieobecnościach na świadectwie pracy.
""",
    ),
    (
        "payroll",
        "test",
        "insurance_retirement_records",
        """
Zgłoszenie członka rodziny pracownika do ubezpieczenia zdrowotnego.
Wyrejestrowanie członka rodziny po uzyskaniu własnego ubezpieczenia.
Potwierdzenie zgłoszenia nowego pracownika do ubezpieczeń społecznych.
Korekta danych identyfikacyjnych w zgłoszeniu ubezpieczeniowym pracownika.
Wydanie zaświadczenia o zarobkach potrzebnego do ustalenia emerytury.
Wyjaśnienie wykazanej podstawy składek pracownika za miesiąc.
Przekazanie deklaracji rezygnacji z pracowniczego planu kapitałowego.
Sprawdzenie zapisania ponownego przystąpienia do programu kapitałowego.
Uzyskanie dokumentu potwierdzającego okresy zatrudnienia do celów rentowych.
Wyjaśnienie braku potwierdzenia ubezpieczenia mimo trwającego zatrudnienia.
""",
    ),
    (
        "help_desk",
        "train",
        "workstation_sessions",
        """
Pojedynczy komputer zatrzymuje się przed ekranem logowania.
Pulpit jednego użytkownika nie ładuje się po udanym zalogowaniu.
Laptop pracownika zapętla ponowne uruchamianie po aktualizacji.
Jedno stanowisko zawiesza się po wybudzeniu ze snu.
Profil użytkownika uruchamia się jako tymczasowy i nie pokazuje ustawień.
Komputer jednej osoby działa nadmiernie wolno przy zwykłych zadaniach.
Pracownik potrzebuje pomocy z wyborem właściwego systemu przy uruchamianiu.
Na pojedynczej stacji pojawia się komunikat o niedokończonej aktualizacji.
Sesja użytkownika wylogowuje się bez świadomego zamknięcia pracy.
Pracownik potrzebuje diagnozy jednego komputera po zawieszeniu aplikacji.
""",
    ),
    (
        "help_desk",
        "train",
        "personal_peripherals_audio",
        """
Dźwięk na jednym laptopie działa tylko w jednym kanale mimo zmiany słuchawek.
Mikrofon pojedynczego użytkownika nie jest wykrywany podczas spotkań.
Kamera jednej osoby pokazuje czarny obraz przy działającej usłudze rozmów.
Klawiatura na jednym stanowisku wpisuje inne znaki niż naciskane.
Mysz pracownika gubi połączenie z odbiornikiem.
Skaner podłączony lokalnie do jednego komputera nie jest widoczny.
Słuchawki pracownika odtwarzają dźwięk przez niewłaściwe urządzenie wyjściowe.
Monitor jednej osoby nie pokazuje obrazu po podłączeniu do stacji dokującej.
Touchpad pojedynczego laptopa przestał reagować na gesty.
Pracownik potrzebuje konfiguracji dodatkowego monitora na swoim stanowisku.
""",
    ),
    (
        "help_desk",
        "train",
        "individual_printing",
        """
Dokumenty jednej osoby pozostają w jej lokalnej kolejce druku.
Pracownik nie widzi drukarki dostępnej u pozostałych kolegów.
Wydruki z jednego komputera trafiają na niewłaściwe urządzenie.
Jedna osoba potrzebuje konfiguracji druku dwustronnego.
Sterownik drukarki na pojedynczym stanowisku zgłasza błąd.
Użytkownik potrzebuje pomocy z wydrukiem dokumentu w odpowiedniej skali.
Prywatna kolejka jednego użytkownika pokazuje drukarkę jako offline.
Pracownik nie potrafi dodać udostępnionej drukarki do swojego profilu.
Wydruk PDF z jednej stacji ma nieprawidłowe marginesy.
Jedno stanowisko drukuje puste kartki z działającej wspólnej drukarki.
""",
    ),
    (
        "help_desk",
        "train",
        "ordinary_login",
        """
Pracownik zapomniał hasła do własnego konta bez oznak naruszenia bezpieczeństwa.
Konto jednej osoby zostało zablokowane po błędnych próbach wpisania hasła.
Użytkownik potrzebuje pomocy w zwykłej zmianie wygasającego hasła.
Pracownik nie wie, którego identyfikatora użyć w ekranie logowania.
Jedna osoba potrzebuje konfiguracji aplikacji uwierzytelniającej na nowym telefonie.
Kod drugiego składnika nie pojawia się na własnym urządzeniu użytkownika.
Pracownik nie może zalogować się po legalnej zmianie nazwiska konta.
Menedżer haseł jednego użytkownika podpowiada nieaktualne dane.
Pojedyncza osoba utknęła w pętli logowania do portalu służbowego.
Pracownik potrzebuje odzyskania dostępu po samodzielnym usunięciu własnej metody logowania.
""",
    ),
    (
        "help_desk",
        "train",
        "local_connectivity",
        """
Tylko laptop jednej osoby nie łączy się z firmowym Wi-Fi.
Kabel sieciowy na jednym stanowisku nie zapewnia połączenia.
Pojedynczy klient VPN pracownika nie uruchamia połączenia z domu.
Użytkownik potrzebuje skonfigurowania nowego profilu sieci na swoim laptopie.
Tylko jedna stacja ma błędne ustawienia serwera proxy.
Bluetooth jednego komputera nie znajduje służbowego urządzenia.
Pracownik nie może połączyć laptopa z własnym hotspotem telefonicznym.
Jedna karta sieciowa pozostaje wyłączona po aktualizacji sterownika.
Połączenie zrywa się wyłącznie na komputerze jednego pracownika.
Użytkownik potrzebuje pomocy z lokalną konfiguracją VPN po wymianie laptopa.
""",
    ),
    (
        "help_desk",
        "train",
        "desktop_applications",
        """
Edytor dokumentów jednej osoby zamyka się przy otwarciu zwykłego pliku.
Arkusz kalkulacyjny na pojedynczym stanowisku zawiesza się przy starcie.
Lokalny czytnik PDF nie otwiera dokumentów użytkownika.
Program do prezentacji jednej osoby nie zapisuje ustawień.
Pracownik potrzebuje przywrócenia paska narzędzi w aplikacji biurowej.
Jedna aplikacja uruchamia się poza widocznym obszarem ekranu.
Użytkownik potrzebuje naprawy skojarzenia plików z właściwym programem.
Lokalny dodatek do edytora blokuje uruchamianie programu.
Pracownik zgłasza uszkodzony profil ustawień swojego programu.
Jeden program wyświetla okno błędu przy zamykaniu dokumentu.
""",
    ),
    (
        "help_desk",
        "train",
        "personal_mail_client",
        """
Włączenie ostrzeżenia przed wysłaniem wiadomości bez zapowiedzianego załącznika w programie pocztowym jednej osoby.
Użytkownik potrzebuje skonfigurowania podpisu w swoim kliencie pocztowym.
Lokalna wyszukiwarka wiadomości jednej osoby nie znajduje starych maili.
Jedna skrzynka pokazuje nieprawidłowo ustawioną strefę czasową spotkań.
Pracownik nie widzi własnego kalendarza w programie pocztowym.
Pojedynczy klient poczty nie otwiera legalnych załączników.
Użytkownik potrzebuje naprawy lokalnego profilu programu pocztowego.
Jedna osoba ma błędne reguły kierujące własną pocztę do folderów.
Pracownik potrzebuje pomocy w dodaniu zatwierdzonej skrzynki do aplikacji.
Powiadomienia o nowych wiadomościach nie działają u jednego użytkownika.
""",
    ),
    (
        "help_desk",
        "train",
        "local_files_permissions",
        """
Odzyskanie własnego pliku omyłkowo usuniętego z lokalnego profilu.
Edytor jednej osoby odmawia zapisu we własnym katalogu z powodu uprawnień.
Pracownik nie może rozpakować legalnego archiwum na swoim komputerze.
Lokalny dysk jednej stacji jest pełny i wymaga bezpiecznego uporządkowania.
Użytkownik potrzebuje przywrócenia poprzedniej wersji własnego dokumentu.
Pojedynczy klient synchronizacji własnych plików utknął przy jednym dokumencie.
Pracownik potrzebuje pomocy ze zmianą uprawnień do własnego katalogu roboczego.
Lokalny pendrive nie jest widoczny na jednym stanowisku bez podejrzeń ataku.
Jedna osoba nie może zmienić nazwy swojego pliku z powodu blokady procesu.
Pracownik potrzebuje przeniesienia własnych ustawień i plików na nowy komputer.
""",
    ),
    (
        "help_desk",
        "validation",
        "individual_mobile_device",
        """
Służbowy telefon jednej osoby nie synchronizuje kontaktów.
Pracownik potrzebuje konfiguracji eSIM na własnym urządzeniu służbowym.
Tablet jednego użytkownika nie obraca obrazu po zmianie orientacji.
Pojedynczy smartfon nie odczytuje kodów kreskowych w działającej aplikacji magazynowej.
Pojedynczy smartfon nie pozwala zaktualizować aplikacji z zatwierdzonego sklepu.
Użytkownik potrzebuje pomocy z ustawieniem blokady ekranu telefonu.
Służbowy tablet pracownika nie reaguje na rysik.
Telefon jednej osoby nie zapisuje zdjęć dokumentów do aplikacji roboczej.
Automatyczna jasność ekranu jednego telefonu nie reaguje na zmianę oświetlenia.
Lokalizacja GPS jednego służbowego telefonu wskazuje błędną pozycję.
""",
    ),
    (
        "help_desk",
        "validation",
        "individual_hardware_maintenance",
        """
Bateria pojedynczego laptopa rozładowuje się po kilkunastu minutach.
Ładowarka jednego pracownika przestała zasilać komputer.
Wentylator na jednym stanowisku hałasuje przy niewielkim obciążeniu.
Obudowa służbowego laptopa jednej osoby ma uszkodzony zawias.
Pracownik potrzebuje diagnozy przegrzewania własnego komputera.
Pojedynczy port USB fizycznie nie utrzymuje wtyczki.
Ekran laptopa użytkownika jest pęknięty i potrzebuje serwisu.
Jeden komputer wydaje nietypowy dźwięk mechaniczny z obudowy.
Pracownik zgłasza zalanie własnego służbowego laptopa.
Stacja dokująca jednej osoby ma uszkodzone złącze zasilania.
""",
    ),
    (
        "help_desk",
        "test",
        "individual_software_installation",
        """
Instalacja zatwierdzonego programu potrzebnego jednemu pracownikowi.
Aktywacja legalnie przyznanej licencji aplikacji na jednym stanowisku.
Usunięcie starej wersji programu przed instalacją nowej u użytkownika.
Pracownik potrzebuje instalacji firmowej czcionki na swoim komputerze.
Dodanie zatwierdzonego słownika językowego do edytora jednej osoby.
Instalacja wtyczki dostępności dla indywidualnego użytkownika.
Naprawa przerwanej aktualizacji legalnego programu na jednym laptopie.
Przeniesienie przypisanej pracownikowi licencji na wymieniony komputer.
Instalacja wymaganej biblioteki do legalnej aplikacji jednej osoby.
Pracownik potrzebuje pomocy w skonfigurowaniu nowo zainstalowanego narzędzia.
""",
    ),
    (
        "help_desk",
        "test",
        "individual_browser_accessibility",
        """
Przeglądarka jednej osoby pokazuje stronę w niewłaściwym powiększeniu.
Użytkownik potrzebuje ustawienia czytnika ekranu na swoim stanowisku.
Lokalna przeglądarka blokuje potrzebne okno formularza wyskakującego.
Pracownik chce przywrócić zakładki we własnym profilu przeglądarki.
Jedna osoba potrzebuje konfiguracji kontrastu i wielkości tekstu systemowego.
Przeglądarka użytkownika nie zapamiętuje preferowanego języka stron.
Pracownik potrzebuje usunięcia uszkodzonej pamięci lokalnej jednej strony.
Tylko jeden profil przeglądarki błędnie wyświetla działający portal.
Użytkownik potrzebuje konfiguracji skrótów dostępności na własnym komputerze.
Przeglądarka jednego użytkownika nie wyświetla dostępnych napisów w materiałach wideo.
""",
    ),
    (
        "it",
        "train",
        "shared_compute_services",
        """
Wspólny serwer aplikacji przestał odpowiadać wszystkim użytkownikom.
Klaster maszyn wirtualnych utracił jeden węzeł i wymaga interwencji infrastrukturalnej.
Centralna usługa harmonogramu zadań nie uruchamia procesów wielu zespołów.
Brama dostępu do aplikacji firmowych zwraca błędy dla całej organizacji.
Wspólna platforma kontenerowa zgłasza brak zasobów i zatrzymuje usługi.
Serwer raportowy nie kończy zadań zlecanych przez różne działy.
Usługa centralnego logowania zdarzeń przestała przyjmować dane serwerów.
Firmowy system kolejkowania zadań ma rosnący zaległy ruch wielu aplikacji.
Maszyny wirtualne całego środowiska uruchamiają się z błędami infrastruktury.
Wspólny reverse proxy przestał kierować ruch do usług wewnętrznych.
""",
    ),
    (
        "it",
        "train",
        "organisation_network",
        """
Cały oddział utracił dostęp do sieci firmowej jednocześnie.
Sieć bezprzewodowa w całym budynku nie przydziela połączeń pracownikom.
Centralny serwer DHCP przestał wydawać adresy komputerom wielu działów.
Firmowa brama VPN nie przyjmuje połączeń żadnego pracownika.
Połączenie między dwiema lokalizacjami firmy jest niedostępne.
Routing między firmowymi podsieciami blokuje pracę kilku zespołów.
Wspólne łącze internetowe ma potwierdzoną awarię obejmującą całą siedzibę.
Kontroler firmowych punktów Wi-Fi zgłasza utratę wielu urządzeń.
Konfiguracja centralnej zapory blokuje legalny ruch całego działu.
Cała sieć gościnna firmy przestała działać po zmianie infrastruktury.
""",
    ),
    (
        "it",
        "train",
        "dns_certificates_domains",
        """
Centralny urząd certyfikacji odmawia wystawiania certyfikatów nowym usługom z powodu błędnego szablonu uprawnień.
Wygasający certyfikat centralnej usługi wymaga odnowienia na serwerze.
Firmowa domena ma błędny rekord kierujący wszystkich użytkowników do złej usługi.
Wewnętrzny resolver DNS zwraca nieaktualne rekordy wielu komputerom.
Centralna usługa po odnowieniu certyfikatu nie prezentuje pełnego łańcucha.
Konfiguracja DNS dla nowej firmowej domeny wymaga wdrożenia.
Firmowa domena przestała być rozpoznawana z kilku sieci zewnętrznych.
Zegar infrastruktury powoduje błędy ważności certyfikatów w wielu usługach.
Wspólne repozytorium certyfikatów wymaga uporządkowania automatycznego odnawiania.
Niedostępność wewnętrznej strefy DNS blokuje dostęp kilku aplikacji.
""",
    ),
    (
        "it",
        "train",
        "backup_recovery_infrastructure",
        """
Wdrożenie centralnej polityki niezmienialności kopii zapasowych, aby usunięcie ich wymagało odrębnej autoryzacji.
Test odtworzenia danych całej usługi z backupu zakończył się błędem.
Centralne repozytorium kopii zapasowych ma wyczerpującą się pojemność.
Należy przeprowadzić uzgodniony test odzyskiwania infrastruktury po awarii.
Replikacja kopii do zapasowej lokalizacji nie działa dla kilku serwerów.
Harmonogram backupów pomija nową produkcyjną usługę.
System kopii zapasowych zgłasza uszkodzone archiwa wielu projektów.
Potrzebne jest odtworzenie wspólnej aplikacji po awarii całego serwera.
Centralny backup działa, ale automatyczny monitoring nie raportuje jego wyniku.
Plan odzyskania infrastruktury wymaga weryfikacji dostępnych kopii.
""",
    ),
    (
        "it",
        "train",
        "malware_incidents",
        """
Na służbowym urządzeniu wykryto szyfrowanie plików przez ransomware.
Oprogramowanie ochronne wykryło aktywnego trojana na koncie pracownika.
Wiele stacji komunikuje się z adresem związanym ze złośliwym oprogramowaniem.
Po otwarciu podejrzanego załącznika uruchomił się nieznany proces.
Na firmowym serwerze wykryto koparkę kryptowalut bez autoryzacji.
Użytkownik podłączył nośnik, po którym ochrona wykryła złośliwy kod.
Monitoring bezpieczeństwa wykazał próbę rozprzestrzeniania robaka między stacjami.
Antywirus potwierdził infekcję i potrzebna jest koordynacja izolacji urządzenia.
Nieznany program wyłączył zabezpieczenia na służbowym komputerze.
W firmowej aplikacji pojawił się wstrzyknięty złośliwy skrypt.
""",
    ),
    (
        "it",
        "train",
        "account_intrusion",
        """
Ktoś zalogował się na konto pracownika z nieznanej lokalizacji.
Pracownik otrzymuje niezamówione zatwierdzenia drugiego składnika logowania.
Na koncie administratora wykryto działania, których właściciel nie wykonywał.
Hasło pracownika znalazło się w potwierdzonym wycieku i wymaga reakcji incydentowej.
Nieuprawniona osoba zmieniła metody odzyskiwania konta służbowego.
Konto pracownika wysyła wiadomości bez jego udziału.
W logach widoczne jest przejęcie aktywnej sesji użytkownika.
Podejrzana aplikacja otrzymała nieautoryzowany dostęp OAuth do firmowego konta.
Wykrycie próby password spraying wobec setek firmowych kont z jednego zakresu adresów.
Potwierdzono nieautoryzowane utworzenie uprzywilejowanego konta w systemie firmy.
""",
    ),
    (
        "it",
        "train",
        "data_exposure_incidents",
        """
Link do danych klientów jest dostępny publicznie po wylogowaniu.
Poufny dokument służbowy wysłano omyłkowo do nieuprawnionego odbiorcy.
Odbiorca widzi fragment cudzej faktury przez współdzieloną pamięć podręczną firmowego portalu; zgłoszenie ujawnienia danych.
Konfiguracja zasobu chmurowego ujawniła pliki przedsiębiorstwa osobom z zewnątrz.
Nieautoryzowany eksport danych pracowników został wykryty w logach.
Otwarty panel administracyjny ujawnia dane bez uwierzytelnienia.
Współpracownik zgłasza potwierdzoną kradzież nośnika z danymi służbowymi.
Wyniki wyszukiwarki zawierają poufny plik z firmowej usługi.
System alarmuje o masowym kopiowaniu informacji przez nieuprawnione konto.
W logach publicznego serwisu przypadkowo ujawniono sekret aplikacji.
""",
    ),
    (
        "it",
        "train",
        "phishing_and_abuse",
        """
Zgłoszenie fałszywych kodów jednorazowych przychodzących SMS-em z prośbą o oddzwonienie i podanie hasła.
Do pracowników trafia wiadomość podszywająca się pod kierownika i żądająca hasła.
Fałszywa strona logowania naśladuje portal organizacji.
Użytkownik zeskanował podejrzany kod QR prowadzący do kradzieży danych dostępu.
Napastnik podszywa się telefonicznie pod wsparcie i prosi o zatwierdzenie logowania.
Rozsyłana kampania wyłudzeń wykorzystuje podobną do firmowej domenę.
Pracownicy dostali fałszywe zaproszenie do udostępnienia konta służbowego.
Zgłoszono próbę przejęcia konta przez spreparowany formularz resetu hasła.
Ktoś nakłania pracownika do instalacji zdalnego dostępu w celu kradzieży danych.
Podejrzana strona obiecuje dokument kadrowy w zamian za firmowe dane logowania.
""",
    ),
    (
        "it",
        "validation",
        "datacenter_physical_infrastructure",
        """
Zasilacz awaryjny obsługujący serwerownię zgłasza krytyczny stan baterii.
Chłodzenie szafy serwerowej przestało utrzymywać wymaganą temperaturę.
Przełącznik centralny stracił zasilanie na kilku modułach.
Należy zaplanować przeniesienie firmowych serwerów do nowej szafy rack.
Panel krosowy infrastruktury ma uszkodzony tor łączący dwa piętra.
Czujnik zalania w serwerowni zgłasza realne zagrożenie sprzętu sieciowego.
Przygotowywane jest planowane wyłączenie zasilania infrastruktury serwerowej.
Wentylator w serwerze produkcyjnym zgłasza awarię sprzętową.
Łącze światłowodowe między szafami technicznymi ma uszkodzony moduł optyczny.
Centralna infrastruktura wymaga sprawdzenia redundancji zasilania po alarmie.
""",
    ),
    (
        "it",
        "validation",
        "shared_communication_platforms",
        """
Serwer pocztowy nie dostarcza wiadomości dla całej domeny firmy.
Centralna usługa kalendarzy nie udostępnia spotkań żadnemu zespołowi.
Firmowa centrala telefoniczna przestała zestawiać połączenia.
Usługa wideokonferencji organizacji nie pozwala tworzyć spotkań wielu osobom.
Wspólna bramka antyspamowa odrzuca całą przychodzącą pocztę.
Firmowy mostek konferencyjny łączy uczestników dwóch odrębnych spotkań w jednej rozmowie.
Platforma komunikatora firmowego nie synchronizuje kanałów żadnego działu.
Wspólny serwer książki adresowej przestał odpowiadać klientom.
Infrastruktura telefonii internetowej utraciła rejestrację wszystkich numerów.
Centralna usługa archiwizacji poczty nie zapisuje nowych wiadomości.
""",
    ),
    (
        "it",
        "test",
        "preventive_security_engineering",
        """
Zaplanowanie wdrożenia obowiązkowego MFA w systemach organizacji.
Przegląd uprawnień administratorów infrastruktury przed audytem bezpieczeństwa.
Ustalenie procesu rotacji kluczy dostępowych używanych przez usługi.
Wdrożenie segmentacji sieci ograniczającej dostęp do serwerów produkcyjnych.
Przygotowanie technicznego skanowania podatności firmowych serwerów.
Centralne wdrożenie poprawek bezpieczeństwa na infrastrukturze.
Uzgodnienie polityki technicznej szyfrowania danych organizacji.
Konfiguracja monitorowania podejrzanych logowań w systemie bezpieczeństwa.
Przygotowanie technicznego procesu zarządzania uprzywilejowanym dostępem.
Utworzenie zabezpieczeń chroniących firmową aplikację przed atakami sieciowymi.
""",
    ),
    (
        "it",
        "test",
        "shared_storage_databases",
        """
Wspólny serwer plików nie udostępnia katalogów żadnemu działowi.
Klaster bazy danych aplikacji firmowej utracił dostępny węzeł podstawowy.
Centralna baza danych zatrzymuje zapisy po wyczerpaniu puli identyfikatorów sekwencji, mimo wolnej przestrzeni dyskowej.
Wspólna baza danych blokuje zapytania wielu aplikacji przez długą transakcję.
Centralny zasób dokumentów osiągnął limit pojemności dla całej organizacji.
Replikacja produkcyjnej bazy danych między serwerami ma duże opóźnienie.
System przechowywania obiektów zwraca błędy wielu usługom.
Wspólny serwer plików wymaga zaplanowania migracji danych między macierzami.
Baza danych firmy wymaga odtworzenia działania po uszkodzeniu indeksów.
Centralna infrastruktura pamięci masowej zgłasza utratę jednej ścieżki dostępu.
""",
    ),
    (
        "other",
        "train",
        "building_facilities",
        """
Naprawa zablokowanej mechanicznej rolety w sali przy sprawnym sprzęcie.
Usunięcie przecieku pod zlewem w kuchni biurowej.
Zgłoszenie uszkodzonego zamka w drzwiach do pomieszczenia.
Wymiana przepalonej żarówki nad stołem w sali.
Naprawa cieknącej spłuczki w toalecie budynku.
Uzgodnienie sprzątania zabrudzonej wspólnej kuchni.
Naprawa krzesła biurowego z uszkodzonym oparciem.
Zgłoszenie niedomykającego się okna w pomieszczeniu.
Uzupełnienie mydła i ręczników w toalecie.
Naprawa ogrzewania w pokoju bez związku z serwerownią.
""",
    ),
    (
        "other",
        "train",
        "purchasing_deliveries",
        """
Zamówienie papierowych materiałów biurowych do magazynku.
Uzgodnienie odbioru przesyłki kurierskiej przez recepcję.
Wyjaśnienie opóźnionej dostawy zamówionych mebli.
Zgłoszenie brakującej pozycji w paczce z artykułami biurowymi.
Ustalenie miejsca składowania nowej dostawy drukowanych broszur.
Reklamacja uszkodzonego opakowania dostarczonego towaru.
Zamówienie zapasu kopert do wysyłki dokumentów.
Uzgodnienie zwrotu źle dostarczonych segregatorów.
Prośba o ofertę na tablice korkowe do pomieszczeń.
Ustalenie godziny odbioru paczek przez kuriera.
""",
    ),
    (
        "other",
        "train",
        "customer_commercial_billing",
        """
Klient prosi o fakturę za zakupioną usługę.
Kontrahent pyta o termin opłacenia faktury handlowej.
Reklamacja nieprawidłowej kwoty na fakturze dla klienta.
Potwierdzenie zaksięgowania płatności za zamówiony produkt.
Prośba o zmianę danych nabywcy na dokumencie sprzedaży.
Uzgodnienie warunków płatności za zewnętrzne zamówienie.
Klient pyta o zwrot wpłaconej zaliczki za usługę.
Prośba o przesłanie cennika usług organizacji.
Kontrahent prosi o kopię umowy handlowej.
Wyjaśnienie numeru rachunku do płatności za zamówienie klienta.
""",
    ),
    (
        "other",
        "train",
        "student_academic_matters",
        """
Student pyta o termin egzaminu końcowego.
Osoba studiująca prosi o przesunięcie terminu oddania pracy.
Kandydat na studia pyta o wymagania przyjęcia na kierunek.
Student prosi o zaświadczenie potwierdzające status studenta.
Pytanie o harmonogram zjazdów studiów podyplomowych.
Student zgłasza brak wpisanej oceny z zaliczonego przedmiotu.
Prośba o informację o opłatach za semestr studiów.
Zapytanie o zasady obrony pracy dyplomowej.
Student prosi o kontakt do opiekuna kierunku.
Pytanie o procedurę przeniesienia między kierunkami studiów.
""",
    ),
    (
        "other",
        "train",
        "public_content_events",
        """
Prośba o publikację zapowiedzi otwartego wydarzenia w aktualnościach.
Uzgodnienie tekstu broszury promującej usługi dla klientów.
Pytanie o możliwość patronatu nad lokalnym wydarzeniem kulturalnym.
Redakcja zewnętrzna prosi o komentarz prasowy organizacji.
Prośba o udostępnienie logotypu do legalnego materiału promocyjnego.
Zaproszenie organizacji do udziału w akcji charytatywnej.
Zamówienie plakatów informacyjnych na otwartą wystawę.
Uzgodnienie programu publicznej konferencji niezwiązanej ze szkoleniem pracowników.
Pytanie odbiorcy o godziny otwarcia publicznego wydarzenia.
Prośba o zdjęcia z zakończonego wydarzenia do publikacji.
""",
    ),
    (
        "other",
        "train",
        "private_food_leisure",
        """
Prywatna prośba o przepis na kruche ciasto z owocami.
Pytanie koleżeńskie o sposób przygotowania domowego chleba.
Prośba o polecenie filmu na wieczór.
Zaproszenie znajomych do wspólnej gry planszowej po pracy.
Pytanie o przepis na domową zupę.
Poszukiwanie nut do prywatnej nauki gry na instrumencie.
Koleżeńska wymiana opinii o przeczytanej powieści.
Pytanie o zasady amatorskiej gry karcianej.
Prośba o pomysł na prywatny prezent urodzinowy.
Zaproszenie do rozmowy o ulubionej muzyce.
""",
    ),
    (
        "other",
        "train",
        "closed_no_action",
        """
Potwierdzenie rozwiązania wcześniejszej sprawy bez dalszej prośby.
Podziękowanie za otrzymaną pomoc bez nowego zadania.
Informacja, że poprzednia wiadomość została wysłana omyłkowo i jest nieaktualna.
Potwierdzenie przeczytania komunikatu bez pytania.
Życzenia świąteczne dla odbiorcy wiadomości.
Gratulacje z okazji osobistego sukcesu bez zlecenia pracy.
Krótkie przywitanie bez dalszej treści i kontekstu.
Pożegnanie po zakończonej rozmowie bez otwartej sprawy.
Informacja o anulowaniu poprzedniego pytania bez podawania tematu.
Neutralne potwierdzenie otrzymania materiału bez oczekiwanej czynności.
""",
    ),
    (
        "other",
        "train",
        "insufficient_context",
        """
Niejasna prośba o pomoc bez opisu problemu ani wskazówek działu.
Wiadomość zawierająca przypadkowy ciąg znaków bez znaczenia.
Pytanie o status nieokreślonej sprawy bez wcześniejszej historii.
Samo zdanie, że coś nie działa, bez określenia przedmiotu.
Wiadomość z urwanym zdaniem bez informacji pozwalających ustalić temat.
Prośba o pilny kontakt bez wskazania powodu.
Sam numer sprawy bez opisu i bez rozpoznawalnego kontekstu.
Nieczytelna transkrypcja złożona z niepowiązanych słów.
Pytanie, do kogo się zwrócić, bez podania sprawy.
Wiadomość informująca o brakującym załączniku, którego treść nie jest znana.
""",
    ),
    (
        "other",
        "validation",
        "private_health",
        """
Prywatne pytanie o godzinę wizyty u dentysty.
Prośba do znajomego o namiar na fizjoterapeutę.
Pytanie pacjenta o dostępny termin badania wzroku.
Prywatna prośba o przypomnienie adresu przychodni.
Pytanie o odbiór wyników własnego badania laboratoryjnego.
Uzgodnienie terminu prywatnej wizyty szczepiennej.
Pytanie o godziny otwarcia apteki w okolicy.
Prośba o przesłanie kontaktu do gabinetu ortodontycznego.
Pacjent chce zmienić datę konsultacji dietetycznej.
Pytanie o możliwość zapisania się na prywatny masaż leczniczy.
""",
    ),
    (
        "other",
        "validation",
        "municipal_neighbourhood",
        """
Pytanie mieszkańca o termin odbioru odpadów wielkogabarytowych.
Zgłoszenie uszkodzonej ławki w miejskim parku.
Prośba do wspólnoty mieszkaniowej o harmonogram zebrania.
Pytanie o godziny otwarcia biblioteki publicznej.
Zgłoszenie niedziałającej latarni na osiedlu.
Pytanie mieszkańca o miejsce składania wniosku paszportowego.
Prośba o informację o przerwie w dostawie wody na osiedlu.
Zapytanie o zapisy na miejskie zajęcia sportowe.
Zgłoszenie przepełnionego publicznego kosza na śmieci.
Pytanie o termin lokalnego festynu sąsiedzkiego.
""",
    ),
    (
        "other",
        "test",
        "private_travel",
        """
Prywatne pytanie o rezerwację noclegu na weekend.
Prośba o informację o rozkładzie turystycznego promu.
Pytanie o trasę pieszej wycieczki w góry.
Zmiana terminu prywatnej rezerwacji biletu kolejowego.
Zapytanie o zasady przewozu bagażu podczas urlopowej podróży.
Prośba o wskazówki dojazdu do muzeum podczas prywatnej wycieczki.
Pytanie o możliwość wypożyczenia roweru na wakacjach.
Poszukiwanie mapy szlaku turystycznego.
Prośba o kontakt do pensjonatu polecanego przez znajomego.
Pytanie o godziny zwiedzania zamku w wolnym dniu.
""",
    ),
    (
        "other",
        "test",
        "private_plants_animals",
        """
Prywatna prośba o poradę dotyczącą podlewania storczyka.
Pytanie o karmę dla domowego kota.
Poszukiwanie opiekuna do psa podczas prywatnej nieobecności.
Prośba o wskazówki przesadzania domowej paprotki.
Pytanie o termin wizyty zwierzęcia u weterynarza.
Prośba o polecenie ziemi do balkonowych ziół.
Pytanie o sposób czyszczenia domowego akwarium.
Zapytanie o adopcję królika z lokalnego schroniska.
Prywatna prośba o rozpoznanie szkodnika na roślinie doniczkowej.
Pytanie o pielęgnację drzewka owocowego w prywatnym ogrodzie.
""",
    ),
]
