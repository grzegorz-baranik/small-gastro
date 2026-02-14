# Test Plan: Day Closing Wizard

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
- Verify the wizard navigation flow works correctly (4 steps)
- Ensure real-time calculations are accurate and performant
- Validate form inputs and error handling
- Confirm successful day closing with correct data submission
- Test edge cases (negative usage, zero values, large discrepancies)

### 1.2 In Scope
- [x] WizardStepper component navigation
- [x] Step 1: Opening inventory display
- [x] Step 2: Day events summary
- [x] Step 3: Closing inventory input with live calculations
- [x] Step 4: Confirmation and close
- [x] useClosingCalculations hook accuracy
- [x] Form validation (required fields, numeric values)
- [x] Discrepancy level calculation (OK/Warning/Critical)
- [x] API integration for closing the day

### 1.3 Out of Scope
- Backend API tests (already covered)
- Mobile layout testing
- Performance under extreme load (>1000 ingredients)

---

## 2. Testing Strategy

### 2.1 Test Levels

| Level | Coverage | Tools |
|-------|----------|-------|
| Unit (Frontend) | 80% | Vitest, React Testing Library |
| Unit (Backend) | Existing | pytest |
| Integration | 70% | Vitest, MSW (API mocking) |
| E2E | 60% | Playwright |
| Manual | 20% | Browser testing |

### 2.2 Entry Criteria
- [x] Specification approved
- [ ] Test environment configured
- [ ] Test data fixtures prepared
- [ ] Components implemented

### 2.3 Exit Criteria
- [ ] All critical tests passed
- [ ] Code coverage >= 80% for new components
- [ ] No critical or high severity bugs
- [ ] All BDD scenarios verified

---

## 3. Test Cases

### 3.1 Unit Tests (Frontend)

#### TC-UNIT-001: useClosingCalculations - Basic Usage Calculation
**Component:** `useClosingCalculations`
**Description:** Verify usage is calculated correctly: Expected - Closing

**Test Code:**
```typescript
describe('useClosingCalculations', () => {
  it('calculates usage correctly', () => {
    const usageItems = [
      {
        ingredient_id: 1,
        ingredient_name: 'Mięso kebab',
        unit_type: 'weight',
        opening_quantity: 10.5,
        deliveries_quantity: 5.0,
        transfers_quantity: 0,
        spoilage_quantity: 0.5,
        expected_closing: 15.0,
        expected_usage: 3.0
      }
    ];
    const closingInventory = { 1: '12.0' };

    const { result } = renderHook(() =>
      useClosingCalculations({ usageItems, closingInventory })
    );

    expect(result.current.rows[0].usage).toBe(3.0);
    expect(result.current.rows[0].closing).toBe(12.0);
  });
});
```

---

#### TC-UNIT-002: useClosingCalculations - Discrepancy Levels
**Component:** `useClosingCalculations`
**Description:** Verify discrepancy levels are assigned correctly

**Test Code:**
```typescript
describe('useClosingCalculations - discrepancy levels', () => {
  it('returns OK for discrepancy <= 5%', () => {
    const usageItems = [{
      ingredient_id: 1,
      expected_closing: 100,
      expected_usage: 20,
      // other fields...
    }];
    const closingInventory = { 1: '80' }; // usage = 20, 0% discrepancy

    const { result } = renderHook(() =>
      useClosingCalculations({ usageItems, closingInventory })
    );

    expect(result.current.rows[0].discrepancyLevel).toBe('ok');
  });

  it('returns warning for discrepancy 5-10%', () => {
    const usageItems = [{
      ingredient_id: 1,
      expected_closing: 100,
      expected_usage: 20,
    }];
    const closingInventory = { 1: '78' }; // usage = 22, 10% discrepancy

    const { result } = renderHook(() =>
      useClosingCalculations({ usageItems, closingInventory })
    );

    expect(result.current.rows[0].discrepancyLevel).toBe('warning');
  });

  it('returns critical for discrepancy > 10%', () => {
    const usageItems = [{
      ingredient_id: 1,
      expected_closing: 100,
      expected_usage: 20,
    }];
    const closingInventory = { 1: '70' }; // usage = 30, 50% discrepancy

    const { result } = renderHook(() =>
      useClosingCalculations({ usageItems, closingInventory })
    );

    expect(result.current.rows[0].discrepancyLevel).toBe('critical');
  });
});
```

