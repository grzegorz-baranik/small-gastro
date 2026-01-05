# Functional Specification: Employees & Shifts Management

## Metadata

| Field | Value |
|-------|-------|
| **Author** | AI Assistant |
| **Created** | 2026-01-04 |
| **Version** | 1.0 |
| **Status** | Draft |
| **Approved by** | - |

---

## 1. Overview

### 1.1 Purpose
Enable comprehensive employee and shift management for the gastro business, allowing owners to track who works when, manage positions with hourly rates, record wage expenses, and analyze labor costs through detailed reports.

### 1.2 Business Context
Small gastro businesses need to:
- Track which employees work each day and their hours
- Manage different positions (cook, cashier, etc.) with associated pay rates
- Record wage expenses and link them to specific employees
- Analyze labor costs to understand profitability and plan staffing

### 1.3 Scope
**In scope:**
- Employee management (CRUD operations)
- Position management with default hourly rates
- Shift assignments linked to daily records
- Wage expense recording with flexible periods (daily/weekly/bi-weekly/monthly)
- Labor cost analytics and reporting

**Out of scope:**
- Break tracking
- Overtime calculations
- Scheduling ahead (future shift planning)
- Payroll integration
- Tax calculations
- Employee self-service portal

---

## 2. User Stories

### US-001: Manage Positions
**As a** business owner
**I want** to define available positions with default hourly rates
**So that** I can categorize employees and have base rates for wage calculations

**Acceptance Criteria:**
- [ ] Can create a new position with name and default hourly rate
- [ ] Can view list of all positions
- [ ] Can edit position name and hourly rate
- [ ] Can delete position only if no employees are assigned
- [ ] Position names must be unique

**Priority:** High

---

### US-002: Manage Employees
**As a** business owner
**I want** to add and manage employee records
**So that** I can track my workforce

**Acceptance Criteria:**
- [ ] Can create employee with: name, position, hourly rate (optional override), active status
- [ ] Employee inherits position's default rate if no custom rate specified
- [ ] Can view list of all employees (with filter for active/inactive)
- [ ] Can edit employee details
- [ ] Can deactivate employee (soft delete - keeps history)
- [ ] Can reactivate inactive employee

**Priority:** High

---

### US-003: Assign Employees to Shifts
**As a** business owner
**I want** to assign employees to daily shifts with start/end times
**So that** I can track who worked and for how long

**Acceptance Criteria:**
- [ ] Can add one or more employees to a daily record
- [ ] Must specify start time and end time for each employee
- [ ] At least one employee must be assigned before closing the day
- [ ] Can edit shift times while the day is open
- [ ] Can remove employee from shift while day is open
- [ ] System calculates total hours worked automatically

**Priority:** High

---

### US-004: Record Wage Expenses
**As a** business owner
**I want** to record wage payments for employees
**So that** I can track labor costs as part of my expenses

**Acceptance Criteria:**
- [ ] A special "Wynagrodzenia" (Wages) expense category exists
- [ ] When recording wage expense, must select an employee
- [ ] Can specify period type: daily, weekly, bi-weekly, monthly
- [ ] Amount can be entered manually or calculated from shift hours
- [ ] Wage transactions appear in regular expense reports

**Priority:** High

---

### US-005: View Wage Analytics
**As a** business owner
**I want** to see aggregated wage reports by employee and month
**So that** I can analyze labor costs and make staffing decisions

**Acceptance Criteria:**
- [ ] View total wages paid per employee for selected month
- [ ] View total hours worked per employee for selected month
- [ ] View average cost per hour per employee
- [ ] Compare current month to previous month
- [ ] Filter by specific employee or view all
- [ ] Export data (optional enhancement)

**Priority:** Medium

---

## 3. Functional Requirements

### 3.1 Position Management
**ID:** FR-001
**Description:** System must support CRUD operations for employee positions. Each position has a unique name and a default hourly rate in PLN. Positions cannot be deleted if employees are assigned to them.
**Priority:** High

### 3.2 Employee Management
**ID:** FR-002
**Description:** System must support employee records with name, assigned position, optional custom hourly rate (overrides position default), and active/inactive status. Inactive employees are hidden from assignment dropdowns but retain historical data.
**Priority:** High

