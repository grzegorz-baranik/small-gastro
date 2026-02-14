# Technical Specification: Sales Tracking Hybrid

## Metadata

| Field | Value |
|-------|-------|
| **Author** | AI Assistant |
| **Created** | 2026-01-06 |
| **Version** | 1.0 |
| **Status** | Draft |
| **Functional Specification** | [README.md](./README.md) |

---

## 1. Architecture Overview

### 1.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                           FRONTEND                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐  │
│  │ SalesEntryPage  │  │ Reconciliation  │  │ InsightsPage        │  │
│  │ (touch-optimized│  │ WizardStep      │  │ (popularity, hours, │  │
│  │  POS interface) │  │                 │  │  portion accuracy)  │  │
│  └────────┬────────┘  └────────┬────────┘  └──────────┬──────────┘  │
│           │                    │                      │             │
│  ┌────────▼────────────────────▼──────────────────────▼──────────┐  │
│  │                  React Query + Context                        │  │
│  │  (useSalesEntry, useReconciliation, useSalesInsights hooks)   │  │
│  └────────┬──────────────────────────────────────────────────────┘  │
└───────────┼─────────────────────────────────────────────────────────┘
            │ HTTP
┌───────────▼─────────────────────────────────────────────────────────┐
│                           BACKEND                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐  │
│  │ recorded_sales  │  │ reconciliation  │  │ sales_insights      │  │
│  │ router          │  │ router          │  │ router              │  │
│  └────────┬────────┘  └────────┬────────┘  └──────────┬──────────┘  │
│           │                    │                      │             │
│  ┌────────▼────────────────────▼──────────────────────▼──────────┐  │
│  │                    Services Layer                             │  │
│  │  RecordedSalesService │ ReconciliationService │ InsightsServ  │  │
│  └────────┬──────────────────────────────────────────────────────┘  │
│           │                                                         │
│  ┌────────▼─────────────────────────────────────────────────────┐   │
│  │                    Data Access Layer                          │  │
│  │  RecordedSale │ CalculatedSale │ DailyRecord │ ProductVariant │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
            │
┌───────────▼─────────────────────────────────────────────────────────┐
│                         PostgreSQL                                  │
│  recorded_sales │ calculated_sales │ daily_records │ product_categories │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Components to Modify

| Component | Change Description |
|-----------|-------------------|
| `Product` model | Add `category_id` FK to new `ProductCategory` table |
| `DailyRecord` model | Add revenue tracking fields: `recorded_revenue_pln`, `calculated_revenue_pln`, `revenue_source` |
| `ShiftAssignment` model | Add relationship to `RecordedSale` |
| `CloseDayWizard` | Add new reconciliation step between events and confirmation |
| `DailyOperationsPage` | Add "Sprzedaż" button linking to sales entry |
| `router.py` | Include new routers for recorded sales, reconciliation, insights |

### 1.3 New Components

| Component | Description |
|-----------|-------------|
| `RecordedSale` model | New table for manually entered sales |
| `ProductCategory` model | Categories for organizing products in UI |
| `RecordedSalesService` | Business logic for recording/voiding sales |
| `ReconciliationService` | Comparison of recorded vs calculated sales |
| `InsightsService` | Analytics: popularity, peak hours, portion accuracy |
| `SalesEntryPage` | Touch-optimized POS interface |
| `ReconciliationStep` | Wizard step showing comparison |

---

## 2. API Endpoints

### 2.1 Record Sale

```http
POST /api/v1/daily-records/{record_id}/sales
```

**Request:**
```json
{
  "product_variant_id": 5,
  "quantity": 1
}
```

**Response (201):**
```json
{
  "id": 42,
  "daily_record_id": 10,
  "product_variant_id": 5,
  "product_name": "Kebab",
  "variant_name": "Duży",
  "shift_assignment_id": 3,
  "quantity": 1,
  "unit_price_pln": "28.00",
  "total_pln": "28.00",
  "recorded_at": "2026-01-06T12:34:56Z",
  "voided_at": null,
  "void_reason": null,
  "void_notes": null
}
```

**Response (400):**
```json
{
  "detail": "Dzień nie jest otwarty"
}
```

---

### 2.2 Get Day Sales

```http
GET /api/v1/daily-records/{record_id}/sales?include_voided=false
```

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| record_id | integer | Yes | - | Daily record ID |
| include_voided | boolean | No | false | Include voided sales |

**Response (200):**
```json
[
  {
    "id": 42,
    "daily_record_id": 10,
    "product_variant_id": 5,
    "product_name": "Kebab",
    "variant_name": "Duży",
    "quantity": 1,
    "unit_price_pln": "28.00",
    "total_pln": "28.00",
    "recorded_at": "2026-01-06T12:34:56Z",
    "voided_at": null
  }
]
```

---

### 2.3 Get Day Sales Total

```http
GET /api/v1/daily-records/{record_id}/sales/total
```

**Response (200):**
```json
{
  "total_pln": "1245.00",
  "sales_count": 47,
  "items_count": 52
}
```

---

### 2.4 Void Sale

```http
POST /api/v1/daily-records/{record_id}/sales/{sale_id}/void
```

**Request:**
```json
{
  "reason": "mistake",
  "notes": "Klient zmienił zamówienie"
}
```

