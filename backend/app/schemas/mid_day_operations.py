"""
Schemas for mid-day operations: deliveries, storage transfers, and spoilage.

These schemas support recording events that occur during an open day:
- Deliveries: Ingredients received from suppliers (with cost)
- Storage Transfers: Moving ingredients from storage to shop
- Spoilage: Recording wasted/damaged ingredients
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


# -----------------------------------------------------------------------------
# Enums (matching model)
# -----------------------------------------------------------------------------

class SpoilageReasonEnum(str, Enum):
    EXPIRED = "expired"
    OVER_PREPARED = "over_prepared"
    CONTAMINATED = "contaminated"
    EQUIPMENT_FAILURE = "equipment_failure"
    OTHER = "other"


# Map for Polish display names
SPOILAGE_REASON_LABELS = {
    SpoilageReasonEnum.EXPIRED: "Przeterminowany",
    SpoilageReasonEnum.OVER_PREPARED: "Nadmiernie przygotowany",
    SpoilageReasonEnum.CONTAMINATED: "Zanieczyszczony",
    SpoilageReasonEnum.EQUIPMENT_FAILURE: "Awaria sprzetu",
    SpoilageReasonEnum.OTHER: "Inne",
}


# -----------------------------------------------------------------------------
# Delivery Schemas (Multi-item structure)
# -----------------------------------------------------------------------------

class DeliveryItemCreate(BaseModel):
    """Request schema for a single delivery item (ingredient line)."""
    ingredient_id: int = Field(..., description="ID skladnika")
    quantity: Decimal = Field(..., gt=0, description="Ilosc w jednostce skladnika")
    cost_pln: Optional[Decimal] = Field(None, ge=0, description="Opcjonalny koszt pozycji w PLN")
    expiry_date: Optional[date] = Field(None, description="Data waznosci (opcjonalna, dla sledzenia partii)")

    @field_validator("quantity", mode="before")
    @classmethod
    def coerce_quantity(cls, v):
        if v is None:
            return Decimal("0")
        return Decimal(str(v))

    @field_validator("cost_pln", mode="before")
    @classmethod
    def coerce_cost(cls, v):
        if v is None:
            return None
        return Decimal(str(v))


class DeliveryItemResponse(BaseModel):
    """Response schema for a delivery item."""
    id: int
    delivery_id: int
    ingredient_id: int
    ingredient_name: str
    unit_label: str
    quantity: Decimal
    cost_pln: Optional[Decimal]
    expiry_date: Optional[date] = None
    batch_id: Optional[int] = None
    batch_number: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DeliveryCreate(BaseModel):
    """Request schema for creating a multi-item delivery record."""
    daily_record_id: int = Field(..., description="ID otwartego dnia")
    items: list[DeliveryItemCreate] = Field(..., min_length=1, description="Lista skladnikow w dostawie")
    total_cost_pln: Decimal = Field(..., ge=0, description="Calkowity koszt dostawy w PLN")
    supplier_name: Optional[str] = Field(None, max_length=255, description="Nazwa dostawcy")
    invoice_number: Optional[str] = Field(None, max_length=100, description="Numer faktury")
    destination: Optional[str] = Field("storage", description="Miejsce docelowe dostawy: 'storage' (magazyn) lub 'shop' (sklep)")
    notes: Optional[str] = Field(None, description="Dodatkowe notatki")
    delivered_at: Optional[datetime] = Field(None, description="Czas dostawy (domyslnie teraz)")

    @field_validator("total_cost_pln", mode="before")
    @classmethod
    def coerce_total_cost(cls, v):
        if v is None:
            return Decimal("0")
        return Decimal(str(v))


class DeliveryResponse(BaseModel):
    """Response schema for a delivery record with all items."""
    id: int
    daily_record_id: int
    supplier_name: Optional[str]
    invoice_number: Optional[str]
    total_cost_pln: Decimal
    destination: str = "storage"
    notes: Optional[str]
    transaction_id: Optional[int]
    items: list[DeliveryItemResponse] = []
    delivered_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class DeliveryListResponse(BaseModel):
    """Response schema for a list of deliveries."""
    items: list[DeliveryResponse] = []
    total: int = 0


# -----------------------------------------------------------------------------
# Storage Transfer Schemas
# -----------------------------------------------------------------------------

class StorageTransferCreate(BaseModel):
    """Request schema for creating a storage transfer record."""
    daily_record_id: int = Field(..., description="ID otwartego dnia")
    ingredient_id: int = Field(..., description="ID skladnika")
    quantity: Decimal = Field(..., gt=0, description="Ilosc do przeniesienia")
    transferred_at: Optional[datetime] = Field(None, description="Czas transferu (domyslnie teraz)")

    @field_validator("quantity", mode="before")
    @classmethod
    def coerce_quantity(cls, v):
        if v is None:
            return Decimal("0")
        return Decimal(str(v))


class StorageTransferResponse(BaseModel):
    """Response schema for a storage transfer record."""
    id: int
    daily_record_id: int
    ingredient_id: int
    ingredient_name: str
    unit_label: str
    quantity: Decimal
    transferred_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class StorageTransferListResponse(BaseModel):
    """Response schema for a list of storage transfers."""
    items: list[StorageTransferResponse] = []
    total: int = 0


# -----------------------------------------------------------------------------
# Spoilage Schemas
# -----------------------------------------------------------------------------

class SpoilageCreate(BaseModel):
    """Request schema for creating a spoilage record."""
    daily_record_id: int = Field(..., description="ID otwartego dnia")
    ingredient_id: int = Field(..., description="ID skladnika")
    quantity: Decimal = Field(..., gt=0, description="Ilosc stracona")
    reason: SpoilageReasonEnum = Field(..., description="Przyczyna straty")
    batch_id: Optional[int] = Field(None, description="ID partii (opcjonalne, dla powiazania ze strata)")
    notes: Optional[str] = Field(None, max_length=500, description="Dodatkowe uwagi")
    recorded_at: Optional[datetime] = Field(None, description="Czas zarejestrowania (domyslnie teraz)")

    @field_validator("quantity", mode="before")
    @classmethod
    def coerce_quantity(cls, v):
        if v is None:
            return Decimal("0")
        return Decimal(str(v))


class SpoilageResponse(BaseModel):
    """Response schema for a spoilage record."""
    id: int
    daily_record_id: int
    ingredient_id: int
    ingredient_name: str
    unit_label: str
    quantity: Decimal
    reason: str
    reason_label: str  # Polish display name
    batch_id: Optional[int] = None
    batch_number: Optional[str] = None
    notes: Optional[str]
    recorded_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class SpoilageListResponse(BaseModel):
    """Response schema for a list of spoilage records."""
    items: list[SpoilageResponse] = []
    total: int = 0
