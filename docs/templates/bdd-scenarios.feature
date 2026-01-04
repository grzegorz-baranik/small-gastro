# language: pl
# encoding: utf-8

# BDD Scenario Template for the small-gastro project
# Use this template as a basis for new features
# Note: Polish Gherkin keywords are used as this represents user-facing behavior

@{feature-tag}
Funkcja: {Feature Name}
  Jako {user role}
  Chcę {action/capability}
  Aby {benefit/business goal}

  Założenia:
    # Common steps for all scenarios in this feature
    Zakładając że baza danych jest pusta
    I jestem zalogowany jako "{role}"

  # ============================================
  # POSITIVE SCENARIOS (Happy Path)
  # ============================================

  @happy-path @smoke
  Scenariusz: {Basic success scenario}
    Zakładając że {precondition}
    Gdy {user action}
    Wtedy {expected result}
    I {additional verification}

  @happy-path
  Scenariusz: {Second success scenario}
    Zakładając że {precondition}
    Gdy {user action}
    Wtedy {expected result}

  # ============================================
  # DATA-DRIVEN SCENARIOS (Scenario Outline)
  # ============================================

  @parametrized
  Szablon scenariusza: {Name with parameters}
    Zakładając że istnieje {object} o nazwie "<nazwa>"
    Gdy zmieniam {field} na "<nowa_wartość>"
    Wtedy {field} powinno mieć wartość "<nowa_wartość>"

    Przykłady:
      | nazwa     | nowa_wartość |
      | Example1  | Value1       |
      | Example2  | Value2       |
      | Example3  | Value3       |

  # ============================================
  # ERROR SCENARIOS
  # ============================================

  @error-handling
  Scenariusz: Validation error - {error description}
    Zakładając że jestem na stronie {page name}
    Gdy próbuję utworzyć {object} z pustym polem "{field}"
    Wtedy powinienem zobaczyć komunikat błędu "{Field is required}"
    I {object} nie powinien zostać utworzony

  @error-handling
  Scenariusz: Validation error - invalid format
    Zakładając że jestem na stronie {page name}
    Gdy wprowadzam "{invalid_value}" w polu "{field}"
    Wtedy powinienem zobaczyć komunikat błędu "{Invalid format}"

  @error-handling @404
  Scenariusz: Attempt to access non-existent resource
    Gdy próbuję wyświetlić {object} o ID 99999
    Wtedy powinienem zobaczyć komunikat "Nie znaleziono"
    I zostanę przekierowany na {main page/list}

  # ============================================
  # EDGE CASES
  # ============================================

  @edge-case
  Scenariusz: {Edge case name}
    Zakładając że {special condition}
    Gdy {action}
    Wtedy {expected behavior in this case}

  @edge-case @concurrent
  Scenariusz: Concurrent modification of the same resource
    Zakładając że dwóch użytkowników edytuje ten sam {object}
    Gdy pierwszy użytkownik zapisuje zmiany
    I drugi użytkownik próbuje zapisać swoje zmiany
    Wtedy drugi użytkownik powinien zobaczyć komunikat o konflikcie

  # ============================================
  # PERFORMANCE
  # ============================================

  @performance
  Scenariusz: List loading performance
    Zakładając że w bazie jest 1000 {objects}
    Gdy otwieram stronę z listą {objects}
    Wtedy strona powinna załadować się w mniej niż 2 sekundy
    I powinienem zobaczyć paginację

  # ============================================
  # SECURITY
  # ============================================

  @security
  Scenariusz: Access attempt without permissions
    Zakładając że jestem zalogowany jako użytkownik bez uprawnień
    Gdy próbuję uzyskać dostęp do {protected function}
    Wtedy powinienem zobaczyć komunikat "Brak uprawnień"
    I nie powinienem zobaczyć {protected data}

# ============================================
# EXAMPLES FOR SMALL-GASTRO PROJECT
# ============================================

# Below are example scenarios specific to small-gastro

@ingredients
Funkcja: Ingredient Management
  Jako właściciel lokalu gastronomicznego
  Chcę zarządzać listą składników
  Aby móc kontrolować stany magazynowe

  @happy-path @smoke
  Scenariusz: Adding a new weight-based ingredient
    Zakładając że jestem na stronie "Składniki"
    Gdy klikam przycisk "Dodaj składnik"
    I wprowadzam nazwę "Sałata lodowa"
    I wybieram jednostkę "kg"
    I klikam "Zapisz"
    Wtedy składnik "Sałata lodowa" powinien pojawić się na liście
    I powinien mieć jednostkę "kg"

  @happy-path
  Scenariusz: Adding a new count-based ingredient
    Zakładając że jestem na stronie "Składniki"
    Gdy klikam przycisk "Dodaj składnik"
    I wprowadzam nazwę "Bułka burger"
    I wybieram jednostkę "szt"
    I klikam "Zapisz"
    Wtedy składnik "Bułka burger" powinien pojawić się na liście
    I powinien mieć jednostkę "szt"

  @error-handling
  Scenariusz: Error - attempt to add ingredient with existing name
    Zakładając że istnieje składnik "Pomidor"
    Gdy próbuję dodać składnik o nazwie "Pomidor"
    Wtedy powinienem zobaczyć komunikat "Składnik o tej nazwie już istnieje"
    I nowy składnik nie powinien zostać utworzony

@products
Funkcja: Product Management
  Jako właściciel lokalu gastronomicznego
  Chcę tworzyć produkty z przypisanymi składnikami
  Aby móc śledzić zużycie składników przy sprzedaży

  @happy-path
  Scenariusz: Creating a product with assigned ingredients
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

@daily-report
Funkcja: Day Open and Close
  Jako pracownik lokalu
  Chcę otwierać i zamykać dzień pracy
  Aby śledzić stany magazynowe na początku i końcu dnia

  @happy-path @smoke
  Scenariusz: Opening a new day
    Zakładając że poprzedni dzień został zamknięty
    Gdy otwieram nowy dzień
    I wprowadzam stany początkowe składników
    Wtedy nowy rekord dnia powinien zostać utworzony
    I stany początkowe powinny zostać zapisane

  @edge-case
  Scenariusz: Attempt to open day when previous is not closed
    Zakładając że poprzedni dzień nie został zamknięty
    Gdy próbuję otworzyć nowy dzień
    Wtedy powinienem zobaczyć komunikat "Najpierw zamknij poprzedni dzień"
    I nowy dzień nie powinien zostać otwarty
