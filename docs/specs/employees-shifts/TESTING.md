# Test Plan: Employees & Shifts Management

## Metadata

| Field | Value |
|-------|-------|
| **Author** | AI Assistant |
| **Created** | 2026-01-04 |
| **Version** | 1.0 |
| **Functional Specification** | [Link](./README.md) |
| **Technical Specification** | [Link](./TECHNICAL.md) |
| **BDD Scenarios** | [Link](./scenarios.feature) |

---

## 1. Test Scope

### 1.1 Testing Objectives
- Verify position CRUD operations with hourly rate management
- Verify employee CRUD operations with position assignment and rate override
- Verify shift assignment functionality linked to daily records
- Verify wage transaction creation with employee linkage
- Verify wage analytics calculations and period comparisons
- Ensure data integrity across all related entities

### 1.2 In Scope
- [ ] Position management (create, read, update, delete)
- [ ] Employee management (create, read, update, deactivate, activate)
- [ ] Shift assignment to daily records
- [ ] Wage transaction creation with employee selection
- [ ] Wage analytics aggregation and reporting
- [ ] Validation rules and error handling
- [ ] UI components for settings, daily operations, and reports

### 1.3 Out of Scope
- Authentication/Authorization testing (single-tenant for now)
- Performance testing under load (basic performance only)
- Mobile responsiveness (desktop-first)

---

## 2. Testing Strategy

### 2.1 Test Levels

| Level | Coverage | Tools |
|-------|----------|-------|
| Unit | 80% | pytest, vitest |
| Integration | 70% | pytest, TestClient |
| E2E | 60% | Playwright |
| Manual | Critical paths | - |

### 2.2 Entry Criteria
- [ ] Specification approved
- [ ] Test environment configured (PostgreSQL test database)
- [ ] Test data fixtures prepared
- [ ] All dependencies installed

### 2.3 Exit Criteria
- [ ] All critical and high priority tests passed
- [ ] Code coverage >= 80% for backend, >= 70% for frontend
- [ ] No critical or high severity bugs open
- [ ] All BDD scenarios passing

---

## 3. Test Cases

### 3.1 Unit Tests (Backend)

#### TC-UNIT-001: PositionService.create() - Success
**Component:** `PositionService`
**Method:** `create`
**Description:** Creating a new position with valid data

**Input Data:**
```python
{
    "name": "Kucharz",
    "hourly_rate": Decimal("25.00")
}
```

**Expected Result:**
```python
Position(
    id=1,
    name="Kucharz",
    hourly_rate=Decimal("25.00"),
    created_at=datetime(...)
)
```

**Test Code:**
```python
def test_create_position_success(db_session):
    service = PositionService(db_session)
    data = PositionCreate(name="Kucharz", hourly_rate=Decimal("25.00"))

    result = service.create(data)

    assert result.id is not None
    assert result.name == "Kucharz"
    assert result.hourly_rate == Decimal("25.00")
```

---

#### TC-UNIT-002: PositionService.create() - Duplicate Name
**Component:** `PositionService`
**Method:** `create`
**Description:** Error when creating position with existing name

**Input Data:**
```python
{
    "name": "Kucharz",  # Already exists
    "hourly_rate": Decimal("30.00")
}
```

**Expected Result:** `ValueError` with message "Stanowisko o tej nazwie juz istnieje"

**Test Code:**
```python
def test_create_position_duplicate_name(db_session, sample_position):
    service = PositionService(db_session)
    data = PositionCreate(name=sample_position.name, hourly_rate=Decimal("30.00"))

    with pytest.raises(ValueError) as exc_info:
        service.create(data)

    assert "Stanowisko o tej nazwie juz istnieje" in str(exc_info.value)
```

---

#### TC-UNIT-003: PositionService.delete() - Has Employees
**Component:** `PositionService`
**Method:** `delete`
**Description:** Error when deleting position with assigned employees