**Response (200):**
```json
{
  "id": 42,
  "voided_at": "2026-01-06T12:45:00Z",
  "void_reason": "mistake",
  "void_notes": "Klient zmienił zamówienie"
}
```

**Void Reason Enum:**
- `mistake` - Pomyłka przy rejestracji
- `customer_refund` - Zwrot klientowi
- `duplicate` - Duplikat
- `other` - Inny

---

### 2.5 Get Reconciliation Report

```http
GET /api/v1/daily-records/{record_id}/reconciliation
```

**Response (200):**
```json
{
  "daily_record_id": 10,
  "recorded_total_pln": "1850.00",
  "calculated_total_pln": "2100.00",
  "discrepancy_pln": "250.00",
  "discrepancy_percent": 11.9,
  "has_critical_discrepancy": false,
  "by_product": [
    {
      "product_variant_id": 5,
      "product_name": "Kebab",
      "variant_name": "Duży",
      "recorded_qty": 10,
      "recorded_revenue": "280.00",
      "calculated_qty": 12,
      "calculated_revenue": "336.00",
      "qty_difference": 2,
      "revenue_difference": "56.00"
    }
  ],
  "suggestions": [
    {
      "product_variant_id": 5,
      "product_name": "Kebab",
      "variant_name": "Duży",
      "suggested_qty": 2,
      "suggested_revenue": "56.00",
      "reason": "Zużycie składników sugeruje 2 więcej"
    }
  ]
}
```

---

### 2.6 Get Product Categories

```http
GET /api/v1/products/categories
```

**Response (200):**
```json
[
  {"id": 1, "name": "Kebaby", "sort_order": 1},
  {"id": 2, "name": "Burgery", "sort_order": 2},
  {"id": 3, "name": "Hot Dogi", "sort_order": 3},
  {"id": 4, "name": "Napoje", "sort_order": 4},
  {"id": 5, "name": "Inne", "sort_order": 99}
]
```

---

### 2.7 Get Products by Category

```http
GET /api/v1/products?category_id=1&active_only=true
```

**Response (200):**
```json
[
  {
    "id": 1,
    "name": "Kebab",
    "category_id": 1,
    "variants": [
      {"id": 1, "name": "Mały", "price_pln": "18.00"},
      {"id": 2, "name": "Średni", "price_pln": "22.00"},
      {"id": 3, "name": "Duży", "price_pln": "28.00"}
    ]
  }
]
```

---

### 2.8 Insights: Product Popularity

```http
GET /api/v1/insights/popularity?from_date=2026-01-01&to_date=2026-01-06
```

**Response (200):**
```json
{
  "period": {"from": "2026-01-01", "to": "2026-01-06"},
  "products": [
    {
      "product_variant_id": 3,
      "product_name": "Kebab",
      "variant_name": "Duży",
      "recorded_qty": 145,
      "calculated_qty": 152,
      "recorded_revenue": "4060.00",
      "trend": "up"
    }
  ]
}
```

---

### 2.9 Insights: Peak Hours

```http
GET /api/v1/insights/peak-hours?from_date=2026-01-01&to_date=2026-01-06
```

**Response (200):**
```json
{
  "period": {"from": "2026-01-01", "to": "2026-01-06"},
  "has_sufficient_data": true,
  "hourly": [
    {"hour": 10, "sales_count": 12, "revenue": "245.00"},
    {"hour": 11, "sales_count": 25, "revenue": "520.00"},
    {"hour": 12, "sales_count": 48, "revenue": "980.00"},
    {"hour": 13, "sales_count": 52, "revenue": "1120.00"}
  ],
  "peak_hour": 13,
  "slowest_hour": 10
}
```

---

### 2.10 Insights: Portion Accuracy

```http
GET /api/v1/insights/portions?from_date=2026-01-01&to_date=2026-01-06
```

**Response (200):**
```json
{
  "period": {"from": "2026-01-01", "to": "2026-01-06"},
  "ingredients": [
    {
      "ingredient_id": 1,
      "ingredient_name": "Mięso wołowe",
      "expected_usage_kg": 45.5,
      "actual_usage_kg": 49.2,
      "accuracy_percent": 92.5,
      "status": "warning",
      "message": "Zużycie o 8% wyższe niż oczekiwane"
    }
  ]
}
```

---

## 3. Database Schema

### 3.1 New Tables

#### `product_categories`

```sql
CREATE TABLE product_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Seed data
INSERT INTO product_categories (name, sort_order) VALUES
    ('Kebaby', 1),
    ('Burgery', 2),
    ('Hot Dogi', 3),
    ('Napoje', 4),
    ('Inne', 99);
```

#### `recorded_sales`

