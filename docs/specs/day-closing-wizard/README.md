# Functional Specification: Day Closing Wizard

## Metadata

| Field | Value |
|-------|-------|
| **Author** | AI Assistant |
| **Created** | 2026-01-04 |
| **Version** | 1.0 |
| **Status** | Draft |
| **Approved by** | Pending |

---

## 1. Overview

### 1.1 Purpose
Replace the current single-screen day closing modal with a step-by-step wizard that provides clear transparency into inventory calculations, real-time feedback while entering closing quantities, and a more intuitive user experience.

### 1.2 Business Context
The current day closing modal presents all information at once, making it difficult to understand:
- What quantities were at the beginning of the day
- How deliveries, transfers, and spoilage affected inventory
- What the expected vs actual closing quantities mean
- The calculation formula: `Usage = Opening + Deliveries + Transfers - Spoilage - Closing`

Users must click a "Calculate Usage" button to see results, which adds friction and doesn't provide immediate feedback. The scattered information layout makes it hard to follow the flow.

### 1.3 Scope
**In scope:**
- Multi-step wizard UI with horizontal stepper navigation
- Step 1: Review opening inventory (read-only)
- Step 2: Review day events (deliveries, transfers, spoilage)
- Step 3: Enter closing quantities with live calculations
- Step 4: Review summary and confirm close
- Real-time usage and discrepancy calculations as user types
- Visual comparison bars for expected vs actual quantities
- Formula explanation displayed clearly

**Out of scope:**
- Changes to backend API (reuse existing endpoints)
- Changes to database schema
- Mobile-specific layout optimizations
- Undo/reopen closed days

---

## 2. User Stories

### US-001: View Opening Inventory Before Closing
**As a** business operator
**I want** to see my opening inventory clearly before entering closing quantities
**So that** I understand my starting baseline for the day

**Acceptance Criteria:**
- [ ] Opening quantities are displayed in a clean table format
- [ ] The opening date and time are clearly shown
- [ ] Users cannot edit values in this step (read-only)
- [ ] Each ingredient shows name, unit type (kg/szt), and quantity

**Priority:** High

---

### US-002: Review Day Events (Deliveries, Transfers, Spoilage)
**As a** business operator
**I want** to see a summary of all day events before entering closing quantities
**So that** I understand what changed during the day

**Acceptance Criteria:**
- [ ] All deliveries are listed with ingredient, quantity, and cost
- [ ] All transfers are listed with ingredient, quantity, and direction
- [ ] All spoilage is listed with ingredient, quantity, and reason
- [ ] Totals are shown per category (total delivery cost, total items transferred, etc.)
- [ ] Per-ingredient impact is summarized

**Priority:** High

---

### US-003: Real-time Calculations While Entering Closing Quantities
**As a** business operator
**I want** to see usage and discrepancy calculations update instantly as I type
**So that** I can verify my counts before submitting

**Acceptance Criteria:**
- [ ] Usage column updates immediately when closing quantity is entered
- [ ] Discrepancy percentage updates in real-time
- [ ] Status indicator (OK/Warning/Critical) shows immediately
- [ ] No need to click a separate "Calculate" button
- [ ] Formula `Opening + Deliveries + Transfers - Spoilage - Closing = Usage` is visible

**Priority:** High

---

### US-004: Visual Discrepancy Comparison
**As a** business operator
**I want** to see a visual comparison of expected vs actual closing quantities
**So that** I can quickly identify significant discrepancies

**Acceptance Criteria:**
- [ ] Progress bar or visual indicator compares expected vs entered closing
- [ ] Color coding: green (OK ≤5%), yellow (Warning 5-10%), red (Critical >10%)
- [ ] Percentage difference is displayed numerically
- [ ] Large discrepancies are highlighted prominently

**Priority:** Medium

---

### US-005: Step-by-Step Navigation
**As a** business operator
**I want** to navigate through the closing process step by step
**So that** I can focus on one task at a time without feeling overwhelmed