**Test Code:**
```python
def test_delete_position_with_employees(db_session, sample_position, sample_employee):
    service = PositionService(db_session)

    with pytest.raises(ValueError) as exc_info:
        service.delete(sample_position.id)

    assert "Nie mozna usunac stanowiska z przypisanymi pracownikami" in str(exc_info.value)
```

---

#### TC-UNIT-004: Employee.effective_hourly_rate - Override
**Component:** `Employee`
**Property:** `effective_hourly_rate`
**Description:** Returns override rate when set

**Test Code:**
```python
def test_employee_effective_rate_with_override(db_session, sample_position):
    employee = Employee(
        name="Jan Kowalski",
        position_id=sample_position.id,
        hourly_rate_override=Decimal("27.00")
    )

    assert employee.effective_hourly_rate == Decimal("27.00")
```

---

#### TC-UNIT-005: Employee.effective_hourly_rate - Position Default
**Component:** `Employee`
**Property:** `effective_hourly_rate`
**Description:** Returns position rate when no override

**Test Code:**
```python
def test_employee_effective_rate_position_default(db_session, sample_position):
    employee = Employee(
        name="Anna Nowak",
        position_id=sample_position.id,
        hourly_rate_override=None
    )
    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)

    assert employee.effective_hourly_rate == sample_position.hourly_rate
```

---

#### TC-UNIT-006: ShiftAssignment.hours_worked - Calculation
**Component:** `ShiftAssignment`
**Property:** `hours_worked`
**Description:** Correctly calculates hours from start/end time

**Test Code:**
```python
def test_shift_hours_worked_calculation():
    from datetime import time

    shift = ShiftAssignment(
        start_time=time(8, 0),
        end_time=time(16, 30)
    )

    assert shift.hours_worked == 8.5
```

---

#### TC-UNIT-007: ShiftAssignmentCreate - Time Validation
**Component:** `ShiftAssignmentCreate`
**Method:** `validate_end_time`
**Description:** Error when end_time before start_time

**Test Code:**
```python
def test_shift_time_validation_error():
    from datetime import time

    with pytest.raises(ValueError) as exc_info:
        ShiftAssignmentCreate(
            employee_id=1,
            start_time=time(16, 0),
            end_time=time(8, 0)
        )

    assert "Godzina zakonczenia musi byc po godzinie rozpoczecia" in str(exc_info.value)
```

---

### 3.2 Unit Tests (Frontend)

#### TC-UNIT-FE-001: PositionList Component
**Component:** `PositionList`
**Description:** Renders list of positions with rates

**Test Code:**
```typescript
describe('PositionList', () => {
  it('renders positions with hourly rates', () => {
    const positions = [
      { id: 1, name: 'Kucharz', hourlyRate: 25.00, employeeCount: 2 },
      { id: 2, name: 'Kasjer', hourlyRate: 22.00, employeeCount: 1 }
    ];

    render(<PositionList positions={positions} />);

    expect(screen.getByText('Kucharz')).toBeInTheDocument();
    expect(screen.getByText('25,00 PLN/h')).toBeInTheDocument();
    expect(screen.getByText('Kasjer')).toBeInTheDocument();
  });
});
```

---

#### TC-UNIT-FE-002: EmployeeForm - Position Dropdown
**Component:** `EmployeeForm`
**Description:** Shows position dropdown with default rate hint

**Test Code:**
```typescript
describe('EmployeeForm', () => {
  it('shows position default rate as placeholder', async () => {
    const positions = [
      { id: 1, name: 'Kucharz', hourlyRate: 25.00 }
    ];

    render(<EmployeeForm positions={positions} />);

    await userEvent.selectOptions(
      screen.getByLabelText('Stanowisko'),
      'Kucharz'
    );

    expect(screen.getByPlaceholderText('25,00 (domyslna)')).toBeInTheDocument();
  });
});
```

---

