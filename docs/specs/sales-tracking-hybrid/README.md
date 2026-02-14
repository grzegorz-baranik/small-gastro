# Functional Specification: Sales Tracking Hybrid

## Metadata

| Field | Value |
|-------|-------|
| **Author** | AI Assistant |
| **Created** | 2026-01-06 |
| **Version** | 1.0 |
| **Status** | Draft |
| **Approved by** | Pending |

---

## 1. Overview

### 1.1 Purpose

Enable optional real-time sales recording alongside the existing inventory-derived sales calculation, creating a hybrid system that provides reconciliation insights and supports gradual transition from ingredient-first to sales-first tracking.

### 1.2 Business Context

Currently, the system calculates revenue by deriving sales from ingredient usage at day close. This approach:
- Cannot determine exact product mix (e.g., 5kg meat = how many large vs small kebabs?)
- Hides waste, theft, and over-portioning as "sales"
- Provides no real-time revenue visibility
- Offers no customer behavior insights (peak hours, popular items)

The hybrid approach adds optional sales recording that runs parallel to inventory calculations, enabling:
- Accurate revenue tracking when sales are recorded
- Reconciliation between recorded and calculated sales
- Insights into portion accuracy, waste, and operational efficiency
- Soft transition path without disrupting existing workflow

### 1.3 Scope

**In scope:**
- Real-time sales recording via touch-optimized interface
- Per-shift staff attribution for recorded sales
- Void/cancel functionality with reason tracking
- Reconciliation report comparing recorded vs calculated sales
- Insights: daily comparison, product popularity, portion accuracy, peak hours
- Integration into day closing wizard as new step
- Suggestion system for missing sales based on inventory gaps

**Out of scope:**
- Payment method tracking (deferred)
- Per-sale staff attribution (simplified to per-shift)
- External POS hardware integration
- Customer loyalty/rewards
- Discounts and promotions
- Multi-location/multi-register support

---

## 2. User Stories

### US-001: Record Sales in Real-Time
**As a** shop staff member
**I want** to quickly record each sale as it happens
**So that** I have accurate revenue data and can see my running total

**Acceptance Criteria:**
- [ ] Products organized in category tabs (kebabs, burgers, drinks, etc.)
- [ ] Single tap adds one unit of a product
- [ ] Running total displayed prominently
- [ ] Works smoothly on smartphone/tablet
- [ ] Sales attributed to current shift automatically

**Priority:** High

---

### US-002: View Running Sales Total
**As a** shop owner/manager
**I want** to see today's recorded sales total at a glance
**So that** I know how the day is going without waiting for close

**Acceptance Criteria:**
- [ ] Running total visible on main daily operations screen
- [ ] Updates immediately when sale is recorded
- [ ] Shows count of items sold alongside revenue

**Priority:** High

---

### US-003: Void a Recorded Sale
**As a** shop staff member
**I want** to cancel a mistakenly recorded sale
**So that** my sales records are accurate

**Acceptance Criteria:**
- [ ] Tap on sale opens void dialog
- [ ] Must provide reason (mistake, customer refund, duplicate, other)
- [ ] Voided sales remain in history but don't count toward totals
- [ ] Running total updates after void

**Priority:** High

---

### US-004: Reconcile Sales at Day Close
**As a** shop owner
**I want** to compare recorded sales against inventory-calculated sales
**So that** I can identify discrepancies and understand their causes

**Acceptance Criteria:**
- [ ] Reconciliation step added to day closing wizard
- [ ] Shows side-by-side: recorded total vs calculated total
- [ ] Shows discrepancy amount and percentage
- [ ] Breaks down comparison by product
- [ ] Suggests possible missing sales when calculated > recorded

**Priority:** High

---

### US-005: Close Day Without Recording Sales
**As a** shop staff member (during transition period)
**I want** to close the day even if I didn't record all sales
**So that** I can gradually adopt the new system

**Acceptance Criteria:**
- [ ] Warning shown if no/few sales recorded
- [ ] Can proceed with calculated-only revenue
- [ ] Clear indication of which revenue source was used
- [ ] No blocking - recording is optional

**Priority:** High

---

### US-006: View Product Popularity
**As a** shop owner
**I want** to see which products sell most often
**So that** I can optimize my menu and inventory

