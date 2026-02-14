# Test Plan: Sales Tracking Hybrid

## Metadata

| Field | Value |
|-------|-------|
| **Author** | AI Assistant |
| **Created** | 2026-01-06 |
| **Version** | 1.0 |
| **Functional Specification** | [README.md](./README.md) |
| **Technical Specification** | [TECHNICAL.md](./TECHNICAL.md) |
| **BDD Scenarios** | [scenarios.feature](./scenarios.feature) |

---

## 1. Test Scope

### 1.1 Testing Objectives
- Verify sales can be recorded in real-time with correct data capture
- Ensure voiding sales works correctly with audit trail
- Validate reconciliation calculations are accurate
- Confirm UI is responsive and touch-friendly on mobile devices
- Test integration with existing day open/close workflow

### 1.2 In Scope
- [x] RecordedSale CRUD operations
- [x] Void sale functionality with reason tracking
- [x] Running total calculations
- [x] Reconciliation comparison (recorded vs calculated)
- [x] Missing sales suggestions
- [x] Product category filtering
- [x] Shift attribution for sales
- [x] Integration with CloseDayWizard
- [x] Insights endpoints (popularity, peak hours, portion accuracy)

### 1.3 Out of Scope
- Payment method tracking (deferred)
- Offline sync functionality (future phase)
- External POS hardware integration
- Multi-location support

---

## 2. Testing Strategy

### 2.1 Test Levels

| Level | Coverage Target | Tools |
|-------|----------------|-------|
| Unit (Backend) | 80% | pytest |
| Unit (Frontend) | 70% | vitest, React Testing Library |
| Integration (API) | 90% | pytest, TestClient |
| E2E | Critical paths | Playwright |
| Manual | Mobile UX | Physical devices |

### 2.2 Entry Criteria
- [x] Functional specification approved
- [x] Technical specification approved
- [ ] Database migration created and tested
- [ ] Test environment configured with Docker
- [ ] Test data fixtures prepared

### 2.3 Exit Criteria
- [ ] All critical and high-priority tests passed
- [ ] Backend code coverage >= 80%
- [ ] Frontend code coverage >= 70%
- [ ] No critical or high severity bugs open
- [ ] Performance requirements met (< 500ms for sales recording)

---

## 3. Test Cases

### 3.1 Unit Tests (Backend)

#### TC-UNIT-001: Record Sale - Happy Path
**Component:** `RecordedSalesService`
**Method:** `record_sale`
**Description:** Successfully record a sale for an open day

**Input Data:**
```python
{
    "daily_record_id": 1,
    "variant_id": 5,
    "quantity": 1
}
```

**Expected Result:**
```python
{
    "id": 1,
    "daily_record_id": 1,
    "product_variant_id": 5,
    "quantity": 1,
    "unit_price_pln": Decimal("28.00"),
    "shift_assignment_id": 3,  # If shift active
    "voided_at": None
}
```

**Test Code:**
```python
def test_record_sale_success(db_session, open_day, active_shift, product_variant):
    # Arrange
    service = RecordedSalesService(db_session)

    # Act
    result = service.record_sale(
        daily_record_id=open_day.id,
        variant_id=product_variant.id,
        quantity=1
    )

    # Assert
    assert result.id is not None
    assert result.daily_record_id == open_day.id
    assert result.product_variant_id == product_variant.id
    assert result.unit_price_pln == product_variant.price_pln
    assert result.shift_assignment_id == active_shift.id
    assert result.voided_at is None
```

---

#### TC-UNIT-002: Record Sale - Day Not Open
**Component:** `RecordedSalesService`
**Method:** `record_sale`
**Description:** Reject sale when day is closed

**Test Code:**
```python
def test_record_sale_day_closed(db_session, closed_day, product_variant):
    service = RecordedSalesService(db_session)

    with pytest.raises(ValueError) as exc_info:
        service.record_sale(
            daily_record_id=closed_day.id,
            variant_id=product_variant.id
        )

    assert "Dzien nie jest otwarty" in str(exc_info.value)
```

---

#### TC-UNIT-003: Record Sale - Inactive Product
**Component:** `RecordedSalesService`
**Method:** `record_sale`
**Description:** Reject sale for inactive product variant

