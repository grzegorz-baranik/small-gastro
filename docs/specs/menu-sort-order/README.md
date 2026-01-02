# Specyfikacja Funkcjonalna: Sortowanie Menu

## Metadane

| Pole | Wartość |
|------|---------|
| **Autor** | Claude AI |
| **Data utworzenia** | 2026-01-02 |
| **Wersja** | 1.0 |
| **Status** | Zatwierdzony |
| **Zatwierdził** | - |

---

## 1. Przegląd

### 1.1 Cel
Umożliwienie użytkownikom definiowania kolejności wyświetlania produktów w menu za pomocą funkcjonalności drag-and-drop. Zdefiniowana kolejność będzie stosowana we wszystkich miejscach aplikacji, gdzie wyświetlana jest lista produktów.

### 1.2 Kontekst biznesowy
W lokalach gastronomicznych kolejność produktów w menu ma znaczenie - popularne/promowane produkty powinny być wyświetlane jako pierwsze. Obecnie produkty są wyświetlane w kolejności utworzenia, co nie odpowiada potrzebom biznesowym.

### 1.3 Zakres
**W zakresie:**
- Dodanie pola `sort_order` do modelu Product
- Implementacja drag-and-drop na liście produktów w MenuPage
- Zastosowanie sortowania we wszystkich widokach wyświetlających produkty
- Endpoint API do aktualizacji kolejności produktów

**Poza zakresem:**
- Sortowanie składników (ingredients)
- Sortowanie wariantów produktów
- Grupowanie produktów w kategorie

---

## 2. Historie użytkownika

### US-001: Zmiana kolejności produktów
**Jako** właściciel lokalu gastronomicznego
**Chcę** przeciągać produkty na liście menu aby zmienić ich kolejność
**Aby** najpopularniejsze produkty były wyświetlane jako pierwsze

**Kryteria akceptacji:**
- [ ] Mogę przeciągnąć produkt w górę lub w dół listy
- [ ] Kolejność jest zapisywana automatycznie po przeciągnięciu
- [ ] Nowa kolejność jest zachowana po odświeżeniu strony
- [ ] Widzę wizualne wskazanie podczas przeciągania

**Priorytet:** Wysoki

---

### US-002: Spójna kolejność w całej aplikacji
**Jako** użytkownik systemu
**Chcę** widzieć produkty w tej samej kolejności we wszystkich widokach
**Aby** łatwiej znajdować produkty

**Kryteria akceptacji:**
- [ ] Lista produktów w MenuPage jest posortowana według `sort_order`
- [ ] Lista produktów w DailyOperationsPage jest posortowana według `sort_order`
- [ ] Każdy nowy produkt otrzymuje najwyższy `sort_order` (pojawia się na końcu listy)

**Priorytet:** Wysoki

---

## 3. Wymagania funkcjonalne

### 3.1 Drag-and-drop sortowanie
**ID:** FR-001
**Opis:** Lista produktów w zakładce "Produkty" na stronie Menu umożliwia zmianę kolejności metodą drag-and-drop. Po przeciągnięciu produktu w nowe miejsce, kolejność jest automatycznie zapisywana do bazy danych.
**Priorytet:** Wysoki

### 3.2 Persystencja kolejności
**ID:** FR-002
**Opis:** Kolejność produktów jest przechowywana w polu `sort_order` (INTEGER) w tabeli `products`. Niższe wartości oznaczają wyższą pozycję na liście.
**Priorytet:** Wysoki

### 3.3 Domyślna kolejność nowych produktów
**ID:** FR-003
**Opis:** Nowo utworzony produkt otrzymuje wartość `sort_order` równą MAX(sort_order) + 1, co powoduje dodanie go na końcu listy.
**Priorytet:** Średni

### 3.4 Globalny porządek sortowania
**ID:** FR-004
**Opis:** Wszystkie endpointy API zwracające listę produktów domyślnie sortują po polu `sort_order` rosnąco.
**Priorytet:** Wysoki

---

## 4. Interfejs użytkownika

### 4.1 Przepływ użytkownika
```
[MenuPage - zakładka Produkty] -> [Kliknij i przytrzymaj produkt] -> [Przeciągnij w nowe miejsce] -> [Upuść] -> [Automatyczny zapis]
```

### 4.2 Elementy UI
| Element | Typ | Opis |
|---------|-----|------|
| Uchwyt przeciągania | Icon (GripVertical) | Ikona po lewej stronie karty produktu wskazująca możliwość przeciągania |
| Wizualne wskazanie celu | Border/Shadow | Podświetlenie miejsca, gdzie produkt zostanie upuszczony |
| Karta produktu | Draggable card | Cała karta produktu jest elementem przeciąganym |

### 4.3 Stany wizualne
- **Normalny**: Ikona uchwytu w kolorze szarym
- **Hover na uchwycie**: Kursor zmienia się na "grab", ikona podświetlona
- **Podczas przeciągania**: Karta z cieniem, przezroczystość 0.8
- **Cel upuszczenia**: Niebieska linia wskazująca miejsce docelowe

---

## 5. Przypadki brzegowe

### 5.1 Jednoczesna edycja
**Scenariusz:** Dwóch użytkowników zmienia kolejność w tym samym czasie
**Oczekiwane zachowanie:** Ostatni zapis wygrywa (optimistic update). Brak blokowania.

### 5.2 Usunięcie produktu
**Scenariusz:** Produkt w środku listy zostaje usunięty
**Oczekiwane zachowanie:** Luka w `sort_order` nie wpływa na działanie sortowania (ORDER BY nadal działa poprawnie)

### 5.3 Filtrowanie produktów
**Scenariusz:** Lista produktów jest przefiltrowana (np. tylko aktywne)
**Oczekiwane zachowanie:** Drag-and-drop działa tylko na widocznych produktach, kolejność jest aktualizowana poprawnie

---

## 6. Obsługa błędów

| Błąd | Komunikat (PL) | Akcja |
|------|----------------|-------|
| Błąd zapisu kolejności | "Nie udało się zapisać kolejności. Spróbuj ponownie." | Toast z błędem, przywrócenie poprzedniej kolejności |
| Błąd sieciowy | "Błąd połączenia. Sprawdź połączenie z internetem." | Toast z błędem, przywrócenie poprzedniej kolejności |

---

## 7. Wymagania niefunkcjonalne

### 7.1 Wydajność
- Aktualizacja kolejności powinna być wykonana w jednym zapytaniu do bazy danych (bulk update)
- Odpowiedź API w czasie < 500ms

### 7.2 UX
- Animacja drag-and-drop powinna być płynna (60 FPS)
- Feedback wizualny natychmiast po rozpoczęciu przeciągania

---

## 8. Zależności

### 8.1 Wymagane funkcjonalności
- Istniejąca lista produktów (MenuPage)
- Istniejący model Product

### 8.2 Powiązane modele danych
- `Product` - dodanie pola `sort_order`

---

## 9. Metryki sukcesu

| Metryka | Cel | Sposób pomiaru |
|---------|-----|----------------|
| Czas zapisu kolejności | < 500ms | Monitoring API |
| Płynność animacji | 60 FPS | Developer tools |

---

## 10. Pytania otwarte

- [x] Czy sortowanie ma dotyczyć również składników? **Odpowiedź: Nie, tylko produktów**
- [ ] Czy chcemy pokazywać numer pozycji obok produktu?

---

## Historia zmian

| Wersja | Data | Autor | Opis zmian |
|--------|------|-------|------------|
| 1.0 | 2026-01-02 | Claude AI | Wersja początkowa |