**Acceptance Criteria:**
- [ ] Ranking of products by quantity sold
- [ ] Filterable by date range
- [ ] Shows both recorded counts and calculated estimates
- [ ] Trend indicator (up/down vs previous period)

**Priority:** Medium

---

### US-007: Analyze Peak Hours
**As a** shop owner
**I want** to see when most sales occur
**So that** I can optimize staffing and preparation

**Acceptance Criteria:**
- [ ] Hourly breakdown of sales (requires recorded sales with timestamps)
- [ ] Visual chart showing busy periods
- [ ] Filterable by day of week
- [ ] Only available when sufficient recorded sales exist

**Priority:** Medium

---

### US-008: Check Portion Accuracy
**As a** shop owner
**I want** to see if staff are using correct ingredient amounts
**So that** I can maintain margins and train staff

**Acceptance Criteria:**
- [ ] Compare expected ingredient usage (from recorded sales × recipes) vs actual usage
- [ ] Per-ingredient breakdown
- [ ] Highlight products with consistent over/under-portioning
- [ ] Suggest training opportunities

**Priority:** Medium

---

## 3. Functional Requirements

### 3.1 Sales Recording
**ID:** FR-001
**Description:** System shall allow recording individual sales for any product variant. Each recorded sale captures: product variant, quantity (default 1), unit price (snapshot from variant), timestamp, and associated shift.
**Priority:** High

### 3.2 Category-Based Product Display
**ID:** FR-002
**Description:** Products in sales entry screen shall be organized into tabs by category. User taps category tab to see products in that category. Categories derived from existing product categorization or new category field.
**Priority:** High

### 3.3 Shift Attribution
**ID:** FR-003
**Description:** When recording sales, system shall automatically associate sales with the current active shift. If no shift is active, sales are attributed to the day only.
**Priority:** High

### 3.4 Sales Void with Reason
**ID:** FR-004
**Description:** System shall allow voiding recorded sales. Voided sales require a reason (mistake, customer_refund, duplicate, other). Voided sales are soft-deleted (kept in database with voided_at timestamp and reason).
**Priority:** High

### 3.5 Running Total Display
**ID:** FR-005
**Description:** System shall display running total of recorded sales for current day. Total updates in real-time when sales are added or voided.
**Priority:** High

### 3.6 Reconciliation Calculation
**ID:** FR-006
**Description:** System shall calculate reconciliation between recorded and calculated sales. Comparison includes: total revenue, per-product quantities, per-ingredient expected vs actual usage.
**Priority:** High

### 3.7 Missing Sales Suggestions
**ID:** FR-007
**Description:** When calculated sales exceed recorded sales for a product, system shall suggest possible missing sales. Suggestion format: "Możliwe brakujące: 2x Kebab duży (50 PLN)"
**Priority:** Medium

### 3.8 Reconciliation Step in Close Wizard
**ID:** FR-008
**Description:** Day closing wizard shall include reconciliation step before final confirmation. Step shows comparison, insights, and allows user to proceed regardless of discrepancy.
**Priority:** High

### 3.9 Flexible Revenue Source
**ID:** FR-009
**Description:** System shall support using either recorded or calculated revenue for official totals. Default: use recorded if available and complete (>80% match with calculated), otherwise use calculated with note.
**Priority:** Medium

### 3.10 Peak Hours Analysis
**ID:** FR-010
**Description:** System shall aggregate recorded sales by hour to show peak periods. Requires minimum 50 recorded sales to display meaningful data.
**Priority:** Medium

### 3.11 Product Popularity Ranking
**ID:** FR-011
**Description:** System shall rank products by recorded sales quantity. Include comparison with calculated estimates where available.
**Priority:** Medium

### 3.12 Portion Accuracy Report
**ID:** FR-012
**Description:** System shall compare expected ingredient usage (recorded sales × recipe amounts) vs actual ingredient usage (from inventory). Show per-ingredient accuracy percentage.
**Priority:** Medium

---

## 4. User Interface

### 4.1 Sales Entry Screen (Touch-Optimized)

