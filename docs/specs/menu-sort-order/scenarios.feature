# language: pl
# encoding: utf-8

@menu-sort-order
Funkcja: Sortowanie produktow w menu
  Jako wlasciciel lokalu gastronomicznego
  Chce definiowac kolejnosc produktow w menu
  Aby najpopularniejsze produkty byly wyswietlane jako pierwsze

  Zalozenia:
    Zakladajac ze baza danych jest pusta
    I istnieja produkty:
      | nazwa          | cena   |
      | Kebab          | 25.00  |
      | Burger         | 22.00  |
      | Frytki         | 10.00  |
      | Napoj          | 5.00   |

  # ============================================
  # SCENARIUSZE POZYTYWNE (Happy Path)
  # ============================================

  @happy-path @smoke
  Scenariusz: Zmiana kolejnosci produktu metodą drag-and-drop
    Zakladajac ze jestem na stronie "Menu"
    I produkty sa wyswietlane w kolejnosci: Kebab, Burger, Frytki, Napoj
    Gdy przeciagam produkt "Burger" na pozycje 1
    Wtedy produkty sa wyswietlane w kolejnosci: Burger, Kebab, Frytki, Napoj
    I kolejnosc zostaje zapisana w bazie danych

  @happy-path
  Scenariusz: Zachowanie kolejnosci po odswiezeniu strony
    Zakladajac ze jestem na stronie "Menu"
    I zmieniam kolejnosc produktow na: Frytki, Napoj, Kebab, Burger
    Gdy odswiezam strone
    Wtedy produkty sa wyswietlane w kolejnosci: Frytki, Napoj, Kebab, Burger

  @happy-path
  Scenariusz: Nowy produkt pojawia sie na koncu listy
    Zakladajac ze istnieja produkty w kolejnosci: Kebab, Burger, Frytki
    Gdy dodaje nowy produkt "Pizza" w cenie 30.00 PLN
    Wtedy produkty sa wyswietlane w kolejnosci: Kebab, Burger, Frytki, Pizza

  @happy-path
  Scenariusz: Spojnosc kolejnosci w roznych widokach
    Zakladajac ze zmieniam kolejnosc produktow na stronie Menu na: Burger, Kebab, Frytki
    Gdy przechodze na strone "Operacje dzienne"
    Wtedy produkty sa wyswietlane w kolejnosci: Burger, Kebab, Frytki

  # ============================================
  # INTERAKCJE DRAG-AND-DROP
  # ============================================

  @drag-drop
  Scenariusz: Wizualne wskazanie podczas przeciagania
    Zakladajac ze jestem na stronie "Menu"
    Gdy klikam i przytrzymuje uchwyt przeciagania przy produkcie "Kebab"
    Wtedy karta produktu "Kebab" ma cien i przezroczystosc
    I widze wskaznik miejsca docelowego

  @drag-drop
  Scenariusz: Przeciaganie na poczatek listy
    Zakladajac ze produkty sa wyswietlane w kolejnosci: Kebab, Burger, Frytki, Napoj
    Gdy przeciagam produkt "Napoj" na pozycje 1
    Wtedy produkty sa wyswietlane w kolejnosci: Napoj, Kebab, Burger, Frytki

  @drag-drop
  Scenariusz: Przeciaganie na koniec listy
    Zakladajac ze produkty sa wyswietlane w kolejnosci: Kebab, Burger, Frytki, Napoj
    Gdy przeciagam produkt "Kebab" na pozycje 4
    Wtedy produkty sa wyswietlane w kolejnosci: Burger, Frytki, Napoj, Kebab

  # ============================================
  # SCENARIUSZE BLEDOW
  # ============================================

  @error-handling
  Scenariusz: Blad polaczenia podczas zapisywania kolejnosci
    Zakladajac ze jestem na stronie "Menu"
    I polaczenie z serwerem jest niedostepne
    Gdy przeciagam produkt "Burger" na pozycje 1
    Wtedy powinienem zobaczyc komunikat "Nie udalo sie zapisac kolejnosci"
    I produkty wracaja do poprzedniej kolejnosci

  # ============================================
  # API
  # ============================================

  @api
  Scenariusz: PUT /api/v1/products/reorder - sukces
    Zakladajac ze istnieja produkty o ID: 1, 2, 3, 4
    Gdy wysylam zadanie PUT /api/v1/products/reorder z body:
      """
      {"product_ids": [3, 1, 4, 2]}
      """
    Wtedy otrzymuje odpowiedz 200
    I produkty maja sort_order: produkt 3 = 0, produkt 1 = 1, produkt 4 = 2, produkt 2 = 3

  @api @error-handling
  Scenariusz: PUT /api/v1/products/reorder - nieistniejacy produkt
    Zakladajac ze istnieja produkty o ID: 1, 2, 3
    Gdy wysylam zadanie PUT /api/v1/products/reorder z body:
      """
      {"product_ids": [1, 2, 999]}
      """
    Wtedy otrzymuje odpowiedz 400
    I odpowiedz zawiera komunikat "Nie znaleziono produktow"

  @api @error-handling
  Scenariusz: PUT /api/v1/products/reorder - pusta lista
    Gdy wysylam zadanie PUT /api/v1/products/reorder z body:
      """
      {"product_ids": []}
      """
    Wtedy otrzymuje odpowiedz 422

  @api @error-handling
  Scenariusz: PUT /api/v1/products/reorder - duplikaty ID
    Gdy wysylam zadanie PUT /api/v1/products/reorder z body:
      """
      {"product_ids": [1, 2, 1]}
      """
    Wtedy otrzymuje odpowiedz 422
    I odpowiedz zawiera komunikat "duplikaty"

  @api
  Scenariusz: GET /api/v1/products - sortowanie po sort_order
    Zakladajac ze produkty maja sort_order: Kebab = 2, Burger = 0, Frytki = 1
    Gdy wysylam zadanie GET /api/v1/products
    Wtedy produkty sa zwrocone w kolejnosci: Burger, Frytki, Kebab

  # ============================================
  # PRZYPADKI BRZEGOWE
  # ============================================

  @edge-case
  Scenariusz: Sortowanie z jednym produktem
    Zakladajac ze istnieje tylko produkt "Kebab"
    Gdy otwieram strone "Menu"
    Wtedy uchwyt przeciagania jest widoczny
    I nie moge przeciagnac produktu

  @edge-case
  Scenariusz: Sortowanie po usunieciu produktu
    Zakladajac ze produkty maja sort_order: Kebab = 0, Burger = 1, Frytki = 2
    Gdy usuwam produkt "Burger"
    I otwieram strone "Menu"
    Wtedy produkty sa wyswietlane w kolejnosci: Kebab, Frytki
