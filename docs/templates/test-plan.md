# Plan Testów: {Nazwa Funkcjonalności}

## Metadane

| Pole | Wartość |
|------|---------|
| **Autor** | {imię i nazwisko} |
| **Data utworzenia** | {YYYY-MM-DD} |
| **Wersja** | 1.0 |
| **Specyfikacja funkcjonalna** | [Link](./README.md) |
| **Specyfikacja techniczna** | [Link](./TECHNICAL.md) |
| **Scenariusze BDD** | [Link](./scenarios.feature) |

---

## 1. Zakres testów

### 1.1 Cele testowania
- {cel 1}
- {cel 2}
- {cel 3}

### 1.2 W zakresie
- [ ] {element do przetestowania 1}
- [ ] {element do przetestowania 2}

### 1.3 Poza zakresem
- {element poza zakresem}

---

## 2. Strategia testowania

### 2.1 Poziomy testów

| Poziom | Pokrycie | Narzędzia |
|--------|----------|-----------|
| Unit | {%} | pytest, vitest |
| Integracyjne | {%} | pytest, TestClient |
| E2E | {%} | Playwright / Cypress |
| Manualne | {%} | - |

### 2.2 Kryteria wejścia
- [ ] Specyfikacja zatwierdzona
- [ ] Środowisko testowe skonfigurowane
- [ ] Dane testowe przygotowane

### 2.3 Kryteria wyjścia
- [ ] Wszystkie testy krytyczne zaliczone
- [ ] Pokrycie kodu >= {X}%
- [ ] Brak błędów krytycznych i wysokich

---

## 3. Przypadki testowe

### 3.1 Testy jednostkowe (Backend)

#### TC-UNIT-001: {Nazwa testu}
**Komponent:** `{nazwa_serwisu}`
**Metoda:** `{nazwa_metody}`
**Opis:** {Co testujemy}

**Dane wejściowe:**
```python
{
    "field1": "value1",
    "field2": 123
}
```

**Oczekiwany rezultat:**
```python
{
    "id": 1,
    "field1": "value1",
    "field2": 123
}
```

**Kod testu:**
```python
def test_{nazwa_testu}():
    # Arrange
    service = {Name}Service(db_session)
    data = {Name}Create(field1="value1", field2=123)

    # Act
    result = service.create(data)

    # Assert
    assert result.id is not None
    assert result.field1 == "value1"
    assert result.field2 == 123
```

---

#### TC-UNIT-002: {Nazwa testu - walidacja błędu}
**Komponent:** `{nazwa_serwisu}`
**Metoda:** `{nazwa_metody}`
**Opis:** Walidacja błędu dla {przypadek}

**Dane wejściowe:**
```python
{
    "field1": "",  # Puste pole - powinno wywołać błąd
}
```

**Oczekiwany rezultat:** `ValidationError` z komunikatem "{komunikat}"

**Kod testu:**
```python
def test_{nazwa_testu}_validation_error():
    with pytest.raises(ValidationError) as exc_info:
        {Name}Create(field1="")

    assert "field1" in str(exc_info.value)
```

---

### 3.2 Testy jednostkowe (Frontend)

#### TC-UNIT-FE-001: {Nazwa testu komponentu}
**Komponent:** `{NazwaKomponentu}`
**Opis:** {Co testujemy}

**Kod testu:**
```typescript
describe('{NazwaKomponentu}', () => {
  it('{opis testu}', () => {
    render(<{NazwaKomponentu} prop1="value" />);

    expect(screen.getByText('{tekst}')).toBeInTheDocument();
  });
});
```

---

### 3.3 Testy integracyjne (API)

#### TC-INT-001: POST /api/v1/{resource} - Sukces
**Endpoint:** `POST /api/v1/{resource}`
**Opis:** Tworzenie nowego {obiektu}

**Request:**
```http
POST /api/v1/{resource}
Content-Type: application/json

{
    "field1": "test value",
    "field2": 42
}
```

**Expected Response (201):**
```json
{
    "id": 1,
    "field1": "test value",
    "field2": 42,
    "created_at": "2024-01-01T12:00:00Z"
}
```

**Kod testu:**
```python
def test_create_{resource}_success(client: TestClient):
    response = client.post(
        "/api/v1/{resource}",
        json={"field1": "test value", "field2": 42}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["field1"] == "test value"
    assert data["field2"] == 42
    assert "id" in data
```

---

#### TC-INT-002: POST /api/v1/{resource} - Błąd walidacji
**Endpoint:** `POST /api/v1/{resource}`
**Opis:** Błąd przy nieprawidłowych danych

**Request:**
```http
POST /api/v1/{resource}
Content-Type: application/json

{
    "field1": ""
}
```

**Expected Response (422):**
```json
{
    "detail": [{
        "loc": ["body", "field1"],
        "msg": "String should have at least 1 character",
        "type": "string_too_short"
    }]
}
```

