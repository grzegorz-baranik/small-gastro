# Technical Specification: Unified Day Operations

## Metadata

| Field | Value |
|-------|-------|
| **Author** | AI Assistant |
| **Created** | 2026-01-05 |
| **Version** | 1.0 |
| **Status** | Draft |
| **Functional Specification** | [Link](./README.md) |

---

## 1. Architecture Overview

### 1.1 Component Diagram
```
┌─────────────────────────────────────────────────────────────────┐
│                          Frontend                                │
│  ┌───────────────────┐  ┌───────────────────┐  ┌──────────────┐ │
│  │ DailyOperations   │  │ Settings Page     │  │   Context    │ │
│  │ Page              │  │ (Shift Schedule)  │  │              │ │
│  │  └─ DayWizard     │  │  └─ ShiftSchedule │  │ DailyRecord  │ │
│  │     Modal         │  │     Section       │  │ Context      │ │
│  └───────────────────┘  └───────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Backend API                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ daily_records   │  │ shift_templates │  │ shift_schedules │  │
│  │ router          │  │ router (NEW)    │  │ router (NEW)    │  │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘  │
│           │                    │                    │           │
│           ▼                    ▼                    ▼           │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                     Services Layer                          ││
│  │  DailyOperationsService │ ShiftTemplateService │            ││
│  │  InventoryService       │ ShiftScheduleService │            ││
│  │  SalesCalculationService                                    ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   PostgreSQL    │
                    │                 │
                    │ - shift_templates│
                    │ - shift_schedules│
                    │ - daily_records │
                    │ - inventory_*   │
                    └─────────────────┘
```

### 1.2 Components to Modify
- `DailyOperationsPage.tsx` - Replace inline shift section with link to wizard modal
- `DailyRecordContext.tsx` - Remove "todayRecord" concept, focus on selected day
- `SettingsPage.tsx` - Add ShiftScheduleSection
- `ShiftAssignment` model - Keep existing, add `from_template` flag
- `InventorySnapshot` model - Add `location` field (warehouse/kitchen)

### 1.3 New Components
- `ShiftTemplate` model - Recurring shift patterns
- `ShiftSchedule` model - Specific date overrides
- `DayOperationsWizard` component - Main wizard modal
- `ShiftScheduleSection` component - Templates + calendar view
- `ShiftTemplateService` - Template CRUD and generation
- `ShiftScheduleService` - Schedule management and conflict detection

---

## 2. API Endpoints

### 2.1 Shift Templates

#### Create Template
```http
POST /api/v1/shift-templates
```

**Request:**
```json
{
  "employee_id": 1,
  "day_of_week": 1,
  "start_time": "08:00",
  "end_time": "16:00"
}
```

**Response (201):**
```json
{
  "id": 1,
  "employee_id": 1,
  "employee_name": "Anna Kowalska",
  "day_of_week": 1,
  "day_name": "Poniedziałek",
  "start_time": "08:00",
  "end_time": "16:00",
  "created_at": "2026-01-05T12:00:00Z"
}
```

#### List Templates
```http
GET /api/v1/shift-templates?employee_id={id}
```

#### Delete Template
```http
DELETE /api/v1/shift-templates/{id}
```

---

### 2.2 Shift Schedule (Date Overrides)

#### Create/Update Schedule Entry
```http
PUT /api/v1/shift-schedules/{date}/{employee_id}
```

**Request:**
```json
{
  "start_time": "09:00",
  "end_time": "17:00",
  "is_day_off": false
}
```

**Response (200):**
```json
{
  "date": "2026-01-06",
  "employee_id": 1,
  "employee_name": "Anna Kowalska",
  "start_time": "09:00",
  "end_time": "17:00",
  "is_day_off": false,
  "is_override": true
}
```

#### Get Weekly Schedule
```http
GET /api/v1/shift-schedules/week?start_date=2026-01-06
```

**Response (200):**
```json
{
  "week_start": "2026-01-06",
  "week_end": "2026-01-12",
  "schedules": [
    {
      "date": "2026-01-06",
      "day_name": "Poniedziałek",
      "shifts": [
        {
          "employee_id": 1,
          "employee_name": "Anna Kowalska",
          "start_time": "08:00",
          "end_time": "16:00",
          "source": "template",
          "is_override": false
        }
      ]
    }
  ]
}
```

