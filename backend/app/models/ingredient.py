from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class UnitType(str, enum.Enum):
    WEIGHT = "weight"  # measured in grams/kg
    COUNT = "count"    # measured in pieces


class Ingredient(Base):
    __tablename__ = "ingredients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    unit_type = Column(SQLEnum(UnitType, values_callable=lambda x: [e.value for e in x]), nullable=False)
    unit_label = Column(String(20), nullable=False, server_default="szt")  # Display label: kg, g, szt, opak
    is_active = Column(Boolean, nullable=False, server_default="true")  # Soft delete flag
    current_stock_grams = Column(Numeric(10, 2), default=0)  # for weight-based (legacy, will be deprecated)
    current_stock_count = Column(Integer, default=0)          # for count-based (legacy, will be deprecated)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    product_ingredients = relationship("ProductIngredient", back_populates="ingredient")
    inventory_snapshots = relationship("InventorySnapshot", back_populates="ingredient")
    delivery_items = relationship("DeliveryItem", back_populates="ingredient")
    storage_transfers = relationship("StorageTransfer", back_populates="ingredient")
    spoilages = relationship("Spoilage", back_populates="ingredient")
    storage_inventory = relationship("StorageInventory", back_populates="ingredient", uselist=False)