```sql
CREATE TABLE recorded_sales (
    id SERIAL PRIMARY KEY,
    daily_record_id INTEGER NOT NULL REFERENCES daily_records(id) ON DELETE CASCADE,
    product_variant_id INTEGER NOT NULL REFERENCES product_variants(id) ON DELETE RESTRICT,
    shift_assignment_id INTEGER REFERENCES shift_assignments(id) ON DELETE SET NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_price_pln NUMERIC(10,2) NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Void tracking (soft delete)
    voided_at TIMESTAMPTZ,
    void_reason VARCHAR(50),
    void_notes VARCHAR(255),

    -- Constraints
    CONSTRAINT check_quantity_positive CHECK (quantity > 0),
    CONSTRAINT check_price_positive CHECK (unit_price_pln > 0),
    CONSTRAINT check_void_reason_valid CHECK (
        void_reason IS NULL OR
        void_reason IN ('mistake', 'customer_refund', 'duplicate', 'other')
    )
);

-- Indexes
CREATE INDEX idx_recorded_sales_daily_record ON recorded_sales(daily_record_id);
CREATE INDEX idx_recorded_sales_variant ON recorded_sales(product_variant_id);
CREATE INDEX idx_recorded_sales_recorded_at ON recorded_sales(recorded_at);
CREATE INDEX idx_recorded_sales_not_voided ON recorded_sales(daily_record_id)
    WHERE voided_at IS NULL;
```

### 3.2 Modifications to Existing Tables

#### `products` - Add category reference

```sql
ALTER TABLE products
ADD COLUMN category_id INTEGER REFERENCES product_categories(id) ON DELETE SET NULL;

CREATE INDEX idx_products_category ON products(category_id);
```

#### `daily_records` - Add revenue tracking

```sql
ALTER TABLE daily_records
ADD COLUMN recorded_revenue_pln NUMERIC(10,2),
ADD COLUMN calculated_revenue_pln NUMERIC(10,2),
ADD COLUMN revenue_discrepancy_pln NUMERIC(10,2),
ADD COLUMN revenue_source VARCHAR(20) DEFAULT 'calculated'
    CONSTRAINT check_revenue_source_valid
    CHECK (revenue_source IN ('recorded', 'calculated', 'hybrid'));
```

### 3.3 ERD Diagram

```
┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│ product_categories│      │     products     │       │ product_variants │
├──────────────────┤       ├──────────────────┤       ├──────────────────┤
│ id (PK)          │◄──────│ category_id (FK) │       │ id (PK)          │
│ name             │       │ id (PK)          │◄──────│ product_id (FK)  │
│ sort_order       │       │ name             │       │ name             │
└──────────────────┘       │ has_variants     │       │ price_pln        │
                           └──────────────────┘       └────────┬─────────┘
                                                               │
                    ┌──────────────────────────────────────────┤
                    │                                          │
                    ▼                                          ▼
┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│  daily_records   │       │  recorded_sales  │       │ calculated_sales │
├──────────────────┤       ├──────────────────┤       ├──────────────────┤
│ id (PK)          │◄──────│ daily_record_id  │       │ daily_record_id  │──►│
│ date             │       │ product_variant  │───────│ product_variant  │   │
│ status           │       │ shift_assignment │       │ quantity_sold    │   │
│ recorded_revenue │       │ quantity         │       │ revenue_pln      │   │
│ calculated_rev   │       │ unit_price_pln   │       └──────────────────┘   │
│ revenue_source   │       │ recorded_at      │                              │
└────────┬─────────┘       │ voided_at        │                              │
         │                 │ void_reason      │                              │
         │                 └──────────────────┘                              │
         │                          ▲                                        │
         │                          │                                        │
         └──────────────────────────┼────────────────────────────────────────┘
                                    │
         ┌──────────────────────────┘
         ▼
┌──────────────────┐
│ shift_assignments│
├──────────────────┤
│ id (PK)          │
│ daily_record_id  │
│ employee_id      │
│ start_time       │
│ end_time         │
└──────────────────┘
```

### 3.4 Alembic Migration