---

### 2.3 Day Operations Wizard

#### Get Day Wizard State
```http
GET /api/v1/daily-records/{id}/wizard-state
```

**Response (200):**
```json
{
  "daily_record_id": 1,
  "date": "2026-01-05",
  "status": "open",
  "current_step": "mid_day",
  "opening": {
    "completed": true,
    "shifts_confirmed": 3,
    "inventory_entered": true
  },
  "mid_day": {
    "transfers_count": 2,
    "spoilages_count": 0,
    "deliveries_count": 1
  },
  "closing": {
    "completed": false,
    "inventory_entered": false
  }
}
```

#### Complete Opening Step
```http
POST /api/v1/daily-records/{id}/complete-opening
```

**Request:**
```json
{
  "confirmed_shifts": [
    {"employee_id": 1, "start_time": "08:00", "end_time": "16:00"},
    {"employee_id": 2, "start_time": "10:00", "end_time": "18:00"}
  ],
  "opening_inventory": [
    {"ingredient_id": 1, "quantity": 50.0, "location": "kitchen"},
    {"ingredient_id": 2, "quantity": 100.0, "location": "kitchen"}
  ]
}
```

#### Get Pre-populated Shifts for Day
```http
GET /api/v1/daily-records/{date}/suggested-shifts
```

**Response (200):**
```json
{
  "date": "2026-01-05",
  "suggested_shifts": [
    {
      "employee_id": 1,
      "employee_name": "Anna Kowalska",
      "start_time": "08:00",
      "end_time": "16:00",
      "source": "template"
    }
  ]
}
```

#### Calculate Sales Preview
```http
GET /api/v1/daily-records/{id}/sales-preview
```

**Request Query Params:**
```
closing_inventory[1]=45.0&closing_inventory[2]=80.0
```

**Response (200):**
```json
{
  "ingredients_used": [
    {
      "ingredient_id": 1,
      "ingredient_name": "Mięso kebab",
      "opening": 50.0,
      "deliveries": 0.0,
      "transfers": 10.0,
      "spoilage": 0.0,
      "closing": 45.0,
      "used": 15.0,
      "unit": "kg"
    }
  ],
  "calculated_sales": [
    {
      "product_id": 1,
      "product_name": "Kebab duży",
      "estimated_quantity": 50,
      "unit_price_pln": 25.00,
      "total_revenue_pln": 1250.00
    }
  ],
  "summary": {
    "total_revenue_pln": 1250.00,
    "total_delivery_cost_pln": 0.00,
    "total_spoilage_cost_pln": 0.00,
    "gross_profit_pln": 1250.00
  },
  "warnings": []
}
```

---

### 2.4 Inventory Locations

#### Get Warehouse Inventory
```http
GET /api/v1/inventory/warehouse
```

**Response (200):**
```json
{
  "items": [
    {
      "ingredient_id": 1,
      "ingredient_name": "Mięso kebab",
      "quantity": 100.0,
      "unit": "kg",
      "last_updated": "2026-01-05T10:00:00Z"
    }
  ]
}
```

#### Record Transfer
```http
POST /api/v1/daily-records/{id}/transfers
```

**Request:**
```json
{
  "items": [
    {"ingredient_id": 1, "quantity": 10.0}
  ],
  "notes": "Poranny transfer"
}
```

---

## 3. Database Schema

### 3.1 New Tables

#### shift_templates
```sql
CREATE TABLE shift_templates (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    day_of_week INTEGER NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT unique_employee_day UNIQUE (employee_id, day_of_week),
    CONSTRAINT valid_time_range CHECK (end_time > start_time)
);

CREATE INDEX idx_shift_templates_employee ON shift_templates(employee_id);
CREATE INDEX idx_shift_templates_day ON shift_templates(day_of_week);
```

#### shift_schedule_overrides
```sql
CREATE TABLE shift_schedule_overrides (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    start_time TIME,
    end_time TIME,
    is_day_off BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT unique_employee_date UNIQUE (employee_id, date),
    CONSTRAINT valid_override_time CHECK (
        is_day_off = TRUE OR (start_time IS NOT NULL AND end_time IS NOT NULL AND end_time > start_time)
    )
);

CREATE INDEX idx_schedule_overrides_date ON shift_schedule_overrides(date);
CREATE INDEX idx_schedule_overrides_employee ON shift_schedule_overrides(employee_id);
```