**Test Code:**
```python
def test_record_sale_inactive_variant(db_session, open_day, inactive_variant):
    service = RecordedSalesService(db_session)

    with pytest.raises(ValueError) as exc_info:
        service.record_sale(
            daily_record_id=open_day.id,
            variant_id=inactive_variant.id
        )

    assert "Produkt nie istnieje lub jest nieaktywny" in str(exc_info.value)
```

---

#### TC-UNIT-004: Void Sale - Happy Path
**Component:** `RecordedSalesService`
**Method:** `void_sale`
**Description:** Successfully void a recorded sale

**Test Code:**
```python
def test_void_sale_success(db_session, recorded_sale):
    service = RecordedSalesService(db_session)

    result = service.void_sale(
        sale_id=recorded_sale.id,
        reason="mistake",
        notes="Wrong product tapped"
    )

    assert result.voided_at is not None
    assert result.void_reason == "mistake"
    assert result.void_notes == "Wrong product tapped"
```

---

#### TC-UNIT-005: Void Sale - Already Voided
**Component:** `RecordedSalesService`
**Method:** `void_sale`
**Description:** Reject voiding already voided sale

**Test Code:**
```python
def test_void_sale_already_voided(db_session, voided_sale):
    service = RecordedSalesService(db_session)

    with pytest.raises(ValueError) as exc_info:
        service.void_sale(sale_id=voided_sale.id, reason="mistake")

    assert "zostala juz anulowana" in str(exc_info.value)
```

---

#### TC-UNIT-006: Void Sale - Day Closed
**Component:** `RecordedSalesService`
**Method:** `void_sale`
**Description:** Reject voiding sale from closed day

**Test Code:**
```python
def test_void_sale_day_closed(db_session, sale_from_closed_day):
    service = RecordedSalesService(db_session)

    with pytest.raises(ValueError) as exc_info:
        service.void_sale(sale_id=sale_from_closed_day.id, reason="mistake")

    assert "zamknietego dnia" in str(exc_info.value)
```

---

#### TC-UNIT-007: Get Day Total - Excludes Voided
**Component:** `RecordedSalesService`
**Method:** `get_day_total`
**Description:** Total calculation excludes voided sales

**Test Code:**
```python
def test_get_day_total_excludes_voided(db_session, open_day):
    service = RecordedSalesService(db_session)

    # Create 3 sales of 28 PLN each
    for _ in range(3):
        service.record_sale(open_day.id, variant_id=5)  # 28 PLN

    # Void one
    sales = service.get_day_sales(open_day.id)
    service.void_sale(sales[0].id, reason="mistake")

    # Assert total is 2 * 28 = 56
    total = service.get_day_total(open_day.id)
    assert total == Decimal("56.00")
```

---

#### TC-UNIT-008: Reconciliation - Basic Comparison
**Component:** `ReconciliationService`
**Method:** `reconcile`
**Description:** Generate correct reconciliation report

**Test Code:**
```python
def test_reconciliation_basic(db_session, day_with_sales_and_inventory):
    service = ReconciliationService(db_session)

    result = service.reconcile(day_with_sales_and_inventory.id)

    assert result.recorded_total_pln == Decimal("280.00")  # 10 * 28
    assert result.calculated_total_pln == Decimal("336.00")  # 12 * 28
    assert result.discrepancy_pln == Decimal("56.00")
    assert result.discrepancy_percent == pytest.approx(16.67, rel=0.01)
```

---

#### TC-UNIT-009: Reconciliation - Suggestions
**Component:** `ReconciliationService`
**Method:** `_generate_suggestions`
**Description:** Generate suggestions for missing sales

**Test Code:**
```python
def test_reconciliation_suggestions(db_session, day_with_discrepancy):
    service = ReconciliationService(db_session)

    result = service.reconcile(day_with_discrepancy.id)

    assert len(result.suggestions) > 0
    suggestion = result.suggestions[0]
    assert suggestion.suggested_qty == 2
    assert "Kebab" in suggestion.product_name
```

---

