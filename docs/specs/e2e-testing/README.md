# E2E Testing with Playwright

## Status: Ready for Approval
**Created**: 2026-01-06
**Last Updated**: 2026-01-06
**Author**: Claude Code

---

## Overview

This specification defines the implementation of end-to-end (E2E) testing using Playwright for the small-gastro application. E2E tests will validate complete user journeys through the browser, ensuring that multiple system components work together correctly.

## Goals

1. **Validate user journeys** - Test complete workflows from user perspective
2. **Integration verification** - Ensure frontend, backend, and database work together
3. **Regression prevention** - Catch breaking changes before they reach production
4. **Documentation** - Serve as executable documentation of expected behavior

## Non-Goals

- Replace existing unit tests (Vitest/pytest)
- Test individual component behavior in isolation
- Visual regression testing (out of scope for initial implementation)
- Performance/load testing

---

## User Flows to Test

### Priority 1: Day Closing Wizard
The most complex user flow in the application.

| Step | User Action | Expected Result |
|------|-------------|-----------------|
| 1 | Navigate to `/operacje` | Daily operations page loads |
| 2 | Click "Zamknij dzień" | Wizard modal opens at Step 1 |
| 3 | Review opening inventory | Read-only table displays ingredients |
| 4 | Click "Dalej" | Navigate to Step 2 (Events) |
| 5 | Review mid-day events | Deliveries, transfers, spoilage displayed |
| 6 | Click "Dalej" | Navigate to Step 3 (Closing) |
| 7 | Enter closing quantities | Real-time calculations update |
| 8 | Click "Dalej" | Navigate to Step 4 (Confirm) |
| 9 | Review summary, add notes | Financial summary visible |
| 10 | Click "Zamknij dzień" | Day closes, status updates |

**Validation scenarios:**
- Discrepancy levels displayed correctly (text-based)
- Navigation between steps works both forward and backward
- Cannot proceed without required fields
- Negative values rejected in closing quantities

### Priority 2: Menu & Ingredients Management
Product and recipe management workflow.

| Flow | Description |
|------|-------------|
| Create ingredient | Add new ingredient with unit type (kg/szt) |
| Create product | Add product with price in PLN |
| Link ingredients | Assign ingredients to product with quantities |
| Update recipe | Modify ingredient quantities |
| Delete product | Remove product and verify cascade |

### Priority 3: Employee & Shift Management
Staff scheduling workflow.

| Flow | Description |
|------|-------------|
| Create employee | Add employee with basic info |
| Assign position | Link employee to position with wage |
| Create shift template | Define shift with start/end times |
| Assign to shift | Schedule employee for specific date |
| View wage analytics | Verify calculated totals |

### Priority 4: Finances & Categories
Expense and revenue tracking workflow.

| Flow | Description |
|------|-------------|
| Create category hierarchy | Parent → child → grandchild categories |
| Add expense | Create expense under category |
| Add revenue | Record revenue with payment method |
| View dashboard totals | Verify aggregated financials |

---

## Test Data Strategy

### Approach: API Seeding

Tests will prepare data by calling backend API endpoints directly before UI interactions.

**Rationale:**
- Fast execution (no UI overhead for setup)
- Reliable and deterministic
- Tests business logic through API
- UI tests focus on UI behavior

**Implementation:**
```typescript
// Example: Create ingredient via API
async function createIngredient(request: APIRequestContext, data: IngredientCreate) {
  const response = await request.post('/api/v1/ingredients', { data });
  return response.json();
}
```

### Test Isolation: Fresh Database per Test File

Each test file starts with a clean database state.

**Implementation:**
- Docker Compose starts fresh PostgreSQL container
- Alembic migrations run before tests
- Each test file can seed its own required data
- No state leaks between test files

**Benefits:**
- Tests are independent and can run in any order
- Debugging is easier (known initial state)
- No flaky tests due to leftover data

---

## Browser Coverage

| Browser | Priority | Rationale |
|---------|----------|-----------|
| Chromium | Primary | Largest market share, fastest execution |
| WebKit | Secondary | Safari/iOS coverage |

Mobile viewport testing is excluded from initial scope.

