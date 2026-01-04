# Technical Specification: {Feature Name}

## Metadata

| Field | Value |
|-------|-------|
| **Author** | {author} |
| **Created** | {YYYY-MM-DD} |
| **Version** | 1.0 |
| **Status** | Draft / In Review / Approved |
| **Functional Specification** | [Link](./README.md) |

---

## 1. Architecture Overview

### 1.1 Component Diagram
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

### 1.2 Components to Modify
- {component 1} - {change description}
- {component 2} - {change description}

### 1.3 New Components
- {new component} - {description}

---

## 2. API Endpoints

### 2.1 {Endpoint Name}

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
  "detail": "Validation error: {error description in Polish}"
}
```

**Response (404):**
```json
{
  "detail": "Nie znaleziono"
}
```

---

### 2.2 {Endpoint Name}

```http
GET /api/v1/{resource}/{id}
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | integer | Yes | Resource ID |

**Response (200):**
```json
{
  "id": 1,
  "field1": "string"
}
```

---

## 3. Database Schema

### 3.1 New Tables

```sql
CREATE TABLE {table_name} (
    id SERIAL PRIMARY KEY,
    {column1} VARCHAR(255) NOT NULL,
    {column2} INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 3.2 Modifications to Existing Tables

```sql
ALTER TABLE {existing_table}
ADD COLUMN {new_column} VARCHAR(100);
```

### 3.3 ERD Diagram
```
┌──────────────┐       ┌──────────────┐
│   Table1     │       │   Table2     │
├──────────────┤       ├──────────────┤
│ id (PK)      │───┐   │ id (PK)      │
│ name         │   └──▶│ table1_id    │
│ created_at   │       │ value        │
└──────────────┘       └──────────────┘
```

### 3.4 Alembic Migration

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

## 4. SQLAlchemy Models

### 4.1 {Model Name}

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

## 5. Pydantic Schemas

### 5.1 {Name}Create

```python
class {Name}Create(BaseModel):
    {field1}: str = Field(..., min_length=1, max_length=255)
    {field2}: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "field1": "example",
                "field2": 123
            }
        }
```

### 5.2 {Name}Response

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

## 6. Service Layer

### 6.1 {Name}Service

```python
class {Name}Service:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: {Name}Create) -> {Name}:
        """
        Creates a new {object}.

        Args:
            data: Data for creation

        Returns:
            Created object

        Raises:
            ValueError: When data is invalid
        """
        # Implementation
        pass

    def get_by_id(self, id: int) -> Optional[{Name}]:
        """Gets object by ID."""
        pass
```

---

## 7. Frontend Components

### 7.1 File Structure

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

### 7.2 TypeScript Interfaces

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

## 8. Security

### 8.1 Data Validation
- {validation description}

### 8.2 Authorization
- {authorization description}

### 8.3 Potential Threats
| Threat | Mitigation |
|--------|------------|
| {threat} | {solution} |

---

## 9. Performance

### 9.1 Database Indexes
```sql
CREATE INDEX idx_{table}_{column} ON {table}({column});
```

### 9.2 Caching
- {cache strategy}

### 9.3 Query Optimizations
- {optimization}

---

## 10. Testing

### 10.1 Unit Tests
- [ ] {Name}Service.create()
- [ ] {Name}Service.get_by_id()
- [ ] Pydantic schema validation

### 10.2 Integration Tests
- [ ] POST /api/v1/{resource}
- [ ] GET /api/v1/{resource}/{id}

### 10.3 E2E Tests
- [ ] Full {object} creation flow

---

## 11. Deployment Plan

### 11.1 Database Migration
```bash
alembic upgrade head
```

### 11.2 Deployment Steps
1. {step 1}
2. {step 2}
3. {step 3}

### 11.3 Rollback
```bash
alembic downgrade -{n}
```

---

## 12. Monitoring

### 12.1 Logs
- {what we log}

### 12.2 Metrics
- {metrics to track}

---

## Change History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | {date} | {author} | Initial version |