#### TC-UNIT-010: Reconciliation - Critical Threshold
**Component:** `ReconciliationService`
**Method:** `reconcile`
**Description:** Flag critical discrepancy when > 30%

**Test Code:**
```python
def test_reconciliation_critical_threshold(db_session, day_with_large_discrepancy):
    service = ReconciliationService(db_session)

    result = service.reconcile(day_with_large_discrepancy.id)

    assert result.discrepancy_percent > 30
    assert result.has_critical_discrepancy is True
```

---

### 3.2 Unit Tests (Frontend)

#### TC-UNIT-FE-001: ProductButton Renders
**Component:** `ProductButton`
**Description:** Button renders with correct data

**Test Code:**
```typescript
describe('ProductButton', () => {
  it('renders product name, variant, and price', () => {
    const variant = {
      id: 1,
      product_name: 'Kebab',
      name: 'Duzy',
      price_pln: '28.00'
    };

    render(<ProductButton variant={variant} todayCount={5} onTap={vi.fn()} isLoading={false} />);

    expect(screen.getByText('Kebab')).toBeInTheDocument();
    expect(screen.getByText('Duzy')).toBeInTheDocument();
    expect(screen.getByText('28,00 PLN')).toBeInTheDocument();
    expect(screen.getByText('(5)')).toBeInTheDocument();
  });
});
```

---

#### TC-UNIT-FE-002: RunningTotal Updates
**Component:** `RunningTotal`
**Description:** Total updates when prop changes

**Test Code:**
```typescript
describe('RunningTotal', () => {
  it('displays formatted total', () => {
    const { rerender } = render(<RunningTotal total={1245.50} itemCount={47} />);

    expect(screen.getByText('1 245,50 PLN')).toBeInTheDocument();
    expect(screen.getByText('47 szt.')).toBeInTheDocument();

    rerender(<RunningTotal total={1273.50} itemCount={48} />);

    expect(screen.getByText('1 273,50 PLN')).toBeInTheDocument();
  });
});
```

---

#### TC-UNIT-FE-003: VoidSaleModal Reason Selection
**Component:** `VoidSaleModal`
**Description:** User must select reason before confirming

**Test Code:**
```typescript
describe('VoidSaleModal', () => {
  it('requires reason selection', async () => {
    const onVoid = vi.fn();
    render(<VoidSaleModal sale={mockSale} onVoid={onVoid} onClose={vi.fn()} />);

    const confirmButton = screen.getByText('Potwierdz');
    expect(confirmButton).toBeDisabled();

    await userEvent.click(screen.getByLabelText('Pomylka przy rejestracji'));

    expect(confirmButton).toBeEnabled();
  });
});
```

---

#### TC-UNIT-FE-004: CategoryTabs Selection
**Component:** `CategoryTabs`
**Description:** Tab selection updates state

**Test Code:**
```typescript
describe('CategoryTabs', () => {
  it('calls onSelect when tab clicked', async () => {
    const onSelect = vi.fn();
    const categories = [
      { id: 1, name: 'Kebaby', sort_order: 1 },
      { id: 2, name: 'Burgery', sort_order: 2 }
    ];

    render(<CategoryTabs categories={categories} selected={1} onSelect={onSelect} />);

    await userEvent.click(screen.getByText('Burgery'));

    expect(onSelect).toHaveBeenCalledWith(2);
  });
});
```

---

### 3.3 Integration Tests (API)

#### TC-INT-001: POST /daily-records/{id}/sales - Success
**Endpoint:** `POST /api/v1/daily-records/{id}/sales`
**Description:** Create recorded sale

**Test Code:**
```python
def test_record_sale_api_success(client: TestClient, open_day, product_variant):
    response = client.post(
        f"/api/v1/daily-records/{open_day.id}/sales",
        json={"product_variant_id": product_variant.id, "quantity": 1}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["product_variant_id"] == product_variant.id
    assert data["quantity"] == 1
    assert data["unit_price_pln"] == str(product_variant.price_pln)
    assert data["voided_at"] is None
```

---

#### TC-INT-002: GET /daily-records/{id}/sales - List Sales
**Endpoint:** `GET /api/v1/daily-records/{id}/sales`
**Description:** List recorded sales for a day