### 3.2 Modifications to Existing Tables

#### inventory_snapshots - Add location
```sql
ALTER TABLE inventory_snapshots
ADD COLUMN location VARCHAR(20) NOT NULL DEFAULT 'kitchen'
CHECK (location IN ('warehouse', 'kitchen'));

-- Update index
CREATE INDEX idx_inventory_snapshots_location ON inventory_snapshots(location);
```

#### shift_assignments - Add source tracking
```sql
ALTER TABLE shift_assignments
ADD COLUMN source VARCHAR(20) NOT NULL DEFAULT 'manual'
CHECK (source IN ('template', 'schedule', 'manual'));

ALTER TABLE shift_assignments
ADD COLUMN confirmed BOOLEAN NOT NULL DEFAULT TRUE;
```

### 3.3 ERD Diagram
```
┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│   Employee       │       │  ShiftTemplate   │       │ ShiftSchedule    │
├──────────────────┤       ├──────────────────┤       │ Override         │
│ id (PK)          │◄──────│ employee_id (FK) │       ├──────────────────┤
│ name             │       │ day_of_week      │       │ employee_id (FK) │
│ position_id      │       │ start_time       │       │ date             │
│ hourly_rate      │       │ end_time         │       │ start_time       │
│ is_active        │       └──────────────────┘       │ end_time         │
└──────────────────┘                                  │ is_day_off       │
        │                                             └──────────────────┘
        │
        │ employee_id
        ▼
┌──────────────────┐       ┌──────────────────┐
│ ShiftAssignment  │       │  DailyRecord     │
├──────────────────┤       ├──────────────────┤
│ id (PK)          │──────▶│ id (PK)          │
│ daily_record_id  │       │ date             │
│ employee_id (FK) │       │ status           │
│ start_time       │       │ opened_at        │
│ end_time         │       │ closed_at        │
│ source           │       └──────────────────┘
│ confirmed        │               │
└──────────────────┘               │
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
        ▼                          ▼                          ▼
┌──────────────────┐   ┌──────────────────┐    ┌──────────────────┐
│ InventorySnapshot│   │    Delivery      │    │ StorageTransfer  │
├──────────────────┤   ├──────────────────┤    ├──────────────────┤
│ daily_record_id  │   │ daily_record_id  │    │ daily_record_id  │
│ ingredient_id    │   │ supplier_name    │    │ ingredient_id    │
│ quantity         │   │ items            │    │ quantity         │
│ snapshot_type    │   │ total_cost       │    │ from_location    │
│ location (NEW)   │   └──────────────────┘    │ to_location      │
└──────────────────┘                           └──────────────────┘
```

### 3.4 Alembic Migration

```python
# alembic/versions/010_add_shift_scheduling.py

def upgrade():
    # Create shift_templates table
    op.create_table(
        'shift_templates',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('employee_id', sa.Integer(), sa.ForeignKey('employees.id', ondelete='CASCADE'), nullable=False),
        sa.Column('day_of_week', sa.Integer(), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('employee_id', 'day_of_week', name='unique_employee_day'),
        sa.CheckConstraint('day_of_week BETWEEN 0 AND 6', name='valid_day_of_week'),
        sa.CheckConstraint('end_time > start_time', name='shift_templates_valid_time')
    )

    # Create shift_schedule_overrides table
    op.create_table(
        'shift_schedule_overrides',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('employee_id', sa.Integer(), sa.ForeignKey('employees.id', ondelete='CASCADE'), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=True),
        sa.Column('end_time', sa.Time(), nullable=True),
        sa.Column('is_day_off', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('employee_id', 'date', name='unique_employee_date')
    )

    # Add location to inventory_snapshots
    op.add_column('inventory_snapshots',
        sa.Column('location', sa.String(20), nullable=False, server_default='kitchen')
    )

    # Add source and confirmed to shift_assignments
    op.add_column('shift_assignments',
        sa.Column('source', sa.String(20), nullable=False, server_default='manual')
    )
    op.add_column('shift_assignments',
        sa.Column('confirmed', sa.Boolean(), nullable=False, server_default='true')
    )

    # Create indexes
    op.create_index('idx_shift_templates_employee', 'shift_templates', ['employee_id'])
    op.create_index('idx_schedule_overrides_date', 'shift_schedule_overrides', ['date'])
    op.create_index('idx_inventory_snapshots_location', 'inventory_snapshots', ['location'])


def downgrade():
    op.drop_index('idx_inventory_snapshots_location')
    op.drop_index('idx_schedule_overrides_date')
    op.drop_index('idx_shift_templates_employee')

    op.drop_column('shift_assignments', 'confirmed')
    op.drop_column('shift_assignments', 'source')
    op.drop_column('inventory_snapshots', 'location')

    op.drop_table('shift_schedule_overrides')
    op.drop_table('shift_templates')
```