```python
# backend/alembic/versions/012_add_sales_tracking_hybrid.py

"""Add sales tracking hybrid tables and columns

Revision ID: 012
Revises: 011
Create Date: 2026-01-06
"""

from alembic import op
import sqlalchemy as sa


revision = '012'
down_revision = '011'
branch_labels = None
depends_on = None


def upgrade():
    # Create product_categories table
    op.create_table(
        'product_categories',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(50), nullable=False, unique=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )

    # Seed default categories
    op.execute("""
        INSERT INTO product_categories (name, sort_order) VALUES
        ('Kebaby', 1),
        ('Burgery', 2),
        ('Hot Dogi', 3),
        ('Napoje', 4),
        ('Inne', 99)
    """)

    # Add category_id to products
    op.add_column('products', sa.Column(
        'category_id',
        sa.Integer(),
        sa.ForeignKey('product_categories.id', ondelete='SET NULL'),
        nullable=True
    ))
    op.create_index('idx_products_category', 'products', ['category_id'])

    # Create recorded_sales table
    op.create_table(
        'recorded_sales',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('daily_record_id', sa.Integer(),
                  sa.ForeignKey('daily_records.id', ondelete='CASCADE'), nullable=False),
        sa.Column('product_variant_id', sa.Integer(),
                  sa.ForeignKey('product_variants.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('shift_assignment_id', sa.Integer(),
                  sa.ForeignKey('shift_assignments.id', ondelete='SET NULL'), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('unit_price_pln', sa.Numeric(10, 2), nullable=False),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('voided_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('void_reason', sa.String(50), nullable=True),
        sa.Column('void_notes', sa.String(255), nullable=True),
        sa.CheckConstraint('quantity > 0', name='check_recorded_quantity_positive'),
        sa.CheckConstraint('unit_price_pln > 0', name='check_recorded_price_positive'),
        sa.CheckConstraint(
            "void_reason IS NULL OR void_reason IN ('mistake', 'customer_refund', 'duplicate', 'other')",
            name='check_void_reason_valid'
        )
    )

    op.create_index('idx_recorded_sales_daily_record', 'recorded_sales', ['daily_record_id'])
    op.create_index('idx_recorded_sales_variant', 'recorded_sales', ['product_variant_id'])
    op.create_index('idx_recorded_sales_recorded_at', 'recorded_sales', ['recorded_at'])

    # Add revenue tracking to daily_records
    op.add_column('daily_records', sa.Column('recorded_revenue_pln', sa.Numeric(10, 2), nullable=True))
    op.add_column('daily_records', sa.Column('calculated_revenue_pln', sa.Numeric(10, 2), nullable=True))
    op.add_column('daily_records', sa.Column('revenue_discrepancy_pln', sa.Numeric(10, 2), nullable=True))
    op.add_column('daily_records', sa.Column('revenue_source', sa.String(20), server_default='calculated'))
    op.create_check_constraint(
        'check_revenue_source_valid',
        'daily_records',
        "revenue_source IN ('recorded', 'calculated', 'hybrid')"
    )


def downgrade():
    op.drop_constraint('check_revenue_source_valid', 'daily_records')
    op.drop_column('daily_records', 'revenue_source')
    op.drop_column('daily_records', 'revenue_discrepancy_pln')
    op.drop_column('daily_records', 'calculated_revenue_pln')
    op.drop_column('daily_records', 'recorded_revenue_pln')

    op.drop_index('idx_recorded_sales_recorded_at')
    op.drop_index('idx_recorded_sales_variant')
    op.drop_index('idx_recorded_sales_daily_record')
    op.drop_table('recorded_sales')

    op.drop_index('idx_products_category')
    op.drop_column('products', 'category_id')

    op.drop_table('product_categories')
```

---

## 4. SQLAlchemy Models

### 4.1 RecordedSale

```python
# backend/app/models/recorded_sale.py

from sqlalchemy import Column, Integer, Numeric, DateTime, String, ForeignKey, CheckConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from decimal import Decimal
from app.core.database import Base


class RecordedSale(Base):
    """
    Records manually entered sales during daily operations.
    Runs parallel to CalculatedSale for reconciliation.
    """
    __tablename__ = "recorded_sales"

    id = Column(Integer, primary_key=True, index=True)
    daily_record_id = Column(
        Integer,
        ForeignKey("daily_records.id", ondelete="CASCADE"),
        nullable=False
    )
    product_variant_id = Column(
        Integer,
        ForeignKey("product_variants.id", ondelete="RESTRICT"),
        nullable=False
    )
    shift_assignment_id = Column(
        Integer,
        ForeignKey("shift_assignments.id", ondelete="SET NULL"),
        nullable=True
    )
    quantity = Column(Integer, nullable=False, default=1)
    unit_price_pln = Column(Numeric(10, 2), nullable=False)
    recorded_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Void tracking (soft delete)
    voided_at = Column(DateTime(timezone=True), nullable=True)
    void_reason = Column(String(50), nullable=True)
    void_notes = Column(String(255), nullable=True)

    __table_args__ = (
        CheckConstraint("quantity > 0", name="check_recorded_quantity_positive"),
        CheckConstraint("unit_price_pln > 0", name="check_recorded_price_positive"),
        CheckConstraint(
            "void_reason IS NULL OR void_reason IN ('mistake', 'customer_refund', 'duplicate', 'other')",
            name="check_void_reason_valid"
        ),
        Index("idx_recorded_sales_daily_record", "daily_record_id"),
        Index("idx_recorded_sales_variant", "product_variant_id"),
        Index("idx_recorded_sales_recorded_at", "recorded_at"),
    )

    # Relationships
    daily_record = relationship("DailyRecord", back_populates="recorded_sales")
    product_variant = relationship("ProductVariant", back_populates="recorded_sales")
    shift_assignment = relationship("ShiftAssignment", back_populates="recorded_sales")

    @property
    def is_voided(self) -> bool:
        return self.voided_at is not None

    @property
    def total_pln(self) -> Decimal:
        return Decimal(self.quantity) * self.unit_price_pln
```

### 4.2 ProductCategory

```python
# backend/app/models/product_category.py

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class ProductCategory(Base):
    """
    Categories for organizing products in sales entry UI.
    """
    __tablename__ = "product_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True)
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    products = relationship("Product", back_populates="category")
```

### 4.3 Model Updates

#### Update `Product` model

```python
# Add to backend/app/models/product.py

# Add column
category_id = Column(Integer, ForeignKey("product_categories.id", ondelete="SET NULL"), nullable=True)

# Add relationship
category = relationship("ProductCategory", back_populates="products")
```

#### Update `DailyRecord` model

