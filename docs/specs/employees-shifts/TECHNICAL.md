# Technical Specification: Employees & Shifts Management

## Metadata

| Field | Value |
|-------|-------|
| **Author** | AI Assistant |
| **Created** | 2026-01-04 |
| **Version** | 1.0 |
| **Status** | Draft |
| **Functional Specification** | [Link](./README.md) |

---

## 1. Architecture Overview

### 1.1 Component Diagram
```
┌─────────────────────────────────────────────────────────────────────┐
│                           Frontend                                   │
│  ┌───────────────┐  ┌────────────────┐  ┌────────────────────────┐  │
│  │  SettingsPage │  │DailyOperations │  │     ReportsPage        │  │
│  │  - Positions  │  │  - Shifts      │  │  - WageAnalytics       │  │
│  │  - Employees  │  │                │  │                        │  │
│  └───────────────┘  └────────────────┘  └────────────────────────┘  │
│           │                 │                      │                 │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                        API Client                               │ │
│  │  positions.ts | employees.ts | shifts.ts | wageAnalytics.ts    │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Backend API                                  │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌──────────────┐  │
│  │ positions/ │  │ employees/ │  │  shifts/   │  │  analytics/  │  │
│  │   router   │  │   router   │  │   router   │  │wages router  │  │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └──────┬───────┘  │
│        │               │               │                │          │
│  ┌─────▼───────────────▼───────────────▼────────────────▼───────┐  │
│  │                      Services Layer                           │  │
│  │  PositionService | EmployeeService | ShiftService | Analytics │  │
│  └─────────────────────────────────────────────────────────────┬─┘  │
│                                                                 │    │
│  ┌──────────────────────────────────────────────────────────────▼─┐ │
│  │                      SQLAlchemy Models                         │ │
│  │  Position | Employee | ShiftAssignment | Transaction (extended)│ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
                      ┌─────────────────┐
                      │   PostgreSQL    │
                      │  - positions    │
                      │  - employees    │
                      │  - shift_assign │
                      │  - transactions │
                      └─────────────────┘
```

### 1.2 Components to Modify
- `Transaction` model - add `employee_id` and wage-specific fields
- `DailyRecord` model - add relationship to shift assignments
- `SettingsPage.tsx` - add Positions and Employees sections
- `DailyOperationsPage.tsx` - add Shift assignment section
- `ReportsPage.tsx` - add Wage Analytics tab
- `FinancesPage.tsx` - add employee selection for wage transactions

### 1.3 New Components
- `Position` model - store position definitions with default rates
- `Employee` model - store employee information
- `ShiftAssignment` model - link employees to daily records with times
- Position/Employee management UI components
- Shift assignment UI components
- Wage analytics components

---

## 2. API Endpoints

### 2.1 Positions

#### GET /api/v1/positions
List all positions.

**Response (200):**
```json
[
  {
    "id": 1,
    "name": "Kucharz",
    "hourly_rate": 25.00,
    "employee_count": 3,
    "created_at": "2026-01-01T10:00:00Z"
  }
]
```

#### POST /api/v1/positions
Create a new position.

**Request:**
```json
{
  "name": "Kasjer",
  "hourly_rate": 22.50
}
```

**Response (201):**
```json
{
  "id": 2,
  "name": "Kasjer",
  "hourly_rate": 22.50,
  "employee_count": 0,
  "created_at": "2026-01-04T12:00:00Z"
}
```

**Response (400):**
```json
{
  "detail": "Stanowisko o tej nazwie juz istnieje"
}
```

#### PUT /api/v1/positions/{id}
Update a position.

**Request:**
```json
{
  "name": "Kasjer",
  "hourly_rate": 24.00
}
```

#### DELETE /api/v1/positions/{id}
Delete a position (only if no employees assigned).

**Response (400):**
```json
{
  "detail": "Nie mozna usunac stanowiska z przypisanymi pracownikami"
}
```

---

### 2.2 Employees

#### GET /api/v1/employees
List employees.

