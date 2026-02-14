# Test Plan: Unified Day Operations

## Metadata

| Field | Value |
|-------|-------|
| **Author** | AI Assistant |
| **Created** | 2026-01-05 |
| **Version** | 1.0 |
| **Functional Specification** | [Link](./README.md) |
| **Technical Specification** | [Link](./TECHNICAL.md) |
| **BDD Scenarios** | [Link](./scenarios.feature) |

---

## 1. Test Scope

### 1.1 Testing Objectives
- Verify shift template CRUD operations work correctly
- Validate weekly schedule generation with template + override logic
- Ensure Day Operations Wizard guides users through complete day lifecycle
- Confirm inventory calculations are accurate (opening + transfers + deliveries - spoilage - closing = used)
- Validate sales auto-calculation from ingredient usage

### 1.2 In Scope
- [ ] Shift Template API endpoints
- [ ] Shift Schedule Override API endpoints
- [ ] Weekly Schedule generation logic
- [ ] Day Operations Wizard state management
- [ ] Opening step: shift confirmation + inventory entry
- [ ] Mid-day step: transfers, spoilage, deliveries
- [ ] Closing step: closing inventory + sales calculation
- [ ] Inventory location tracking (warehouse vs kitchen)
- [ ] Frontend wizard components
- [ ] Frontend shift scheduling UI

### 1.3 Out of Scope
- Authentication/authorization (existing functionality)
- Multi-location support
- Mobile responsiveness (deferred)
- Performance testing beyond basic benchmarks

---

## 2. Testing Strategy

### 2.1 Test Levels

| Level | Coverage | Tools |
|-------|----------|-------|
| Unit | 80% | pytest, vitest |
| Integration | 70% | pytest, TestClient |
| E2E | Key flows | Playwright |
| Manual | Edge cases | - |

### 2.2 Entry Criteria
- [ ] Specification approved
- [ ] Test environment configured
- [ ] Test data prepared
- [ ] Database migrations applied

### 2.3 Exit Criteria
- [ ] All critical tests passed
- [ ] Code coverage >= 80% (backend), >= 70% (frontend)
- [ ] No critical or high priority bugs
- [ ] All BDD scenarios validated

---

## 3. Test Cases

### 3.1 Unit Tests (Backend)

#### TC-UNIT-001: Create Shift Template
**Component:** `ShiftTemplateService`
**Method:** `create()`
**Description:** Create a valid shift template

**Input Data:**
```python
{
    "employee_id": 1,
    "day_of_week": 0,
    "start_time": "08:00",
    "end_time": "16:00"
}
```

**Expected Result:** Template created with correct values

**Test Code:**
```python
def test_create_shift_template_success(db_session, sample_employee):
    service = ShiftTemplateService(db_session)
    data = ShiftTemplateCreate(
        employee_id=sample_employee.id,
        day_of_week=0,
        start_time=time(8, 0),
        end_time=time(16, 0)
    )

    result = service.create(data)

    assert result.id is not None
    assert result.employee_id == sample_employee.id
    assert result.day_of_week == 0
    assert result.start_time == time(8, 0)
    assert result.end_time == time(16, 0)
```

---

#### TC-UNIT-002: Prevent Duplicate Template
**Component:** `ShiftTemplateService`
**Method:** `create()`
**Description:** Cannot create duplicate template for same employee + day

**Test Code:**
```python
def test_create_duplicate_template_fails(db_session, sample_employee):
    service = ShiftTemplateService(db_session)
    data = ShiftTemplateCreate(
        employee_id=sample_employee.id,
        day_of_week=0,
        start_time=time(8, 0),
        end_time=time(16, 0)
    )

    service.create(data)  # First - should succeed

    with pytest.raises(IntegrityError):
        service.create(data)  # Second - should fail
```

---

#### TC-UNIT-003: Get Shifts for Date - Template Only
**Component:** `ShiftTemplateService`
**Method:** `get_shifts_for_date()`
**Description:** Returns template shifts when no overrides exist