### 3.3 Shift Assignment
**ID:** FR-003
**Description:** When a daily record is open, the owner can assign employees with specific start and end times. Multiple employees can work the same day. The system validates that at least one employee is assigned before allowing day closure. Hours are calculated automatically from the time range.
**Priority:** High

### 3.4 Wage Expense Category
**ID:** FR-004
**Description:** A predefined expense category "Wynagrodzenia" (Wages) must exist in the system. This is a special category that, when selected for a transaction, requires employee selection and shows period type options.
**Priority:** High

### 3.5 Wage Transaction Recording
**ID:** FR-005
**Description:** Wage transactions extend regular transactions with: employee_id (required), period_type (daily/weekly/bi-weekly/monthly), period_start_date, period_end_date. The transaction amount can be manually entered or calculated from recorded shift hours for the period.
**Priority:** High

### 3.6 Labor Analytics
**ID:** FR-006
**Description:** A dedicated section in Reports/Analytics showing: per-employee wage totals, hours worked, cost per hour, and month-over-month comparison. Data can be filtered by date range and employee.
**Priority:** Medium

---

## 4. User Interface

### 4.1 Settings Page - New Sections

#### Positions Section
- Card with header "Stanowiska" (Positions)
- Table showing: Name, Hourly Rate (PLN/h)
- Add button opens modal with: Name input, Hourly Rate input
- Edit/Delete icons in each row

#### Employees Section
- Card with header "Pracownicy" (Employees)
- Toggle to show/hide inactive employees
- Table showing: Name, Position, Hourly Rate, Status (Active/Inactive badge)
- Add button opens modal with: Name input, Position dropdown, Hourly Rate input (optional, placeholder shows position default), Active checkbox
- Edit/Deactivate icons in each row

### 4.2 Daily Operations Page - Shift Assignment

When day is open, new "Zmiana" (Shift) section:
- List of assigned employees with time inputs
- Each row: Employee name, Start time (HH:MM), End time (HH:MM), Hours (calculated), Remove button
- Add employee button opens dropdown with active employees
- Validation message if trying to close day with no employees

### 4.3 Finances Page - Wage Transaction

When category "Wynagrodzenia" is selected:
- Additional employee dropdown appears (required)
- Period type selector: Dzienny/Tygodniowy/Dwutygodniowy/Miesięczny
- Period date range inputs
- Optional "Oblicz z godzin" (Calculate from hours) button

### 4.4 Reports Page - Labor Analytics Section

New tab or section "Wynagrodzenia":
- Month selector
- Employee filter (dropdown with "Wszyscy" option)
- Summary cards: Total wages, Total hours, Avg cost/hour
- Table: Employee, Hours, Wages, Cost/Hour, Change vs Previous Month
- Chart: Monthly wage trends (optional enhancement)

### 4.3 User Flow
```
Settings Page:
[Positions List] -> [Add Position Modal] -> [Save] -> [Updated List]
[Employees List] -> [Add Employee Modal] -> [Select Position] -> [Save] -> [Updated List]

Daily Operations:
[Open Day] -> [Shift Section] -> [Add Employee] -> [Set Times] -> [Close Day]
                                                                      |
                                                        [Validation: At least 1 employee]

Finances:
[New Transaction] -> [Select "Wynagrodzenia"] -> [Select Employee] -> [Set Period] -> [Save]

Reports:
[Select "Wynagrodzenia" Tab] -> [Select Month] -> [View Analytics]
```

### 4.4 UI Elements
| Element | Type | Description |
|---------|------|-------------|
| Stanowiska Table | Table | List of positions with CRUD actions |
| Pracownicy Table | Table | List of employees with filter and CRUD |
| Shift Assignment Card | Card | Section in daily operations for adding/managing shifts |
| Employee Time Inputs | Time Pickers | Start/end time for each employee's shift |
| Wage Period Selector | Radio Group | Daily/Weekly/Bi-weekly/Monthly options |
| Employee Dropdown | Select | Required when creating wage transaction |
| Analytics Cards | Card Grid | Summary stats for labor costs |
| Analytics Table | Table | Per-employee breakdown with period comparison |

