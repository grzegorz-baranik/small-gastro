# language: pl
# encoding: utf-8

# Szablon scenariuszy BDD dla projektu small-gastro
# Użyj tego szablonu jako podstawy dla nowych funkcjonalności

@{tag-funkcjonalności}
Funkcja: {Nazwa funkcjonalności}
  Jako {rola użytkownika}
  Chcę {akcja/możliwość}
  Aby {korzyść/cel biznesowy}

  Założenia:
    # Wspólne kroki dla wszystkich scenariuszy w tej funkcji
    Zakładając że baza danych jest pusta
    I jestem zalogowany jako "{rola}"

  # ============================================
  # SCENARIUSZE POZYTYWNE (Happy Path)
  # ============================================

  @happy-path @smoke
  Scenariusz: {Podstawowy scenariusz sukcesu}
    Zakładając że {warunek wstępny}
    Gdy {akcja użytkownika}
    Wtedy {oczekiwany rezultat}
    I {dodatkowa weryfikacja}

  @happy-path
  Scenariusz: {Drugi scenariusz sukcesu}
    Zakładając że {warunek wstępny}
    Gdy {akcja użytkownika}
    Wtedy {oczekiwany rezultat}

  # ============================================
  # SCENARIUSZE Z DANYMI (Scenario Outline)
  # ============================================

  @parametrized
  Szablon scenariusza: {Nazwa z parametrami}
    Zakładając że istnieje {obiekt} o nazwie "<nazwa>"
    Gdy zmieniam {pole} na "<nowa_wartość>"
    Wtedy {pole} powinno mieć wartość "<nowa_wartość>"

    Przykłady:
      | nazwa     | nowa_wartość |
      | Przykład1 | Wartość1     |
      | Przykład2 | Wartość2     |
      | Przykład3 | Wartość3     |

  # ============================================
  # SCENARIUSZE BŁĘDÓW
  # ============================================

  @error-handling
  Scenariusz: Błąd walidacji - {opis błędu}
    Zakładając że jestem na stronie {nazwa strony}
    Gdy próbuję utworzyć {obiekt} z pustym polem "{pole}"
    Wtedy powinienem zobaczyć komunikat błędu "{Pole jest wymagane}"
    I {obiekt} nie powinien zostać utworzony

  @error-handling
  Scenariusz: Błąd walidacji - nieprawidłowy format
    Zakładając że jestem na stronie {nazwa strony}
    Gdy wprowadzam "{nieprawidłowa_wartość}" w polu "{pole}"
    Wtedy powinienem zobaczyć komunikat błędu "{Nieprawidłowy format}"

  @error-handling @404
  Scenariusz: Próba dostępu do nieistniejącego zasobu
    Gdy próbuję wyświetlić {obiekt} o ID 99999
    Wtedy powinienem zobaczyć komunikat "Nie znaleziono"
    I zostanę przekierowany na {strona główna/lista}

  # ============================================
  # PRZYPADKI BRZEGOWE
  # ============================================

  @edge-case
  Scenariusz: {Nazwa przypadku brzegowego}
    Zakładając że {warunek specjalny}
    Gdy {akcja}
    Wtedy {oczekiwane zachowanie w tym przypadku}

  @edge-case @concurrent
  Scenariusz: Równoczesna modyfikacja tego samego zasobu
    Zakładając że dwóch użytkowników edytuje ten sam {obiekt}
    Gdy pierwszy użytkownik zapisuje zmiany
    I drugi użytkownik próbuje zapisać swoje zmiany
    Wtedy drugi użytkownik powinien zobaczyć komunikat o konflikcie

  # ============================================
  # WYDAJNOŚĆ
  # ============================================

  @performance
  Scenariusz: Wydajność ładowania listy
    Zakładając że w bazie jest 1000 {obiektów}
    Gdy otwieram stronę z listą {obiektów}
    Wtedy strona powinna załadować się w mniej niż 2 sekundy
    I powinienem zobaczyć paginację

  # ============================================
  # BEZPIECZEŃSTWO
  # ============================================

  @security
  Scenariusz: Próba dostępu bez uprawnień
    Zakładając że jestem zalogowany jako użytkownik bez uprawnień
    Gdy próbuję uzyskać dostęp do {chronionej funkcji}
    Wtedy powinienem zobaczyć komunikat "Brak uprawnień"
    I nie powinienem zobaczyć {chronionych danych}

