# Test Plan: Menu Sorting

## Metadata

| Field | Value |
|-------|-------|
| **Author** | Claude AI |
| **Created** | 2026-01-02 |
| **Version** | 1.0 |
| **Functional Specification** | [Link](./README.md) |
| **Technical Specification** | [Link](./TECHNICAL.md) |
| **BDD Scenarios** | [Link](./scenarios.feature) |

---

## 1. Test Scope

### 1.1 Testing Objectives
- Verify correct saving of product order
- Verify drag-and-drop functionality in UI
- Verify sorting consistency across all views
- Verify error handling

### 1.2 In Scope
- [ ] Backend: Endpoint PUT /api/v1/products/reorder
- [ ] Backend: Sorting in GET /api/v1/products
- [ ] Backend: Automatic sort_order for new products
- [ ] Frontend: Drag-and-drop on product list
- [ ] Frontend: Optimistic update
- [ ] Frontend: Error handling

### 1.3 Out of Scope
- Performance tests (product count < 100)
- Accessibility tests

---

## 2. Testing Strategy

### 2.1 Test Levels

| Level | Coverage | Tools |
|-------|----------|-------|
| Unit | 80% | pytest |
| Integration | 100% API | pytest, TestClient |
| E2E | Critical paths | Playwright |
| Manual | Drag-drop UX | - |

### 2.2 Entry Criteria
- [ ] Specification approved
- [ ] Database migration created
- [ ] Frontend dependencies installed (@dnd-kit)

### 2.3 Exit Criteria
- [ ] All unit tests passed
- [ ] All API integration tests passed
- [ ] E2E drag-drop test passed
- [ ] No critical bugs

---

## 3. Test Cases

### 3.1 Unit Tests (Backend)

#### TC-UNIT-001: ProductService.reorder_products - success
**Component:** `ProductService`
**Method:** `reorder_products`
**Description:** Correct update of product order

**Input Data:**
```python
product_ids = [3, 1, 2]
```

**Expected Result:**
- Product 3: sort_order = 0
- Product 1: sort_order = 1
- Product 2: sort_order = 2
- Returns: 3

**Test Code:**
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

#### TC-UNIT-002: ProductService.reorder_products - non-existent product
**Component:** `ProductService`
**Method:** `reorder_products`
**Description:** Error when trying to reorder with non-existent ID

**Input Data:**
```python
product_ids = [1, 999]
```

**Expected Result:** `ValueError` with message about missing IDs

**Test Code:**
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

#### TC-UNIT-003: New product gets highest sort_order
**Component:** `ProductService`
**Method:** `create_product`
**Description:** Newly created product appears at the end of the list

**Test Code:**
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

### 3.2 Integration Tests (API)

#### TC-INT-001: PUT /api/v1/products/reorder - success
**Endpoint:** `PUT /api/v1/products/reorder`
**Description:** Correct order update

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

**Test Code:**
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

#### TC-INT-002: PUT /api/v1/products/reorder - empty list
**Endpoint:** `PUT /api/v1/products/reorder`
**Description:** Validation error on empty list

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

#### TC-INT-003: PUT /api/v1/products/reorder - duplicates
**Endpoint:** `PUT /api/v1/products/reorder`
**Description:** Validation error on duplicate IDs

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

#### TC-INT-004: GET /api/v1/products - sorting
**Endpoint:** `GET /api/v1/products`
**Description:** Products returned in sort_order

**Test Code:**
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

### 3.3 E2E Tests

#### TC-E2E-001: Drag-and-drop product
**Description:** Full drag-and-drop order change flow

**Steps:**
1. Open Menu page
2. Find product "Kebab" at position 1
3. Drag it to position 3
4. Verify new order
5. Refresh page
6. Verify order is preserved

**Test Code (Playwright):**
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

## 4. Test Data

### 4.1 Fixtures

```python
@pytest.fixture
def sample_products(db_session):
    """Creates sample products for tests."""
    products = [
        Product(id=1, name="Kebab", sort_order=0),
        Product(id=2, name="Burger", sort_order=1),
        Product(id=3, name="Frytki", sort_order=2),
    ]
    db_session.add_all(products)
    db_session.commit()
    return products
```

### 4.2 Test Data

| ID | Name | sort_order | Test Purpose |
|----|------|------------|--------------|
| 1 | Kebab | 0 | Standard case |
| 2 | Burger | 1 | Standard case |
| 3 | Frytki | 2 | Standard case |

---

## 5. Edge Cases

| ID | Case | Expected Behavior | Status |
|----|------|-------------------|--------|
| EC-001 | Single product | Drag-drop inactive | [ ] |
| EC-002 | 100 products | Efficient reorder | [ ] |
| EC-003 | Concurrent editing | Last save wins | [ ] |
| EC-004 | Gap in sort_order | Sorting works correctly | [ ] |

---

## 6. Manual Tests

### 6.1 UX Checklist

| Test | Description | Status |
|------|-------------|--------|
| TM-001 | Drag handle is visible | [ ] |
| TM-002 | Cursor changes to grab | [ ] |
| TM-003 | Card has shadow during drag | [ ] |
| TM-004 | Drop target indicator is visible | [ ] |
| TM-005 | Animation is smooth (60 FPS) | [ ] |
| TM-006 | Error toast on connection loss | [ ] |

---

## 7. Test Environment

### 7.1 Running Tests

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

## 8. Reporting

### 8.1 Report Format

| Metric | Value |
|--------|-------|
| Tests executed | - |
| Tests passed | - |
| Tests failed | - |
| Code coverage | - |

---

## Change History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-02 | Claude AI | Initial version |
