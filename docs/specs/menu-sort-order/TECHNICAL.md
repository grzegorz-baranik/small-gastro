# Technical Specification: Menu Sorting

## Metadata

| Field | Value |
|-------|-------|
| **Author** | Claude AI |
| **Created** | 2026-01-02 |
| **Version** | 1.0 |
| **Status** | Draft |
| **Functional Specification** | [Link](./README.md) |

---

## 1. Architecture Overview

### 1.1 Component Diagram
```
+-------------------------------------------------------------+
|                      Frontend                                |
|  +------------------+    +------------------------+          |
|  |   MenuPage.tsx   |    |  @dnd-kit/core        |          |
|  |   (drag-drop)    |--->|  @dnd-kit/sortable    |          |
|  +------------------+    +------------------------+          |
+-------------------------------------------------------------+
                           |
                           v
+-------------------------------------------------------------+
|                    Backend API                               |
|  +------------------+    +------------------+                |
|  |   products.py    |--->|  ProductService  |                |
|  |   (router)       |    |                  |                |
|  +------------------+    +------------------+                |
+-------------------------------------------------------------+
                           |
                           v
                 +-------------------+
                 |   PostgreSQL      |
                 |   products.       |
                 |   sort_order      |
                 +-------------------+
```

### 1.2 Components to Modify
- `backend/app/models/product.py` - add `sort_order` field
- `backend/app/api/v1/products.py` - new endpoint for order update
- `backend/app/services/product_service.py` - sorting logic
- `frontend/src/pages/MenuPage.tsx` - drag-and-drop implementation
- `frontend/src/api/products.ts` - API function for order update

### 1.3 New Dependencies
- Frontend: `@dnd-kit/core`, `@dnd-kit/sortable`, `@dnd-kit/utilities`

---

## 2. API Endpoints

### 2.1 Update Product Order

```http
PUT /api/v1/products/reorder
```

**Request:**
```json
{
  "product_ids": [5, 2, 8, 1, 3]
}
```

**Description:** The `product_ids` array contains product IDs in the new order. The index in the array corresponds to the `sort_order` value (0 = first, 1 = second, etc.).

**Response (200):**
```json
{
  "message": "Kolejność zaktualizowana",
  "updated_count": 5
}
```

**Response (400):**
```json
{
  "detail": "Nieprawidłowa lista produktów"
}
```

---

### 2.2 Modification of Existing Endpoints

#### GET /api/v1/products

Add default sorting by `sort_order`:

```python
products = db.query(Product).order_by(Product.sort_order.asc()).all()
```

---

## 3. Database Schema

### 3.1 Modifications to Existing Table

```sql
ALTER TABLE products
ADD COLUMN sort_order INTEGER NOT NULL DEFAULT 0;

-- Set initial values based on ID
UPDATE products SET sort_order = id;

-- Create index for efficient sorting
CREATE INDEX idx_products_sort_order ON products(sort_order);
```

### 3.2 ERD Diagram (fragment)
```
+------------------+
|    products      |
+------------------+
| id (PK)          |
| name             |
| has_variants     |
| is_active        |
| sort_order (NEW) |  <-- INTEGER NOT NULL DEFAULT 0
| created_at       |
| updated_at       |
+------------------+
```

### 3.3 Alembic Migration

```python
# alembic/versions/xxx_add_product_sort_order.py

def upgrade():
    op.add_column('products', sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'))

    # Set initial sort_order based on id
    op.execute("UPDATE products SET sort_order = id")

    op.create_index('idx_products_sort_order', 'products', ['sort_order'])

def downgrade():
    op.drop_index('idx_products_sort_order', 'products')
    op.drop_column('products', 'sort_order')
```

---

## 4. SQLAlchemy Models

### 4.1 Product Modification

```python
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    has_variants = Column(Boolean, nullable=False, server_default="false")
    is_active = Column(Boolean, nullable=False, server_default="true")
    sort_order = Column(Integer, nullable=False, server_default="0", index=True)  # NEW
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")
```

---

## 5. Pydantic Schemas

### 5.1 ProductReorderRequest

```python
class ProductReorderRequest(BaseModel):
    product_ids: list[int] = Field(..., min_length=1, description="List of product IDs in new order")

    @field_validator('product_ids')
    @classmethod
    def validate_unique_ids(cls, v):
        if len(v) != len(set(v)):
            raise ValueError("Lista zawiera duplikaty ID")
        return v
```

### 5.2 ProductReorderResponse

```python
class ProductReorderResponse(BaseModel):
    message: str
    updated_count: int
```

### 5.3 ProductResponse Modification

```python
class ProductResponse(BaseModel):
    id: int
    name: str
    has_variants: bool
    is_active: bool
    sort_order: int  # NEW
    variants: list[ProductVariantResponse]

    class Config:
        from_attributes = True
```

---

## 6. Service Layer

### 6.1 ProductService - new method