**Note:** All UI labels and text should be in Polish.

---

## 5. Edge Cases

### 5.1 Delete Position with Employees
**Scenario:** User tries to delete a position that has employees assigned
**Expected behavior:** Show error message "Nie mozna usunac stanowiska z przypisanymi pracownikami" and prevent deletion

### 5.2 Deactivate Employee with Open Shift
**Scenario:** User tries to deactivate an employee who is assigned to today's open shift
**Expected behavior:** Allow deactivation but keep them in current day's shift. Hide from future assignment dropdowns.

### 5.3 Close Day Without Employees
**Scenario:** User tries to close a day with no employees assigned
**Expected behavior:** Show warning "Musisz dodac przynajmniej jednego pracownika do zmiany" and prevent closure

### 5.4 Overlapping Shift Times
**Scenario:** User enters end time before start time
**Expected behavior:** Show validation error "Godzina zakonczenia musi byc po godzinie rozpoczecia"

### 5.5 Delete Employee with Wage History
**Scenario:** User tries to delete an employee who has wage transactions
**Expected behavior:** Prevent deletion, only allow deactivation. Show message "Nie mozna usunac pracownika z historia wynagrodzen. Mozesz go dezaktywowac."

### 5.6 Calculate Wages with No Shifts
**Scenario:** User tries to auto-calculate wages for a period with no recorded shifts
**Expected behavior:** Show message "Brak zarejestrowanych godzin w wybranym okresie" and keep amount field empty

---

## 6. Error Handling

| Error | Message (Polish) | Action |
|-------|------------------|--------|
| Position name exists | "Stanowisko o tej nazwie juz istnieje" | Fix name and retry |
| Position has employees | "Nie mozna usunac stanowiska z przypisanymi pracownikami" | Reassign employees first |
| Employee name required | "Imie i nazwisko jest wymagane" | Fill in name field |
| Invalid hourly rate | "Stawka godzinowa musi byc wieksza od 0" | Enter valid rate |
| No shift employee | "Musisz dodac przynajmniej jednego pracownika do zmiany" | Add employee before closing |
| Invalid shift times | "Godzina zakonczenia musi byc po godzinie rozpoczecia" | Fix times |
| Wage amount required | "Kwota wynagrodzenia jest wymagana" | Enter amount |
| Employee required for wage | "Wybierz pracownika dla transakcji wynagrodzenia" | Select employee |

---

## 7. Non-Functional Requirements

### 7.1 Performance
- Position and employee lists should load within 500ms
- Shift data should be included in daily record response (no extra request)
- Analytics should load within 1 second for up to 12 months of data

### 7.2 Security
- All data accessible only by authenticated business owner
- Employee data is business-specific (no cross-business access)

### 7.3 Accessibility
- Form fields have proper labels for screen readers
- Time pickers support keyboard navigation
- Status badges have proper contrast ratios

---

## 8. Dependencies

### 8.1 Required Features
- Daily Records (existing) - shifts are linked to daily records
- Expense Categories (existing) - wages category extends existing system
- Transactions (existing) - wage transactions extend transaction model

### 8.2 Related Data Models
- DailyRecord - add shift assignments relationship
- Transaction - extend with employee_id and wage-specific fields
- ExpenseCategory - need special handling for "Wages" category

---

## 9. Success Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Feature adoption | 80% of users create at least 1 employee within first week | Database query |
| Shift recording | 90% of closed days have at least 1 shift recorded | Automated check |
| Wage tracking | 70% of wage transactions have employee assigned | Database query |

---

## 10. Open Questions

- [x] Should positions have default rates? **Yes, with employee override option**
- [x] How should shifts integrate with daily records? **Linked to DailyRecord**
- [x] What time tracking granularity? **Start and end time only**
- [x] What wage periods to support? **Daily, weekly, bi-weekly, monthly**
- [x] Employee data scope? **Basic: name, position, rate, status**
- [x] Multiple employees per shift? **Yes**
- [x] Analytics scope? **Full: wages, hours, cost/hour, comparison**
- [x] Multi-position per employee? **No, single position**

---

## Change History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-04 | AI Assistant | Initial version based on interview |