**Acceptance Criteria:**
- [ ] Horizontal stepper shows 4 steps at the top
- [ ] Current step is highlighted
- [ ] Completed steps show checkmark and are clickable to go back
- [ ] Future steps are grayed out and not clickable
- [ ] Next/Back buttons navigate between steps
- [ ] Step 3 (Enter Closing) requires all fields before proceeding

**Priority:** High

---

### US-006: Final Confirmation with Full Summary
**As a** business operator
**I want** to review all data before confirming day close
**So that** I can catch any errors before it's finalized

**Acceptance Criteria:**
- [ ] Summary shows: date, opening/closing times, total income, total costs
- [ ] Discrepancy alerts are prominently displayed
- [ ] Calculated sales are shown
- [ ] Confirmation button requires explicit action
- [ ] Notes field is available for optional comments

**Priority:** High

---

## 3. Functional Requirements

### 3.1 Wizard Step Navigation
**ID:** FR-001
**Description:** The wizard displays 4 steps in a horizontal stepper. Users progress linearly but can click back to previous steps. The stepper shows step numbers, titles, and completion status.
**Priority:** High

### 3.2 Step 1: Opening Inventory Display
**ID:** FR-002
**Description:** Display a read-only table showing all ingredients with their opening quantities for the current day. Include the date and time the day was opened.
**Priority:** High

### 3.3 Step 2: Day Events Summary
**ID:** FR-003
**Description:** Display grouped lists of all mid-day events: Deliveries (with cost), Transfers (with direction), and Spoilage (with reason). Show per-ingredient totals and overall totals.
**Priority:** High

### 3.4 Step 3: Closing Inventory Entry with Live Calculations
**ID:** FR-004
**Description:** For each ingredient, display:
- Opening quantity (read-only)
- + Deliveries (read-only, green if >0)
- + Transfers (read-only, blue if >0)
- - Spoilage (read-only, red if >0)
- = Expected closing (calculated)
- Closing quantity (user input)
- Usage (live-calculated: Expected - Closing)
- Discrepancy % and status (live-calculated)

All calculations update in real-time as the user types.
**Priority:** High

### 3.5 Live Discrepancy Indicators
**ID:** FR-005
**Description:** As the user enters closing quantities, the system immediately calculates:
- Usage = Expected Closing - User's Closing Value
- Discrepancy % = |Usage - Expected Usage| / Expected Usage × 100
- Status: OK (≤5%), Warning (5-10%), Critical (>10%)

Display with appropriate colors and icons.
**Priority:** High

### 3.6 Expected Value Copy Function
**ID:** FR-006
**Description:** Provide a "Copy Expected Values" button that fills all closing quantity fields with their expected values. This serves as a quick starting point for adjustments.
**Priority:** Medium

### 3.7 Step 4: Confirmation Summary
**ID:** FR-007
**Description:** Display a complete summary before close:
- Day date and duration
- All discrepancy alerts (Warning/Critical)
- Calculated sales with revenue totals
- Delivery costs total
- Gross profit calculation
- Optional notes field
**Priority:** High

### 3.8 Form Validation
**ID:** FR-008
**Description:** All closing quantity fields are required. Values must be non-negative numbers. Weight-based ingredients allow decimals; count-based require integers.
**Priority:** High

---

## 4. User Interface

### 4.1 Wizard Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│                     ZAMKNIJ DZIEŃ: 2026-01-04                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐           │
│  │ ✓ 1     │────│ ✓ 2     │────│ ● 3     │────│ ○ 4     │           │
│  │Otwarcie │    │Zdarzenia│    │Zamknięcie│   │Potwierdź│           │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘           │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                                                                   │ │
│  │                    [STEP CONTENT HERE]                            │ │
│  │                                                                   │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  [Anuluj]                            [← Wstecz]  [Dalej →]       │ │
│  └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 Step 1: Opening Inventory