---

#### TC-UNIT-003: useClosingCalculations - Validation
**Component:** `useClosingCalculations`
**Description:** Verify isValid flag works correctly

**Test Code:**
```typescript
describe('useClosingCalculations - validation', () => {
  it('returns isValid=false when fields are empty', () => {
    const usageItems = [
      { ingredient_id: 1, /* ... */ },
      { ingredient_id: 2, /* ... */ }
    ];
    const closingInventory = { 1: '10' }; // Missing id: 2

    const { result } = renderHook(() =>
      useClosingCalculations({ usageItems, closingInventory })
    );

    expect(result.current.isValid).toBe(false);
  });

  it('returns isValid=true when all fields have values', () => {
    const usageItems = [
      { ingredient_id: 1, /* ... */ },
      { ingredient_id: 2, /* ... */ }
    ];
    const closingInventory = { 1: '10', 2: '20' };

    const { result } = renderHook(() =>
      useClosingCalculations({ usageItems, closingInventory })
    );

    expect(result.current.isValid).toBe(true);
  });
});
```

---

#### TC-UNIT-004: WizardStepper - Rendering
**Component:** `WizardStepper`
**Description:** Verify stepper renders all steps with correct statuses

**Test Code:**
```typescript
describe('WizardStepper', () => {
  const steps = [
    { id: 1, title: 'Otwarcie', status: 'completed' },
    { id: 2, title: 'Zdarzenia', status: 'current' },
    { id: 3, title: 'Zamknięcie', status: 'pending' },
    { id: 4, title: 'Potwierdź', status: 'pending' },
  ];

  it('renders all step titles', () => {
    render(<WizardStepper steps={steps} currentStep={1} onStepClick={() => {}} />);

    expect(screen.getByText('Otwarcie')).toBeInTheDocument();
    expect(screen.getByText('Zdarzenia')).toBeInTheDocument();
    expect(screen.getByText('Zamknięcie')).toBeInTheDocument();
    expect(screen.getByText('Potwierdź')).toBeInTheDocument();
  });

  it('shows checkmark for completed steps', () => {
    render(<WizardStepper steps={steps} currentStep={1} onStepClick={() => {}} />);

    const completedStep = screen.getAllByRole('button')[0];
    expect(completedStep).toHaveClass('bg-primary-600');
  });

  it('disables pending steps', () => {
    render(<WizardStepper steps={steps} currentStep={1} onStepClick={() => {}} />);

    const pendingStep = screen.getAllByRole('button')[2];
    expect(pendingStep).toBeDisabled();
  });
});
```

---

#### TC-UNIT-005: WizardStepper - Navigation
**Component:** `WizardStepper`
**Description:** Verify clicking completed steps triggers navigation

**Test Code:**
```typescript
describe('WizardStepper - navigation', () => {
  it('calls onStepClick when clicking completed step', async () => {
    const onStepClick = vi.fn();
    const steps = [
      { id: 1, title: 'Otwarcie', status: 'completed' },
      { id: 2, title: 'Zdarzenia', status: 'current' },
    ];

    render(<WizardStepper steps={steps} currentStep={1} onStepClick={onStepClick} />);

    await userEvent.click(screen.getAllByRole('button')[0]);

    expect(onStepClick).toHaveBeenCalledWith(0);
  });

  it('does not call onStepClick when clicking pending step', async () => {
    const onStepClick = vi.fn();
    const steps = [
      { id: 1, title: 'Otwarcie', status: 'current' },
      { id: 2, title: 'Zdarzenia', status: 'pending' },
    ];

    render(<WizardStepper steps={steps} currentStep={0} onStepClick={onStepClick} />);

    await userEvent.click(screen.getAllByRole('button')[1]);

    expect(onStepClick).not.toHaveBeenCalled();
  });
});
```