#### TC-UNIT-FE-003: ShiftRow - Hours Calculation Display
**Component:** `ShiftRow`
**Description:** Displays calculated hours from time inputs

**Test Code:**
```typescript
describe('ShiftRow', () => {
  it('displays calculated hours worked', () => {
    const shift = {
      id: 1,
      employeeId: 1,
      employeeName: 'Jan Kowalski',
      startTime: '08:00',
      endTime: '16:00',
      hoursWorked: 8.0,
      hourlyRate: 25.00
    };

    render(<ShiftRow shift={shift} />);

    expect(screen.getByText('8.0 h')).toBeInTheDocument();
  });
});
```

---

### 3.3 Integration Tests (API)

#### TC-INT-001: POST /api/v1/positions - Success
**Endpoint:** `POST /api/v1/positions`
**Description:** Creating a new position

**Request:**
```http
POST /api/v1/positions
Content-Type: application/json

{
    "name": "Kucharz",
    "hourly_rate": 25.00
}
```

**Expected Response (201):**
```json
{
    "id": 1,
    "name": "Kucharz",
    "hourly_rate": 25.00,
    "employee_count": 0,
    "created_at": "2026-01-04T12:00:00Z"
}
```

**Test Code:**
```python
def test_create_position_success(client: TestClient):
    response = client.post(
        "/api/v1/positions",
        json={"name": "Kucharz", "hourly_rate": 25.00}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Kucharz"
    assert data["hourly_rate"] == 25.00
    assert data["employee_count"] == 0
```

---

#### TC-INT-002: DELETE /api/v1/positions/{id} - With Employees
**Endpoint:** `DELETE /api/v1/positions/1`
**Description:** Error when position has employees

**Expected Response (400):**
```json
{
    "detail": "Nie mozna usunac stanowiska z przypisanymi pracownikami"
}
```

**Test Code:**
```python
def test_delete_position_with_employees(client: TestClient, sample_position, sample_employee):
    response = client.delete(f"/api/v1/positions/{sample_position.id}")

    assert response.status_code == 400
    assert "Nie mozna usunac" in response.json()["detail"]
```

---

#### TC-INT-003: POST /api/v1/employees - With Rate Override
**Endpoint:** `POST /api/v1/employees`
**Description:** Creating employee with custom hourly rate

**Request:**
```http
POST /api/v1/employees
Content-Type: application/json

{
    "name": "Jan Kowalski",
    "position_id": 1,
    "hourly_rate": 27.00,
    "is_active": true
}
```

**Expected Response (201):**
```json
{
    "id": 1,
    "name": "Jan Kowalski",
    "position_id": 1,
    "position_name": "Kucharz",
    "hourly_rate": 27.00,
    "is_active": true,
    "created_at": "2026-01-04T12:00:00Z"
}
```

---

#### TC-INT-004: GET /api/v1/employees - Filter Active Only
**Endpoint:** `GET /api/v1/employees`
**Description:** Returns only active employees by default

**Test Code:**
```python
def test_get_employees_active_only(client: TestClient, active_employee, inactive_employee):
    response = client.get("/api/v1/employees")

    assert response.status_code == 200
    data = response.json()
    names = [e["name"] for e in data]
    assert active_employee.name in names
    assert inactive_employee.name not in names
```

---

#### TC-INT-005: GET /api/v1/employees?include_inactive=true
**Endpoint:** `GET /api/v1/employees?include_inactive=true`
**Description:** Returns all employees including inactive

**Test Code:**
```python
def test_get_employees_include_inactive(client: TestClient, active_employee, inactive_employee):
    response = client.get("/api/v1/employees?include_inactive=true")

    assert response.status_code == 200
    data = response.json()
    names = [e["name"] for e in data]
    assert active_employee.name in names
    assert inactive_employee.name in names
```

---

#### TC-INT-006: POST /api/v1/daily-records/{id}/shifts - Success
**Endpoint:** `POST /api/v1/daily-records/1/shifts`
**Description:** Adding employee to shift