---

## 4. SQLAlchemy Models

### 4.1 ShiftTemplate

```python
# app/models/shift_template.py

from sqlalchemy import Column, Integer, Time, DateTime, ForeignKey, UniqueConstraint, CheckConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class ShiftTemplate(Base):
    """
    Recurring shift pattern for an employee.
    Defines which days of the week an employee typically works.
    """
    __tablename__ = "shift_templates"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(
        Integer,
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False
    )
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('employee_id', 'day_of_week', name='unique_employee_day'),
        CheckConstraint('day_of_week BETWEEN 0 AND 6', name='valid_day_of_week'),
        CheckConstraint('end_time > start_time', name='shift_templates_valid_time'),
        Index("idx_shift_templates_employee", "employee_id"),
    )

    # Relationships
    employee = relationship("Employee", back_populates="shift_templates")
```

### 4.2 ShiftScheduleOverride

```python
# app/models/shift_schedule_override.py

from sqlalchemy import Column, Integer, Date, Time, Boolean, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class ShiftScheduleOverride(Base):
    """
    Override for a specific date, replacing the template schedule.
    Can mark a day off or change shift times for a specific date.
    """
    __tablename__ = "shift_schedule_overrides"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(
        Integer,
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False
    )
    date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=True)  # Null if is_day_off
    end_time = Column(Time, nullable=True)    # Null if is_day_off
    is_day_off = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('employee_id', 'date', name='unique_employee_date'),
        Index("idx_schedule_overrides_date", "date"),
        Index("idx_schedule_overrides_employee", "employee_id"),
    )

    # Relationships
    employee = relationship("Employee", back_populates="schedule_overrides")
```

---

## 5. Pydantic Schemas

### 5.1 Shift Template Schemas

```python
# app/schemas/shift_template.py

from pydantic import BaseModel, Field
from datetime import time, datetime
from typing import Optional


class ShiftTemplateCreate(BaseModel):
    employee_id: int
    day_of_week: int = Field(..., ge=0, le=6, description="0=Monday, 6=Sunday")
    start_time: time
    end_time: time

    class Config:
        json_schema_extra = {
            "example": {
                "employee_id": 1,
                "day_of_week": 0,
                "start_time": "08:00:00",
                "end_time": "16:00:00"
            }
        }


class ShiftTemplateResponse(BaseModel):
    id: int
    employee_id: int
    employee_name: str
    day_of_week: int
    day_name: str
    start_time: time
    end_time: time
    created_at: datetime

    class Config:
        from_attributes = True


class ShiftTemplateUpdate(BaseModel):
    start_time: Optional[time] = None
    end_time: Optional[time] = None
```

### 5.2 Weekly Schedule Schemas

```python
# app/schemas/shift_schedule.py

from pydantic import BaseModel
from datetime import date, time
from typing import List, Optional


class ScheduledShift(BaseModel):
    employee_id: int
    employee_name: str
    start_time: time
    end_time: time
    source: str  # 'template', 'override', 'manual'
    is_override: bool


class DaySchedule(BaseModel):
    date: date
    day_name: str
    shifts: List[ScheduledShift]


class WeeklyScheduleResponse(BaseModel):
    week_start: date
    week_end: date
    schedules: List[DaySchedule]


class ScheduleOverrideCreate(BaseModel):
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    is_day_off: bool = False
```

### 5.3 Day Wizard Schemas