**Test Code:**
```python
def test_get_day_sales_api(client: TestClient, day_with_5_sales):
    response = client.get(f"/api/v1/daily-records/{day_with_5_sales.id}/sales")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
    assert all(sale["voided_at"] is None for sale in data)
```

---

#### TC-INT-003: GET /daily-records/{id}/sales?include_voided=true
**Endpoint:** `GET /api/v1/daily-records/{id}/sales`
**Description:** Include voided sales when requested

**Test Code:**
```python
def test_get_day_sales_include_voided(client: TestClient, day_with_voided_sales):
    response = client.get(
        f"/api/v1/daily-records/{day_with_voided_sales.id}/sales",
        params={"include_voided": True}
    )

    assert response.status_code == 200
    data = response.json()
    voided_count = sum(1 for sale in data if sale["voided_at"] is not None)
    assert voided_count > 0
```

---

#### TC-INT-004: GET /daily-records/{id}/sales/total
**Endpoint:** `GET /api/v1/daily-records/{id}/sales/total`
**Description:** Get running total for day

**Test Code:**
```python
def test_get_day_total_api(client: TestClient, day_with_5_sales):
    response = client.get(f"/api/v1/daily-records/{day_with_5_sales.id}/sales/total")

    assert response.status_code == 200
    data = response.json()
    assert "total_pln" in data
    assert "sales_count" in data
    assert "items_count" in data
    assert data["sales_count"] == 5
```

---

#### TC-INT-005: POST /daily-records/{id}/sales/{sale_id}/void
**Endpoint:** `POST /api/v1/daily-records/{id}/sales/{sale_id}/void`
**Description:** Void a recorded sale

**Test Code:**
```python
def test_void_sale_api(client: TestClient, recorded_sale):
    response = client.post(
        f"/api/v1/daily-records/{recorded_sale.daily_record_id}/sales/{recorded_sale.id}/void",
        json={"reason": "mistake", "notes": "Test void"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["voided_at"] is not None
    assert data["void_reason"] == "mistake"
```

---

#### TC-INT-006: GET /daily-records/{id}/reconciliation
**Endpoint:** `GET /api/v1/daily-records/{id}/reconciliation`
**Description:** Get reconciliation report

**Test Code:**
```python
def test_reconciliation_api(client: TestClient, day_with_sales_and_inventory):
    response = client.get(
        f"/api/v1/daily-records/{day_with_sales_and_inventory.id}/reconciliation"
    )

    assert response.status_code == 200
    data = response.json()
    assert "recorded_total_pln" in data
    assert "calculated_total_pln" in data
    assert "discrepancy_pln" in data
    assert "by_product" in data
    assert "suggestions" in data
```

---

#### TC-INT-007: POST /daily-records/{id}/sales - Day Closed Error
**Endpoint:** `POST /api/v1/daily-records/{id}/sales`
**Description:** Error when recording to closed day

**Test Code:**
```python
def test_record_sale_day_closed_api(client: TestClient, closed_day, product_variant):
    response = client.post(
        f"/api/v1/daily-records/{closed_day.id}/sales",
        json={"product_variant_id": product_variant.id}
    )

    assert response.status_code == 400
    assert "Dzien nie jest otwarty" in response.json()["detail"]
```

---

### 3.4 E2E Tests

#### TC-E2E-001: Full Sales Recording Flow
**Description:** Record multiple sales and verify totals

**Steps:**
1. Open sales entry page
2. Tap on "Kebab Duzy" 3 times
3. Tap on "Burger Classic" 2 times
4. Verify running total = (3 * 28) + (2 * 25) = 134 PLN
5. Verify recent sales list shows 5 items