```python
# Add to backend/app/models/daily_record.py

# Add columns
recorded_revenue_pln = Column(Numeric(10, 2), nullable=True)
calculated_revenue_pln = Column(Numeric(10, 2), nullable=True)
revenue_discrepancy_pln = Column(Numeric(10, 2), nullable=True)
revenue_source = Column(String(20), server_default="calculated")

# Add relationship
recorded_sales = relationship("RecordedSale", back_populates="daily_record", cascade="all, delete-orphan")
```

#### Update `ShiftAssignment` model

```python
# Add to backend/app/models/shift_assignment.py

# Add relationship
recorded_sales = relationship("RecordedSale", back_populates="shift_assignment")
```

#### Update `ProductVariant` model

```python
# Add to backend/app/models/product.py (ProductVariant class)

# Add relationship
recorded_sales = relationship("RecordedSale", back_populates="product_variant")
```

---

## 5. Pydantic Schemas

### 5.1 Recorded Sales Schemas

```python
# backend/app/schemas/recorded_sales.py

from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime
from typing import Optional
from enum import Enum


class VoidReason(str, Enum):
    MISTAKE = "mistake"
    CUSTOMER_REFUND = "customer_refund"
    DUPLICATE = "duplicate"
    OTHER = "other"


class RecordedSaleCreate(BaseModel):
    product_variant_id: int
    quantity: int = Field(default=1, ge=1, le=100)


class RecordedSaleVoid(BaseModel):
    reason: VoidReason
    notes: Optional[str] = Field(None, max_length=255)


class RecordedSaleResponse(BaseModel):
    id: int
    daily_record_id: int
    product_variant_id: int
    product_name: str
    variant_name: Optional[str]
    shift_assignment_id: Optional[int]
    quantity: int
    unit_price_pln: Decimal
    total_pln: Decimal
    recorded_at: datetime
    voided_at: Optional[datetime]
    void_reason: Optional[str]
    void_notes: Optional[str]

    class Config:
        from_attributes = True


class DaySalesTotal(BaseModel):
    total_pln: Decimal
    sales_count: int
    items_count: int
```

### 5.2 Reconciliation Schemas

```python
# backend/app/schemas/reconciliation.py

from pydantic import BaseModel
from decimal import Decimal
from typing import List, Optional


class ProductReconciliation(BaseModel):
    product_variant_id: int
    product_name: str
    variant_name: Optional[str]
    recorded_qty: int
    recorded_revenue: Decimal
    calculated_qty: Decimal
    calculated_revenue: Decimal
    qty_difference: Decimal
    revenue_difference: Decimal


class MissingSuggestion(BaseModel):
    product_variant_id: int
    product_name: str
    variant_name: Optional[str]
    suggested_qty: int
    suggested_revenue: Decimal
    reason: str


class ReconciliationReportResponse(BaseModel):
    daily_record_id: int
    recorded_total_pln: Decimal
    calculated_total_pln: Decimal
    discrepancy_pln: Decimal
    discrepancy_percent: float
    has_critical_discrepancy: bool
    by_product: List[ProductReconciliation]
    suggestions: List[MissingSuggestion]
```

### 5.3 Category Schemas

```python
# backend/app/schemas/product_category.py

from pydantic import BaseModel
from datetime import datetime


class ProductCategoryResponse(BaseModel):
    id: int
    name: str
    sort_order: int

    class Config:
        from_attributes = True
```

---

## 6. Service Layer

### 6.1 RecordedSalesService

```python
# backend/app/services/recorded_sales_service.py

from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
from datetime import datetime
from typing import Optional, List
from app.models import RecordedSale, DailyRecord, ProductVariant, ShiftAssignment
from app.models.daily_record import DayStatus


class RecordedSalesService:
    def __init__(self, db: Session):
        self.db = db

    def record_sale(
        self,
        daily_record_id: int,
        variant_id: int,
        quantity: int = 1
    ) -> RecordedSale:
        """Record a new sale for the given day and product variant."""
        # Validate day is open
        daily_record = self.db.query(DailyRecord).filter(
            DailyRecord.id == daily_record_id,
            DailyRecord.status == DayStatus.OPEN
        ).first()
        if not daily_record:
            raise ValueError("Dzień nie jest otwarty")

        # Get variant with current price
        variant = self.db.query(ProductVariant).filter(
            ProductVariant.id == variant_id,
            ProductVariant.is_active == True
        ).first()
        if not variant:
            raise ValueError("Produkt nie istnieje lub jest nieaktywny")

        # Find current active shift (optional)
        current_shift = self._get_active_shift(daily_record_id)

        sale = RecordedSale(
            daily_record_id=daily_record_id,
            product_variant_id=variant_id,
            shift_assignment_id=current_shift.id if current_shift else None,
            quantity=quantity,
            unit_price_pln=variant.price_pln,
            recorded_at=datetime.now()
        )
        self.db.add(sale)
        self.db.commit()
        self.db.refresh(sale)
        return sale

    def void_sale(
        self,
        sale_id: int,
        reason: str,
        notes: Optional[str] = None
    ) -> RecordedSale:
        """Void (soft delete) a recorded sale."""
        sale = self.db.query(RecordedSale).filter(
            RecordedSale.id == sale_id,
            RecordedSale.voided_at.is_(None)
        ).first()
        if not sale:
            raise ValueError("Sprzedaż nie istnieje lub została już anulowana")

        # Check day is still open
        if sale.daily_record.status != DayStatus.OPEN:
            raise ValueError("Nie można anulować sprzedaży z zamkniętego dnia")

        sale.voided_at = datetime.now()
        sale.void_reason = reason
        sale.void_notes = notes
        self.db.commit()
        self.db.refresh(sale)
        return sale

    def get_day_sales(
        self,
        daily_record_id: int,
        include_voided: bool = False
    ) -> List[RecordedSale]:
        """Get all recorded sales for a day."""
        query = self.db.query(RecordedSale).filter(
            RecordedSale.daily_record_id == daily_record_id
        )
        if not include_voided:
            query = query.filter(RecordedSale.voided_at.is_(None))
        return query.order_by(RecordedSale.recorded_at.desc()).all()

    def get_day_total(self, daily_record_id: int) -> Decimal:
        """Get total revenue from recorded sales (excluding voided)."""
        result = self.db.query(
            func.sum(RecordedSale.quantity * RecordedSale.unit_price_pln)
        ).filter(
            RecordedSale.daily_record_id == daily_record_id,
            RecordedSale.voided_at.is_(None)
        ).scalar()
        return result or Decimal("0")

    def _get_active_shift(self, daily_record_id: int) -> Optional[ShiftAssignment]:
        """Find shift assignment that covers current time."""
        now = datetime.now().time()
        return self.db.query(ShiftAssignment).filter(
            ShiftAssignment.daily_record_id == daily_record_id,
            ShiftAssignment.start_time <= now,
            ShiftAssignment.end_time >= now
        ).first()
```