**Query Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| include_inactive | boolean | No | Include inactive employees (default: false) |

**Response (200):**
```json
[
  {
    "id": 1,
    "name": "Jan Kowalski",
    "position_id": 1,
    "position_name": "Kucharz",
    "hourly_rate": 27.00,
    "is_active": true,
    "created_at": "2026-01-01T10:00:00Z"
  }
]
```

#### POST /api/v1/employees
Create a new employee.

**Request:**
```json
{
  "name": "Anna Nowak",
  "position_id": 2,
  "hourly_rate": null,
  "is_active": true
}
```

**Response (201):**
```json
{
  "id": 2,
  "name": "Anna Nowak",
  "position_id": 2,
  "position_name": "Kasjer",
  "hourly_rate": 22.50,
  "is_active": true,
  "created_at": "2026-01-04T12:00:00Z"
}
```

#### PUT /api/v1/employees/{id}
Update an employee.

#### PATCH /api/v1/employees/{id}/deactivate
Deactivate an employee (soft delete).

#### PATCH /api/v1/employees/{id}/activate
Reactivate an employee.

---

### 2.3 Shift Assignments

#### GET /api/v1/daily-records/{daily_record_id}/shifts
Get all shift assignments for a daily record.

**Response (200):**
```json
[
  {
    "id": 1,
    "employee_id": 1,
    "employee_name": "Jan Kowalski",
    "start_time": "08:00",
    "end_time": "16:00",
    "hours_worked": 8.0,
    "hourly_rate": 27.00
  }
]
```

#### POST /api/v1/daily-records/{daily_record_id}/shifts
Add employee to shift.

**Request:**
```json
{
  "employee_id": 1,
  "start_time": "08:00",
  "end_time": "16:00"
}
```

**Response (400 - invalid times):**
```json
{
  "detail": "Godzina zakonczenia musi byc po godzinie rozpoczecia"
}
```

#### PUT /api/v1/daily-records/{daily_record_id}/shifts/{shift_id}
Update shift times.

**Request:**
```json
{
  "start_time": "09:00",
  "end_time": "17:00"
}
```

#### DELETE /api/v1/daily-records/{daily_record_id}/shifts/{shift_id}
Remove employee from shift.

---

### 2.4 Wage Analytics

#### GET /api/v1/analytics/wages
Get wage analytics for a period.

**Query Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| month | integer | Yes | Month (1-12) |
| year | integer | Yes | Year |
| employee_id | integer | No | Filter by employee |

**Response (200):**
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

## 3. Database Schema

### 3.1 New Tables

```sql
-- Positions table
CREATE TABLE positions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    hourly_rate NUMERIC(10, 2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Employees table
CREATE TABLE employees (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    position_id INTEGER NOT NULL REFERENCES positions(id),
    hourly_rate_override NUMERIC(10, 2),  -- NULL means use position's rate
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_employees_position ON employees(position_id);
CREATE INDEX idx_employees_active ON employees(is_active);

-- Shift assignments table
CREATE TABLE shift_assignments (
    id SERIAL PRIMARY KEY,
    daily_record_id INTEGER NOT NULL REFERENCES daily_records(id) ON DELETE CASCADE,
    employee_id INTEGER NOT NULL REFERENCES employees(id),
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT unique_employee_per_day UNIQUE(daily_record_id, employee_id),
    CONSTRAINT valid_time_range CHECK (end_time > start_time)
);

CREATE INDEX idx_shift_assignments_daily_record ON shift_assignments(daily_record_id);
CREATE INDEX idx_shift_assignments_employee ON shift_assignments(employee_id);
```

### 3.2 Modifications to Existing Tables

```sql
-- Add wage-specific fields to transactions
ALTER TABLE transactions
ADD COLUMN employee_id INTEGER REFERENCES employees(id),
ADD COLUMN wage_period_type VARCHAR(20),  -- 'daily', 'weekly', 'biweekly', 'monthly'
ADD COLUMN wage_period_start DATE,
ADD COLUMN wage_period_end DATE;

CREATE INDEX idx_transactions_employee ON transactions(employee_id);
```