```python
# app/schemas/day_wizard.py

from pydantic import BaseModel
from datetime import date, time
from typing import List, Optional
from decimal import Decimal


class ConfirmedShift(BaseModel):
    employee_id: int
    start_time: time
    end_time: time


class InventoryEntry(BaseModel):
    ingredient_id: int
    quantity: Decimal
    location: str = "kitchen"


class CompleteOpeningRequest(BaseModel):
    confirmed_shifts: List[ConfirmedShift]
    opening_inventory: List[InventoryEntry]


class WizardStepStatus(BaseModel):
    completed: bool


class OpeningStatus(WizardStepStatus):
    shifts_confirmed: int
    inventory_entered: bool


class MidDayStatus(BaseModel):
    transfers_count: int
    spoilages_count: int
    deliveries_count: int


class ClosingStatus(WizardStepStatus):
    inventory_entered: bool


class WizardStateResponse(BaseModel):
    daily_record_id: int
    date: date
    status: str
    current_step: str
    opening: OpeningStatus
    mid_day: MidDayStatus
    closing: ClosingStatus


class SuggestedShift(BaseModel):
    employee_id: int
    employee_name: str
    start_time: time
    end_time: time
    source: str


class SuggestedShiftsResponse(BaseModel):
    date: date
    suggested_shifts: List[SuggestedShift]
```

---

## 6. Service Layer

### 6.1 ShiftTemplateService

```python
# app/services/shift_template_service.py

from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from app.models.shift_template import ShiftTemplate
from app.models.shift_schedule_override import ShiftScheduleOverride
from app.schemas.shift_template import ShiftTemplateCreate


class ShiftTemplateService:
    DAY_NAMES = ['Poniedziałek', 'Wtorek', 'Środa', 'Czwartek', 'Piątek', 'Sobota', 'Niedziela']

    def __init__(self, db: Session):
        self.db = db

    def create(self, data: ShiftTemplateCreate) -> ShiftTemplate:
        """Creates a new shift template."""
        template = ShiftTemplate(**data.model_dump())
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template

    def get_by_employee(self, employee_id: int) -> List[ShiftTemplate]:
        """Gets all templates for an employee."""
        return self.db.query(ShiftTemplate)\
            .filter(ShiftTemplate.employee_id == employee_id)\
            .order_by(ShiftTemplate.day_of_week)\
            .all()

    def get_shifts_for_date(self, target_date: date) -> List[dict]:
        """
        Gets scheduled shifts for a specific date.
        Combines templates with overrides, where overrides take precedence.
        """
        day_of_week = target_date.weekday()

        # Get templates for this day of week
        templates = self.db.query(ShiftTemplate)\
            .filter(ShiftTemplate.day_of_week == day_of_week)\
            .all()

        # Get overrides for this date
        overrides = self.db.query(ShiftScheduleOverride)\
            .filter(ShiftScheduleOverride.date == target_date)\
            .all()

        override_map = {o.employee_id: o for o in overrides}

        shifts = []
        seen_employees = set()

        # Process templates, applying overrides
        for template in templates:
            override = override_map.get(template.employee_id)

            if override:
                if override.is_day_off:
                    continue  # Skip - employee has day off
                shifts.append({
                    'employee_id': template.employee_id,
                    'employee': template.employee,
                    'start_time': override.start_time,
                    'end_time': override.end_time,
                    'source': 'override'
                })
            else:
                shifts.append({
                    'employee_id': template.employee_id,
                    'employee': template.employee,
                    'start_time': template.start_time,
                    'end_time': template.end_time,
                    'source': 'template'
                })

            seen_employees.add(template.employee_id)

        # Add overrides for employees without templates (extra shifts)
        for override in overrides:
            if override.employee_id not in seen_employees and not override.is_day_off:
                shifts.append({
                    'employee_id': override.employee_id,
                    'employee': override.employee,
                    'start_time': override.start_time,
                    'end_time': override.end_time,
                    'source': 'override'
                })

        return shifts

    def delete(self, template_id: int) -> bool:
        """Deletes a shift template."""
        template = self.db.query(ShiftTemplate).filter(ShiftTemplate.id == template_id).first()
        if template:
            self.db.delete(template)
            self.db.commit()
            return True
        return False
```

### 6.2 DayWizardService