**Test Code (Playwright):**
```typescript
test('record multiple sales and verify total', async ({ page }) => {
  // Setup: Ensure day is open
  await page.goto('/daily');
  await openDayIfNeeded(page);

  await page.goto('/sales');

  // Record 3 Kebab Duzy
  await page.click('button:has-text("Kebab Duzy")');
  await page.click('button:has-text("Kebab Duzy")');
  await page.click('button:has-text("Kebab Duzy")');

  // Switch to Burgery and record 2
  await page.click('[role="tab"]:has-text("Burgery")');
  await page.click('button:has-text("Burger Classic")');
  await page.click('button:has-text("Burger Classic")');

  // Verify total
  await expect(page.locator('[data-testid="running-total"]')).toContainText('134,00 PLN');

  // Verify recent sales count
  const salesList = page.locator('[data-testid="recent-sales-list"] li');
  await expect(salesList).toHaveCount(5);
});
```

---

#### TC-E2E-002: Void Sale Flow
**Description:** Record and void a sale

**Test Code (Playwright):**
```typescript
test('void a recorded sale', async ({ page }) => {
  await page.goto('/sales');

  // Record a sale
  await page.click('button:has-text("Kebab Maly")');
  await expect(page.locator('[data-testid="running-total"]')).toContainText('18,00 PLN');

  // Void it
  await page.click('[data-testid="recent-sales-list"] li:first-child');
  await page.click('label:has-text("Pomylka przy rejestracji")');
  await page.click('button:has-text("Potwierdz")');

  // Verify total is 0
  await expect(page.locator('[data-testid="running-total"]')).toContainText('0,00 PLN');
});
```

---

#### TC-E2E-003: Reconciliation in Close Wizard
**Description:** View reconciliation step during day close

**Test Code (Playwright):**
```typescript
test('reconciliation step shows comparison', async ({ page }) => {
  // Setup: Day with sales
  await setupDayWithSales(page, 10);

  await page.goto('/daily');
  await page.click('button:has-text("Zamknij dzien")');

  // Navigate to reconciliation step
  await page.click('button:has-text("Dalej")'); // Inventory step
  await page.click('button:has-text("Dalej")'); // Events step

  // Verify reconciliation shows
  await expect(page.locator('h2')).toContainText('Uzgodnienie sprzedazy');
  await expect(page.locator('[data-testid="recorded-total"]')).toBeVisible();
  await expect(page.locator('[data-testid="calculated-total"]')).toBeVisible();
  await expect(page.locator('[data-testid="discrepancy"]')).toBeVisible();
});
```

---

#### TC-E2E-004: Mobile Touch Experience
**Description:** Verify touch targets on mobile viewport

**Test Code (Playwright):**
```typescript
test('product buttons are touch-friendly on mobile', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 667 }); // iPhone SE
  await page.goto('/sales');

  const button = page.locator('button:has-text("Kebab")').first();
  const box = await button.boundingBox();

  // Minimum touch target: 48x48 pixels
  expect(box?.width).toBeGreaterThanOrEqual(48);
  expect(box?.height).toBeGreaterThanOrEqual(48);
});
```

---

## 4. Test Data

### 4.1 Fixtures

```python
@pytest.fixture
def product_categories(db_session):
    """Create test product categories."""
    categories = [
        ProductCategory(name="Kebaby", sort_order=1),
        ProductCategory(name="Burgery", sort_order=2),
        ProductCategory(name="Napoje", sort_order=3),
    ]
    db_session.add_all(categories)
    db_session.commit()
    return categories


@pytest.fixture
def product_variant(db_session, product_categories):
    """Create a test product with variant."""
    product = Product(name="Kebab", category_id=product_categories[0].id)
    db_session.add(product)
    db_session.flush()

    variant = ProductVariant(
        product_id=product.id,
        name="Duzy",
        price_pln=Decimal("28.00"),
        is_active=True
    )
    db_session.add(variant)
    db_session.commit()
    return variant


@pytest.fixture
def open_day(db_session):
    """Create an open day for testing."""
    day = DailyRecord(date=date.today(), status=DayStatus.OPEN)
    db_session.add(day)
    db_session.commit()
    return day


@pytest.fixture
def recorded_sale(db_session, open_day, product_variant):
    """Create a sample recorded sale."""
    sale = RecordedSale(
        daily_record_id=open_day.id,
        product_variant_id=product_variant.id,
        quantity=1,
        unit_price_pln=product_variant.price_pln
    )
    db_session.add(sale)
    db_session.commit()
    return sale
```

### 4.2 Test Data Sets