```
┌────────────────────────────────────────────────────────┐
│  ← Sprzedaż                          Dziś: 1,245 PLN  │
├────────────────────────────────────────────────────────┤
│  [Kebaby] [Burgery] [Hot Dogi] [Napoje] [Inne]        │ ← Category tabs
├────────────────────────────────────────────────────────┤
│                                                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ Kebab    │  │ Kebab    │  │ Kebab    │             │
│  │ Mały     │  │ Średni   │  │ Duży     │             │
│  │          │  │          │  │          │             │
│  │  18 PLN  │  │  22 PLN  │  │  28 PLN  │             │ ← Product buttons
│  │    (3)   │  │    (7)   │  │   (12)   │             │ ← Today's count
│  └──────────┘  └──────────┘  └──────────┘             │
│                                                        │
│  ┌──────────┐  ┌──────────┐                           │
│  │ Falafel  │  │ Mix      │                           │
│  │          │  │          │                           │
│  │  20 PLN  │  │  25 PLN  │                           │
│  │    (2)   │  │    (5)   │                           │
│  └──────────┘  └──────────┘                           │
│                                                        │
├────────────────────────────────────────────────────────┤
│  Ostatnie sprzedaże:                                  │
│  12:34  Kebab Duży         28 PLN              [Anuluj]│
│  12:32  Kebab Średni       22 PLN              [Anuluj]│
│  12:30  Hot Dog            12 PLN              [Anuluj]│
└────────────────────────────────────────────────────────┘
```

### 4.2 Reconciliation Screen

```
┌────────────────────────────────────────────────────────┐
│  Uzgodnienie sprzedaży                    06.01.2026  │
├────────────────────────────────────────────────────────┤
│                                                        │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐│
│  │ Zarejestr.  │    │ Obliczone   │    │  Różnica    ││
│  │             │    │             │    │             ││
│  │  1,850 PLN  │    │  2,100 PLN  │    │  -250 PLN   ││
│  │             │    │ (z inwen.)  │    │   (11.9%)   ││
│  └─────────────┘    └─────────────┘    └─────────────┘│
│                                                        │
├────────────────────────────────────────────────────────┤
│  ⚠️ Możliwe brakujące sprzedaże:                      │
│                                                        │
│  • 2x Kebab Duży (56 PLN) - mięso sugeruje więcej     │
│  • 1x Burger (25 PLN) - bułki sugerują więcej         │
│                                                        │
├────────────────────────────────────────────────────────┤
│  Szczegóły wg produktu:                               │
│                                                        │
│  Produkt          Zarej.  Oblic.  Różnica             │
│  ─────────────────────────────────────────            │
│  Kebab Duży         10      12      -2                │
│  Kebab Średni        7       7       0                │
│  Burger              4       5      -1                │
│  Hot Dog            15      14      +1                │
│                                                        │
├────────────────────────────────────────────────────────┤
│                                                        │
│  [Wróć]                              [Kontynuuj →]    │
│                                                        │
└────────────────────────────────────────────────────────┘
```

### 4.3 Void Dialog

```
┌────────────────────────────────────────┐
│  Anuluj sprzedaż                       │
├────────────────────────────────────────┤
│                                        │
│  Kebab Duży - 28 PLN                   │
│  Zarejestrowano: 12:34                 │
│                                        │
│  Powód anulowania:                     │
│                                        │
│  ○ Pomyłka przy rejestracji            │
│  ○ Zwrot klientowi                     │
│  ○ Duplikat                            │
│  ○ Inny: [________________]            │
│                                        │
├────────────────────────────────────────┤
│  [Anuluj]              [Potwierdź]     │
└────────────────────────────────────────┘
```

### 4.4 User Flow

```
Main Flow:
[Daily Ops Page] → [Tap "Sprzedaż"] → [Sales Entry Screen] → [Tap Product] → [Sale Recorded]
                                                           ↓
                                              [Tap Recent Sale] → [Void Dialog] → [Voided]

Close Day Flow:
[Close Wizard Step 1: Inventory] → [Step 2: Review Events] → [Step 3: Reconciliation] → [Step 4: Confirm]
                                                                      ↓
                                                            (If no sales recorded)
                                                                      ↓
                                                              [Warning Modal] → [Proceed Anyway]
```

### 4.5 UI Elements

| Element | Type | Description |
|---------|------|-------------|
| Category tabs | Tab bar | Switch between product categories |
| Product button | Large button | Tap to record one sale, shows name, price, today's count |
| Running total | Text display | Top-right, updates on each sale |
| Recent sales list | List | Last 5-10 sales with void option |
| Void button | Icon button | Opens void dialog for specific sale |
| Reconciliation cards | Card group | Three cards showing recorded/calculated/difference |
| Missing sales alert | Alert box | Yellow warning with suggested missing items |
| Product breakdown table | Table | Rows per product with recorded vs calculated |