### 6.2 ReconciliationService

```python
# backend/app/services/reconciliation_service.py

from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
from typing import List, Dict, Tuple
from app.models import RecordedSale, CalculatedSale, ProductVariant
from app.schemas.reconciliation import (
    ProductReconciliation,
    MissingSuggestion,
    ReconciliationReportResponse
)


class ReconciliationService:
    CRITICAL_THRESHOLD = 30.0  # 30% discrepancy
    WARNING_THRESHOLD = 10.0   # 10% discrepancy

    def __init__(self, db: Session):
        self.db = db

    def reconcile(self, daily_record_id: int) -> ReconciliationReportResponse:
        """Generate reconciliation report comparing recorded vs calculated sales."""
        # Get recorded totals by product
        recorded = self._get_recorded_by_product(daily_record_id)

        # Get calculated totals by product
        calculated = self._get_calculated_by_product(daily_record_id)

        # Merge and compare
        by_product = self._merge_comparisons(recorded, calculated)

        # Calculate totals
        recorded_total = sum(p.recorded_revenue for p in by_product)
        calculated_total = sum(p.calculated_revenue for p in by_product)
        discrepancy = calculated_total - recorded_total

        discrepancy_percent = 0.0
        if calculated_total > 0:
            discrepancy_percent = float(abs(discrepancy) / calculated_total * 100)

        # Generate suggestions for missing sales
        suggestions = self._generate_suggestions(by_product)

        return ReconciliationReportResponse(
            daily_record_id=daily_record_id,
            recorded_total_pln=recorded_total,
            calculated_total_pln=calculated_total,
            discrepancy_pln=discrepancy,
            discrepancy_percent=round(discrepancy_percent, 1),
            by_product=by_product,
            suggestions=suggestions,
            has_critical_discrepancy=discrepancy_percent >= self.CRITICAL_THRESHOLD
        )

    def _get_recorded_by_product(self, daily_record_id: int) -> Dict[int, Tuple[int, Decimal]]:
        """Aggregate recorded sales by product variant."""
        results = self.db.query(
            RecordedSale.product_variant_id,
            func.sum(RecordedSale.quantity).label('total_qty'),
            func.sum(RecordedSale.quantity * RecordedSale.unit_price_pln).label('total_revenue')
        ).filter(
            RecordedSale.daily_record_id == daily_record_id,
            RecordedSale.voided_at.is_(None)
        ).group_by(RecordedSale.product_variant_id).all()

        return {r.product_variant_id: (int(r.total_qty), Decimal(r.total_revenue)) for r in results}

    def _get_calculated_by_product(self, daily_record_id: int) -> Dict[int, Tuple[Decimal, Decimal]]:
        """Get calculated sales by product variant."""
        results = self.db.query(CalculatedSale).filter(
            CalculatedSale.daily_record_id == daily_record_id
        ).all()

        return {r.product_variant_id: (r.quantity_sold, r.revenue_pln) for r in results}

    def _merge_comparisons(
        self,
        recorded: Dict[int, Tuple],
        calculated: Dict[int, Tuple]
    ) -> List[ProductReconciliation]:
        """Merge recorded and calculated data into comparison list."""
        all_variant_ids = set(recorded.keys()) | set(calculated.keys())
        comparisons = []

        for variant_id in all_variant_ids:
            variant = self.db.query(ProductVariant).filter(
                ProductVariant.id == variant_id
            ).first()

            rec_qty, rec_rev = recorded.get(variant_id, (0, Decimal("0")))
            calc_qty, calc_rev = calculated.get(variant_id, (Decimal("0"), Decimal("0")))

            comparisons.append(ProductReconciliation(
                product_variant_id=variant_id,
                product_name=variant.product.name if variant else "Unknown",
                variant_name=variant.name if variant else None,
                recorded_qty=rec_qty,
                recorded_revenue=rec_rev,
                calculated_qty=calc_qty,
                calculated_revenue=calc_rev,
                qty_difference=calc_qty - rec_qty,
                revenue_difference=calc_rev - rec_rev
            ))

        return sorted(comparisons, key=lambda x: x.revenue_difference, reverse=True)

    def _generate_suggestions(
        self,
        by_product: List[ProductReconciliation]
    ) -> List[MissingSuggestion]:
        """Generate suggestions for products where calculated > recorded."""
        suggestions = []
        for p in by_product:
            if p.qty_difference > 0:
                suggestions.append(MissingSuggestion(
                    product_variant_id=p.product_variant_id,
                    product_name=p.product_name,
                    variant_name=p.variant_name,
                    suggested_qty=int(p.qty_difference),
                    suggested_revenue=p.revenue_difference,
                    reason=f"Zużycie składników sugeruje {int(p.qty_difference)} więcej"
                ))
        return suggestions[:5]  # Limit to top 5 suggestions
```