| ID | Product | Variant | Price | Quantity | Purpose |
|----|---------|---------|-------|----------|---------|
| 1 | Kebab | Maly | 18.00 | 1 | Basic sale |
| 2 | Kebab | Duzy | 28.00 | 5 | Multiple quantity |
| 3 | Burger | Classic | 25.00 | 1 | Different category |
| 4 | Cola | 0.5L | 6.00 | 10 | High volume |

---

## 5. Edge Cases

| ID | Case | Expected Behavior | Status |
|----|------|------------------|--------|
| EC-001 | Record sale with no active shift | Sale recorded with shift_id=NULL | [ ] |
| EC-002 | Void all sales for a product | Reconciliation shows 0 recorded | [ ] |
| EC-003 | Close day with 0 recorded sales | Warning shown, calculated used | [ ] |
| EC-004 | Recorded > Calculated | Positive discrepancy, suggest inventory check | [ ] |
| EC-005 | Very large discrepancy (>30%) | Critical warning displayed | [ ] |
| EC-006 | Multiple shifts per day | Sales attributed to correct shift | [ ] |
| EC-007 | Inactive product variant | Cannot record sale, error message | [ ] |

---

## 6. Performance Tests

### 6.1 Scenarios

| Scenario | Expected Time | Maximum |
|----------|---------------|---------|
| Record single sale | < 200ms | 500ms |
| Get day sales (50 items) | < 100ms | 300ms |
| Get running total | < 50ms | 100ms |
| Reconciliation report | < 500ms | 2000ms |
| Product list by category | < 100ms | 300ms |

### 6.2 Load Tests

```python
def test_record_sale_performance(client: TestClient, open_day, product_variant, benchmark):
    def record_sale():
        return client.post(
            f"/api/v1/daily-records/{open_day.id}/sales",
            json={"product_variant_id": product_variant.id}
        )

    result = benchmark(record_sale)
    assert result.status_code == 201
    # Benchmark will report timing


def test_reconciliation_performance(client: TestClient, day_with_200_sales, benchmark):
    def get_reconciliation():
        return client.get(
            f"/api/v1/daily-records/{day_with_200_sales.id}/reconciliation"
        )

    result = benchmark(get_reconciliation)
    assert result.status_code == 200
    # Target: < 2 seconds
```

---

## 7. Security Tests

| ID | Test | Description | Status |
|----|------|-------------|--------|
| SEC-001 | Price tampering | Verify price comes from DB, not request | [ ] |
| SEC-002 | Cross-day access | Cannot record sale for other day | [ ] |
| SEC-003 | Void authorization | Void requires valid reason | [ ] |
| SEC-004 | Immutable history | Cannot modify voided_at after set | [ ] |
| SEC-005 | SQL injection | Test search parameters | [ ] |

---

## 8. Test Environment

### 8.1 Configuration

```yaml
# docker-compose.test.yml
services:
  test-db:
    image: postgres:15
    environment:
      POSTGRES_DB: test_small_gastro
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
    ports:
      - "5433:5432"

  test-backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql://test:test@test-db:5432/test_small_gastro
      TESTING: "true"
    depends_on:
      - test-db
```

### 8.2 Running Tests

```bash
# Backend unit + integration tests
cd backend
docker compose -f docker-compose.test.yml up -d test-db
pytest --cov=app --cov-report=html -v

# Frontend unit tests
cd frontend
npm run test
npm run test:coverage

# E2E tests
npm run test:e2e

# Specific test file
pytest tests/test_recorded_sales.py -v

# Run with markers
pytest -m "not slow" -v
```

---

## 9. Reporting

### 9.1 Report Format

| Metric | Target | Actual |
|--------|--------|--------|
| Unit tests (backend) | 25 | - |
| Unit tests (frontend) | 15 | - |
| Integration tests | 10 | - |
| E2E tests | 5 | - |
| Backend coverage | 80% | - |
| Frontend coverage | 70% | - |

### 9.2 Bug Tracking

| ID | Description | Priority | Status |
|----|-------------|----------|--------|
| - | - | - | - |

---

## Change History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-06 | AI Assistant | Initial version |