### 3.3 ERD Diagram
```
┌──────────────┐       ┌──────────────┐       ┌────────────────┐
│  positions   │       │  employees   │       │ daily_records  │
├──────────────┤       ├──────────────┤       ├────────────────┤
│ id (PK)      │◀──┐   │ id (PK)      │       │ id (PK)        │
│ name         │   └───│ position_id  │       │ date           │
│ hourly_rate  │       │ name         │       │ status         │
│ created_at   │       │ hourly_rate_ │       │ ...            │
│ updated_at   │       │   override   │       └───────┬────────┘
└──────────────┘       │ is_active    │               │
                       │ created_at   │               │
                       │ updated_at   │               │
                       └───────┬──────┘               │
                               │                      │
                               │    ┌─────────────────┘
                               │    │
                               ▼    ▼
                       ┌───────────────────┐
                       │ shift_assignments │
                       ├───────────────────┤
                       │ id (PK)           │
                       │ daily_record_id   │───▶ daily_records.id
                       │ employee_id       │───▶ employees.id
                       │ start_time        │
                       │ end_time          │
                       │ created_at        │
                       │ updated_at        │
                       └───────────────────┘

┌──────────────┐       ┌──────────────────────────────┐
│  employees   │       │        transactions          │
├──────────────┤       ├──────────────────────────────┤
│ id (PK)      │◀──────│ employee_id (FK, nullable)   │
│ ...          │       │ wage_period_type             │
└──────────────┘       │ wage_period_start            │
                       │ wage_period_end              │
                       │ ... (existing fields)        │
                       └──────────────────────────────┘
```

### 3.4 Alembic Migration

```python
# alembic/versions/{revision}_add_employees_shifts.py

def upgrade():
    # Create positions table
    op.create_table(
        'positions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('hourly_rate', sa.Numeric(10, 2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())
    )

    # Create employees table
    op.create_table(
        'employees',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('position_id', sa.Integer(), sa.ForeignKey('positions.id'), nullable=False),
        sa.Column('hourly_rate_override', sa.Numeric(10, 2), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())
    )
    op.create_index('idx_employees_position', 'employees', ['position_id'])
    op.create_index('idx_employees_active', 'employees', ['is_active'])

    # Create shift_assignments table
    op.create_table(
        'shift_assignments',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('daily_record_id', sa.Integer(), sa.ForeignKey('daily_records.id', ondelete='CASCADE'), nullable=False),
        sa.Column('employee_id', sa.Integer(), sa.ForeignKey('employees.id'), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('daily_record_id', 'employee_id', name='unique_employee_per_day'),
        sa.CheckConstraint('end_time > start_time', name='valid_time_range')
    )
    op.create_index('idx_shift_assignments_daily_record', 'shift_assignments', ['daily_record_id'])
    op.create_index('idx_shift_assignments_employee', 'shift_assignments', ['employee_id'])

    # Add wage columns to transactions
    op.add_column('transactions', sa.Column('employee_id', sa.Integer(), sa.ForeignKey('employees.id'), nullable=True))
    op.add_column('transactions', sa.Column('wage_period_type', sa.String(20), nullable=True))
    op.add_column('transactions', sa.Column('wage_period_start', sa.Date(), nullable=True))
    op.add_column('transactions', sa.Column('wage_period_end', sa.Date(), nullable=True))
    op.create_index('idx_transactions_employee', 'transactions', ['employee_id'])


def downgrade():
    op.drop_index('idx_transactions_employee', 'transactions')
    op.drop_column('transactions', 'wage_period_end')
    op.drop_column('transactions', 'wage_period_start')
    op.drop_column('transactions', 'wage_period_type')
    op.drop_column('transactions', 'employee_id')

    op.drop_table('shift_assignments')
    op.drop_table('employees')
    op.drop_table('positions')
```

---

## 4. SQLAlchemy Models

### 4.1 Position Model