**Test Code:**
```python
def test_get_shifts_for_date_from_template(db_session, sample_template_monday):
    service = ShiftTemplateService(db_session)
    monday_date = date(2026, 1, 5)  # Monday

    shifts = service.get_shifts_for_date(monday_date)

    assert len(shifts) == 1
    assert shifts[0]['source'] == 'template'
    assert shifts[0]['employee_id'] == sample_template_monday.employee_id
```

---

#### TC-UNIT-004: Get Shifts for Date - With Override
**Component:** `ShiftTemplateService`
**Method:** `get_shifts_for_date()`
**Description:** Override takes precedence over template

**Test Code:**
```python
def test_get_shifts_for_date_with_override(db_session, sample_template_monday, sample_override):
    service = ShiftTemplateService(db_session)
    monday_date = date(2026, 1, 5)

    shifts = service.get_shifts_for_date(monday_date)

    assert len(shifts) == 1
    assert shifts[0]['source'] == 'override'
    assert shifts[0]['start_time'] == sample_override.start_time
```

---

#### TC-UNIT-005: Get Shifts for Date - Day Off
**Component:** `ShiftTemplateService`
**Method:** `get_shifts_for_date()`
**Description:** Employee with day_off override is excluded

**Test Code:**
```python
def test_get_shifts_for_date_day_off(db_session, sample_template_monday, sample_day_off_override):
    service = ShiftTemplateService(db_session)
    monday_date = date(2026, 1, 5)

    shifts = service.get_shifts_for_date(monday_date)

    assert len(shifts) == 0  # Employee has day off
```

---

#### TC-UNIT-006: Calculate Sales Preview
**Component:** `DayWizardService`
**Method:** `calculate_sales_preview()`
**Description:** Correct calculation of ingredient usage

**Test Code:**
```python
def test_calculate_sales_preview(db_session, day_with_operations):
    service = DayWizardService(db_session)
    closing_inventory = {1: Decimal("38.0"), 2: Decimal("50")}

    result = service.calculate_sales_preview(
        daily_record_id=day_with_operations.id,
        closing_inventory=closing_inventory
    )

    # opening=50 + transfers=20 + deliveries=0 - spoilage=2 - closing=38 = 30 used
    meat_usage = next(i for i in result['ingredients_used'] if i['ingredient_id'] == 1)
    assert meat_usage['used'] == Decimal("30.0")
```

---

#### TC-UNIT-007: Wizard State Determination
**Component:** `DayWizardService`
**Method:** `get_wizard_state()`
**Description:** Correctly determines current wizard step

**Test Code:**
```python
def test_wizard_state_opening_step(db_session, new_daily_record):
    service = DayWizardService(db_session)

    state = service.get_wizard_state(new_daily_record.id)

    assert state.current_step == 'opening'
    assert state.opening.completed == False
    assert state.opening.inventory_entered == False


def test_wizard_state_midday_step(db_session, daily_record_with_opening):
    service = DayWizardService(db_session)

    state = service.get_wizard_state(daily_record_with_opening.id)

    assert state.current_step == 'mid_day'
    assert state.opening.completed == True
```

---

### 3.2 Unit Tests (Frontend)

#### TC-UNIT-FE-001: WizardStepper Component
**Component:** `WizardStepper`
**Description:** Displays correct step indicators

