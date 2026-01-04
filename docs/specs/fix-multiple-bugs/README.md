# Specification: Fix Multiple Bugs

**Status:** In Progress
**Date:** 2026-01-02
**Version:** 1.0

## Overview

This document describes three bugs found in the small-gastro application and their planned solutions.

---

## Bug 1: RangeError When Viewing Day Details

### Problem Description
After clicking on an open day to view details, a white screen appears with console error:
- `RangeError: invalid time value`
- `Uncaught RangeError: invalid time value`

### Root Cause
**Date format mismatch** between backend and frontend:

| Component | Format | Example |
|-----------|--------|---------|
| Backend sends | `%H:%M` (short time) | `"14:30"` |
| Frontend expects | ISO 8601 datetime | `"2026-01-02T14:30:00"` |

**Code Location:**
- Backend: `backend/app/services/daily_operations_service.py` (lines 724-725)
  ```python
  opening_time = db_record.opened_at.strftime("%H:%M")
  ```
- Frontend: `frontend/src/components/daily/DaySummary.tsx` (lines 110-111, 122-123)
  ```javascript
  formatDateTime(summary.opening_time)
  ```
- Formatter: `frontend/src/utils/formatters.ts` (lines 14-21)
  ```javascript
  new Date(dateString)  // Doesn't parse "14:30" correctly
  ```

### Solution
Change backend to send full ISO datetime instead of short time format.

### Files to Modify
1. `backend/app/services/daily_operations_service.py`
2. `backend/app/schemas/daily_operations.py` (optionally - change type to datetime)

---

## Bug 2: Internal Server Error When Adding Transaction

### Problem Description
When attempting to add a transaction (with: amount, payment method, category, date, and optional description) a 500 Internal Server Error occurs.

### Root Cause
**Unsafe relationship access** in `_to_response()` function:

```python
category_name=t.category.name if t.category else None,  # Line 31
```

When `category_id` is `None` (for revenue transactions or those without category), accessing `t.category` may throw an exception.

**Code Location:**
- API: `backend/app/api/v1/transactions.py` (line 31)
- Service: `backend/app/services/transaction_service.py`
- Model: `backend/app/models/transaction.py`

### Solution
Safe relationship access by checking `category_id` before accessing `category.name`.

### Files to Modify
1. `backend/app/api/v1/transactions.py`

---

## Bug 3: 405 Method Not Allowed in Reports

### Problem Description
When attempting to view reports (monthly trends, ingredient usage, spoilage) the following occurs:
- Message: "Błąd ładowania raportu" (Report loading error)
- Console: `405 Method Not Allowed`

### Root Cause
**HTTP method mismatch**:

| Component | HTTP Method | Expected |
|-----------|-------------|----------|
| Frontend | GET with query params | - |
| Backend | POST with body | - |

**Code Location:**
- Frontend: `frontend/src/api/reports.ts` (lines 46, 56, 70, 86, 100, 110)
  ```typescript
  client.get<MonthlyTrendsResponse>('/reports/monthly-trends', { params: range })
  ```
- Backend: `backend/app/api/v1/reports.py` (lines 102, 128, 162, 190, 225, 257)
  ```python
  @router.post("/monthly-trends", ...)
  ```

### Solution
Change backend endpoints from POST to GET and accept parameters as query params instead of body.

### Endpoints to Fix
| Endpoint | Current Method | Target Method |
|----------|---------------|---------------|
| `/reports/monthly-trends` | POST | GET |
| `/reports/monthly-trends/export` | POST | GET |
| `/reports/ingredient-usage` | POST | GET |
| `/reports/ingredient-usage/export` | POST | GET |
| `/reports/spoilage` | POST | GET |
| `/reports/spoilage/export` | POST | GET |

### Files to Modify
1. `backend/app/api/v1/reports.py`

---

## Test Plan

### Bug 1 - Tests
- Open a day
- Close the day
- Click "View details"
- Verify opening/closing times display correctly

### Bug 2 - Tests
- Add a revenue transaction (without category)
- Add an expense transaction (with category)
- Verify both save correctly

### Bug 3 - Tests
- Open "Monthly trends" report
- Open "Ingredient usage" report
- Open "Spoilage" report
- Verify all load correctly

---

## Fix Priority

1. **Bug 3** (405) - Completely blocks reports functionality
2. **Bug 2** (500) - Blocks adding transactions
3. **Bug 1** (RangeError) - Blocks viewing day details
