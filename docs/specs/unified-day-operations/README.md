# Functional Specification: Unified Day Operations

## Metadata

| Field | Value |
|-------|-------|
| **Author** | AI Assistant |
| **Created** | 2026-01-05 |
| **Version** | 1.0 |
| **Status** | Draft |
| **Approved by** | Pending |

---

## 1. Overview

### 1.1 Purpose
This feature provides a unified, wizard-based system for managing all daily operations in a food business. It combines shift scheduling, inventory management, and day lifecycle (opening → mid-day operations → closing) into a single cohesive workflow.

### 1.2 Business Context
Currently, shift management is tied to "today's date" only, making it impossible to manage shifts for past days or future planning. Daily operations (inventory, deliveries, spoilage, transfers) are scattered across different UI sections. This redesign consolidates all operations into a structured wizard that guides users through the complete day lifecycle.

### 1.3 Scope
**In scope:**
- Shift scheduling module with recurring templates and weekly calendar
- Day Operations Wizard (opening, mid-day, closing phases)
- Warehouse vs Kitchen inventory distinction
- Auto-calculation of sales from inventory differences
- Opening/managing any day (not just today)

**Out of scope:**
- Multi-location support
- Employee payroll integration
- Advanced inventory forecasting
- POS system integration

---

## 2. User Stories

### US-001: Schedule Employee Shifts in Advance
**As a** shop manager
**I want** to define employee shift schedules in advance
**So that** shifts are automatically populated when I open a day

**Acceptance Criteria:**
- [ ] Can create recurring shift templates (e.g., "Anna works Mon-Fri 8:00-16:00")
- [ ] Can view and edit weekly calendar showing all scheduled shifts
- [ ] Can override specific dates without changing the template
- [ ] Templates persist across weeks until modified

**Priority:** High

---

### US-002: Open Any Day with Auto-Populated Shifts
**As a** shop manager
**I want** to open any day (not just today) and have shifts auto-populated from the schedule
**So that** I don't have to manually enter shift information every day

**Acceptance Criteria:**
- [ ] Can open a day for any date (past, today, or future within reasonable range)
- [ ] Opening wizard shows pre-populated shifts from schedule
- [ ] Can confirm, modify, or remove auto-populated shifts
- [ ] Can add additional shifts not in the schedule

**Priority:** High

---

### US-003: Record Opening Inventory
**As a** shop manager
**I want** to record the kitchen inventory when opening a day
**So that** the system can calculate sales at end of day

**Acceptance Criteria:**
- [ ] Opening wizard prompts for kitchen inventory counts
- [ ] Previous day's closing inventory is shown as reference
- [ ] Can enter actual counts for each ingredient
- [ ] System flags significant discrepancies from expected values

**Priority:** High

---

### US-004: Transfer Stock from Warehouse to Kitchen
**As a** shop manager
**I want** to record transfers from warehouse to kitchen during the day
**So that** inventory calculations account for restocking

**Acceptance Criteria:**
- [ ] Can select ingredients and quantities to transfer
- [ ] Transfer reduces warehouse stock and increases kitchen stock
- [ ] All transfers are logged with timestamp
- [ ] Can make multiple transfers throughout the day

**Priority:** High

---

### US-005: Record Spoilage
**As a** shop manager
**I want** to record ingredients that are spoiled/wasted
**So that** inventory calculations don't count spoilage as sales

**Acceptance Criteria:**
- [ ] Can select ingredients and quantities that were spoiled
- [ ] Must provide reason for spoilage (expired, damaged, etc.)
- [ ] Spoilage reduces kitchen inventory
- [ ] Spoilage is tracked separately in reports

**Priority:** High

---

### US-006: Record Deliveries
**As a** shop manager
**I want** to record ingredient deliveries received during the day
**So that** inventory calculations account for new stock

**Acceptance Criteria:**
- [ ] Can enter delivery details (supplier, items, quantities, cost)
- [ ] Delivery increases warehouse stock
- [ ] Can attach delivery receipt/invoice reference
- [ ] Multiple deliveries per day supported

**Priority:** High

---

### US-007: Close Day with Auto-Calculated Sales
**As a** shop manager
**I want** to enter closing inventory and have sales auto-calculated
**So that** I know exactly what was sold without manual counting

**Acceptance Criteria:**
- [ ] Closing wizard prompts for end-of-day kitchen inventory
- [ ] System calculates: `sold = opening + deliveries + transfers - spoilage - closing`
- [ ] Shows calculated quantities for each menu item
- [ ] Can review and adjust calculated values before confirming
- [ ] Day summary shows revenue, costs, and profit

