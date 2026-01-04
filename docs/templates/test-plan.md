# Test Plan: {Feature Name}

## Metadata

| Field | Value |
|-------|-------|
| **Author** | {author} |
| **Created** | {YYYY-MM-DD} |
| **Version** | 1.0 |
| **Functional Specification** | [Link](./README.md) |
| **Technical Specification** | [Link](./TECHNICAL.md) |
| **BDD Scenarios** | [Link](./scenarios.feature) |

---

## 1. Test Scope

### 1.1 Testing Objectives
- {objective 1}
- {objective 2}
- {objective 3}

### 1.2 In Scope
- [ ] {item to test 1}
- [ ] {item to test 2}

### 1.3 Out of Scope
- {item out of scope}

---

## 2. Testing Strategy

### 2.1 Test Levels

| Level | Coverage | Tools |
|-------|----------|-------|
| Unit | {%} | pytest, vitest |
| Integration | {%} | pytest, TestClient |
| E2E | {%} | Playwright / Cypress |
| Manual | {%} | - |

### 2.2 Entry Criteria
- [ ] Specification approved
- [ ] Test environment configured
- [ ] Test data prepared

### 2.3 Exit Criteria
- [ ] All critical tests passed
- [ ] Code coverage >= {X}%
- [ ] No critical or high bugs

---

## 3. Test Cases

### 3.1 Unit Tests (Backend)

#### TC-UNIT-001: {Test Name}
**Component:** `{service_name}`
**Method:** `{method_name}`
**Description:** {What we're testing}

**Input Data:**
```python
{
    "field1": "value1",
    "field2": 123
}
```

**Expected Result:**
```python
{
    "id": 1,
    "field1": "value1",
    "field2": 123
}
```

**Test Code:**
```python
def test_{test_name}():
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

#### TC-UNIT-002: {Test Name - error validation}
**Component:** `{service_name}`
**Method:** `{method_name}`
**Description:** Error validation for {case}

**Input Data:**
```python
{
    "field1": "",  # Empty field - should cause error
}
```

**Expected Result:** `ValidationError` with message "{message}"

**Test Code:**
```python
def test_{test_name}_validation_error():
    with pytest.raises(ValidationError) as exc_info:
        {Name}Create(field1="")

    assert "field1" in str(exc_info.value)
```

---

### 3.2 Unit Tests (Frontend)

#### TC-UNIT-FE-001: {Component Test Name}
**Component:** `{ComponentName}`
**Description:** {What we're testing}

**Test Code:**
```typescript
describe('{ComponentName}', () => {
  it('{test description}', () => {
    render(<{ComponentName} prop1="value" />);

    expect(screen.getByText('{text}')).toBeInTheDocument();
  });
});
```

---

### 3.3 Integration Tests (API)

#### TC-INT-001: POST /api/v1/{resource} - Success
**Endpoint:** `POST /api/v1/{resource}`
**Description:** Creating a new {object}

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

**Test Code:**
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

#### TC-INT-002: POST /api/v1/{resource} - Validation Error
**Endpoint:** `POST /api/v1/{resource}`
**Description:** Error with invalid data

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

#### TC-INT-003: GET /api/v1/{resource}/{id} - Success
**Endpoint:** `GET /api/v1/{resource}/{id}`
**Description:** Getting {object} by ID

**Test Code:**
```python
def test_get_{resource}_by_id(client: TestClient, sample_{resource}):
    response = client.get(f"/api/v1/{resource}/{sample_{resource}.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_{resource}.id
```

---

#### TC-INT-004: GET /api/v1/{resource}/{id} - Not Found
**Endpoint:** `GET /api/v1/{resource}/99999`
**Description:** 404 for non-existent ID

**Expected Response (404):**
```json
{
    "detail": "Nie znaleziono"
}
```

---

### 3.4 E2E Tests

#### TC-E2E-001: {Full User Flow}
**Description:** {End-to-end scenario description}

**Steps:**
1. Open page {URL}
2. Click button "{name}"
3. Fill out form:
   - Field "{field1}": "{value1}"
   - Field "{field2}": "{value2}"
4. Click "Save"
5. Verify that {object} appears in the list

**Test Code (Playwright):**
```typescript
test('{test name}', async ({ page }) => {
  await page.goto('/api/v1/{resource}');

  await page.click('button:has-text("Dodaj")');
  await page.fill('input[name="field1"]', 'Test Value');
  await page.click('button:has-text("Zapisz")');

  await expect(page.locator('text=Test Value')).toBeVisible();
});
```

---

## 4. Test Data

### 4.1 Fixtures

```python
@pytest.fixture
def sample_{resource}(db_session):
    """Creates a sample {object} for tests."""
    {resource} = {Model}(
        field1="Test",
        field2=123
    )
    db_session.add({resource})
    db_session.commit()
    return {resource}
```

### 4.2 Test Data

| ID | field1 | field2 | Test Purpose |
|----|--------|--------|--------------|
| 1 | "Test 1" | 100 | Standard case |
| 2 | "Test 2" | 0 | Edge value |
| 3 | "A" * 255 | 999999 | Maximum values |

---

## 5. Edge Cases

| ID | Case | Expected Behavior | Status |
|----|------|------------------|--------|
| EC-001 | Empty data | Validation message | [ ] |
| EC-002 | Very long text | Truncation or error | [ ] |
| EC-003 | Special characters | Correct save | [ ] |
| EC-004 | Concurrent editing | Conflict or merge | [ ] |

---

## 6. Performance Tests

### 6.1 Scenarios

| Scenario | Expected Time | Limit |
|----------|---------------|-------|
| List of 100 {objects} | < 500ms | 1s |
| Creating {object} | < 200ms | 500ms |
| Search | < 300ms | 1s |

### 6.2 Load Tests

```python
def test_list_{resources}_performance(client: TestClient, benchmark):
    # Setup: Create 1000 {resources}

    result = benchmark(
        lambda: client.get("/api/v1/{resources}")
    )

    assert result.stats.mean < 0.5  # < 500ms
```

---

## 7. Security Tests

| Test | Description | Status |
|------|-------------|--------|
| SEC-001 | SQL Injection | [ ] |
| SEC-002 | XSS | [ ] |
| SEC-003 | CSRF | [ ] |
| SEC-004 | Authorization | [ ] |

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
```

### 8.2 Running Tests

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

## 9. Reporting

### 9.1 Report Format

| Metric | Value |
|--------|-------|
| Tests executed | {X} |
| Tests passed | {Y} |
| Tests failed | {Z} |
| Code coverage | {%} |

### 9.2 Found Bugs

| ID | Description | Priority | Status |
|----|-------------|----------|--------|
| BUG-001 | {description} | Critical/High/Medium/Low | Open/Fixed |

---

## Change History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | {date} | {author} | Initial version |