**Request:**
```http
POST /api/v1/daily-records/1/shifts
Content-Type: application/json

{
    "employee_id": 1,
    "start_time": "08:00",
    "end_time": "16:00"
}
```

**Expected Response (201):**
```json
{
    "id": 1,
    "employee_id": 1,
    "employee_name": "Jan Kowalski",
    "start_time": "08:00",
    "end_time": "16:00",
    "hours_worked": 8.0,
    "hourly_rate": 27.00
}
```

---

#### TC-INT-007: POST /api/v1/daily-records/{id}/shifts - Invalid Times
**Endpoint:** `POST /api/v1/daily-records/1/shifts`
**Description:** Error with end time before start time

**Request:**
```http
POST /api/v1/daily-records/1/shifts
Content-Type: application/json

{
    "employee_id": 1,
    "start_time": "16:00",
    "end_time": "08:00"
}
```

**Expected Response (400):**
```json
{
    "detail": "Godzina zakonczenia musi byc po godzinie rozpoczecia"
}
```

---

#### TC-INT-008: POST /api/v1/daily-records/{id}/shifts - Day Closed
**Endpoint:** `POST /api/v1/daily-records/1/shifts`
**Description:** Error when trying to add shift to closed day

**Expected Response (400):**
```json
{
    "detail": "Nie mozna modyfikowac zmian dla zamknietego dnia"
}
```

---

#### TC-INT-009: GET /api/v1/analytics/wages - Monthly Summary
**Endpoint:** `GET /api/v1/analytics/wages?month=1&year=2026`
**Description:** Get wage analytics for January 2026

**Expected Response (200):**
```json
{
    "summary": {
        "total_wages": 15000.00,
        "total_hours": 520.5,
        "avg_cost_per_hour": 28.82
    },
    "previous_month_summary": {
        "total_wages": 14200.00,
        "total_hours": 500.0,
        "avg_cost_per_hour": 28.40
    },
    "by_employee": [
        {
            "employee_id": 1,
            "employee_name": "Jan Kowalski",
            "position_name": "Kucharz",
            "hours_worked": 168.0,
            "wages_paid": 4536.00,
            "cost_per_hour": 27.00,
            "previous_month_wages": 4320.00,
            "change_percent": 5.0
        }
    ]
}
```

---

### 3.4 E2E Tests

#### TC-E2E-001: Full Position Creation Flow
**Description:** Create a new position through the UI

**Steps:**
1. Open Settings page (`/settings`)
2. Click "Dodaj stanowisko" button
3. Fill form:
   - Nazwa: "Kucharz"
   - Stawka godzinowa: "25.00"
4. Click "Zapisz"
5. Verify "Kucharz" appears in positions list

**Test Code (Playwright):**
```typescript
test('create new position', async ({ page }) => {
  await page.goto('/settings');

  await page.click('button:has-text("Dodaj stanowisko")');
  await page.fill('input[name="name"]', 'Kucharz');
  await page.fill('input[name="hourlyRate"]', '25.00');
  await page.click('button:has-text("Zapisz")');

  await expect(page.locator('text=Kucharz')).toBeVisible();
  await expect(page.locator('text=25,00 PLN/h')).toBeVisible();
});
```

---

#### TC-E2E-002: Employee Creation with Position
**Description:** Create employee and verify rate inheritance

**Steps:**
1. Ensure position "Kasjer" exists with rate 22.00
2. Click "Dodaj pracownika"
3. Fill:
   - Imie i nazwisko: "Anna Nowak"
   - Stanowisko: "Kasjer"
   - Leave rate empty
4. Click "Zapisz"
5. Verify employee shows rate 22.00