**Test Code:**
```typescript
describe('WizardStepper', () => {
  const steps = [
    { label: 'Otwarcie', key: 'opening' },
    { label: 'Operacje', key: 'mid_day' },
    { label: 'Zamknięcie', key: 'closing' }
  ];

  it('renders all steps', () => {
    render(<WizardStepper steps={steps} activeStep={0} />);

    expect(screen.getByText('Otwarcie')).toBeInTheDocument();
    expect(screen.getByText('Operacje')).toBeInTheDocument();
    expect(screen.getByText('Zamknięcie')).toBeInTheDocument();
  });

  it('marks active step correctly', () => {
    render(<WizardStepper steps={steps} activeStep={1} />);

    const midDayStep = screen.getByText('Operacje').closest('div');
    expect(midDayStep).toHaveClass('active');
  });

  it('marks completed steps', () => {
    render(<WizardStepper steps={steps} activeStep={2} />);

    const openingStep = screen.getByText('Otwarcie').closest('div');
    expect(openingStep).toHaveClass('completed');
  });
});
```

---

#### TC-UNIT-FE-002: OpeningStep Shift List
**Component:** `OpeningStep`
**Description:** Displays suggested shifts and allows confirmation

**Test Code:**
```typescript
describe('OpeningStep', () => {
  const mockSuggestedShifts = [
    { employeeId: 1, employeeName: 'Anna Kowalska', startTime: '08:00', endTime: '16:00', source: 'template' },
    { employeeId: 2, employeeName: 'Jan Nowak', startTime: '10:00', endTime: '18:00', source: 'template' }
  ];

  beforeEach(() => {
    vi.mocked(getSuggestedShifts).mockResolvedValue({ suggested_shifts: mockSuggestedShifts });
  });

  it('displays suggested shifts from schedule', async () => {
    render(<OpeningStep dailyRecordId={1} date="2026-01-05" onComplete={() => {}} />);

    await waitFor(() => {
      expect(screen.getByText('Anna Kowalska')).toBeInTheDocument();
      expect(screen.getByText('Jan Nowak')).toBeInTheDocument();
    });
  });

  it('allows removing a shift', async () => {
    render(<OpeningStep dailyRecordId={1} date="2026-01-05" onComplete={() => {}} />);

    await waitFor(() => {
      expect(screen.getByText('Anna Kowalska')).toBeInTheDocument();
    });

    const removeButton = screen.getAllByRole('button', { name: /usuń/i })[0];
    fireEvent.click(removeButton);

    expect(screen.queryByText('Anna Kowalska')).not.toBeInTheDocument();
  });
});
```

---

#### TC-UNIT-FE-003: Closing Inventory Form
**Component:** `ClosingStep`
**Description:** Validates closing inventory input and shows calculation

**Test Code:**
```typescript
describe('ClosingStep', () => {
  it('shows calculated usage after entering closing inventory', async () => {
    vi.mocked(getSalesPreview).mockResolvedValue({
      ingredients_used: [
        { ingredient_id: 1, ingredient_name: 'Mięso kebab', opening: 50, transfers: 20, deliveries: 0, spoilage: 2, closing: 38, used: 30 }
      ],
      calculated_sales: [],
      summary: { total_revenue_pln: 1250 },
      warnings: []
    });

    render(<ClosingStep dailyRecordId={1} onComplete={() => {}} />);

    const input = screen.getByLabelText('Mięso kebab');
    fireEvent.change(input, { target: { value: '38' } });
    fireEvent.blur(input);

    await waitFor(() => {
      expect(screen.getByText('30')).toBeInTheDocument(); // used quantity
    });
  });
});
```

---

### 3.3 Integration Tests (API)

#### TC-INT-001: POST /api/v1/shift-templates - Success
**Endpoint:** `POST /api/v1/shift-templates`
**Description:** Create a new shift template

**Request:**
```http
POST /api/v1/shift-templates
Content-Type: application/json

{
    "employee_id": 1,
    "day_of_week": 0,
    "start_time": "08:00",
    "end_time": "16:00"
}
```

**Expected Response (201):**
```json
{
    "id": 1,
    "employee_id": 1,
    "employee_name": "Anna Kowalska",
    "day_of_week": 0,
    "day_name": "Poniedziałek",
    "start_time": "08:00:00",
    "end_time": "16:00:00",
    "created_at": "2026-01-05T12:00:00Z"
}
```