```python
def reorder_products(self, product_ids: list[int]) -> int:
    """
    Updates product order.

    Args:
        product_ids: List of product IDs in new order

    Returns:
        Number of updated products

    Raises:
        ValueError: When list contains non-existent IDs
    """
    # Verify all IDs exist
    existing_ids = {p.id for p in self.db.query(Product.id).filter(
        Product.id.in_(product_ids)
    ).all()}

    missing_ids = set(product_ids) - existing_ids
    if missing_ids:
        raise ValueError(f"Nie znaleziono produktów o ID: {missing_ids}")

    # Bulk update
    for index, product_id in enumerate(product_ids):
        self.db.query(Product).filter(Product.id == product_id).update(
            {"sort_order": index}
        )

    self.db.commit()
    return len(product_ids)
```

### 6.2 ProductService - create modification

```python
def create_product(self, data: ProductCreate) -> Product:
    # Get maximum sort_order
    max_sort = self.db.query(func.max(Product.sort_order)).scalar() or 0

    product = Product(
        name=data.name,
        sort_order=max_sort + 1
    )
    # ... rest of logic
```

---

## 7. Frontend Components

### 7.1 File Structure

```
frontend/src/
├── api/
│   └── products.ts           # + reorderProducts function
├── components/
│   └── products/
│       └── SortableProductCard.tsx  # NEW - draggable product card
└── pages/
    └── MenuPage.tsx          # + drag-drop integration
```

### 7.2 TypeScript Interfaces

```typescript
// types/index.ts
export interface Product {
  id: number;
  name: string;
  has_variants: boolean;
  is_active: boolean;
  sort_order: number;  // NEW
  variants: ProductVariantInProduct[];
}

export interface ReorderProductsRequest {
  product_ids: number[];
}

export interface ReorderProductsResponse {
  message: string;
  updated_count: number;
}
```

### 7.3 API Client

```typescript
// api/products.ts
export const reorderProducts = async (productIds: number[]): Promise<ReorderProductsResponse> => {
  const response = await fetch(`${API_BASE}/products/reorder`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ product_ids: productIds })
  });

  if (!response.ok) {
    throw new Error('Nie udało się zaktualizować kolejności');
  }

  return response.json();
};
```

### 7.4 React Query Hook

```typescript
// hooks/useReorderProducts.ts
export function useReorderProducts() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: reorderProducts,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] });
    },
    onError: (error) => {
      toast.error('Nie udało się zapisać kolejności');
    }
  });
}
```

### 7.5 SortableProductCard Component

```typescript
// components/products/SortableProductCard.tsx
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { GripVertical } from 'lucide-react';

interface SortableProductCardProps {
  product: Product;
  onManageVariants: () => void;
  onDelete: () => void;
}

export function SortableProductCard({ product, onManageVariants, onDelete }: SortableProductCardProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: product.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.8 : 1,
  };

  return (
    <div ref={setNodeRef} style={style} className={`card ${isDragging ? 'shadow-lg' : ''}`}>
      <div className="flex items-start gap-3">
        <button
          {...attributes}
          {...listeners}
          className="p-2 hover:bg-gray-100 rounded cursor-grab active:cursor-grabbing"
        >
          <GripVertical className="w-4 h-4 text-gray-400" />
        </button>
        {/* Rest of ProductCard content */}
      </div>
    </div>
  );
}
```

### 7.6 MenuPage Integration

```typescript
// pages/MenuPage.tsx (fragment)
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core';
import {
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';

function ProductsList({ products, onReorder }) {
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (over && active.id !== over.id) {
      const oldIndex = products.findIndex(p => p.id === active.id);
      const newIndex = products.findIndex(p => p.id === over.id);

      const newOrder = arrayMove(products, oldIndex, newIndex);
      onReorder(newOrder.map(p => p.id));
    }
  };

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragEnd={handleDragEnd}
    >
      <SortableContext
        items={products.map(p => p.id)}
        strategy={verticalListSortingStrategy}
      >
        {products.map(product => (
          <SortableProductCard key={product.id} product={product} />
        ))}
      </SortableContext>
    </DndContext>
  );
}
```

---

## 8. Performance

### 8.1 Database Indexes
```sql
CREATE INDEX idx_products_sort_order ON products(sort_order);
```

### 8.2 Optimizations
- Bulk update in a single transaction instead of separate UPDATEs for each product
- Optimistic update in UI - immediate order change before API confirmation

---

## 9. Testing

### 9.1 Unit Tests
- [ ] ProductService.reorder_products() - correct update
- [ ] ProductService.reorder_products() - error on non-existent ID
- [ ] ProductService.create_product() - correct sort_order for new product

### 9.2 Integration Tests
- [ ] PUT /api/v1/products/reorder - success
- [ ] PUT /api/v1/products/reorder - validation error
- [ ] GET /api/v1/products - sorted by sort_order

### 9.3 E2E Tests
- [ ] Drag-and-drop product and verify new order

---

## 10. Deployment Plan

### 10.1 Database Migration
```bash
cd backend
alembic upgrade head
```

### 10.2 Deployment Steps
1. Deploy backend with new migration
2. Deploy frontend with new @dnd-kit dependency
3. Verify sorting in production

### 10.3 Rollback
```bash
alembic downgrade -1
```

---

## Change History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-02 | Claude AI | Initial version |
