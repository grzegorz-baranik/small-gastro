# Specyfikacja Techniczna: Sortowanie Menu

## Metadane

| Pole | Wartość |
|------|---------|
| **Autor** | Claude AI |
| **Data utworzenia** | 2026-01-02 |
| **Wersja** | 1.0 |
| **Status** | Draft |
| **Specyfikacja funkcjonalna** | [Link](./README.md) |

---

## 1. Przegląd architektury

### 1.1 Diagram komponentów
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

### 1.2 Komponenty do modyfikacji
- `backend/app/models/product.py` - dodanie pola `sort_order`
- `backend/app/api/v1/products.py` - nowy endpoint do aktualizacji kolejności
- `backend/app/services/product_service.py` - logika sortowania
- `frontend/src/pages/MenuPage.tsx` - implementacja drag-and-drop
- `frontend/src/api/products.ts` - funkcja API do aktualizacji kolejności

### 1.3 Nowe zależności
- Frontend: `@dnd-kit/core`, `@dnd-kit/sortable`, `@dnd-kit/utilities`

---

## 2. API Endpoints

### 2.1 Aktualizacja kolejności produktów

```http
PUT /api/v1/products/reorder
```

**Request:**
```json
{
  "product_ids": [5, 2, 8, 1, 3]
}
```

**Opis:** Tablica `product_ids` zawiera ID produktów w nowej kolejności. Indeks w tablicy odpowiada wartości `sort_order` (0 = pierwszy, 1 = drugi, itd.).

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

### 2.2 Modyfikacja istniejących endpointów

#### GET /api/v1/products

Dodanie domyślnego sortowania po `sort_order`:

```python
products = db.query(Product).order_by(Product.sort_order.asc()).all()
```

---

## 3. Schemat bazy danych

### 3.1 Modyfikacje istniejącej tabeli

```sql
ALTER TABLE products
ADD COLUMN sort_order INTEGER NOT NULL DEFAULT 0;

-- Ustawienie początkowych wartości na podstawie ID
UPDATE products SET sort_order = id;

-- Utworzenie indeksu dla wydajnego sortowania
CREATE INDEX idx_products_sort_order ON products(sort_order);
```

### 3.2 Diagram ERD (fragment)
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

### 3.3 Migracja Alembic

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

## 4. Modele SQLAlchemy

### 4.1 Modyfikacja Product

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

## 5. Schematy Pydantic

### 5.1 ProductReorderRequest

```python
class ProductReorderRequest(BaseModel):
    product_ids: list[int] = Field(..., min_length=1, description="Lista ID produktów w nowej kolejności")

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

### 5.3 Modyfikacja ProductResponse

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

## 6. Warstwa serwisów

### 6.1 ProductService - nowa metoda

```python
def reorder_products(self, product_ids: list[int]) -> int:
    """
    Aktualizuje kolejność produktów.

    Args:
        product_ids: Lista ID produktów w nowej kolejności

    Returns:
        Liczba zaktualizowanych produktów

    Raises:
        ValueError: Gdy lista zawiera nieistniejące ID
    """
    # Weryfikacja że wszystkie ID istnieją
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

### 6.2 ProductService - modyfikacja create

```python
def create_product(self, data: ProductCreate) -> Product:
    # Pobranie maksymalnego sort_order
    max_sort = self.db.query(func.max(Product.sort_order)).scalar() or 0

    product = Product(
        name=data.name,
        sort_order=max_sort + 1
    )
    # ... reszta logiki
```

---

## 7. Komponenty Frontend

### 7.1 Struktura plików

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

### 7.2 Interfejsy TypeScript

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

### 7.5 Komponent SortableProductCard

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

### 7.6 Integracja w MenuPage

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

## 8. Wydajność

### 8.1 Indeksy bazy danych
```sql
CREATE INDEX idx_products_sort_order ON products(sort_order);
```

### 8.2 Optymalizacje
- Bulk update w jednej transakcji zamiast osobnych UPDATE dla każdego produktu
- Optimistic update w UI - natychmiastowa zmiana kolejności przed potwierdzeniem z API

---

## 9. Testowanie

### 9.1 Testy jednostkowe
- [ ] ProductService.reorder_products() - poprawna aktualizacja
- [ ] ProductService.reorder_products() - błąd przy nieistniejącym ID
- [ ] ProductService.create_product() - prawidłowy sort_order dla nowego produktu

### 9.2 Testy integracyjne
- [ ] PUT /api/v1/products/reorder - sukces
- [ ] PUT /api/v1/products/reorder - błąd walidacji
- [ ] GET /api/v1/products - sortowanie po sort_order

### 9.3 Testy E2E
- [ ] Drag-and-drop produktu i weryfikacja nowej kolejności

---

## 10. Plan wdrożenia

### 10.1 Migracja bazy danych
```bash
cd backend
alembic upgrade head
```

### 10.2 Kroki wdrożenia
1. Deploy backend z nową migracją
2. Deploy frontend z nową zależnością @dnd-kit
3. Weryfikacja sortowania na produkcji

### 10.3 Rollback
```bash
alembic downgrade -1
```

---

## Historia zmian

| Wersja | Data | Autor | Opis zmian |
|--------|------|-------|------------|
| 1.0 | 2026-01-02 | Claude AI | Wersja początkowa |