**Priority:** High

---

### US-008: View Day Summary
**As a** shop manager
**I want** to see a complete summary of any day's operations
**So that** I can review performance and identify issues

**Acceptance Criteria:**
- [ ] Summary shows: shifts worked, inventory movements, sales, revenue
- [ ] Can access summary for any closed day
- [ ] Summary includes any discrepancies or warnings
- [ ] Can export/print summary

**Priority:** Medium

---

## 3. Functional Requirements

### 3.1 Shift Scheduling Module
**ID:** FR-001
**Description:** A separate module for managing employee shift schedules. Includes:
- **Recurring Templates:** Define weekly patterns for each employee (days, start/end times)
- **Calendar View:** Visual weekly/monthly calendar showing all scheduled shifts
- **Override System:** Ability to modify specific dates without changing templates
- **Conflict Detection:** Warn if employee is double-booked

**Priority:** High

### 3.2 Day Operations Wizard
**ID:** FR-002
**Description:** A modal wizard that guides users through all daily operations. The wizard has three main phases:
1. **Opening Phase:** Confirm shifts, record opening inventory
2. **Mid-day Phase:** Record transfers, spoilage, deliveries (accessible anytime while day is open)
3. **Closing Phase:** Record closing inventory, review calculated sales, confirm and close

**Priority:** High

### 3.3 Inventory Location Tracking
**ID:** FR-003
**Description:** Track inventory in two locations:
- **Warehouse:** Long-term storage, receives deliveries
- **Kitchen:** Active cooking area, used for daily operations
- **Transfers:** Movement from warehouse to kitchen

**Priority:** High

### 3.4 Sales Auto-Calculation
**ID:** FR-004
**Description:** Calculate sold items using the formula:
```
sold_quantity = opening_inventory + deliveries + transfers - spoilage - closing_inventory
```
The system maps ingredient usage back to menu items sold based on recipes.

**Priority:** High

### 3.5 Day State Management
**ID:** FR-005
**Description:** A day can be in one of these states:
- **Not Started:** No record exists for this date
- **Open:** Day is active, operations can be recorded
- **Closed:** Day is finalized, read-only
- **Reopened:** Previously closed day opened for corrections (with audit trail)

**Priority:** High

---

## 4. User Interface

### 4.1 Module Structure

```
┌─────────────────────────────────────────────────────────┐
│  Settings Page                                          │
│  └── Shift Schedule Section (NEW)                       │
│      ├── Recurring Templates Tab                        │
│      └── Weekly Calendar Tab                            │
├─────────────────────────────────────────────────────────┤
│  Daily Operations Page                                  │
│  └── Day List (recent days with status indicators)      │
│      └── Click day → Day Operations Modal (Wizard)      │
│          ├── Step 1: Opening                            │
│          │   ├── Confirm Shifts                         │
│          │   └── Opening Inventory                      │
│          ├── Step 2: Mid-Day Operations                 │
│          │   ├── Warehouse Transfers                    │
│          │   ├── Spoilage                               │
│          │   └── Deliveries                             │
│          └── Step 3: Closing                            │
│              ├── Closing Inventory                      │
│              ├── Sales Summary (auto-calculated)        │
│              └── Day Summary & Close                    │
└─────────────────────────────────────────────────────────┘
```

### 4.2 User Flow

```
[Day List] → [Select Day] → [Day Operations Modal]
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
            [Day Not Open]                    [Day Is Open]
                    │                               │
            [Open Day Wizard]              [Continue Operations]
                    │                               │
            [Step 1: Opening]              [Step 2: Mid-Day]
            - Confirm shifts               - Add transfers
            - Enter opening inventory      - Record spoilage
                    │                      - Log deliveries
                    │                               │
                    └───────────┬───────────────────┘
                                │
                        [Step 3: Closing]
                        - Enter closing inventory
                        - Review calculated sales
                        - Confirm and close
                                │
                        [Day Summary View]
```

### 4.3 UI Elements

| Element | Type | Description |
|---------|------|-------------|
| Harmonogram zmian | Tab section | Shift scheduling with templates and calendar |
| Kreator dnia | Modal wizard | Main wizard for day operations |
| Krok 1: Otwarcie | Wizard step | Opening phase with shifts and inventory |
| Krok 2: Operacje | Wizard step | Mid-day operations (transfers, spoilage, deliveries) |
| Krok 3: Zamknięcie | Wizard step | Closing inventory and summary |
| Lista zmian | Data table | Shows scheduled/confirmed shifts |
| Formularz transferu | Form | Warehouse to kitchen transfer entry |
| Formularz strat | Form | Spoilage recording with reason |
| Podsumowanie dnia | Summary card | Final day summary with all metrics |