```python
# app/models/position.py
from sqlalchemy import Column, Integer, String, Numeric, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Position(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    hourly_rate = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    employees = relationship("Employee", back_populates="position")
```

### 4.2 Employee Model

```python
# app/models/employee.py
from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=False, index=True)
    hourly_rate_override = Column(Numeric(10, 2), nullable=True)
    is_active = Column(Boolean, nullable=False, server_default="true", index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    position = relationship("Position", back_populates="employees")
    shift_assignments = relationship("ShiftAssignment", back_populates="employee")
    transactions = relationship("Transaction", back_populates="employee")

    @property
    def effective_hourly_rate(self):
        """Return override rate if set, otherwise position's default rate."""
        if self.hourly_rate_override is not None:
            return self.hourly_rate_override
        return self.position.hourly_rate
```

### 4.3 ShiftAssignment Model

```python
# app/models/shift_assignment.py
from sqlalchemy import Column, Integer, Time, DateTime, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timedelta
from app.core.database import Base


class ShiftAssignment(Base):
    __tablename__ = "shift_assignments"

    id = Column(Integer, primary_key=True, index=True)
    daily_record_id = Column(Integer, ForeignKey("daily_records.id", ondelete="CASCADE"), nullable=False, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('daily_record_id', 'employee_id', name='unique_employee_per_day'),
        CheckConstraint('end_time > start_time', name='valid_time_range'),
    )

    # Relationships
    daily_record = relationship("DailyRecord", back_populates="shift_assignments")
    employee = relationship("Employee", back_populates="shift_assignments")

    @property
    def hours_worked(self) -> float:
        """Calculate hours worked from start and end time."""
        start = datetime.combine(datetime.min, self.start_time)
        end = datetime.combine(datetime.min, self.end_time)
        delta = end - start
        return delta.total_seconds() / 3600
```

### 4.4 Transaction Model Updates

```python
# app/models/transaction.py (additions)
import enum

class WagePeriodType(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"


# Add to Transaction model:
employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True, index=True)
wage_period_type = Column(EnumColumn(WagePeriodType), nullable=True)
wage_period_start = Column(Date, nullable=True)
wage_period_end = Column(Date, nullable=True)

# Add relationship:
employee = relationship("Employee", back_populates="transactions")
```

### 4.5 DailyRecord Model Updates

```python
# Add to DailyRecord model:
shift_assignments = relationship("ShiftAssignment", back_populates="daily_record", cascade="all, delete-orphan")
```

---

## 5. Pydantic Schemas

### 5.1 Position Schemas

```python
# app/schemas/position.py
from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal


class PositionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    hourly_rate: Decimal = Field(..., gt=0, decimal_places=2)


class PositionUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    hourly_rate: Decimal | None = Field(None, gt=0, decimal_places=2)


class PositionResponse(BaseModel):
    id: int
    name: str
    hourly_rate: Decimal
    employee_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True
```

### 5.2 Employee Schemas

```python
# app/schemas/employee.py
from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal


class EmployeeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    position_id: int
    hourly_rate: Decimal | None = Field(None, gt=0, decimal_places=2)
    is_active: bool = True


class EmployeeUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    position_id: int | None = None
    hourly_rate: Decimal | None = Field(None, gt=0, decimal_places=2)


class EmployeeResponse(BaseModel):
    id: int
    name: str
    position_id: int
    position_name: str
    hourly_rate: Decimal  # Effective rate (override or position default)
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
```

### 5.3 ShiftAssignment Schemas

```python
# app/schemas/shift_assignment.py
from pydantic import BaseModel, Field, field_validator
from datetime import time
from decimal import Decimal


class ShiftAssignmentCreate(BaseModel):
    employee_id: int
    start_time: time
    end_time: time

    @field_validator('end_time')
    @classmethod
    def validate_end_time(cls, v, info):
        if 'start_time' in info.data and v <= info.data['start_time']:
            raise ValueError('Godzina zakonczenia musi byc po godzinie rozpoczecia')
        return v


class ShiftAssignmentUpdate(BaseModel):
    start_time: time
    end_time: time

    @field_validator('end_time')
    @classmethod
    def validate_end_time(cls, v, info):
        if 'start_time' in info.data and v <= info.data['start_time']:
            raise ValueError('Godzina zakonczenia musi byc po godzinie rozpoczecia')
        return v


class ShiftAssignmentResponse(BaseModel):
    id: int
    employee_id: int
    employee_name: str
    start_time: time
    end_time: time
    hours_worked: float
    hourly_rate: Decimal

    class Config:
        from_attributes = True
```