```python
# app/services/day_wizard_service.py

from sqlalchemy.orm import Session
from datetime import date
from typing import List
from decimal import Decimal
from app.models import DailyRecord, ShiftAssignment, InventorySnapshot
from app.schemas.day_wizard import CompleteOpeningRequest, WizardStateResponse


class DayWizardService:
    def __init__(self, db: Session):
        self.db = db
        self.template_service = ShiftTemplateService(db)

    def get_wizard_state(self, daily_record_id: int) -> WizardStateResponse:
        """Gets the current state of the day wizard."""
        record = self.db.query(DailyRecord).get(daily_record_id)

        shifts_count = len(record.shift_assignments)
        has_opening_inventory = any(
            s.snapshot_type == 'opening'
            for s in record.inventory_snapshots
        )
        has_closing_inventory = any(
            s.snapshot_type == 'closing'
            for s in record.inventory_snapshots
        )

        # Determine current step
        if not has_opening_inventory:
            current_step = 'opening'
        elif record.status == 'open':
            current_step = 'mid_day'
        else:
            current_step = 'closing'

        return WizardStateResponse(
            daily_record_id=record.id,
            date=record.date,
            status=record.status.value,
            current_step=current_step,
            opening={
                'completed': has_opening_inventory,
                'shifts_confirmed': shifts_count,
                'inventory_entered': has_opening_inventory
            },
            mid_day={
                'transfers_count': len(record.storage_transfers),
                'spoilages_count': len(record.spoilages),
                'deliveries_count': len(record.deliveries)
            },
            closing={
                'completed': record.status == 'closed',
                'inventory_entered': has_closing_inventory
            }
        )

    def get_suggested_shifts(self, target_date: date) -> List[dict]:
        """Gets auto-populated shifts from schedule for a date."""
        return self.template_service.get_shifts_for_date(target_date)

    def complete_opening(self, daily_record_id: int, data: CompleteOpeningRequest):
        """Completes the opening step of the wizard."""
        record = self.db.query(DailyRecord).get(daily_record_id)

        # Create shift assignments
        for shift in data.confirmed_shifts:
            assignment = ShiftAssignment(
                daily_record_id=daily_record_id,
                employee_id=shift.employee_id,
                start_time=shift.start_time,
                end_time=shift.end_time,
                source='template',  # or determine from schedule
                confirmed=True
            )
            self.db.add(assignment)

        # Create opening inventory snapshots
        for inv in data.opening_inventory:
            snapshot = InventorySnapshot(
                daily_record_id=daily_record_id,
                ingredient_id=inv.ingredient_id,
                quantity=inv.quantity,
                snapshot_type='opening',
                location=inv.location
            )
            self.db.add(snapshot)

        self.db.commit()
        return self.get_wizard_state(daily_record_id)

    def calculate_sales_preview(
        self,
        daily_record_id: int,
        closing_inventory: dict[int, Decimal]
    ) -> dict:
        """
        Calculates preview of sales based on closing inventory.
        Formula: used = opening + deliveries + transfers - spoilage - closing
        """
        record = self.db.query(DailyRecord).get(daily_record_id)

        # Gather all inventory movements
        opening = {s.ingredient_id: s.quantity for s in record.inventory_snapshots
                   if s.snapshot_type == 'opening'}

        deliveries = {}
        for d in record.deliveries:
            for item in d.items:
                deliveries[item.ingredient_id] = deliveries.get(item.ingredient_id, 0) + item.quantity

        transfers = {}
        for t in record.storage_transfers:
            if t.to_location == 'kitchen':
                transfers[t.ingredient_id] = transfers.get(t.ingredient_id, 0) + t.quantity

        spoilage = {}
        for s in record.spoilages:
            spoilage[s.ingredient_id] = spoilage.get(s.ingredient_id, 0) + s.quantity

        # Calculate used quantities
        ingredients_used = []
        for ing_id, opening_qty in opening.items():
            used = (
                opening_qty
                + deliveries.get(ing_id, 0)
                + transfers.get(ing_id, 0)
                - spoilage.get(ing_id, 0)
                - closing_inventory.get(ing_id, 0)
            )
            ingredients_used.append({
                'ingredient_id': ing_id,
                'opening': opening_qty,
                'deliveries': deliveries.get(ing_id, 0),
                'transfers': transfers.get(ing_id, 0),
                'spoilage': spoilage.get(ing_id, 0),
                'closing': closing_inventory.get(ing_id, 0),
                'used': max(0, used)  # Prevent negative
            })

        # Map to products (using recipe data)
        # ... product calculation logic ...

        return {
            'ingredients_used': ingredients_used,
            'calculated_sales': [],  # Filled by product mapping
            'summary': {},
            'warnings': []
        }
```