---

## 7. Frontend Components

### 7.1 File Structure

```
frontend/src/
├── api/
│   ├── recordedSales.ts       # API client for recorded sales
│   ├── reconciliation.ts      # API client for reconciliation
│   └── productCategories.ts   # API client for categories
├── components/
│   └── sales/
│       ├── index.ts
│       ├── CategoryTabs.tsx       # Tab bar for product categories
│       ├── ProductGrid.tsx        # Grid of product buttons
│       ├── ProductButton.tsx      # Individual product button
│       ├── RunningTotal.tsx       # Top-right total display
│       ├── RecentSalesList.tsx    # Recent sales with void option
│       ├── VoidSaleModal.tsx      # Void confirmation dialog
│       └── ReconciliationStep.tsx # Wizard step component
├── hooks/
│   └── sales/
│       ├── useSalesEntry.ts       # Recording sales mutation
│       ├── useRecordedSales.ts    # Fetching recorded sales
│       ├── useSalesTotal.ts       # Running total query
│       ├── useVoidSale.ts         # Void mutation
│       └── useReconciliation.ts   # Reconciliation query
├── pages/
│   └── SalesEntryPage.tsx         # Main POS-like interface
└── types/
    ├── recordedSales.ts           # TypeScript interfaces
    └── reconciliation.ts
```

### 7.2 TypeScript Interfaces

```typescript
// frontend/src/types/recordedSales.ts

export type VoidReason = 'mistake' | 'customer_refund' | 'duplicate' | 'other';

export interface RecordedSale {
  id: number;
  daily_record_id: number;
  product_variant_id: number;
  product_name: string;
  variant_name: string | null;
  shift_assignment_id: number | null;
  quantity: number;
  unit_price_pln: string;
  total_pln: string;
  recorded_at: string;
  voided_at: string | null;
  void_reason: VoidReason | null;
  void_notes: string | null;
}

export interface RecordedSaleCreate {
  product_variant_id: number;
  quantity?: number;
}

export interface RecordedSaleVoid {
  reason: VoidReason;
  notes?: string;
}

export interface DaySalesTotal {
  total_pln: string;
  sales_count: number;
  items_count: number;
}
```

```typescript
// frontend/src/types/reconciliation.ts

export interface ProductReconciliation {
  product_variant_id: number;
  product_name: string;
  variant_name: string | null;
  recorded_qty: number;
  recorded_revenue: string;
  calculated_qty: string;
  calculated_revenue: string;
  qty_difference: string;
  revenue_difference: string;
}

export interface MissingSuggestion {
  product_variant_id: number;
  product_name: string;
  variant_name: string | null;
  suggested_qty: number;
  suggested_revenue: string;
  reason: string;
}

export interface ReconciliationReport {
  daily_record_id: number;
  recorded_total_pln: string;
  calculated_total_pln: string;
  discrepancy_pln: string;
  discrepancy_percent: number;
  has_critical_discrepancy: boolean;
  by_product: ProductReconciliation[];
  suggestions: MissingSuggestion[];
}
```

### 7.3 API Client

```typescript
// frontend/src/api/recordedSales.ts

import { api } from './client';
import { RecordedSale, RecordedSaleCreate, RecordedSaleVoid, DaySalesTotal } from '../types';

export const recordedSalesApi = {
  recordSale: (dailyRecordId: number, data: RecordedSaleCreate) =>
    api.post<RecordedSale>(`/daily-records/${dailyRecordId}/sales`, data),

  getDaySales: (dailyRecordId: number, includeVoided = false) =>
    api.get<RecordedSale[]>(`/daily-records/${dailyRecordId}/sales`, {
      params: { include_voided: includeVoided }
    }),

  getDayTotal: (dailyRecordId: number) =>
    api.get<DaySalesTotal>(`/daily-records/${dailyRecordId}/sales/total`),

  voidSale: (dailyRecordId: number, saleId: number, data: RecordedSaleVoid) =>
    api.post<RecordedSale>(`/daily-records/${dailyRecordId}/sales/${saleId}/void`, data)
};
```