```
┌─────────────────────────────────────────────────────────────────────┐
│  📅 Dzień otwarty: 2026-01-04 o 08:00                               │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │ Składnik                    │ Stan otwarcia                      │ │
│  ├─────────────────────────────┼────────────────────────────────────┤ │
│  │ Mięso kebab (kg)            │                         10.50 kg   │ │
│  │ Bułki (szt)                 │                            50 szt  │ │
│  │ Warzywa mix (kg)            │                          5.00 kg   │ │
│  │ Sos czosnkowy (kg)          │                          2.00 kg   │ │
│  └─────────────────────────────┴────────────────────────────────────┘ │
│                                                                       │
│  ℹ️ Te wartości zostały wprowadzone przy otwieraniu dnia.            │
│     Przejdź dalej, aby zobaczyć zdarzenia w ciągu dnia.              │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.3 Step 2: Day Events

```
┌─────────────────────────────────────────────────────────────────────┐
│  📊 Zdarzenia dnia                                                   │
│                                                                       │
│  ┌─ 🚚 DOSTAWY (3 pozycje, łącznie 450.00 PLN) ─────────────────────┐│
│  │ Mięso kebab      +5.00 kg       250.00 PLN                       ││
│  │ Bułki            +30 szt         50.00 PLN                       ││
│  │ Warzywa mix      +3.00 kg       150.00 PLN                       ││
│  └──────────────────────────────────────────────────────────────────┘│
│                                                                       │
│  ┌─ 📦 TRANSFERY (1 pozycja) ───────────────────────────────────────┐│
│  │ Sos czosnkowy    +1.00 kg       (z magazynu do sklepu)           ││
│  └──────────────────────────────────────────────────────────────────┘│
│                                                                       │
│  ┌─ 🗑️ STRATY (2 pozycje) ──────────────────────────────────────────┐│
│  │ Mięso kebab      -0.50 kg       (przeterminowane)                ││
│  │ Bułki            -5 szt         (przesolone)                     ││
│  └──────────────────────────────────────────────────────────────────┘│
│                                                                       │
│  ┌─ Podsumowanie wpływu na stan ────────────────────────────────────┐│
│  │ Składnik         │ Otwarcie │ +Dostawy │ +Transfer │ -Straty │    │
│  │ Mięso kebab      │ 10.50 kg │ +5.00 kg │    -      │ -0.50 kg│    │
│  │ Bułki            │ 50 szt   │ +30 szt  │    -      │ -5 szt  │    │
│  │ Warzywa mix      │ 5.00 kg  │ +3.00 kg │    -      │    -    │    │
│  │ Sos czosnkowy    │ 2.00 kg  │    -     │ +1.00 kg  │    -    │    │
│  └──────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
```

### 4.4 Step 3: Enter Closing Quantities

```
┌─────────────────────────────────────────────────────────────────────┐
│  📝 Wprowadź ilości zamknięcia                                       │
│                                                                       │
│  Formuła: Otwarcie + Dostawy + Transfery - Straty - Zamknięcie = Zużycie
│                                    [Kopiuj oczekiwane]               │
│                                                                       │
│  ┌───────────────────────────────────────────────────────────────────┐
│  │ Składnik     │Otw.│+Dost│+Trans│-Straty│=Oczek.│Zamkn.│Zużycie│%  │
│  ├──────────────┼────┼─────┼──────┼───────┼───────┼──────┼───────┼───┤
│  │ Mięso (kg)   │10.5│+5.0 │  -   │ -0.5  │ 15.0  │[12.0]│  3.0  │✓  │
│  │              │    │green│      │  red  │ bold  │input │       │OK │
│  ├──────────────┼────┼─────┼──────┼───────┼───────┼──────┼───────┼───┤
│  │ Bułki (szt)  │ 50 │+30  │  -   │  -5   │  75   │[60]  │  15   │⚠️ │
│  │              │    │green│      │  red  │ bold  │input │       │8% │
│  ├──────────────┼────┼─────┼──────┼───────┼───────┼──────┼───────┼───┤
│  │ Warzywa (kg) │5.0 │+3.0 │  -   │   -   │  8.0  │[7.5] │  0.5  │✓  │
│  │              │    │green│      │       │ bold  │input │       │OK │
│  ├──────────────┼────┼─────┼──────┼───────┼───────┼──────┼───────┼───┤
│  │ Sos (kg)     │2.0 │  -  │ +1.0 │   -   │  3.0  │[1.0] │  2.0  │🔴 │
│  │              │    │     │ blue │       │ bold  │input │       │15%│
│  └──────────────┴────┴─────┴──────┴───────┴───────┴──────┴───────┴───┘
│                                                                       │
│  ┌─ Rozbieżności ───────────────────────────────────────────────────┐│
│  │ ⚠️ Bułki: 8% różnicy - poziom średni                              ││
│  │ 🔴 Sos czosnkowy: 15% różnicy - poziom wysoki                     ││
│  └──────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
```

### 4.5 Step 4: Confirmation

```
┌─────────────────────────────────────────────────────────────────────┐
│  ✅ Potwierdzenie zamknięcia dnia                                    │
│                                                                       │
│  ┌─ Podsumowanie ───────────────────────────────────────────────────┐│
│  │ 📅 Data: 2026-01-04 (sobota)                                      ││
│  │ ⏰ Otwarcie: 08:00  │  Zamknięcie: teraz                          ││
│  └──────────────────────────────────────────────────────────────────┘│
│                                                                       │
│  ┌─ ⚠️ Ostrzeżenia (2) ─────────────────────────────────────────────┐│
│  │ ⚠️ Bułki: 8% różnicy - poziom średni                              ││
│  │ 🔴 Sos czosnkowy: 15% różnicy - poziom wysoki                     ││
│  └──────────────────────────────────────────────────────────────────┘│
│                                                                       │
│  ┌─ 💰 Wyliczona sprzedaż ──────────────────────────────────────────┐│
│  │ Produkt          │ Ilość │ Cena    │ Przychód                     ││
│  │ Kebab duży       │   12  │ 25.00   │ 300.00 PLN                   ││
│  │ Kebab mały       │    8  │ 18.00   │ 144.00 PLN                   ││
│  │ Burger           │    5  │ 22.00   │ 110.00 PLN                   ││
│  ├──────────────────┴───────┴─────────┼──────────────────────────────┤│
│  │                      RAZEM PRZYCHÓD │           554.00 PLN        ││
│  └─────────────────────────────────────┴─────────────────────────────┘│
│                                                                       │
│  ┌─ 📊 Podsumowanie finansowe ──────────────────────────────────────┐│
│  │ Przychód:        554.00 PLN                                       ││
│  │ Koszty dostaw:   450.00 PLN                                       ││
│  │ ─────────────────────────                                         ││
│  │ Zysk brutto:     104.00 PLN                                       ││
│  └──────────────────────────────────────────────────────────────────┘│
│                                                                       │
│  ┌─ Notatki (opcjonalne) ───────────────────────────────────────────┐│
│  │ [                                                              ]  ││
│  └──────────────────────────────────────────────────────────────────┘│
│                                                                       │
│              [Zamknij dzień ⏹️]                                       │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.6 User Flow
```
[Open Wizard]
    → [Step 1: View Opening Inventory]
    → [Click "Next"]
    → [Step 2: View Day Events]
    → [Click "Next"]
    → [Step 3: Enter Closing Quantities]
        → (Real-time calculations as user types)
        → (Optional: "Copy Expected" button)
        → (Validation: all fields required)
    → [Click "Next"]
    → [Step 4: Review Summary]
        → (Optional: Add notes)
    → [Click "Close Day"]
    → [Confirmation Dialog]
    → [Success Toast & Modal Closes]
```