---

#### TC-INT-003: GET /api/v1/{resource}/{id} - Sukces
**Endpoint:** `GET /api/v1/{resource}/{id}`
**Opis:** Pobieranie {obiektu} po ID

**Kod testu:**
```python
def test_get_{resource}_by_id(client: TestClient, sample_{resource}):
    response = client.get(f"/api/v1/{resource}/{sample_{resource}.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_{resource}.id
```

---

#### TC-INT-004: GET /api/v1/{resource}/{id} - Nie znaleziono
**Endpoint:** `GET /api/v1/{resource}/99999`
**Opis:** 404 dla nieistniejącego ID

**Expected Response (404):**
```json
{
    "detail": "Nie znaleziono"
}
```

---

### 3.4 Testy E2E

#### TC-E2E-001: {Pełny przepływ użytkownika}
**Opis:** {Opis scenariusza end-to-end}

**Kroki:**
1. Otwórz stronę {URL}
2. Kliknij przycisk "{nazwa}"
3. Wypełnij formularz:
   - Pole "{pole1}": "{wartość1}"
   - Pole "{pole2}": "{wartość2}"
4. Kliknij "Zapisz"
5. Zweryfikuj że {obiekt} pojawił się na liście

**Kod testu (Playwright):**
```typescript
test('{nazwa testu}', async ({ page }) => {
  await page.goto('/api/v1/{resource}');

  await page.click('button:has-text("Dodaj")');
  await page.fill('input[name="field1"]', 'Test Value');
  await page.click('button:has-text("Zapisz")');

  await expect(page.locator('text=Test Value')).toBeVisible();
});
```

---

## 4. Dane testowe

### 4.1 Fixtures

```python
@pytest.fixture
def sample_{resource}(db_session):
    """Tworzy przykładowy {obiekt} do testów."""
    {resource} = {Model}(
        field1="Test",
        field2=123
    )
    db_session.add({resource})
    db_session.commit()
    return {resource}
```

### 4.2 Dane testowe

| ID | field1 | field2 | Cel testu |
|----|--------|--------|-----------|
| 1 | "Test 1" | 100 | Standardowy przypadek |
| 2 | "Test 2" | 0 | Wartość brzegowa |
| 3 | "A" * 255 | 999999 | Maksymalne wartości |

---

## 5. Przypadki brzegowe

| ID | Przypadek | Oczekiwane zachowanie | Status |
|----|-----------|----------------------|--------|
| EC-001 | Puste dane | Komunikat walidacji | [ ] |
| EC-002 | Bardzo długi tekst | Obcięcie lub błąd | [ ] |
| EC-003 | Znaki specjalne | Poprawne zapisanie | [ ] |
| EC-004 | Równoczesna edycja | Konflikt lub merge | [ ] |

---

## 6. Testy wydajnościowe

### 6.1 Scenariusze

| Scenariusz | Oczekiwany czas | Limit |
|------------|-----------------|-------|
| Lista 100 {obiektów} | < 500ms | 1s |
| Tworzenie {obiektu} | < 200ms | 500ms |
| Wyszukiwanie | < 300ms | 1s |

### 6.2 Testy obciążeniowe

```python
def test_list_{resources}_performance(client: TestClient, benchmark):
    # Setup: Create 1000 {resources}

    result = benchmark(
        lambda: client.get("/api/v1/{resources}")
    )

    assert result.stats.mean < 0.5  # < 500ms
```

---

## 7. Testy bezpieczeństwa

| Test | Opis | Status |
|------|------|--------|
| SEC-001 | SQL Injection | [ ] |
| SEC-002 | XSS | [ ] |
| SEC-003 | CSRF | [ ] |
| SEC-004 | Autoryzacja | [ ] |

---

## 8. Środowisko testowe

### 8.1 Konfiguracja

```yaml
# docker-compose.test.yml
services:
  test-db:
    image: postgres:15
    environment:
      POSTGRES_DB: test_small_gastro
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
```

### 8.2 Uruchomienie testów

```bash
# Backend
cd backend
pytest --cov=app --cov-report=html

# Frontend
cd frontend
npm run test
npm run test:coverage

# E2E
npm run test:e2e
```

---

## 9. Raportowanie

### 9.1 Format raportu

| Metryka | Wartość |
|---------|---------|
| Testy wykonane | {X} |
| Testy zaliczone | {Y} |
| Testy niezaliczone | {Z} |
| Pokrycie kodu | {%} |

### 9.2 Znalezione błędy

| ID | Opis | Priorytet | Status |
|----|------|-----------|--------|
| BUG-001 | {opis} | Krytyczny/Wysoki/Średni/Niski | Otwarty/Naprawiony |

---

## Historia zmian

| Wersja | Data | Autor | Opis zmian |
|--------|------|-------|------------|
| 1.0 | {data} | {autor} | Wersja początkowa |
