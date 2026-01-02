# Plan Testow: Sortowanie Menu

## Metadane

| Pole | Wartosc |
|------|---------|
| **Autor** | Claude AI |
| **Data utworzenia** | 2026-01-02 |
| **Wersja** | 1.0 |
| **Specyfikacja funkcjonalna** | [Link](./README.md) |
| **Specyfikacja techniczna** | [Link](./TECHNICAL.md) |
| **Scenariusze BDD** | [Link](./scenarios.feature) |

---

## 1. Zakres testow

### 1.1 Cele testowania
- Weryfikacja poprawnosci zapisywania kolejnosci produktow
- Weryfikacja dzialania drag-and-drop w UI
- Weryfikacja spojnosci sortowania we wszystkich widokach
- Weryfikacja obslugi bledow

### 1.2 W zakresie
- [ ] Backend: Endpoint PUT /api/v1/products/reorder
- [ ] Backend: Sortowanie w GET /api/v1/products
- [ ] Backend: Automatyczny sort_order dla nowych produktow
- [ ] Frontend: Drag-and-drop na liscie produktow
- [ ] Frontend: Optimistic update
- [ ] Frontend: Obsluga bledow

### 1.3 Poza zakresem
- Testy wydajnosciowe (liczba produktow < 100)
- Testy dostepnosci (accessibility)

---

## 2. Strategia testowania

### 2.1 Poziomy testow

| Poziom | Pokrycie | Narzedzia |
|--------|----------|-----------|
| Unit | 80% | pytest |
| Integracyjne | 100% API | pytest, TestClient |
| E2E | Krytyczne sciezki | Playwright |
| Manualne | Drag-drop UX | - |

### 2.2 Kryteria wejscia
- [ ] Specyfikacja zatwierdzona
- [ ] Migracja bazy danych utworzona
- [ ] Zaleznosci frontend zainstalowane (@dnd-kit)

### 2.3 Kryteria wyjscia
- [ ] Wszystkie testy jednostkowe zaliczone
- [ ] Wszystkie testy integracyjne API zaliczone
- [ ] Test E2E drag-drop zaliczony
- [ ] Brak bledow krytycznych

---

## 3. Przypadki testowe

### 3.1 Testy jednostkowe (Backend)

#### TC-UNIT-001: ProductService.reorder_products - sukces
**Komponent:** `ProductService`
**Metoda:** `reorder_products`
**Opis:** Poprawna aktualizacja kolejnosci produktow

**Dane wejsciowe:**
```python
product_ids = [3, 1, 2]
```

**Oczekiwany rezultat:**
- Produkt 3: sort_order = 0
- Produkt 1: sort_order = 1
- Produkt 2: sort_order = 2
- Zwraca: 3

**Kod testu:**
```python
def test_reorder_products_success(db_session):
    # Arrange
    p1 = Product(id=1, name="A", sort_order=0)
    p2 = Product(id=2, name="B", sort_order=1)
    p3 = Product(id=3, name="C", sort_order=2)
    db_session.add_all([p1, p2, p3])
    db_session.commit()

    service = ProductService(db_session)

    # Act
    result = service.reorder_products([3, 1, 2])

    # Assert
    assert result == 3
    assert db_session.get(Product, 3).sort_order == 0
    assert db_session.get(Product, 1).sort_order == 1
    assert db_session.get(Product, 2).sort_order == 2
```

---

#### TC-UNIT-002: ProductService.reorder_products - nieistniejacy produkt
**Komponent:** `ProductService`
**Metoda:** `reorder_products`
**Opis:** Blad przy probie zmiany kolejnosci z nieistniejacym ID

**Dane wejsciowe:**
```python
product_ids = [1, 999]
```

**Oczekiwany rezultat:** `ValueError` z komunikatem o brakujacych ID

**Kod testu:**
```python
def test_reorder_products_missing_id(db_session):
    # Arrange
    p1 = Product(id=1, name="A", sort_order=0)
    db_session.add(p1)
    db_session.commit()

    service = ProductService(db_session)

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        service.reorder_products([1, 999])

    assert "999" in str(exc_info.value)
```

---

#### TC-UNIT-003: Nowy produkt otrzymuje najwyzszy sort_order
**Komponent:** `ProductService`
**Metoda:** `create_product`
**Opis:** Nowo utworzony produkt pojawia sie na koncu listy

**Kod testu:**
```python
def test_new_product_gets_max_sort_order(db_session):
    # Arrange
    p1 = Product(id=1, name="A", sort_order=0)
    p2 = Product(id=2, name="B", sort_order=5)
    db_session.add_all([p1, p2])
    db_session.commit()

    service = ProductService(db_session)

    # Act
    new_product = service.create_product(ProductCreate(name="C", price_pln=10.0))

    # Assert
    assert new_product.sort_order == 6  # max(5) + 1
```

---

### 3.2 Testy integracyjne (API)

#### TC-INT-001: PUT /api/v1/products/reorder - sukces
**Endpoint:** `PUT /api/v1/products/reorder`
**Opis:** Poprawna aktualizacja kolejnosci

**Request:**
```http
PUT /api/v1/products/reorder
Content-Type: application/json

{
    "product_ids": [3, 1, 2]
}
```

**Expected Response (200):**
```json
{
    "message": "Kolejność zaktualizowana",
    "updated_count": 3
}
```

**Kod testu:**
```python
def test_reorder_products_success(client: TestClient, sample_products):
    response = client.put(
        "/api/v1/products/reorder",
        json={"product_ids": [3, 1, 2]}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["updated_count"] == 3
```