### 4.7 UI Elements

| Element | Type | Description |
|---------|------|-------------|
| Stepper | Component | Horizontal 4-step progress indicator with clickable completed steps |
| Step Title | Text | "Otwarcie" / "Zdarzenia" / "Zamknięcie" / "Potwierdź" |
| Opening Table | Read-only table | Ingredient name, unit, opening quantity |
| Events List | Grouped cards | Deliveries, Transfers, Spoilage with totals |
| Closing Input | Input field | Numeric input with validation |
| Usage Column | Calculated text | Live-updates: Expected - Closing |
| Discrepancy Badge | Status badge | Icon + percentage + color (green/yellow/red) |
| Copy Expected | Button | Fills all closing fields with expected values |
| Navigation | Button group | "Anuluj" / "Wstecz" / "Dalej" or "Zamknij dzień" |

**Note:** All UI labels and text are in Polish.

---

## 5. Edge Cases

### 5.1 No Day Events
**Scenario:** Day was opened but no deliveries, transfers, or spoilage recorded.
**Expected behavior:** Step 2 shows "Brak zdarzeń w ciągu dnia" message. Expected closing = Opening.

### 5.2 Zero Expected for Ingredient
**Scenario:** An ingredient has 0 expected closing (all was used/spoiled).
**Expected behavior:** Discrepancy calculation handles division by zero gracefully. Show "N/A" for percentage if expected usage is 0.