**Note:** All UI labels and text should be in Polish.

---

## 5. Edge Cases

### 5.1 Opening Day Without Schedule
**Scenario:** User opens a day but no shifts are scheduled for that date
**Expected behavior:** Show empty shift list with option to add shifts manually. Display info message: "Brak zaplanowanych zmian na ten dzień"

### 5.2 Negative Calculated Sales
**Scenario:** Closing inventory is higher than expected (opening + additions)
**Expected behavior:** Flag as discrepancy, show warning: "Wykryto rozbieżność w inwentarzu - stan końcowy większy niż oczekiwany". Allow user to review and correct values.

### 5.3 Reopening Closed Day
**Scenario:** User needs to correct a mistake on an already closed day
**Expected behavior:** Require confirmation with reason. Log the reopening in audit trail. Show warning that changes will affect historical reports.

### 5.4 Missing Opening Inventory
**Scenario:** User tries to close day without having entered opening inventory
**Expected behavior:** Prevent closing. Show error: "Nie można zamknąć dnia bez stanu początkowego magazynu"

### 5.5 Employee No Longer Active
**Scenario:** Scheduled shift is for an employee who has been deactivated
**Expected behavior:** Show shift with warning indicator. Allow removal or reassignment. Do not auto-confirm.

### 5.6 Overlapping Days
**Scenario:** User tries to open a new day while another day is still open
**Expected behavior:** Allow it (business may need to manage multiple days). Show clear indicator of which days are currently open.

---

## 6. Error Handling

| Error | Message (Polish) | Action |
|-------|------------------|--------|
| Day already open | "Ten dzień jest już otwarty" | Navigate to existing open day |
| No shifts confirmed | "Potwierdź przynajmniej jedną zmianę przed kontynuowaniem" | Must confirm at least one shift |
| Invalid inventory count | "Ilość musi być liczbą nieujemną" | Re-enter valid number |
| Transfer exceeds warehouse stock | "Niewystarczająca ilość w magazynie ({available} dostępne)" | Adjust transfer quantity |
| Missing required fields | "Wypełnij wszystkie wymagane pola" | Highlight missing fields |
| Network error | "Błąd połączenia. Spróbuj ponownie." | Retry button |
| Concurrent modification | "Dane zostały zmienione przez innego użytkownika. Odśwież stronę." | Refresh to get latest |

---

## 7. Non-Functional Requirements

### 7.1 Performance
- Wizard should load within 2 seconds
- Inventory calculations should complete within 500ms
- Schedule calendar should handle 50+ employees smoothly

### 7.2 Security
- Only authorized users can open/close days
- Audit trail for all inventory modifications
- Reopening closed days requires elevated permissions (future)

### 7.3 Accessibility
- Keyboard navigation through wizard steps
- Clear focus indicators
- Screen reader compatible labels

---

## 8. Dependencies

### 8.1 Required Features
- Employee management (existing)
- Position management (existing)
- Ingredient management (existing)
- Product/Recipe management (existing)

### 8.2 Related Data Models
- `Employee` - Workers who can be assigned shifts
- `Position` - Job roles
- `Ingredient` - Items tracked in inventory
- `Product` - Menu items with recipes
- `DailyRecord` - Day state and timestamps
- `ShiftAssignment` - Employee shift records (existing, needs modification)
- `InventorySnapshot` - Point-in-time inventory counts
- `InventoryLocation` (NEW) - Warehouse vs Kitchen distinction
- `ShiftTemplate` (NEW) - Recurring shift patterns

---

## 9. Success Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Time to open day | < 3 minutes | User testing |
| Time to close day | < 5 minutes | User testing |
| Inventory accuracy | 95% match with physical count | Compare calculated vs manual verification |
| User adoption | 100% of daily operations through wizard | Analytics tracking |

---

## 10. Open Questions

- [x] How should shift scheduling work? → Both templates + calendar
- [x] How should shift confirmation work on day open? → Auto-populate from schedule
- [x] Wizard vs tabs? → Wizard with step-by-step flow
- [x] Where to manage warehouse inventory? → Settings + day details
- [ ] Should there be a mobile-friendly version for inventory counting?
- [ ] How far back should days be openable? (7 days? 30 days? unlimited?)
- [ ] Should we track inventory by batch/expiry date?

---

## Change History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-05 | AI Assistant | Initial version based on user requirements interview |