### 5.4 Wage Analytics Schemas

```python
# app/schemas/wage_analytics.py
from pydantic import BaseModel
from decimal import Decimal


class WageSummary(BaseModel):
    total_wages: Decimal
    total_hours: float
    avg_cost_per_hour: Decimal


class EmployeeWageStats(BaseModel):
    employee_id: int
    employee_name: str
    position_name: str
    hours_worked: float
    wages_paid: Decimal
    cost_per_hour: Decimal
    previous_month_wages: Decimal | None
    change_percent: float | None


class WageAnalyticsResponse(BaseModel):
    summary: WageSummary
    previous_month_summary: WageSummary | None
    by_employee: list[EmployeeWageStats]
```

---

## 6. Service Layer

### 6.1 PositionService

```python
# app/services/position_service.py
class PositionService:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> list[Position]:
        """Get all positions with employee counts."""
        pass

    def get_by_id(self, position_id: int) -> Position | None:
        """Get position by ID."""
        pass

    def create(self, data: PositionCreate) -> Position:
        """Create new position. Raises ValueError if name exists."""
        pass

    def update(self, position_id: int, data: PositionUpdate) -> Position:
        """Update position."""
        pass

    def delete(self, position_id: int) -> None:
        """Delete position. Raises ValueError if has employees."""
        pass
```

### 6.2 EmployeeService

```python
# app/services/employee_service.py
class EmployeeService:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, include_inactive: bool = False) -> list[Employee]:
        """Get all employees, optionally including inactive."""
        pass

    def get_by_id(self, employee_id: int) -> Employee | None:
        """Get employee by ID."""
        pass

    def create(self, data: EmployeeCreate) -> Employee:
        """Create new employee."""
        pass

    def update(self, employee_id: int, data: EmployeeUpdate) -> Employee:
        """Update employee details."""
        pass

    def deactivate(self, employee_id: int) -> Employee:
        """Soft delete - set is_active to False."""
        pass

    def activate(self, employee_id: int) -> Employee:
        """Reactivate employee."""
        pass
```

### 6.3 ShiftService

```python
# app/services/shift_service.py
class ShiftService:
    def __init__(self, db: Session):
        self.db = db

    def get_by_daily_record(self, daily_record_id: int) -> list[ShiftAssignment]:
        """Get all shifts for a daily record."""
        pass

    def create(self, daily_record_id: int, data: ShiftAssignmentCreate) -> ShiftAssignment:
        """Add employee to shift. Validates day is open."""
        pass

    def update(self, shift_id: int, data: ShiftAssignmentUpdate) -> ShiftAssignment:
        """Update shift times. Validates day is open."""
        pass

    def delete(self, shift_id: int) -> None:
        """Remove employee from shift. Validates day is open."""
        pass

    def validate_minimum_employees(self, daily_record_id: int) -> bool:
        """Check if at least one employee is assigned."""
        pass

    def calculate_hours_for_period(
        self,
        employee_id: int,
        start_date: date,
        end_date: date
    ) -> float:
        """Calculate total hours worked by employee in date range."""
        pass
```

### 6.4 WageAnalyticsService

```python
# app/services/wage_analytics_service.py
class WageAnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def get_analytics(
        self,
        month: int,
        year: int,
        employee_id: int | None = None
    ) -> WageAnalyticsResponse:
        """
        Get wage analytics for specified month.
        Includes comparison with previous month.
        """
        pass

    def get_employee_hours(
        self,
        employee_id: int,
        month: int,
        year: int
    ) -> float:
        """Get total hours worked by employee in month."""
        pass

    def get_employee_wages(
        self,
        employee_id: int,
        month: int,
        year: int
    ) -> Decimal:
        """Get total wages paid to employee in month."""
        pass
```