---

## 7. Frontend Components

### 7.1 File Structure

```
frontend/src/
├── api/
│   ├── shiftTemplates.ts          # Template CRUD
│   ├── shiftSchedules.ts          # Schedule/calendar API
│   └── dayWizard.ts               # Wizard state API
├── components/
│   ├── employees/
│   │   ├── ShiftScheduleSection/
│   │   │   ├── index.tsx          # Main section
│   │   │   ├── TemplatesTab.tsx   # Recurring templates
│   │   │   └── CalendarTab.tsx    # Weekly calendar
│   │   └── index.ts
│   └── daily/
│       ├── DayOperationsWizard/
│       │   ├── index.tsx          # Main wizard modal
│       │   ├── OpeningStep.tsx    # Step 1: Shifts + Opening inventory
│       │   ├── MidDayStep.tsx     # Step 2: Transfers, spoilage, deliveries
│       │   ├── ClosingStep.tsx    # Step 3: Closing inventory + summary
│       │   └── WizardStepper.tsx  # Progress indicator
│       └── index.ts
├── hooks/
│   └── useWizardState.ts          # Wizard state management
└── types/
    ├── shiftTemplate.ts
    └── dayWizard.ts
```

### 7.2 TypeScript Interfaces

```typescript
// types/shiftTemplate.ts

export interface ShiftTemplate {
  id: number;
  employeeId: number;
  employeeName: string;
  dayOfWeek: number;
  dayName: string;
  startTime: string;
  endTime: string;
  createdAt: string;
}

export interface ShiftTemplateCreate {
  employeeId: number;
  dayOfWeek: number;
  startTime: string;
  endTime: string;
}

export interface ScheduledShift {
  employeeId: number;
  employeeName: string;
  startTime: string;
  endTime: string;
  source: 'template' | 'override' | 'manual';
  isOverride: boolean;
}

export interface DaySchedule {
  date: string;
  dayName: string;
  shifts: ScheduledShift[];
}

export interface WeeklySchedule {
  weekStart: string;
  weekEnd: string;
  schedules: DaySchedule[];
}
```

```typescript
// types/dayWizard.ts

export interface WizardState {
  dailyRecordId: number;
  date: string;
  status: 'open' | 'closed';
  currentStep: 'opening' | 'mid_day' | 'closing';
  opening: {
    completed: boolean;
    shiftsConfirmed: number;
    inventoryEntered: boolean;
  };
  midDay: {
    transfersCount: number;
    spoilagesCount: number;
    deliveriesCount: number;
  };
  closing: {
    completed: boolean;
    inventoryEntered: boolean;
  };
}

export interface SuggestedShift {
  employeeId: number;
  employeeName: string;
  startTime: string;
  endTime: string;
  source: 'template' | 'override';
}

export interface ConfirmedShift {
  employeeId: number;
  startTime: string;
  endTime: string;
}

export interface InventoryEntry {
  ingredientId: number;
  quantity: number;
  location: 'warehouse' | 'kitchen';
}

export interface CompleteOpeningRequest {
  confirmedShifts: ConfirmedShift[];
  openingInventory: InventoryEntry[];
}
```

### 7.3 Wizard Component Structure