**Test Code:**
```python
def test_create_shift_template_success(client: TestClient, sample_employee):
    response = client.post(
        "/api/v1/shift-templates",
        json={
            "employee_id": sample_employee.id,
            "day_of_week": 0,
            "start_time": "08:00",
            "end_time": "16:00"
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["employee_id"] == sample_employee.id
    assert data["day_name"] == "Poniedziałek"
```

---

#### TC-INT-002: GET /api/v1/shift-schedules/week - Success
**Endpoint:** `GET /api/v1/shift-schedules/week?start_date=2026-01-05`
**Description:** Get weekly schedule with templates and overrides

**Test Code:**
```python
def test_get_weekly_schedule(client: TestClient, sample_templates, sample_override):
    response = client.get("/api/v1/shift-schedules/week?start_date=2026-01-05")

    assert response.status_code == 200
    data = response.json()
    assert data["week_start"] == "2026-01-05"
    assert data["week_end"] == "2026-01-11"
    assert len(data["schedules"]) == 7  # 7 days
```

---

#### TC-INT-003: GET /api/v1/daily-records/{id}/wizard-state
**Endpoint:** `GET /api/v1/daily-records/{id}/wizard-state`
**Description:** Get current wizard state for a day

**Test Code:**
```python
def test_get_wizard_state(client: TestClient, sample_open_day):
    response = client.get(f"/api/v1/daily-records/{sample_open_day.id}/wizard-state")

    assert response.status_code == 200
    data = response.json()
    assert data["daily_record_id"] == sample_open_day.id
    assert data["status"] == "open"
    assert "current_step" in data
    assert "opening" in data
    assert "mid_day" in data
    assert "closing" in data
```

---

#### TC-INT-004: POST /api/v1/daily-records/{id}/complete-opening
**Endpoint:** `POST /api/v1/daily-records/{id}/complete-opening`
**Description:** Complete opening step with shifts and inventory

**Test Code:**
```python
def test_complete_opening(client: TestClient, sample_open_day, sample_employees, sample_ingredients):
    response = client.post(
        f"/api/v1/daily-records/{sample_open_day.id}/complete-opening",
        json={
            "confirmed_shifts": [
                {"employee_id": sample_employees[0].id, "start_time": "08:00", "end_time": "16:00"}
            ],
            "opening_inventory": [
                {"ingredient_id": sample_ingredients[0].id, "quantity": 50.0, "location": "kitchen"}
            ]
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["opening"]["completed"] == True
    assert data["opening"]["shifts_confirmed"] == 1
    assert data["opening"]["inventory_entered"] == True
```

---

#### TC-INT-005: GET /api/v1/daily-records/{id}/sales-preview
**Endpoint:** `GET /api/v1/daily-records/{id}/sales-preview`
**Description:** Calculate sales preview from closing inventory

**Test Code:**
```python
def test_get_sales_preview(client: TestClient, day_with_all_operations):
    response = client.get(
        f"/api/v1/daily-records/{day_with_all_operations.id}/sales-preview",
        params={"closing_inventory[1]": 38.0, "closing_inventory[2]": 50}
    )

    assert response.status_code == 200
    data = response.json()
    assert "ingredients_used" in data
    assert "calculated_sales" in data
    assert "summary" in data
```

---

### 3.4 E2E Tests

#### TC-E2E-001: Complete Day Lifecycle
**Description:** Open day, add operations, close day

**Steps:**
1. Navigate to Daily Operations page
2. Click on date "2026-01-05"
3. Click "Otwórz dzień"
4. Confirm suggested shifts
5. Enter opening inventory
6. Click "Kontynuuj"
7. Add a transfer
8. Click "Przejdź do zamknięcia"
9. Enter closing inventory
10. Click "Zamknij dzień"
11. Verify day summary displayed