---

## Assertion Strategy

### Text-Based Assertions Only

Tests will verify behavior through:
- Text content presence/absence
- Element visibility
- Input values
- URL navigation
- Form validation messages

**Not included:**
- CSS color/style verification
- Visual regression screenshots
- Animation states

**Example assertions:**
```typescript
// Good: Text-based
await expect(page.locator('.status')).toHaveText('Zamknięty');
await expect(page.locator('.error-message')).toBeVisible();

// Avoided: Style-based
// await expect(element).toHaveCSS('background-color', 'red');
```

---

## Project Structure

```
small-gastro/
├── tests/
│   ├── features/           # Existing BDD specs
│   └── e2e/                # NEW: Playwright tests
│       ├── playwright.config.ts
│       ├── global-setup.ts
│       ├── fixtures/
│       │   ├── api.fixture.ts      # API helper functions
│       │   └── database.fixture.ts # DB reset utilities
│       ├── pages/                  # Page Object Model
│       │   ├── BasePage.ts
│       │   ├── DailyOperationsPage.ts
│       │   ├── CloseDayWizard.ts
│       │   ├── MenuPage.ts
│       │   ├── EmployeesPage.ts
│       │   └── FinancesPage.ts
│       └── specs/                  # Test specifications
│           ├── day-closing.spec.ts
│           ├── menu-management.spec.ts
│           ├── employee-shifts.spec.ts
│           └── finances.spec.ts
```

---

## Authentication

**Requirement:** None

The application does not require authentication for the flows being tested. All pages are accessible without login.

---

## CI/CD Integration

**Current scope:** Local execution only

Tests will be run manually during development:
```bash
npx playwright test
```

CI/CD integration (GitHub Actions) is deferred to a future iteration.

---

## Success Criteria

| Criteria | Target |
|----------|--------|
| Critical happy paths covered | 100% |
| Test execution time | **< 2 minutes total** |
| Flaky test rate | < 5% |
| Tests run on Chromium and WebKit | Both passing |
| HTML report generated | Yes |

### Scope Reduction for Speed

To meet the 2-minute execution target, tests focus on **critical happy paths only**:

| Flow | Included Scenarios | Est. Time |
|------|-------------------|-----------|
| Day Closing | Complete wizard flow | ~30 sec |
| Menu | Create product with ingredients | ~20 sec |
| Employees | Create employee + assign shift | ~20 sec |
| Finances | Create category + expense | ~20 sec |
| **Total** | **4 scenarios** | **~90 sec** |

Edge cases and validation scenarios are covered by existing unit tests (Vitest/pytest).

---

## Dependencies

### Required Packages
- `@playwright/test` - Test framework
- `playwright` - Browser automation

### Infrastructure
- Docker Compose for full stack
- PostgreSQL database
- Backend API running
- Frontend served (Nginx or dev server)

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Flaky tests due to timing | Medium | High | Use Playwright's auto-waiting, explicit waits where needed |
| Test data conflicts | Low | Medium | Fresh database per test file |
| Slow test execution | Medium | Medium | API seeding, parallel test files |
| UI changes break selectors | High | Medium | Page Object Model, data-testid attributes |

---

## Resolved Decisions

| Question | Decision |
|----------|----------|
| Add `data-testid` attributes? | **Yes** - Add to all interactive elements for stable selectors |
| Execution time budget? | **< 2 minutes** - Focus on critical happy paths only |
| Generate HTML reports? | **Yes** - For reviewing test results |

### data-testid Convention

Components will use `data-testid` attributes following this pattern:

```tsx
// Buttons
<button data-testid="close-day-button">Zamknij dzień</button>

// Forms
<input data-testid="ingredient-name-input" />

// Tables
<table data-testid="ingredients-table">
  <tr data-testid="ingredient-row-{id}">

// Wizard steps
<div data-testid="wizard-step-1">
```

This requires updating React components during implementation.

---

## Related Documents

- [TECHNICAL.md](./TECHNICAL.md) - Technical implementation details
- [scenarios.feature](./scenarios.feature) - BDD test scenarios
- [TESTING.md](./TESTING.md) - Test execution plan