```typescript
// components/daily/DayOperationsWizard/index.tsx

import { useState, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import Modal from '../../common/Modal';
import WizardStepper from './WizardStepper';
import OpeningStep from './OpeningStep';
import MidDayStep from './MidDayStep';
import ClosingStep from './ClosingStep';
import { getWizardState } from '../../../api/dayWizard';
import type { WizardState } from '../../../types/dayWizard';

interface DayOperationsWizardProps {
  isOpen: boolean;
  onClose: () => void;
  dailyRecordId: number;
  date: string;
}

export default function DayOperationsWizard({
  isOpen,
  onClose,
  dailyRecordId,
  date
}: DayOperationsWizardProps) {
  const { t } = useTranslation();
  const [activeStep, setActiveStep] = useState(0);

  const { data: wizardState, isLoading } = useQuery({
    queryKey: ['wizardState', dailyRecordId],
    queryFn: () => getWizardState(dailyRecordId),
    enabled: isOpen && !!dailyRecordId
  });

  // Sync active step with wizard state
  useEffect(() => {
    if (wizardState) {
      const stepMap = { opening: 0, mid_day: 1, closing: 2 };
      setActiveStep(stepMap[wizardState.currentStep]);
    }
  }, [wizardState]);

  const steps = [
    { label: t('dayWizard.steps.opening'), key: 'opening' },
    { label: t('dayWizard.steps.midDay'), key: 'mid_day' },
    { label: t('dayWizard.steps.closing'), key: 'closing' }
  ];

  const renderStep = () => {
    switch (activeStep) {
      case 0:
        return (
          <OpeningStep
            dailyRecordId={dailyRecordId}
            date={date}
            onComplete={() => setActiveStep(1)}
          />
        );
      case 1:
        return (
          <MidDayStep
            dailyRecordId={dailyRecordId}
            onProceedToClosing={() => setActiveStep(2)}
          />
        );
      case 2:
        return (
          <ClosingStep
            dailyRecordId={dailyRecordId}
            onComplete={onClose}
          />
        );
      default:
        return null;
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`${t('dayWizard.title')} - ${date}`}
      size="xl"
    >
      <WizardStepper steps={steps} activeStep={activeStep} />
      <div className="mt-6">
        {isLoading ? <LoadingSpinner /> : renderStep()}
      </div>
    </Modal>
  );
}
```

---

## 8. Security

### 8.1 Data Validation
- All time inputs validated: end_time > start_time
- day_of_week constrained to 0-6 range
- Inventory quantities must be non-negative
- Employee must exist and be active for shift assignment

### 8.2 Authorization
- Only authenticated users can access day operations
- Future: Role-based permissions for reopening closed days

### 8.3 Potential Threats
| Threat | Mitigation |
|--------|------------|
| Inventory manipulation | Audit trail on all changes, validation on calculations |
| Unauthorized day reopening | Require elevated permissions, log all reopen events |
| Data injection | Pydantic validation on all inputs, parameterized queries |

---

## 9. Performance

### 9.1 Database Indexes
```sql
-- Already defined in migration
CREATE INDEX idx_shift_templates_employee ON shift_templates(employee_id);
CREATE INDEX idx_shift_templates_day ON shift_templates(day_of_week);
CREATE INDEX idx_schedule_overrides_date ON shift_schedule_overrides(date);
CREATE INDEX idx_inventory_snapshots_location ON inventory_snapshots(location);
```

### 9.2 Caching
- React Query caches wizard state with 30-second stale time
- Weekly schedule cached for 5 minutes (invalidated on changes)

### 9.3 Query Optimizations
- Eager load relationships when fetching daily record for wizard
- Batch insert for opening inventory snapshots
- Single query for weekly schedule generation

---

## 10. Testing

### 10.1 Unit Tests
- [ ] ShiftTemplateService.create()
- [ ] ShiftTemplateService.get_shifts_for_date() with overrides
- [ ] DayWizardService.calculate_sales_preview()
- [ ] Pydantic schema validation for all new schemas

### 10.2 Integration Tests
- [ ] POST /api/v1/shift-templates
- [ ] GET /api/v1/shift-schedules/week
- [ ] POST /api/v1/daily-records/{id}/complete-opening
- [ ] GET /api/v1/daily-records/{id}/sales-preview

### 10.3 E2E Tests
- [ ] Full day lifecycle: open → mid-day operations → close
- [ ] Shift template creation and auto-population
- [ ] Calendar override flow

---

## 11. Deployment Plan

### 11.1 Database Migration
```bash
docker compose exec backend alembic upgrade head
```

### 11.2 Deployment Steps
1. Deploy backend with new migration
2. Run migration on database
3. Deploy frontend with new wizard components
4. Verify wizard loads correctly
5. Test shift template creation

### 11.3 Rollback
```bash
docker compose exec backend alembic downgrade -1
```

---

## 12. Monitoring

### 12.1 Logs
- Log all day open/close events
- Log inventory calculation discrepancies
- Log shift template modifications

### 12.2 Metrics
- Time to complete opening step
- Time to complete closing step
- Number of inventory discrepancies per week
- Shift schedule utilization rate

---

## Change History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-05 | AI Assistant | Initial version |