**Test Code (Playwright):**
```typescript
test('complete day lifecycle', async ({ page }) => {
  await page.goto('/daily-operations');

  // Open day
  await page.click('text=2026-01-05');
  await page.click('button:has-text("Otwórz dzień")');

  // Step 1: Opening
  await expect(page.locator('text=Krok 1: Otwarcie')).toBeVisible();
  await page.click('button:has-text("Potwierdź wszystkie")');
  await page.fill('input[name="ingredient-1"]', '50');
  await page.click('button:has-text("Kontynuuj")');

  // Step 2: Mid-day
  await expect(page.locator('text=Krok 2: Operacje')).toBeVisible();
  await page.click('button:has-text("Dodaj transfer")');
  await page.selectOption('select[name="ingredient"]', '1');
  await page.fill('input[name="quantity"]', '20');
  await page.click('button:has-text("Zapisz")');
  await page.click('button:has-text("Przejdź do zamknięcia")');

  // Step 3: Closing
  await expect(page.locator('text=Krok 3: Zamknięcie')).toBeVisible();
  await page.fill('input[name="closing-1"]', '38');
  await page.click('button:has-text("Zamknij dzień")');

  // Verify summary
  await expect(page.locator('text=Podsumowanie dnia')).toBeVisible();
  await expect(page.locator('text=zamknięty')).toBeVisible();
});
```

---

#### TC-E2E-002: Shift Template Creation and Usage
**Description:** Create shift template, verify it appears when opening a day

**Test Code (Playwright):**
```typescript
test('shift template auto-populates on day open', async ({ page }) => {
  // Create template
  await page.goto('/settings');
  await page.click('text=Harmonogram zmian');
  await page.click('button:has-text("Dodaj szablon")');
  await page.selectOption('select[name="employee"]', '1');
  await page.selectOption('select[name="dayOfWeek"]', '0'); // Monday
  await page.fill('input[name="startTime"]', '08:00');
  await page.fill('input[name="endTime"]', '16:00');
  await page.click('button:has-text("Zapisz")');

  // Open a Monday
  await page.goto('/daily-operations');
  await page.click('text=2026-01-05'); // Monday
  await page.click('button:has-text("Otwórz dzień")');

  // Verify shift is suggested
  await expect(page.locator('text=Anna Kowalska')).toBeVisible();
  await expect(page.locator('text=08:00 - 16:00')).toBeVisible();
});
```

---

## 4. Test Data

### 4.1 Fixtures

```python
@pytest.fixture
def sample_employee(db_session):
    """Creates a sample employee for tests."""
    employee = Employee(
        name="Anna Kowalska",
        position_id=1,
        hourly_rate_pln=Decimal("25.00"),
        is_active=True
    )
    db_session.add(employee)
    db_session.commit()
    return employee


@pytest.fixture
def sample_template_monday(db_session, sample_employee):
    """Creates a shift template for Monday."""
    template = ShiftTemplate(
        employee_id=sample_employee.id,
        day_of_week=0,
        start_time=time(8, 0),
        end_time=time(16, 0)
    )
    db_session.add(template)
    db_session.commit()
    return template


@pytest.fixture
def day_with_operations(db_session, sample_ingredients):
    """Creates a day with opening inventory, transfers, and spoilage."""
    record = DailyRecord(date=date(2026, 1, 5), status=DayStatus.OPEN)
    db_session.add(record)
    db_session.flush()

    # Opening inventory
    snapshot = InventorySnapshot(
        daily_record_id=record.id,
        ingredient_id=sample_ingredients[0].id,
        quantity=Decimal("50.0"),
        snapshot_type='opening',
        location='kitchen'
    )
    db_session.add(snapshot)

    # Transfer
    transfer = StorageTransfer(
        daily_record_id=record.id,
        ingredient_id=sample_ingredients[0].id,
        quantity=Decimal("20.0"),
        from_location='warehouse',
        to_location='kitchen'
    )
    db_session.add(transfer)

    # Spoilage
    spoilage = Spoilage(
        daily_record_id=record.id,
        ingredient_id=sample_ingredients[0].id,
        quantity=Decimal("2.0"),
        reason='expired'
    )
    db_session.add(spoilage)

    db_session.commit()
    return record
```