**Note:** All UI labels and text should be in Polish.

---

## 5. Edge Cases

### 5.1 No Sales Recorded
**Scenario:** User closes day without recording any sales
**Expected behavior:** Show warning message, allow proceeding with calculated-only revenue. Store `revenue_source = "calculated"` on daily record.

### 5.2 Recorded Exceeds Calculated
**Scenario:** More sales recorded than inventory suggests (e.g., counted wrong, or ingredients restocked mid-day without recording)
**Expected behavior:** Show positive discrepancy, suggest possible causes (under-counted closing inventory, missed delivery).

### 5.3 Void All Sales for a Product
**Scenario:** All recorded sales for a product are voided
**Expected behavior:** Product shows 0 recorded, calculated remains based on inventory. No special handling needed.

### 5.4 Multiple Shifts per Day
**Scenario:** Two shifts work the same day
**Expected behavior:** Sales attributed to whichever shift is active when recorded. Reconciliation shows combined totals.

### 5.5 No Active Shift
**Scenario:** Sales recorded but no shift is marked active
**Expected behavior:** Sales recorded with `shift_id = null`, attributed to day only.

### 5.6 Product Without Primary Ingredient
**Scenario:** Product has no primary ingredient set (cannot calculate derived sales)
**Expected behavior:** Product appears in recorded sales but has no calculated comparison. Mark as "tylko zarejestrowane" in reconciliation.

### 5.7 Very Large Discrepancy
**Scenario:** Discrepancy exceeds 30%
**Expected behavior:** Show critical warning (red), strongly suggest reviewing inventory counts before proceeding.

---

## 6. Error Handling

| Error | Message (Polish) | Action |
|-------|------------------|--------|
| Network error on record sale | "Nie udało się zapisać sprzedaży. Spróbuj ponownie." | Retry button |
| Void failed | "Nie udało się anulować sprzedaży. Spróbuj ponownie." | Retry or dismiss |
| Day already closed | "Dzień jest już zamknięty. Nie można dodawać sprzedaży." | Redirect to summary |
| No open day | "Brak otwartego dnia. Otwórz dzień aby rejestrować sprzedaż." | Redirect to open day |

---

## 7. Non-Functional Requirements

### 7.1 Performance
- Sales recording must complete in < 500ms (perceived instant)
- Running total must update within 100ms of tap
- Reconciliation calculation must complete in < 2s for day with 200+ sales

### 7.2 Security
- Only authenticated users can record sales
- Void history is immutable (soft delete only)
- All sales actions are logged with user/timestamp

### 7.3 Accessibility
- Product buttons minimum 48x48dp touch target
- High contrast text on buttons
- Running total readable at arm's length

### 7.4 Offline Behavior
- Sales should be queued locally if network unavailable
- Sync when connection restored
- Show offline indicator

---

## 8. Dependencies

### 8.1 Required Features
- Daily Records (open/close day) - **exists**
- Product Variants with prices - **exists**
- Inventory snapshots - **exists**
- Shift management - **exists** (shift_assignments)
- Day closing wizard - **exists**

### 8.2 Related Data Models
- `DailyRecord` - extend with revenue tracking fields
- `ProductVariant` - use for sales buttons
- `ShiftAssignment` - determine current shift for attribution
- `CalculatedSale` - existing, for comparison
- `RecordedSale` - **new model**
- `Product` - need category field for tabs

---

## 9. Success Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Recording adoption | 50% of days have recorded sales within 1 month | Count days with recorded_sales > 0 |
| Reconciliation accuracy | <10% average discrepancy after 2 months | Average of abs(recorded - calculated) / calculated |
| User engagement | Sales entry used on 80% of open days | Track page visits vs open days |
| Insights usage | 3+ insight reports viewed per week | Track report views |

---

## 10. Open Questions

- [x] Payment method tracking? → **Deferred (skip for now)**
- [x] Staff attribution granularity? → **Per shift**
- [x] Device type? → **Smartphone/tablet (touch-optimized)**
- [x] Enforcement level? → **Fully optional**
- [ ] Product categories - use existing field or add new? (Need to check current model)
- [ ] Offline sync strategy details - PWA or native feel?

---

## Change History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-06 | AI Assistant | Initial version based on interview |