---

#### TC-UNIT-006: WizardStepClosing - Real-time Updates
**Component:** `WizardStepClosing`
**Description:** Verify inputs update calculations in real-time

**Test Code:**
```typescript
describe('WizardStepClosing', () => {
  it('updates usage when closing value changes', async () => {
    const onChange = vi.fn();
    const rows = [{
      ingredientId: 1,
      ingredientName: 'Mięso kebab',
      unitType: 'weight',
      opening: 10.5,
      deliveries: 5.0,
      transfers: 0,
      spoilage: 0.5,
      expected: 15.0,
      closing: null,
      usage: null,
      discrepancyPercent: null,
      discrepancyLevel: null
    }];

    render(
      <WizardStepClosing
        rows={rows}
        closingInventory={{}}
        onChange={onChange}
        alerts={[]}
      />
    );

    const input = screen.getByRole('spinbutton');
    await userEvent.type(input, '12');

    expect(onChange).toHaveBeenCalled();
  });
});
```

---

### 3.2 Integration Tests

#### TC-INT-001: Complete Wizard Flow
**Description:** Test full wizard flow from open to close

**Test Code:**
```typescript
describe('CloseDayWizard - full flow', () => {
  it('completes day closing successfully', async () => {
    // Mock API responses
    server.use(
      rest.get('/api/v1/daily-records/:id/summary', (req, res, ctx) => {
        return res(ctx.json(mockDaySummary));
      }),
      rest.post('/api/v1/daily-records/:id/close', (req, res, ctx) => {
        return res(ctx.json({ status: 'CLOSED' }));
      })
    );

    render(
      <QueryClientProvider client={queryClient}>
        <CloseDayWizard
          isOpen={true}
          onClose={() => {}}
          onSuccess={() => {}}
          dailyRecord={mockDailyRecord}
        />
      </QueryClientProvider>
    );

    // Step 1: View opening
    expect(screen.getByText('Otwarcie')).toBeInTheDocument();
    await userEvent.click(screen.getByText('Dalej'));

    // Step 2: View events
    await waitFor(() => {
      expect(screen.getByText('Zdarzenia')).toBeInTheDocument();
    });
    await userEvent.click(screen.getByText('Dalej'));

    // Step 3: Enter closing quantities
    await waitFor(() => {
      expect(screen.getByText('Zamknięcie')).toBeInTheDocument();
    });
    await userEvent.click(screen.getByText('Kopiuj oczekiwane'));
    await userEvent.click(screen.getByText('Dalej'));

    // Step 4: Confirm
    await waitFor(() => {
      expect(screen.getByText('Potwierdź')).toBeInTheDocument();
    });
    await userEvent.click(screen.getByText('Zamknij dzień'));

    // Verify success
    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });
  });
});
```

---

#### TC-INT-002: Validation Prevents Navigation
**Description:** Test that empty fields prevent proceeding from Step 3

**Test Code:**
```typescript
describe('CloseDayWizard - validation', () => {
  it('disables Next button when fields are empty', async () => {
    render(<CloseDayWizard {...props} />);

    // Navigate to Step 3
    await userEvent.click(screen.getByText('Dalej'));
    await userEvent.click(screen.getByText('Dalej'));

    // Next button should be disabled
    const nextButton = screen.getByText('Dalej');
    expect(nextButton).toBeDisabled();
  });
});
```

---

### 3.3 E2E Tests (Playwright)

#### TC-E2E-001: Complete Day Closing Flow
**Description:** End-to-end test of closing a day