---

## 7. Frontend Components

### 7.1 File Structure

```
frontend/src/
├── api/
│   ├── positions.ts          # Position API client
│   ├── employees.ts          # Employee API client
│   ├── shifts.ts             # Shift assignment API client
│   └── wageAnalytics.ts      # Wage analytics API client
├── components/
│   ├── employees/
│   │   ├── PositionList.tsx
│   │   ├── PositionForm.tsx
│   │   ├── EmployeeList.tsx
│   │   ├── EmployeeForm.tsx
│   │   ├── ShiftAssignmentCard.tsx
│   │   ├── ShiftRow.tsx
│   │   └── AddEmployeeToShift.tsx
│   └── analytics/
│       ├── WageAnalyticsSummary.tsx
│       └── WageAnalyticsTable.tsx
├── pages/
│   └── (existing pages modified)
└── types/
    ├── position.ts
    ├── employee.ts
    ├── shift.ts
    └── wageAnalytics.ts
```

### 7.2 TypeScript Interfaces

```typescript
// types/position.ts
export interface Position {
  id: number;
  name: string;
  hourlyRate: number;
  employeeCount: number;
  createdAt: string;
}

export interface PositionCreate {
  name: string;
  hourlyRate: number;
}

// types/employee.ts
export interface Employee {
  id: number;
  name: string;
  positionId: number;
  positionName: string;
  hourlyRate: number;
  isActive: boolean;
  createdAt: string;
}

export interface EmployeeCreate {
  name: string;
  positionId: number;
  hourlyRate?: number;
  isActive: boolean;
}

// types/shift.ts
export interface ShiftAssignment {
  id: number;
  employeeId: number;
  employeeName: string;
  startTime: string;  // "HH:MM"
  endTime: string;    // "HH:MM"
  hoursWorked: number;
  hourlyRate: number;
}

export interface ShiftAssignmentCreate {
  employeeId: number;
  startTime: string;
  endTime: string;
}

// types/wageAnalytics.ts
export interface WageSummary {
  totalWages: number;
  totalHours: number;
  avgCostPerHour: number;
}

export interface EmployeeWageStats {
  employeeId: number;
  employeeName: string;
  positionName: string;
  hoursWorked: number;
  wagesPaid: number;
  costPerHour: number;
  previousMonthWages: number | null;
  changePercent: number | null;
}

export interface WageAnalyticsResponse {
  summary: WageSummary;
  previousMonthSummary: WageSummary | null;
  byEmployee: EmployeeWageStats[];
}
```

### 7.3 API Client

