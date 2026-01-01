# Specyfikacja Techniczna: {Nazwa Funkcjonalności}

## Metadane

| Pole | Wartość |
|------|---------|
| **Autor** | {imię i nazwisko} |
| **Data utworzenia** | {YYYY-MM-DD} |
| **Wersja** | 1.0 |
| **Status** | Draft / W recenzji / Zatwierdzony |
| **Specyfikacja funkcjonalna** | [Link](./README.md) |

---

## 1. Przegląd architektury

### 1.1 Diagram komponentów
```
┌─────────────────────────────────────────────────────────┐
│                      Frontend                            │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │   Pages     │    │  Components │    │   Context   │  │
│  └─────────────┘    └─────────────┘    └─────────────┘  │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                    Backend API                           │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │   Routers   │───▶│   Services  │───▶│   Models    │  │
│  └─────────────┘    └─────────────┘    └─────────────┘  │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
                 ┌─────────────────┐
                 │   PostgreSQL    │
                 └─────────────────┘
```

### 1.2 Komponenty do modyfikacji
- {komponent 1} - {opis zmian}
- {komponent 2} - {opis zmian}

### 1.3 Nowe komponenty
- {nowy komponent} - {opis}

---

## 2. API Endpoints

### 2.1 {Nazwa endpointu}

```http
POST /api/v1/{resource}
```

**Request:**
```json
{
  "field1": "string",
  "field2": 123
}
```

**Response (200):**
```json
{
  "id": 1,
  "field1": "string",
  "field2": 123,
  "created_at": "2024-01-01T12:00:00Z"
}
```

**Response (400):**
```json
{
  "detail": "Błąd walidacji: {opis błędu}"
}
```

**Response (404):**
```json
{
  "detail": "Nie znaleziono zasobu"
}
```

---

### 2.2 {Nazwa endpointu}

```http
GET /api/v1/{resource}/{id}
```

**Parameters:**
| Nazwa | Typ | Wymagany | Opis |
|-------|-----|----------|------|
| id | integer | Tak | ID zasobu |

**Response (200):**
```json
{
  "id": 1,
  "field1": "string"
}
```

---

## 3. Schemat bazy danych

### 3.1 Nowe tabele

```sql
CREATE TABLE {table_name} (
    id SERIAL PRIMARY KEY,
    {column1} VARCHAR(255) NOT NULL,
    {column2} INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 3.2 Modyfikacje istniejących tabel

```sql
ALTER TABLE {existing_table}
ADD COLUMN {new_column} VARCHAR(100);
```

### 3.3 Diagram ERD
```
┌──────────────┐       ┌──────────────┐
│   Table1     │       │   Table2     │
├──────────────┤       ├──────────────┤
│ id (PK)      │───┐   │ id (PK)      │
│ name         │   └──▶│ table1_id    │
│ created_at   │       │ value        │
└──────────────┘       └──────────────┘
```

### 3.4 Migracja Alembic

```python
# alembic/versions/{revision}_add_{feature}.py

def upgrade():
    op.create_table(
        '{table_name}',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('{column}', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now())
    )

def downgrade():
    op.drop_table('{table_name}')
```

---

## 4. Modele SQLAlchemy

### 4.1 {Nazwa modelu}

```python
class {ModelName}(Base):
    __tablename__ = "{table_name}"

    id: Mapped[int] = mapped_column(primary_key=True)
    {field}: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    # Relationships
    {related}: Mapped["{RelatedModel}"] = relationship(
        back_populates="{back_ref}"
    )
```

---

## 5. Schematy Pydantic

### 5.1 {Nazwa}Create

```python
class {Name}Create(BaseModel):
    {field1}: str = Field(..., min_length=1, max_length=255)
    {field2}: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "field1": "przykład",
                "field2": 123
            }
        }
```

### 5.2 {Nazwa}Response

```python
class {Name}Response(BaseModel):
    id: int
    {field1}: str
    {field2}: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True
```

---

## 6. Warstwa serwisów

### 6.1 {Nazwa}Service

```python
class {Name}Service:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: {Name}Create) -> {Name}:
        """
        Tworzy nowy {obiekt}.

        Args:
            data: Dane do utworzenia

        Returns:
            Utworzony obiekt

        Raises:
            ValueError: Gdy dane są nieprawidłowe
        """
        # Implementacja
        pass

    def get_by_id(self, id: int) -> Optional[{Name}]:
        """Pobiera obiekt po ID."""
        pass
```

---

## 7. Komponenty Frontend

### 7.1 Struktura plików

```
frontend/src/
├── api/
│   └── {feature}.ts           # API client functions
├── components/
│   └── {feature}/
│       ├── {Component1}.tsx
│       └── {Component2}.tsx
├── pages/
│   └── {Feature}Page.tsx
└── types/
    └── {feature}.ts           # TypeScript interfaces
```

### 7.2 Interfejsy TypeScript

```typescript
export interface {Name} {
  id: number;
  field1: string;
  field2?: number;
  createdAt: string;
}

export interface {Name}Create {
  field1: string;
  field2?: number;
}
```

### 7.3 API Client

```typescript
export const {name}Api = {
  getAll: async (): Promise<{Name}[]> => {
    const response = await fetch(`${API_BASE}/{resource}`);
    return response.json();
  },

  create: async (data: {Name}Create): Promise<{Name}> => {
    const response = await fetch(`${API_BASE}/{resource}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return response.json();
  }
};
```

### 7.4 React Query Hooks

```typescript
export function use{Names}() {
  return useQuery({
    queryKey: ['{names}'],
    queryFn: {name}Api.getAll
  });
}

export function useCreate{Name}() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: {name}Api.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['{names}'] });
    }
  });
}
```

---

## 8. Bezpieczeństwo

### 8.1 Walidacja danych
- {opis walidacji}

### 8.2 Autoryzacja
- {opis autoryzacji}

### 8.3 Potencjalne zagrożenia
| Zagrożenie | Mitygacja |
|------------|-----------|
| {zagrożenie} | {rozwiązanie} |

---

## 9. Wydajność

### 9.1 Indeksy bazy danych
```sql
CREATE INDEX idx_{table}_{column} ON {table}({column});
```

### 9.2 Caching
- {strategia cache}

### 9.3 Optymalizacje zapytań
- {optymalizacja}

---

## 10. Testowanie

### 10.1 Testy jednostkowe
- [ ] {Name}Service.create()
- [ ] {Name}Service.get_by_id()
- [ ] Walidacja schematów Pydantic

### 10.2 Testy integracyjne
- [ ] POST /api/v1/{resource}
- [ ] GET /api/v1/{resource}/{id}

### 10.3 Testy E2E
- [ ] Pełny przepływ tworzenia {obiektu}

---

## 11. Plan wdrożenia

### 11.1 Migracja bazy danych
```bash
alembic upgrade head
```

### 11.2 Kroki wdrożenia
1. {krok 1}
2. {krok 2}
3. {krok 3}

### 11.3 Rollback
```bash
alembic downgrade -{n}
```

---

## 12. Monitoring

### 12.1 Logi
- {co logujemy}

### 12.2 Metryki
- {metryki do śledzenia}

---

## Historia zmian

| Wersja | Data | Autor | Opis zmian |
|--------|------|-------|------------|
| 1.0 | {data} | {autor} | Wersja początkowa |