**Test Code:**
```typescript
test('closes day using wizard', async ({ page }) => {
  // Setup: Ensure day is open
  await page.goto('/daily-operations');
  await expect(page.locator('text=OTWARTA')).toBeVisible();

  // Open wizard
  await page.click('button:has-text("Zamknij dzień")');

  // Step 1: Verify opening inventory visible
  await expect(page.locator('text=Otwarcie')).toBeVisible();
  await expect(page.locator('text=Mięso kebab')).toBeVisible();
  await page.click('button:has-text("Dalej")');

  // Step 2: Verify events visible
  await expect(page.locator('text=Zdarzenia')).toBeVisible();
  await page.click('button:has-text("Dalej")');

  // Step 3: Enter closing quantities
  await expect(page.locator('text=Zamknięcie')).toBeVisible();
  await page.click('button:has-text("Kopiuj oczekiwane")');

  // Verify calculations appear
  await expect(page.locator('text=Zużycie')).toBeVisible();
  await page.click('button:has-text("Dalej")');

  // Step 4: Confirm
  await expect(page.locator('text=Potwierdź')).toBeVisible();
  await page.click('button:has-text("Zamknij dzień")');

  // Confirm dialog
  await page.click('button:has-text("Potwierdź")');

  // Verify success
  await expect(page.locator('text=Dzień został zamknięty')).toBeVisible();
});
```

---

#### TC-E2E-002: Real-time Calculations
**Description:** Verify calculations update as user types

**Test Code:**
```typescript
test('calculations update in real-time', async ({ page }) => {
  await page.goto('/daily-operations');
  await page.click('button:has-text("Zamknij dzień")');

  // Navigate to Step 3
  await page.click('button:has-text("Dalej")');
  await page.click('button:has-text("Dalej")');

  // Find input for first ingredient
  const input = page.locator('input[type="number"]').first();
  await input.fill('10');

  // Verify usage updates immediately
  await expect(page.locator('text=Zużycie')).toBeVisible();
  // The usage value should appear without clicking any button
});
```

---

## 4. Test Data

### 4.1 Fixtures

```typescript
// fixtures/wizard.ts

export const mockDailyRecord = {
  id: 1,
  date: '2026-01-04',
  status: 'OPEN',
  opened_at: '2026-01-04T08:00:00'
};

export const mockDaySummary = {
  id: 1,
  date: '2026-01-04',
  status: 'OPEN',
  opening_time: '2026-01-04T08:00:00',
  events: {
    deliveries_count: 2,
    deliveries_total_pln: 300.00,
    transfers_count: 1,
    spoilage_count: 1
  },
  usage_items: [
    {
      ingredient_id: 1,
      ingredient_name: 'Mięso kebab',
      unit_type: 'weight',
      opening_quantity: 10.5,
      deliveries_quantity: 5.0,
      transfers_quantity: 0,
      spoilage_quantity: 0.5,
      expected_closing: 15.0,
      expected_usage: 3.0
    },
    {
      ingredient_id: 2,
      ingredient_name: 'Bułki',
      unit_type: 'count',
      opening_quantity: 50,
      deliveries_quantity: 30,
      transfers_quantity: 0,
      spoilage_quantity: 5,
      expected_closing: 75,
      expected_usage: 20
    }
  ],
  calculated_sales: [],
  total_income_pln: 0,
  total_delivery_cost_pln: 300.00
};
```

### 4.2 Test Data Matrix

| ID | Scenario | Expected Closing | User Input | Expected Usage | Discrepancy |
|----|----------|------------------|------------|----------------|-------------|
| 1 | Normal case | 15.0 | 12.0 | 3.0 | OK (0%) |
| 2 | Small discrepancy | 15.0 | 11.5 | 3.5 | OK (3%) |
| 3 | Warning range | 15.0 | 10.5 | 4.5 | Warning (8%) |
| 4 | Critical | 15.0 | 8.0 | 7.0 | Critical (25%) |
| 5 | Negative usage | 15.0 | 17.0 | -2.0 | Highlighted |
| 6 | Zero expected | 0 | 0 | 0 | N/A |

