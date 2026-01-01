"""Daily Inventory Management schema changes

Revision ID: 002
Revises: 001
Create Date: 2026-01-01

This migration adds support for:
- Product variants (different sizes with different prices)
- Ingredient unit labels and soft delete
- Daily record financial tracking
- Inventory snapshots with location (shop/storage)
- Deliveries, storage transfers, and spoilage tracking
- Calculated sales derived from ingredient usage
- Storage inventory tracking

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # =========================================================================
    # STEP 1: Create new enum types
    # =========================================================================

    # Create inventory_location enum
    inventory_location_enum = postgresql.ENUM('shop', 'storage', name='inventorylocation', create_type=False)
    inventory_location_enum.create(op.get_bind(), checkfirst=True)

    # Create spoilage_reason enum
    spoilage_reason_enum = postgresql.ENUM(
        'expired', 'over_prepared', 'contaminated', 'equipment_failure', 'other',
        name='spoilagereason', create_type=False
    )
    spoilage_reason_enum.create(op.get_bind(), checkfirst=True)

    # =========================================================================
    # STEP 2: Add new columns to existing tables
    # =========================================================================

    # Add unit_label and is_active to ingredients
    op.add_column('ingredients', sa.Column('unit_label', sa.String(length=20), nullable=True))
    op.add_column('ingredients', sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False))

    # Set default unit_label based on unit_type
    op.execute("""
        UPDATE ingredients
        SET unit_label = CASE
            WHEN unit_type = 'weight' THEN 'kg'
            WHEN unit_type = 'count' THEN 'szt'
            ELSE 'szt'
        END
    """)

    # Make unit_label NOT NULL after data migration
    op.alter_column('ingredients', 'unit_label', nullable=False, server_default='szt')

    # Add has_variants to products
    op.add_column('products', sa.Column('has_variants', sa.Boolean(), server_default='false', nullable=False))

    # Add financial fields to daily_records
    op.add_column('daily_records', sa.Column('total_income_pln', sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column('daily_records', sa.Column('total_delivery_cost_pln', sa.Numeric(precision=10, scale=2), server_default='0', nullable=False))
    op.add_column('daily_records', sa.Column('total_spoilage_cost_pln', sa.Numeric(precision=10, scale=2), server_default='0', nullable=False))
    op.add_column('daily_records', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True))

    # =========================================================================
    # STEP 3: Create product_variants table
    # =========================================================================

    op.create_table(
        'product_variants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=True),
        sa.Column('price_pln', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('price_pln > 0', name='check_variant_price_positive')
    )
    op.create_index(op.f('ix_product_variants_id'), 'product_variants', ['id'], unique=False)
    op.create_index('ix_product_variants_product_id', 'product_variants', ['product_id'], unique=False)

    # =========================================================================
    # STEP 4: Migrate products to product_variants
    # Create one variant per existing product using its price
    # =========================================================================

    op.execute("""
        INSERT INTO product_variants (product_id, name, price_pln, is_active, created_at)
        SELECT id, NULL, price, is_active, created_at
        FROM products
    """)

    # =========================================================================
    # STEP 5: Update product_ingredients table
    # Add new columns, migrate FK, then remove old column
    # =========================================================================

    # Add new columns to product_ingredients
    op.add_column('product_ingredients', sa.Column('product_variant_id', sa.Integer(), nullable=True))
    op.add_column('product_ingredients', sa.Column('is_primary', sa.Boolean(), server_default='false', nullable=False))

    # Migrate product_id to product_variant_id (using the newly created variants)
    op.execute("""
        UPDATE product_ingredients pi
        SET product_variant_id = pv.id
        FROM product_variants pv
        WHERE pi.product_id = pv.product_id
    """)

    # Make product_variant_id NOT NULL
    op.alter_column('product_ingredients', 'product_variant_id', nullable=False)

    # Drop old constraint and FK
    op.drop_constraint('product_ingredients_product_id_ingredient_id_key', 'product_ingredients', type_='unique')
    op.drop_constraint('product_ingredients_product_id_fkey', 'product_ingredients', type_='foreignkey')

    # Drop product_id column
    op.drop_column('product_ingredients', 'product_id')

    # Add new FK constraint
    op.create_foreign_key(
        'product_ingredients_product_variant_id_fkey',
        'product_ingredients',
        'product_variants',
        ['product_variant_id'],
        ['id'],
        ondelete='CASCADE'
    )

    # Add new unique constraint
    op.create_unique_constraint(
        'product_ingredients_variant_ingredient_key',
        'product_ingredients',
        ['product_variant_id', 'ingredient_id']
    )

    # =========================================================================
    # STEP 6: Update inventory_snapshots table
    # Add location column, migrate quantity, update constraint
    # =========================================================================

    # Add new columns
    op.add_column('inventory_snapshots', sa.Column(
        'location',
        sa.Enum('shop', 'storage', name='inventorylocation'),
        server_default='shop',
        nullable=False
    ))
    op.add_column('inventory_snapshots', sa.Column('quantity', sa.Numeric(precision=10, scale=3), nullable=True))

    # Migrate data: use quantity_grams or quantity_count based on ingredient unit_type
    op.execute("""
        UPDATE inventory_snapshots inv
        SET quantity = CASE
            WHEN i.unit_type = 'weight' THEN COALESCE(inv.quantity_grams, 0)
            WHEN i.unit_type = 'count' THEN COALESCE(inv.quantity_count, 0)
            ELSE 0
        END
        FROM ingredients i
        WHERE inv.ingredient_id = i.id
    """)

    # Make quantity NOT NULL
    op.alter_column('inventory_snapshots', 'quantity', nullable=False)

    # Drop old unique constraint
    op.drop_constraint('uq_snapshot_per_day_ingredient_type', 'inventory_snapshots', type_='unique')

    # Create new unique constraint including location
    op.create_unique_constraint(
        'uq_snapshot_per_day_ingredient_type_location',
        'inventory_snapshots',
        ['daily_record_id', 'ingredient_id', 'snapshot_type', 'location']
    )

    # Drop old quantity columns (keeping for now, will be dropped in future migration)
    # op.drop_column('inventory_snapshots', 'quantity_grams')
    # op.drop_column('inventory_snapshots', 'quantity_count')

    # =========================================================================
    # STEP 7: Create new tables for daily operations
    # =========================================================================

    # Deliveries table
    op.create_table(
        'deliveries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('daily_record_id', sa.Integer(), nullable=False),
        sa.Column('ingredient_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=10, scale=3), nullable=False),
        sa.Column('price_pln', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('delivered_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['daily_record_id'], ['daily_records.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['ingredient_id'], ['ingredients.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('quantity > 0', name='check_delivery_quantity_positive'),
        sa.CheckConstraint('price_pln >= 0', name='check_delivery_price_non_negative')
    )
    op.create_index(op.f('ix_deliveries_id'), 'deliveries', ['id'], unique=False)
    op.create_index('ix_deliveries_daily_record_id', 'deliveries', ['daily_record_id'], unique=False)

    # Storage transfers table
    op.create_table(
        'storage_transfers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('daily_record_id', sa.Integer(), nullable=False),
        sa.Column('ingredient_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=10, scale=3), nullable=False),
        sa.Column('transferred_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['daily_record_id'], ['daily_records.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['ingredient_id'], ['ingredients.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('quantity > 0', name='check_transfer_quantity_positive')
    )
    op.create_index(op.f('ix_storage_transfers_id'), 'storage_transfers', ['id'], unique=False)
    op.create_index('ix_storage_transfers_daily_record_id', 'storage_transfers', ['daily_record_id'], unique=False)

    # Spoilages table
    op.create_table(
        'spoilages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('daily_record_id', sa.Integer(), nullable=False),
        sa.Column('ingredient_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=10, scale=3), nullable=False),
        sa.Column('reason', postgresql.ENUM('expired', 'over_prepared', 'contaminated', 'equipment_failure', 'other', name='spoilagereason', create_type=False), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('recorded_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['daily_record_id'], ['daily_records.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['ingredient_id'], ['ingredients.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('quantity > 0', name='check_spoilage_quantity_positive')
    )
    op.create_index(op.f('ix_spoilages_id'), 'spoilages', ['id'], unique=False)
    op.create_index('ix_spoilages_daily_record_id', 'spoilages', ['daily_record_id'], unique=False)

    # Calculated sales table
    op.create_table(
        'calculated_sales',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('daily_record_id', sa.Integer(), nullable=False),
        sa.Column('product_variant_id', sa.Integer(), nullable=False),
        sa.Column('quantity_sold', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('revenue_pln', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['daily_record_id'], ['daily_records.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_variant_id'], ['product_variants.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('quantity_sold >= 0', name='check_calc_sale_quantity_non_negative'),
        sa.CheckConstraint('revenue_pln >= 0', name='check_calc_sale_revenue_non_negative')
    )
    op.create_index(op.f('ix_calculated_sales_id'), 'calculated_sales', ['id'], unique=False)
    op.create_index('ix_calculated_sales_daily_record_id', 'calculated_sales', ['daily_record_id'], unique=False)

    # Storage inventory table
    op.create_table(
        'storage_inventory',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ingredient_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=10, scale=3), server_default='0', nullable=False),
        sa.Column('last_counted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['ingredient_id'], ['ingredients.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('ingredient_id', name='uq_storage_inventory_ingredient'),
        sa.CheckConstraint('quantity >= 0', name='check_storage_quantity_non_negative')
    )
    op.create_index(op.f('ix_storage_inventory_id'), 'storage_inventory', ['id'], unique=False)

    # =========================================================================
    # STEP 8: Drop price column from products (moved to variants)
    # =========================================================================

    op.drop_column('products', 'price')


def downgrade() -> None:
    # =========================================================================
    # STEP 1: Restore price column to products
    # =========================================================================

    op.add_column('products', sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=True))

    # Migrate price back from first variant
    op.execute("""
        UPDATE products p
        SET price = (
            SELECT pv.price_pln
            FROM product_variants pv
            WHERE pv.product_id = p.id
            ORDER BY pv.id
            LIMIT 1
        )
    """)

    op.alter_column('products', 'price', nullable=False)

    # =========================================================================
    # STEP 2: Drop new tables
    # =========================================================================

    op.drop_table('storage_inventory')
    op.drop_table('calculated_sales')
    op.drop_table('spoilages')
    op.drop_table('storage_transfers')
    op.drop_table('deliveries')

    # =========================================================================
    # STEP 3: Restore product_ingredients structure
    # =========================================================================

    # Add product_id back
    op.add_column('product_ingredients', sa.Column('product_id', sa.Integer(), nullable=True))

    # Migrate product_variant_id back to product_id
    op.execute("""
        UPDATE product_ingredients pi
        SET product_id = pv.product_id
        FROM product_variants pv
        WHERE pi.product_variant_id = pv.id
    """)

    op.alter_column('product_ingredients', 'product_id', nullable=False)

    # Drop new constraints and columns
    op.drop_constraint('product_ingredients_variant_ingredient_key', 'product_ingredients', type_='unique')
    op.drop_constraint('product_ingredients_product_variant_id_fkey', 'product_ingredients', type_='foreignkey')
    op.drop_column('product_ingredients', 'product_variant_id')
    op.drop_column('product_ingredients', 'is_primary')

    # Recreate old FK and constraint
    op.create_foreign_key(
        'product_ingredients_product_id_fkey',
        'product_ingredients',
        'products',
        ['product_id'],
        ['id'],
        ondelete='CASCADE'
    )
    op.create_unique_constraint(
        'product_ingredients_product_id_ingredient_id_key',
        'product_ingredients',
        ['product_id', 'ingredient_id']
    )

    # =========================================================================
    # STEP 4: Restore inventory_snapshots structure
    # =========================================================================

    # Drop new constraint and add back old one
    op.drop_constraint('uq_snapshot_per_day_ingredient_type_location', 'inventory_snapshots', type_='unique')
    op.create_unique_constraint(
        'uq_snapshot_per_day_ingredient_type',
        'inventory_snapshots',
        ['daily_record_id', 'ingredient_id', 'snapshot_type']
    )

    # Drop new columns (quantity and location)
    op.drop_column('inventory_snapshots', 'quantity')
    op.drop_column('inventory_snapshots', 'location')

    # =========================================================================
    # STEP 5: Drop product_variants table
    # =========================================================================

    op.drop_index('ix_product_variants_product_id', table_name='product_variants')
    op.drop_index(op.f('ix_product_variants_id'), table_name='product_variants')
    op.drop_table('product_variants')

    # =========================================================================
    # STEP 6: Remove new columns from existing tables
    # =========================================================================

    # daily_records
    op.drop_column('daily_records', 'updated_at')
    op.drop_column('daily_records', 'total_spoilage_cost_pln')
    op.drop_column('daily_records', 'total_delivery_cost_pln')
    op.drop_column('daily_records', 'total_income_pln')

    # products
    op.drop_column('products', 'has_variants')

    # ingredients
    op.drop_column('ingredients', 'is_active')
    op.drop_column('ingredients', 'unit_label')

    # =========================================================================
    # STEP 7: Drop new enum types
    # =========================================================================

    op.execute('DROP TYPE IF EXISTS spoilagereason')
    op.execute('DROP TYPE IF EXISTS inventorylocation')