### 7.4 React Query Hooks

```typescript
// frontend/src/hooks/sales/useSalesEntry.ts

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { recordedSalesApi } from '../../api/recordedSales';

export function useSalesEntry() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ dailyRecordId, productVariantId, quantity = 1 }: {
      dailyRecordId: number;
      productVariantId: number;
      quantity?: number;
    }) => recordedSalesApi.recordSale(dailyRecordId, {
      product_variant_id: productVariantId,
      quantity
    }),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['recordedSales', variables.dailyRecordId]
      });
      queryClient.invalidateQueries({
        queryKey: ['salesTotal', variables.dailyRecordId]
      });
    }
  });
}
```

---

## 8. Security

### 8.1 Data Validation

| Field | Validation |
|-------|------------|
| quantity | Positive integer, max 100 per sale |
| unit_price_pln | Taken from database, not from client |
| void_reason | Must be from enum |
| void_notes | Max 255 characters |

### 8.2 Authorization

- All sales endpoints require authenticated user
- Void operations logged with user ID and timestamp
- Historical void data is immutable

### 8.3 Potential Threats

| Threat | Mitigation |
|--------|------------|
| Price manipulation | Price captured from DB at sale time, not from client |
| Unauthorized voids | Void requires reason, logged with timestamp |
| Data tampering | Soft delete only, no hard deletes allowed |
| Replay attacks | Unique constraints, idempotency checks |

---

## 9. Performance

### 9.1 Database Indexes

```sql
-- Fast lookup by day (most common query)
CREATE INDEX idx_recorded_sales_daily_record ON recorded_sales(daily_record_id);

-- Partial index for active sales only
CREATE INDEX idx_recorded_sales_not_voided ON recorded_sales(daily_record_id)
    WHERE voided_at IS NULL;

-- Time-based queries for peak hours analysis
CREATE INDEX idx_recorded_sales_recorded_at ON recorded_sales(recorded_at);

-- Product lookup for popularity reports
CREATE INDEX idx_recorded_sales_variant ON recorded_sales(product_variant_id);
```

### 9.2 Caching Strategy

| Query | Cache TTL | Invalidation |
|-------|-----------|--------------|
| Categories | 1 hour | Manual refresh only |
| Products by category | 5 minutes | On product update |
| Sales total | 5 seconds | On any sale mutation |
| Recent sales | 5 seconds | On any sale mutation |
| Reconciliation | No cache | Always fresh |

### 9.3 Query Optimizations

- Use `SELECT ... FOR UPDATE SKIP LOCKED` for high-concurrency sale recording
- Aggregate queries use partial index for non-voided sales
- Limit recent sales list to 10-20 items

---

## 10. Testing

### 10.1 Unit Tests

- [ ] RecordedSalesService.record_sale() - happy path
- [ ] RecordedSalesService.record_sale() - day not open
- [ ] RecordedSalesService.record_sale() - variant inactive
- [ ] RecordedSalesService.void_sale() - happy path
- [ ] RecordedSalesService.void_sale() - already voided
- [ ] RecordedSalesService.void_sale() - day closed
- [ ] ReconciliationService.reconcile() - basic comparison
- [ ] ReconciliationService.reconcile() - suggestions generation
- [ ] Pydantic schema validation

### 10.2 Integration Tests

- [ ] POST /daily-records/{id}/sales - create sale
- [ ] GET /daily-records/{id}/sales - list sales
- [ ] GET /daily-records/{id}/sales/total - running total
- [ ] POST /daily-records/{id}/sales/{id}/void - void sale
- [ ] GET /daily-records/{id}/reconciliation - comparison report

### 10.3 E2E Tests

- [ ] Full sales recording flow on mobile viewport
- [ ] Void sale flow with reason selection
- [ ] Reconciliation step in close wizard
- [ ] Empty sales warning on close

---

## 11. Deployment Plan

### 11.1 Database Migration

```bash
# Run migration
docker compose exec backend alembic upgrade head
```

### 11.2 Deployment Steps

1. Deploy backend with new migration
2. Run `alembic upgrade head` in production
3. Deploy frontend with new components
4. Assign default categories to existing products (optional)
5. Verify endpoints work correctly
6. Enable feature flag if using one

### 11.3 Rollback

```bash
# Revert migration
docker compose exec backend alembic downgrade -1
```

Rollback is safe:
- New tables can be dropped without affecting existing functionality
- New columns on `daily_records` and `products` are nullable
- Existing close-day flow unchanged

---

## 12. Monitoring

### 12.1 Logs

- Sale recorded: `INFO: Recorded sale {id} for day {daily_record_id}, variant {variant_id}`
- Sale voided: `INFO: Voided sale {id}, reason: {reason}`
- Reconciliation: `INFO: Reconciliation for day {id}: recorded={X}, calculated={Y}, diff={Z}%`

### 12.2 Metrics

| Metric | Description |
|--------|-------------|
| `sales_recorded_total` | Counter of sales recorded |
| `sales_voided_total` | Counter of sales voided |
| `reconciliation_discrepancy_percent` | Histogram of discrepancy percentages |
| `sales_entry_latency_ms` | Histogram of sale recording latency |

---

## Change History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-06 | AI Assistant | Initial version |
