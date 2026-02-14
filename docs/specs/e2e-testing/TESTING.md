# E2E Testing - Test Execution Plan

## Status: Draft
**Created**: 2026-01-06
**Last Updated**: 2026-01-06

---

## Test Environment

### Prerequisites

| Component | Requirement |
|-----------|-------------|
| Docker | v20.10+ with Compose v2 |
| Node.js | v18+ (for Playwright CLI) |
| Browsers | Installed via `npx playwright install` |
| Ports | 8303 (backend), 8304 (frontend), 5461 (db) available |

### Environment Setup

```bash
# 1. Start Docker stack
docker compose up -d

# 2. Verify services are healthy
docker compose ps
# All services should show "healthy" or "running"

# 3. Run database migrations
docker compose exec backend alembic upgrade head

# 4. Install Playwright (first time only)
cd tests/e2e
npm install
npx playwright install chromium webkit
```

---

## Test Execution

### Running All Tests

```bash
cd tests/e2e

# Run all tests (both browsers)
npm test

# Run only Chromium
npm run test:chromium

# Run only WebKit
npm run test:webkit
```

### Running Specific Test Files

```bash
# Single file
npm test -- specs/day-closing.spec.ts

# Multiple files
npm test -- specs/day-closing.spec.ts specs/menu-management.spec.ts

# By tag/grep pattern
npm test -- --grep "@happy-path"
npm test -- --grep "day closing"
```

### Debug Mode

```bash
# Headed mode (see browser)
npm run test:headed

# Debug mode (pauses at each step)
npm run test:debug

# UI mode (interactive test runner)
npm run test:ui
```

---

## Test Organization

### Test Files by Priority

| Priority | File | Scenarios | Est. Duration |
|----------|------|-----------|---------------|
| 1 | `day-closing.spec.ts` | 6 | ~90 sec |
| 2 | `menu-management.spec.ts` | 5 | ~60 sec |
| 3 | `employee-shifts.spec.ts` | 5 | ~60 sec |
| 4 | `finances.spec.ts` | 4 | ~45 sec |
| - | **Total** | **20** | **~4-5 min** |

### Test Tags

| Tag | Description |
|-----|-------------|
| `@e2e` | All E2E tests (default filter) |
| `@happy-path` | Core success flows |
| `@validation` | Input validation scenarios |
| `@navigation` | Multi-step navigation |
| `@integration` | Cross-feature flows |
| `@error` | Error handling scenarios |

---

## Test Data Management

### Fresh Database Strategy

Each test file starts with a clean database:

```typescript
// In playwright.config.ts globalSetup
// Or in beforeAll hook
test.beforeAll(async () => {
  await resetDatabase();
});
```

### API Seeding Pattern

```typescript
test.beforeEach(async ({ api }) => {
  // Create required data via API
  await api.createIngredient({ name: 'Test Ingredient', unit_type: 'weight' });
  await api.createProduct({ name: 'Test Product', price: 10.00 });
});
```

### Cleanup (Optional)

If needed for specific scenarios:

```typescript
test.afterEach(async ({ api }) => {
  await api.deleteTestData();
});
```

---

## Expected Results

### Test Coverage Matrix

| Flow | Happy Path | Validation | Navigation | Edge Cases |
|------|------------|------------|------------|------------|
| Day Closing | ✓ | ✓ | ✓ | ✓ |
| Menu Management | ✓ | ✓ | - | ✓ |
| Employees | ✓ | ✓ | ✓ | - |
| Finances | ✓ | ✓ | - | - |

### Success Criteria

| Metric | Target |
|--------|--------|
| Pass rate | 100% (no flaky tests) |
| Execution time | < 5 minutes |
| Browser coverage | Chromium + WebKit both pass |

---

## Failure Investigation

### When Tests Fail

1. **Check screenshots** - Located in `tests/e2e/test-results/`
2. **Check traces** - View with `npx playwright show-trace trace.zip`
3. **Check videos** - Retained for failed tests
4. **Check logs** - `docker compose logs backend`

### Common Failure Patterns

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Element not found | Selector changed | Update Page Object |
| Timeout | Slow API response | Increase timeout or check backend |
| Assertion failed | Expected value changed | Update test expectation |
| Connection refused | Docker not running | Start Docker stack |

### Debugging Workflow

```bash
# 1. Run single failing test in debug mode
npm test -- --debug specs/day-closing.spec.ts -g "complete day closing"

# 2. Add breakpoints in test code
await page.pause();  // Opens Playwright Inspector

# 3. Check network requests
await page.route('**/*', route => {
  console.log(route.request().url());
  route.continue();
});
```

---

## Test Reports

### HTML Report

Generated automatically after test run:

```bash
# View report
npm run report
# Opens: tests/e2e/playwright-report/index.html
```

### Report Contents

- Test results summary (pass/fail/skip)
- Execution time per test
- Screenshots of failures
- Trace files for debugging
- Video recordings (failures only)

### Artifacts Location

```
tests/e2e/
├── playwright-report/     # HTML report
│   └── index.html
├── test-results/          # Failure artifacts
│   ├── screenshots/
│   ├── traces/
│   └── videos/
```

---

## Maintenance

### Weekly Tasks

- [ ] Run full test suite
- [ ] Review flaky tests (if any)
- [ ] Update selectors for UI changes

### When UI Changes

1. Run affected tests
2. Update Page Objects with new selectors
3. Verify tests pass
4. Consider adding `data-testid` attributes for stability

### Adding New Tests

1. Identify the flow to test
2. Add scenario to `scenarios.feature`
3. Create/update Page Object if needed
4. Write test in appropriate spec file
5. Run and verify

---

## Test Execution Checklist

### Before Running Tests

- [ ] Docker stack is running (`docker compose ps`)
- [ ] Database migrations are current (`alembic upgrade head`)
- [ ] No port conflicts with other branches
- [ ] Playwright browsers are installed

### During Test Development

- [ ] Use Page Objects for selectors
- [ ] Add appropriate waits (Playwright auto-waits)
- [ ] Keep tests independent (no shared state)
- [ ] Use meaningful test names

### After Test Run

- [ ] All tests pass
- [ ] Check for slow tests (> 30 sec)
- [ ] Review any skipped tests
- [ ] Archive reports if needed

---

## Troubleshooting

### Docker Issues

```bash
# Reset containers
docker compose down -v
docker compose up -d

# Check logs
docker compose logs -f backend
docker compose logs -f frontend
```

### Browser Issues

```bash
# Reinstall browsers
npx playwright install --force

# Check browser versions
npx playwright --version
```

### Network Issues

```bash
# Test backend directly
curl http://localhost:8303/api/v1/health

# Test frontend directly
curl http://localhost:8304
```

---

## Future Improvements

### Phase 2: Performance Metrics

Add performance assertions:
```typescript
const startTime = Date.now();
await page.goto('/operacje');
const loadTime = Date.now() - startTime;
expect(loadTime).toBeLessThan(2000); // 2 seconds
```

### Phase 3: Accessibility Testing

Add a11y checks:
```typescript
import AxeBuilder from '@axe-core/playwright';

test('should have no accessibility violations', async ({ page }) => {
  await page.goto('/');
  const results = await new AxeBuilder({ page }).analyze();
  expect(results.violations).toEqual([]);
});
```

### Phase 4: CI Integration

GitHub Actions workflow (see TECHNICAL.md for details).

---

## Related Documents

- [README.md](./README.md) - Functional specification
- [TECHNICAL.md](./TECHNICAL.md) - Technical implementation
- [scenarios.feature](./scenarios.feature) - BDD test scenarios