```typescript
// api/positions.ts
const API_BASE = import.meta.env.VITE_API_BASE_URL;

export const positionsApi = {
  getAll: async (): Promise<Position[]> => {
    const response = await fetch(`${API_BASE}/positions`);
    return response.json();
  },

  create: async (data: PositionCreate): Promise<Position> => {
    const response = await fetch(`${API_BASE}/positions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail);
    }
    return response.json();
  },

  update: async (id: number, data: Partial<PositionCreate>): Promise<Position> => {
    const response = await fetch(`${API_BASE}/positions/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return response.json();
  },

  delete: async (id: number): Promise<void> => {
    const response = await fetch(`${API_BASE}/positions/${id}`, {
      method: 'DELETE'
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail);
    }
  }
};
```

### 7.4 React Query Hooks

```typescript
// hooks/usePositions.ts
export function usePositions() {
  return useQuery({
    queryKey: ['positions'],
    queryFn: positionsApi.getAll
  });
}

export function useCreatePosition() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: positionsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['positions'] });
    }
  });
}

// hooks/useEmployees.ts
export function useEmployees(includeInactive: boolean = false) {
  return useQuery({
    queryKey: ['employees', { includeInactive }],
    queryFn: () => employeesApi.getAll(includeInactive)
  });
}

// hooks/useShifts.ts
export function useShifts(dailyRecordId: number) {
  return useQuery({
    queryKey: ['shifts', dailyRecordId],
    queryFn: () => shiftsApi.getByDailyRecord(dailyRecordId),
    enabled: !!dailyRecordId
  });
}

// hooks/useWageAnalytics.ts
export function useWageAnalytics(month: number, year: number, employeeId?: number) {
  return useQuery({
    queryKey: ['wageAnalytics', { month, year, employeeId }],
    queryFn: () => wageAnalyticsApi.get(month, year, employeeId)
  });
}
```

---

## 8. Security

### 8.1 Data Validation
- Position name: 1-100 characters, must be unique
- Employee name: 1-200 characters
- Hourly rates: Must be positive decimals
- Time inputs: Validated HH:MM format
- End time must be after start time

### 8.2 Authorization
- All endpoints require authentication (future consideration)
- Data is scoped to business owner (single-tenant for now)

### 8.3 Potential Threats
| Threat | Mitigation |
|--------|------------|
| SQL Injection | SQLAlchemy parameterized queries |
| XSS | React auto-escaping, no dangerouslySetInnerHTML |
| CSRF | SameSite cookies (future) |
| Data exposure | Proper response filtering, no internal IDs exposed |

---

## 9. Performance

### 9.1 Database Indexes
```sql
-- Already defined in migration
CREATE INDEX idx_employees_position ON employees(position_id);
CREATE INDEX idx_employees_active ON employees(is_active);
CREATE INDEX idx_shift_assignments_daily_record ON shift_assignments(daily_record_id);
CREATE INDEX idx_shift_assignments_employee ON shift_assignments(employee_id);
CREATE INDEX idx_transactions_employee ON transactions(employee_id);
```

### 9.2 Caching
- React Query default caching for API responses
- Position list cached for 5 minutes (rarely changes)
- Employee list cached for 1 minute

### 9.3 Query Optimizations
- Use `joinedload` for position data when loading employees
- Include shift assignments in daily record response
- Analytics queries use database aggregations, not Python loops

---

## 10. Testing

### 10.1 Unit Tests
- [ ] PositionService.create() - unique name validation
- [ ] PositionService.delete() - employee constraint
- [ ] EmployeeService.create() - position validation
- [ ] ShiftAssignment.hours_worked property calculation
- [ ] ShiftAssignmentCreate.validate_end_time()

### 10.2 Integration Tests
- [ ] POST /api/v1/positions - create and duplicate handling
- [ ] DELETE /api/v1/positions/{id} - with/without employees
- [ ] POST /api/v1/employees - with/without rate override
- [ ] POST /api/v1/daily-records/{id}/shifts - time validation
- [ ] GET /api/v1/analytics/wages - aggregation correctness

### 10.3 E2E Tests
- [ ] Full position creation → employee assignment flow
- [ ] Day open → add shifts → close day flow
- [ ] Wage transaction creation with employee selection
- [ ] Analytics report generation and filtering

---

## 11. Deployment Plan

### 11.1 Database Migration
```bash
# Backup database first
pg_dump -Fc small_gastro > backup_before_employees.dump

# Run migration
cd backend
alembic upgrade head
```

### 11.2 Deployment Steps
1. Deploy backend with new models and migrations
2. Run database migration
3. Deploy frontend with new UI components
4. Verify endpoints work correctly
5. Test shift assignment in daily operations

### 11.3 Rollback
```bash
# Revert migration
alembic downgrade -1

# Restore backup if needed
pg_restore -d small_gastro backup_before_employees.dump
```

---

## 12. Monitoring

### 12.1 Logs
- Log position/employee CRUD operations
- Log shift assignment changes
- Log wage transaction creation with employee_id

### 12.2 Metrics
- Number of employees created per week
- Average shifts per day
- Wage transactions vs total expense transactions ratio

---

## Change History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-04 | AI Assistant | Initial version |