---

## 5. Edge Cases

| ID | Case | Expected Behavior | Status |
|----|------|------------------|--------|
| EC-001 | All fields empty | Disable Next button | [ ] |
| EC-002 | Negative input | Show error message | [ ] |
| EC-003 | Decimal for count | Show "integer required" error | [ ] |
| EC-004 | Closing > Expected | Show negative usage | [ ] |
| EC-005 | Very large discrepancy (>100%) | Show critical alert | [ ] |
| EC-006 | Zero expected closing | Handle gracefully, no division by zero | [ ] |
| EC-007 | Network error on close | Show error, keep wizard open | [ ] |

---

## 6. Performance Tests

### 6.1 Scenarios

| Scenario | Expected Time | Limit |
|----------|---------------|-------|
| Wizard load | < 500ms | 1s |
| Real-time calculation (20 items) | < 50ms | 100ms |
| Step navigation | < 100ms | 200ms |
| Day close API call | < 1s | 2s |

### 6.2 Test Code

```typescript
test('calculations complete within 50ms', async () => {
  const usageItems = Array.from({ length: 20 }, (_, i) => ({
    ingredient_id: i,
    expected_closing: 100,
    expected_usage: 20,
    // ... other fields
  }));

  const startTime = performance.now();

  const { result } = renderHook(() =>
    useClosingCalculations({
      usageItems,
      closingInventory: Object.fromEntries(
        usageItems.map(item => [item.ingredient_id, '80'])
      )
    })
  );

  const endTime = performance.now();
  expect(endTime - startTime).toBeLessThan(50);
  expect(result.current.rows).toHaveLength(20);
});
```

---

## 7. Accessibility Tests

| Test | Description | Status |
|------|-------------|--------|
| A11Y-001 | All inputs have labels | [ ] |
| A11Y-002 | Stepper is keyboard navigable | [ ] |
| A11Y-003 | Error messages are announced | [ ] |
| A11Y-004 | Color not only indicator | [ ] |
| A11Y-005 | Focus management between steps | [ ] |

---

## 8. Test Environment

### 8.1 Configuration

```bash
# Frontend testing setup
cd frontend
npm install -D vitest @testing-library/react @testing-library/user-event msw

# Playwright setup
npx playwright install
```

### 8.2 Running Tests

```bash
# Unit tests
cd frontend
npm run test                    # Run all tests
npm run test:coverage          # With coverage report
npm run test:watch             # Watch mode

# E2E tests
npm run test:e2e               # Run Playwright tests
npm run test:e2e:headed        # With browser visible

# Specific test file
npm run test -- WizardStepper.test.tsx
npm run test -- useClosingCalculations.test.ts
```

---

## 9. Test Coverage Requirements

| Component | Min Coverage |
|-----------|--------------|
| useClosingCalculations | 90% |
| WizardStepper | 80% |
| WizardStepOpening | 70% |
| WizardStepEvents | 70% |
| WizardStepClosing | 85% |
| WizardStepConfirm | 75% |
| CloseDayWizard | 80% |

---

## 10. Reporting

### 10.1 Report Format

| Metric | Target |
|--------|--------|
| Total tests | 40+ |
| Unit tests | 25+ |
| Integration tests | 10+ |
| E2E tests | 5+ |
| Code coverage | ≥ 80% |

### 10.2 Bug Template

| ID | Description | Severity | Steps to Reproduce | Status |
|----|-------------|----------|-------------------|--------|
| BUG-XXX | {description} | Critical/High/Medium/Low | 1. ... 2. ... | Open/Fixed |

---

## Change History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-04 | AI Assistant | Initial version |