---

#### TC-INT-002: PUT /api/v1/products/reorder - pusta lista
**Endpoint:** `PUT /api/v1/products/reorder`
**Opis:** Blad walidacji przy pustej liscie

**Request:**
```http
PUT /api/v1/products/reorder
Content-Type: application/json

{
    "product_ids": []
}
```

**Expected Response (422):**
```json
{
    "detail": [{
        "loc": ["body", "product_ids"],
        "msg": "List should have at least 1 item after validation",
        "type": "too_short"
    }]
}
```

---

#### TC-INT-003: PUT /api/v1/products/reorder - duplikaty
**Endpoint:** `PUT /api/v1/products/reorder`
**Opis:** Blad walidacji przy duplikatach ID

**Request:**
```http
PUT /api/v1/products/reorder
Content-Type: application/json

{
    "product_ids": [1, 2, 1]
}
```

**Expected Response (422):**
```json
{
    "detail": [{
        "loc": ["body", "product_ids"],
        "msg": "Lista zawiera duplikaty ID",
        "type": "value_error"
    }]
}
```

---

#### TC-INT-004: GET /api/v1/products - sortowanie
**Endpoint:** `GET /api/v1/products`
**Opis:** Produkty zwracane w kolejnosci sort_order

**Kod testu:**
```python
def test_products_sorted_by_sort_order(client: TestClient, db_session):
    # Arrange - products with non-sequential sort_order
    p1 = Product(id=1, name="C", sort_order=2)
    p2 = Product(id=2, name="A", sort_order=0)
    p3 = Product(id=3, name="B", sort_order=1)
    db_session.add_all([p1, p2, p3])
    db_session.commit()

    # Act
    response = client.get("/api/v1/products")

    # Assert
    assert response.status_code == 200
    items = response.json()["items"]
    assert [p["name"] for p in items] == ["A", "B", "C"]
```

---

### 3.3 Testy E2E

#### TC-E2E-001: Drag-and-drop produktu
**Opis:** Pelny przeplyw zmiany kolejnosci metodą drag-and-drop

**Kroki:**
1. Otworz strone Menu
2. Znajdz produkt "Kebab" na pozycji 1
3. Przeciagnij go na pozycje 3
4. Zweryfikuj nowa kolejnosc
5. Odswiez strone
6. Zweryfikuj ze kolejnosc sie zachowala

**Kod testu (Playwright):**
```typescript
test('drag and drop product reorder', async ({ page }) => {
  // Arrange - add test products
  await page.goto('/menu');

  // Get initial order
  const products = page.locator('[data-testid="product-card"]');
  const initialFirst = await products.nth(0).textContent();

  // Act - drag first product to third position
  const source = products.nth(0).locator('[data-testid="drag-handle"]');
  const target = products.nth(2);

  await source.dragTo(target);

  // Assert - order changed
  await expect(products.nth(2)).toContainText(initialFirst!);

  // Refresh and verify persistence
  await page.reload();
  await expect(products.nth(2)).toContainText(initialFirst!);
});
```

---

## 4. Dane testowe

### 4.1 Fixtures

```python
@pytest.fixture
def sample_products(db_session):
    """Tworzy przykladowe produkty do testow."""
    products = [
        Product(id=1, name="Kebab", sort_order=0),
        Product(id=2, name="Burger", sort_order=1),
        Product(id=3, name="Frytki", sort_order=2),
    ]
    db_session.add_all(products)
    db_session.commit()
    return products
```

### 4.2 Dane testowe

| ID | Nazwa | sort_order | Cel testu |
|----|-------|------------|-----------|
| 1 | Kebab | 0 | Standardowy przypadek |
| 2 | Burger | 1 | Standardowy przypadek |
| 3 | Frytki | 2 | Standardowy przypadek |

---

## 5. Przypadki brzegowe

| ID | Przypadek | Oczekiwane zachowanie | Status |
|----|-----------|----------------------|--------|
| EC-001 | Jeden produkt | Drag-drop nieaktywny | [ ] |
| EC-002 | 100 produktow | Wydajny reorder | [ ] |
| EC-003 | Rownoczesna edycja | Ostatni zapis wygrywa | [ ] |
| EC-004 | Luka w sort_order | Sortowanie dziala poprawnie | [ ] |

---

## 6. Testy manualne

### 6.1 Checklist UX

| Test | Opis | Status |
|------|------|--------|
| TM-001 | Uchwyt przeciagania jest widoczny | [ ] |
| TM-002 | Kursor zmienia sie na grab | [ ] |
| TM-003 | Karta ma cien podczas przeciagania | [ ] |
| TM-004 | Wskaznik miejsca docelowego jest widoczny | [ ] |
| TM-005 | Animacja jest plynna (60 FPS) | [ ] |
| TM-006 | Toast z bledem przy braku polaczenia | [ ] |

---

## 7. Srodowisko testowe

### 7.1 Uruchomienie testow

```bash
# Backend
cd backend
pytest tests/test_product_reorder.py -v

# Frontend
cd frontend
npm run test

# E2E
npm run test:e2e
```

---

## 8. Raportowanie

### 8.1 Format raportu

| Metryka | Wartosc |
|---------|---------|
| Testy wykonane | - |
| Testy zaliczone | - |
| Testy niezaliczone | - |
| Pokrycie kodu | - |

---

## Historia zmian

| Wersja | Data | Autor | Opis zmian |
|--------|------|-------|------------|
| 1.0 | 2026-01-02 | Claude AI | Wersja poczatkowa |