**Test Code (Playwright):**
```typescript
test('create employee inherits position rate', async ({ page }) => {
  await page.goto('/settings');

  await page.click('button:has-text("Dodaj pracownika")');
  await page.fill('input[name="name"]', 'Anna Nowak');
  await page.selectOption('select[name="positionId"]', { label: 'Kasjer' });
  await page.click('button:has-text("Zapisz")');

  const employeeRow = page.locator('tr', { hasText: 'Anna Nowak' });
  await expect(employeeRow.locator('text=22,00 PLN/h')).toBeVisible();
});
```

---

#### TC-E2E-003: Shift Assignment Flow
**Description:** Add employee to daily shift

**Steps:**
1. Open day if not open
2. Go to Daily Operations page
3. Click "Dodaj pracownika do zmiany"
4. Select employee "Jan Kowalski"
5. Set start time: 08:00
6. Set end time: 16:00
7. Click "Dodaj"
8. Verify shift appears with 8.0 hours

**Test Code (Playwright):**
```typescript
test('add employee to shift', async ({ page }) => {
  await page.goto('/daily-operations');

  await page.click('button:has-text("Dodaj pracownika do zmiany")');
  await page.selectOption('select[name="employeeId"]', { label: 'Jan Kowalski' });
  await page.fill('input[name="startTime"]', '08:00');
  await page.fill('input[name="endTime"]', '16:00');
  await page.click('button:has-text("Dodaj")');

  await expect(page.locator('text=Jan Kowalski')).toBeVisible();
  await expect(page.locator('text=8.0 h')).toBeVisible();
});
```

---

#### TC-E2E-004: Cannot Close Day Without Employees
**Description:** Verify validation prevents closing day without shifts

**Steps:**
1. Open a new day with no employees
2. Try to click "Zamknij dzien"
3. Verify warning message appears
4. Verify day remains open

**Test Code (Playwright):**
```typescript
test('cannot close day without employees', async ({ page }) => {
  await page.goto('/daily-operations');

  await page.click('button:has-text("Zamknij dzien")');

  await expect(page.locator('text=Musisz dodac przynajmniej jednego pracownika')).toBeVisible();
  await expect(page.locator('button:has-text("Zamknij dzien")')).toBeVisible();
});
```

---

#### TC-E2E-005: Wage Analytics View
**Description:** View wage analytics for current month

**Steps:**
1. Go to Reports page
2. Select "Wynagrodzenia" tab
3. Verify summary cards display
4. Verify employee breakdown table displays

**Test Code (Playwright):**
```typescript
test('view wage analytics', async ({ page }) => {
  await page.goto('/reports');

  await page.click('button:has-text("Wynagrodzenia")');

  await expect(page.locator('[data-testid="total-wages"]')).toBeVisible();
  await expect(page.locator('[data-testid="total-hours"]')).toBeVisible();
  await expect(page.locator('[data-testid="avg-cost"]')).toBeVisible();
  await expect(page.locator('table')).toBeVisible();
});
```

---

## 4. Test Data

### 4.1 Fixtures

```python
@pytest.fixture
def sample_position(db_session):
    """Creates a sample position for tests."""
    position = Position(
        name="Kucharz",
        hourly_rate=Decimal("25.00")
    )
    db_session.add(position)
    db_session.commit()
    return position


@pytest.fixture
def sample_employee(db_session, sample_position):
    """Creates a sample employee for tests."""
    employee = Employee(
        name="Jan Kowalski",
        position_id=sample_position.id,
        hourly_rate_override=Decimal("27.00"),
        is_active=True
    )
    db_session.add(employee)
    db_session.commit()
    return employee


@pytest.fixture
def inactive_employee(db_session, sample_position):
    """Creates an inactive employee for tests."""
    employee = Employee(
        name="Anna Nowak",
        position_id=sample_position.id,
        is_active=False
    )
    db_session.add(employee)
    db_session.commit()
    return employee


@pytest.fixture
def sample_daily_record_open(db_session):
    """Creates an open daily record for tests."""
    from datetime import date
    record = DailyRecord(
        date=date.today(),
        status=DayStatus.OPEN
    )
    db_session.add(record)
    db_session.commit()
    return record


@pytest.fixture
def sample_shift(db_session, sample_daily_record_open, sample_employee):
    """Creates a sample shift assignment for tests."""
    from datetime import time
    shift = ShiftAssignment(
        daily_record_id=sample_daily_record_open.id,
        employee_id=sample_employee.id,
        start_time=time(8, 0),
        end_time=time(16, 0)
    )
    db_session.add(shift)
    db_session.commit()
    return shift
```