### 4.2 Test Data

| ID | Entity | Data | Test Purpose |
|----|--------|------|--------------|
| 1 | Employee | Anna Kowalska, Cook, 25 PLN/h | Standard employee |
| 2 | Employee | Jan Nowak, Helper, 20 PLN/h | Second employee |
| 3 | Ingredient | Mięso kebab, kg | Weight-based ingredient |
| 4 | Ingredient | Chleb pita, szt | Count-based ingredient |
| 5 | ShiftTemplate | Anna, Mon, 08:00-16:00 | Standard template |

---

## 5. Edge Cases

| ID | Case | Expected Behavior | Status |
|----|------|------------------|--------|
| EC-001 | Open day with no templates | Show empty shift list, allow manual add | [ ] |
| EC-002 | Override to day off | Employee excluded from schedule | [ ] |
| EC-003 | Closing inventory > expected | Show warning, allow proceed | [ ] |
| EC-004 | Transfer > warehouse stock | Validation error | [ ] |
| EC-005 | Reopen closed day | Audit log created, wizard in edit mode | [ ] |
| EC-006 | Multiple days open | Both visible in list | [ ] |
| EC-007 | Employee deactivated after template created | Show warning on suggested shift | [ ] |
| EC-008 | Inventory with decimal precision | Handle up to 3 decimal places | [ ] |

---

## 6. Performance Tests

### 6.1 Scenarios

| Scenario | Expected Time | Limit |
|----------|---------------|-------|
| Get weekly schedule (50 employees) | < 200ms | 500ms |
| Calculate sales preview (100 ingredients) | < 500ms | 1s |
| Load wizard state | < 100ms | 200ms |
| Complete opening step | < 300ms | 500ms |

### 6.2 Load Tests

```python
def test_weekly_schedule_performance(client: TestClient, many_employees_with_templates, benchmark):
    result = benchmark(
        lambda: client.get("/api/v1/shift-schedules/week?start_date=2026-01-05")
    )

    assert result.stats.mean < 0.2  # < 200ms


def test_sales_preview_performance(client: TestClient, day_with_many_ingredients, benchmark):
    closing_inventory = {i: 10.0 for i in range(1, 101)}

    result = benchmark(
        lambda: client.get(
            f"/api/v1/daily-records/{day_with_many_ingredients.id}/sales-preview",
            params={f"closing_inventory[{i}]": 10.0 for i in range(1, 101)}
        )
    )

    assert result.stats.mean < 0.5  # < 500ms
```

---

## 7. Security Tests

| Test | Description | Status |
|------|-------------|--------|
| SEC-001 | SQL Injection in schedule query | [ ] |
| SEC-002 | Invalid employee_id in template | [ ] |
| SEC-003 | Access other user's daily record | [ ] |
| SEC-004 | Negative inventory quantities | [ ] |

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
```

### 8.2 Running Tests

```bash
# Backend unit + integration
cd backend
docker compose exec backend pytest tests/ --cov=app --cov-report=html -v

# Frontend unit
cd frontend
npm run test
npm run test:coverage

# E2E (requires running app)
cd frontend
npm run test:e2e

# Run specific test category
docker compose exec backend pytest tests/ -k "shift_template" -v
docker compose exec backend pytest tests/ -k "wizard" -v
```

---

## 9. Reporting

### 9.1 Report Format

| Metric | Value |
|--------|-------|
| Tests executed | TBD |
| Tests passed | TBD |
| Tests failed | TBD |
| Backend coverage | Target: 80% |
| Frontend coverage | Target: 70% |

### 9.2 Found Bugs

| ID | Description | Priority | Status |
|----|-------------|----------|--------|
| - | - | - | - |

---

## Change History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-05 | AI Assistant | Initial version |
