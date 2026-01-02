# Specyfikacja: Naprawa Wielokrotnych Błędów

**Status:** W trakcie realizacji
**Data:** 2026-01-02
**Wersja:** 1.0

## Przegląd

Dokument opisuje trzy błędy znalezione w aplikacji small-gastro oraz planowane rozwiązania.

---

## Błąd 1: RangeError przy przeglądaniu szczegółów dnia

### Opis problemu
Po kliknięciu na otwarty dzień w celu wyświetlenia szczegółów, pojawia się biały ekran z błędem konsoli:
- `RangeError: invalid time value`
- `Uncaught RangeError: invalid time value`

### Przyczyna źródłowa
**Niezgodność formatu daty** między backendem a frontendem:

| Komponent | Format | Przykład |
|-----------|--------|----------|
| Backend wysyła | `%H:%M` (krótki czas) | `"14:30"` |
| Frontend oczekuje | ISO 8601 datetime | `"2026-01-02T14:30:00"` |

**Lokalizacja kodu:**
- Backend: `backend/app/services/daily_operations_service.py` (linie 724-725)
  ```python
  opening_time = db_record.opened_at.strftime("%H:%M")
  ```
- Frontend: `frontend/src/components/daily/DaySummary.tsx` (linie 110-111, 122-123)
  ```javascript
  formatDateTime(summary.opening_time)
  ```
- Formatter: `frontend/src/utils/formatters.ts` (linie 14-21)
  ```javascript
  new Date(dateString)  // Nie parsuje "14:30" poprawnie
  ```

### Rozwiązanie
Zmienić backend aby wysyłał pełne ISO datetime zamiast skróconego formatu czasu.

### Pliki do modyfikacji
1. `backend/app/services/daily_operations_service.py`
2. `backend/app/schemas/daily_operations.py` (opcjonalnie - zmiana typu na datetime)

---

## Błąd 2: Internal Server Error przy dodawaniu transakcji

### Opis problemu
Przy próbie dodania transakcji (z podaniem: kwoty, metody płatności, kategorii, daty i opcjonalnego opisu) pojawia się błąd 500 Internal Server Error.

### Przyczyna źródłowa
**Niebezpieczny dostęp do relacji** w funkcji `_to_response()`:

```python
category_name=t.category.name if t.category else None,  # Linia 31
```

Gdy `category_id` jest `None` (dla transakcji przychodowych lub bez kategorii), dostęp do `t.category` może wywołać wyjątek.

**Lokalizacja kodu:**
- API: `backend/app/api/v1/transactions.py` (linia 31)
- Service: `backend/app/services/transaction_service.py`
- Model: `backend/app/models/transaction.py`

### Rozwiązanie
Bezpieczny dostęp do relacji poprzez sprawdzenie `category_id` przed dostępem do `category.name`.

### Pliki do modyfikacji
1. `backend/app/api/v1/transactions.py`

---

## Błąd 3: 405 Method Not Allowed w Raportach

### Opis problemu
Przy próbie wyświetlenia raportów (trendy miesięczne, zużycie składników, straty) pojawia się:
- Komunikat: "Błąd ładowania raportu"
- Konsola: `405 Method Not Allowed`

### Przyczyna źródłowa
**Niezgodność metod HTTP**:

| Komponent | Metoda HTTP | Oczekiwane |
|-----------|-------------|------------|
| Frontend | GET z query params | - |
| Backend | POST z body | - |

**Lokalizacja kodu:**
- Frontend: `frontend/src/api/reports.ts` (linie 46, 56, 70, 86, 100, 110)
  ```typescript
  client.get<MonthlyTrendsResponse>('/reports/monthly-trends', { params: range })
  ```
- Backend: `backend/app/api/v1/reports.py` (linie 102, 128, 162, 190, 225, 257)
  ```python
  @router.post("/monthly-trends", ...)
  ```

### Rozwiązanie
Zmienić endpointy backendu z POST na GET i przyjmować parametry jako query params zamiast body.

### Endpointy do naprawy
| Endpoint | Obecna metoda | Docelowa metoda |
|----------|---------------|-----------------|
| `/reports/monthly-trends` | POST | GET |
| `/reports/monthly-trends/export` | POST | GET |
| `/reports/ingredient-usage` | POST | GET |
| `/reports/ingredient-usage/export` | POST | GET |
| `/reports/spoilage` | POST | GET |
| `/reports/spoilage/export` | POST | GET |

### Pliki do modyfikacji
1. `backend/app/api/v1/reports.py`

---

## Plan testów

### Błąd 1 - Testy
- Otworzyć dzień
- Zamknąć dzień
- Kliknąć "Zobacz szczegóły"
- Sprawdzić czy czasy otwarcia/zamknięcia wyświetlają się poprawnie

### Błąd 2 - Testy
- Dodać transakcję przychodową (bez kategorii)
- Dodać transakcję wydatkową (z kategorią)
- Sprawdzić czy obie zapisują się poprawnie

### Błąd 3 - Testy
- Otworzyć raport "Trendy miesięczne"
- Otworzyć raport "Zużycie składników"
- Otworzyć raport "Straty"
- Sprawdzić czy wszystkie ładują się poprawnie

---

## Priorytet naprawy

1. **Błąd 3** (405) - Całkowicie blokuje funkcjonalność raportów
2. **Błąd 2** (500) - Blokuje dodawanie transakcji
3. **Błąd 1** (RangeError) - Blokuje podgląd szczegółów dnia