### 4.2 Test Data Sets

| ID | Position | Rate | Test Purpose |
|----|----------|------|--------------|
| 1 | "Kucharz" | 25.00 | Standard cook |
| 2 | "Kasjer" | 22.00 | Standard cashier |
| 3 | "Manager" | 35.00 | Higher rate |
| 4 | "Pomocnik" | 18.50 | Entry level |

| ID | Employee | Position | Rate Override | Active | Test Purpose |
|----|----------|----------|---------------|--------|--------------|
| 1 | "Jan Kowalski" | Kucharz | 27.00 | Yes | With override |
| 2 | "Anna Nowak" | Kasjer | NULL | Yes | Position default |
| 3 | "Piotr Nowak" | Kucharz | NULL | No | Inactive |

---

## 5. Edge Cases

| ID | Case | Expected Behavior | Status |
|----|------|------------------|--------|
| EC-001 | Delete position with employees | Error message | [ ] |
| EC-002 | Employee with NULL rate override | Use position rate | [ ] |
| EC-003 | Shift end time = start time | Validation error | [ ] |
| EC-004 | Deactivate employee on current shift | Keep in shift, hide from dropdown | [ ] |
| EC-005 | Close day with no shifts | Validation warning | [ ] |
| EC-006 | Create wage transaction for "Wynagrodzenia" category | Show employee dropdown | [ ] |
| EC-007 | Calculate wages with no shifts | Show info message | [ ] |
| EC-008 | Same employee added twice to day | Unique constraint error | [ ] |
| EC-009 | Analytics for month with no data | Show zeros | [ ] |

---

## 6. Performance Tests

### 6.1 Scenarios

| Scenario | Expected Time | Limit |
|----------|---------------|-------|
| List 100 employees | < 300ms | 500ms |
| List 50 positions | < 200ms | 300ms |
| Get shifts for daily record | < 100ms | 200ms |
| Calculate monthly analytics | < 800ms | 1000ms |

### 6.2 Load Tests

```python
def test_list_employees_performance(client: TestClient, benchmark, many_employees):
    result = benchmark(
        lambda: client.get("/api/v1/employees?include_inactive=true")
    )

    assert result.stats.mean < 0.3  # < 300ms
```

---

## 7. Security Tests

| Test | Description | Status |
|------|-------------|--------|
| SEC-001 | SQL Injection in position name | [ ] |
| SEC-002 | XSS in employee name | [ ] |
| SEC-003 | Invalid employee_id in shift | [ ] |
| SEC-004 | Negative hourly rate | [ ] |
| SEC-005 | Future date daily record access | [ ] |

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
# Backend unit and integration tests
cd backend
pytest tests/ --cov=app --cov-report=html -v

# Run specific test file
pytest tests/test_positions.py -v

# Frontend unit tests
cd frontend
npm run test

# Frontend with coverage
npm run test:coverage

# E2E tests
npm run test:e2e

# E2E with UI
npm run test:e2e -- --headed
```

---

## 9. Reporting

### 9.1 Report Format

| Metric | Value |
|--------|-------|
| Tests executed | - |
| Tests passed | - |
| Tests failed | - |
| Backend coverage | - % |
| Frontend coverage | - % |

### 9.2 Found Bugs

| ID | Description | Priority | Status |
|----|-------------|----------|--------|
| - | - | - | - |

---

## Change History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-04 | AI Assistant | Initial version |
