from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    has_variants = Column(Boolean, nullable=False, server_default="false")  # True for products with size variants
    is_active = Column(Boolean, nullable=False, server_default="true")
    sort_order = Column(Integer, nullable=False, server_default="0", index=True)  # For menu ordering
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")
    sales_items = relationship("SalesItem", back_populates="product")  # Legacy relationship


class ProductVariant(Base):
    """
    Represents a specific variant of a product (e.g., Kebab Small, Kebab Large).
    For single-size products, name is NULL and the product has one variant.
    """
    __tablename__ = "product_variants"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(50), nullable=True)  # NULL for single-size products
    price_pln = Column(Numeric(10, 2), nullable=False)
    is_default = Column(Boolean, nullable=False, server_default="false")  # Default variant for product
    is_active = Column(Boolean, nullable=False, server_default="true")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint("price_pln > 0", name="check_variant_price_positive"),
    )

    # Relationships
    product = relationship("Product", back_populates="variants")
    ingredients = relationship("ProductIngredient", back_populates="product_variant", cascade="all, delete-orphan")
    calculated_sales = relationship("CalculatedSale", back_populates="product_variant")


class ProductIngredient(Base):
    """
    Junction table linking product variants to ingredients with amounts.
    Each ingredient can be marked as primary for sales derivation.
    """
    __tablename__ = "product_ingredients"

    id = Column(Integer, primary_key=True, index=True)
    product_variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=False)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id", ondelete="RESTRICT"), nullable=False)
    quantity = Column(Numeric(10, 3), nullable=False)  # Amount per product (in ingredient's unit)
    is_primary = Column(Boolean, nullable=False, server_default="false")  # Used for sales derivation

    # Relationships
    product_variant = relationship("ProductVariant", back_populates="ingredients")
    ingredient = relationship("Ingredient", back_populates="product_ingredients")