# ============================================
# PRZYKŁADY DLA PROJEKTU SMALL-GASTRO
# ============================================

# Poniżej przykładowe scenariusze specyficzne dla small-gastro

@skladniki
Funkcja: Zarządzanie składnikami
  Jako właściciel lokalu gastronomicznego
  Chcę zarządzać listą składników
  Aby móc kontrolować stany magazynowe

  @happy-path @smoke
  Scenariusz: Dodanie nowego składnika wagowego
    Zakładając że jestem na stronie "Składniki"
    Gdy klikam przycisk "Dodaj składnik"
    I wprowadzam nazwę "Sałata lodowa"
    I wybieram jednostkę "kg"
    I klikam "Zapisz"
    Wtedy składnik "Sałata lodowa" powinien pojawić się na liście
    I powinien mieć jednostkę "kg"

  @happy-path
  Scenariusz: Dodanie nowego składnika sztukowego
    Zakładając że jestem na stronie "Składniki"
    Gdy klikam przycisk "Dodaj składnik"
    I wprowadzam nazwę "Bułka burger"
    I wybieram jednostkę "szt"
    I klikam "Zapisz"
    Wtedy składnik "Bułka burger" powinien pojawić się na liście
    I powinien mieć jednostkę "szt"

  @error-handling
  Scenariusz: Błąd - próba dodania składnika o istniejącej nazwie
    Zakładając że istnieje składnik "Pomidor"
    Gdy próbuję dodać składnik o nazwie "Pomidor"
    Wtedy powinienem zobaczyć komunikat "Składnik o tej nazwie już istnieje"
    I nowy składnik nie powinien zostać utworzony

@produkty
Funkcja: Zarządzanie produktami
  Jako właściciel lokalu gastronomicznego
  Chcę tworzyć produkty z przypisanymi składnikami
  Aby móc śledzić zużycie składników przy sprzedaży

  @happy-path
  Scenariusz: Tworzenie produktu z przypisanymi składnikami
    Zakładając że istnieją składniki:
      | nazwa       | jednostka |
      | Bułka burger| szt       |
      | Mięso       | kg        |
      | Sałata      | kg        |
    Gdy tworzę produkt "Burger Classic" w cenie 25.00 PLN
    I przypisuję składniki:
      | składnik    | ilość |
      | Bułka burger| 1     |
      | Mięso       | 0.15  |
      | Sałata      | 0.02  |
    Wtedy produkt "Burger Classic" powinien zostać utworzony
    I powinien mieć 3 przypisane składniki

@dzienny-raport
Funkcja: Otwarcie i zamknięcie dnia
  Jako pracownik lokalu
  Chcę otwierać i zamykać dzień pracy
  Aby śledzić stany magazynowe na początku i końcu dnia

  @happy-path @smoke
  Scenariusz: Otwarcie nowego dnia
    Zakładając że poprzedni dzień został zamknięty
    Gdy otwieram nowy dzień
    I wprowadzam stany początkowe składników
    Wtedy nowy rekord dnia powinien zostać utworzony
    I stany początkowe powinny zostać zapisane

  @edge-case
  Scenariusz: Próba otwarcia dnia gdy poprzedni nie jest zamknięty
    Zakładając że poprzedni dzień nie został zamknięty
    Gdy próbuję otworzyć nowy dzień
    Wtedy powinienem zobaczyć komunikat "Najpierw zamknij poprzedni dzień"
    I nowy dzień nie powinien zostać otwarty