### 5.3 Negative Usage
**Scenario:** User enters closing quantity higher than expected (more stock than expected).
**Expected behavior:** Usage shows negative value. This indicates possible missed spoilage entry or counting error.

### 5.4 Decimal vs Integer Inputs
**Scenario:** User enters decimal for count-based ingredient (e.g., 5.5 bułki).
**Expected behavior:** For count-based ingredients, show validation error "Ilość musi być liczbą całkowitą".

### 5.5 Step Navigation with Validation Errors
**Scenario:** User tries to proceed from Step 3 with empty/invalid fields.
**Expected behavior:** Prevent navigation, highlight error fields, show message "Uzupełnij wszystkie pola przed kontynuacją".

### 5.6 Very Large Discrepancies
**Scenario:** Discrepancy exceeds 50%.
**Expected behavior:** Show as Critical (red), optionally prompt user to double-check values.

---

## 6. Error Handling

| Error | Message (Polish) | Action |
|-------|------------------|--------|
| Field required | "To pole jest wymagane" | Highlight field in red |
| Invalid number | "Wprowadź poprawną liczbę" | Highlight field, show error |
| Negative value | "Wartość nie może być ujemna" | Highlight field, show error |
| Integer required | "Ilość musi być liczbą całkowitą" | For count-based ingredients |
| API error | "Wystąpił błąd: {details}" | Show in error banner |
| Close failed | "Nie udało się zamknąć dnia: {details}" | Keep wizard open, show error |

---

## 7. Non-Functional Requirements

### 7.1 Performance
- Real-time calculations must complete within 50ms (no perceptible lag)
- Wizard should load within 500ms after clicking "Close Day" button

### 7.2 Accessibility
- All form inputs have proper labels
- Stepper is keyboard navigable
- Error messages are announced by screen readers
- Color coding is supplemented with icons (not color-only)

### 7.3 Responsiveness
- Wizard adapts to modal width (min 800px recommended)
- Tables use horizontal scroll if needed on smaller screens
- Sticky navigation buttons at bottom

---

## 8. Dependencies

### 8.1 Required Features
- Existing day opening/closing backend API
- Existing day summary endpoint (`GET /api/v1/daily-records/{id}/summary`)
- Existing close day endpoint (`POST /api/v1/daily-records/{id}/close`)

### 8.2 Related Data Models
- DailyRecord
- InventorySnapshot
- Delivery, StorageTransfer, Spoilage
- CalculatedSale

---

## 9. Success Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| User understanding | No clarification questions | User feedback |
| Data entry errors | Reduce by 50% | Compare pre/post discrepancy alerts |
| Time to close day | No increase | Session timing (optional) |
| User satisfaction | Positive feedback | Direct feedback |

---

## 10. Open Questions

- [x] Step navigation style - **Answered: Horizontal stepper with tabs**
- [x] Real-time vs button-click calculations - **Answered: Real-time**
- [x] Should we show historical comparison (yesterday's closing vs today's opening)? - **Answered: Yes**
- [x] Should there be a "Save draft" feature for partial entry? - **Answered: Yes**

---

## Change History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-04 | AI Assistant | Initial version |
