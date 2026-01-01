# CLAUDE_CODE_INSTRUCTIONS.md

## Specification-Driven Development Protocol

This document defines mandatory behavior for all AI coding assistance in the **small-gastro** project.

---

## CRITICAL RULE: Documentation-First Workflow

**BEFORE writing ANY implementation code, you MUST:**

1. Check if specification exists in `docs/specs/{feature-name}/`
2. If no specification exists:
   - STOP and inform the user
   - Offer to create the specification first
   - Use templates from `docs/templates/`
3. If specification exists but is incomplete:
   - Identify missing sections
   - Complete specification before coding

---

## Project Context

- **Language**: Polish (all UI labels, error messages, documentation)
- **Currency**: PLN (Polish Zloty)
- **Stack**:
  - Frontend: React + TypeScript + Vite + TailwindCSS
  - Backend: Python FastAPI + SQLAlchemy
  - Database: PostgreSQL

---

## Workflow Phases

### Phase 1: Specification (REQUIRED)

Before any implementation:

```
docs/specs/{feature-name}/
├── README.md          # Functional specification
├── TECHNICAL.md       # Technical design
├── TESTING.md         # Test plan
└── scenarios.feature  # BDD scenarios (Gherkin)
```

**Specification Checklist:**
- [ ] User stories defined
- [ ] Acceptance criteria clear
- [ ] Edge cases documented
- [ ] API contracts specified
- [ ] Database changes identified
- [ ] BDD scenarios written
- [ ] Success metrics defined

### Phase 2: Review & Approval

- User must explicitly approve specifications
- Document approval in spec file header
- No coding until approval received

### Phase 3: Implementation

Only after approval:
1. Create feature branch
2. Implement according to spec
3. Write tests matching BDD scenarios
4. Update specs if changes needed

### Phase 4: Verification

- Run all tests
- Verify BDD scenarios pass
- Update documentation if needed
- Create PR with spec reference

---

## Required Artifacts

### Functional Specification (README.md)

Must include:
- Feature overview (Polish)
- User stories
- Acceptance criteria
- UI mockups/descriptions
- Edge cases
- Success metrics

### Technical Specification (TECHNICAL.md)

Must include:
- Architecture overview
- API endpoints (OpenAPI format)
- Database schema changes
- Component structure
- Security considerations
- Performance requirements

### BDD Scenarios (scenarios.feature)

Must include:
- Happy path scenarios
- Error scenarios
- Edge case scenarios
- Polish language descriptions

Example:
```gherkin
# language: pl
Funkcja: Zarządzanie składnikami

  Scenariusz: Dodanie nowego składnika
    Zakładając że jestem zalogowany jako administrator
    Gdy dodam nowy składnik "Sałata" z jednostką "kg"
    Wtedy składnik powinien pojawić się na liście
    I powinien mieć jednostkę "kg"
```

### Test Plan (TESTING.md)

Must include:
- Test scope
- Test scenarios
- Expected results
- Edge cases to test

---

## Architecture Decision Records (ADRs)

When making significant architectural decisions:

1. Create ADR in `docs/adrs/ADR-{number}-{title}.md`
2. Use template from `docs/templates/adr-template.md`
3. Document context, decision, and consequences

Triggers for ADR:
- New technology/library
- Database schema changes
- API design decisions
- Security architecture
- Performance optimizations

---

## Existing Models Reference

Use these models when designing features:

| Model | Polish Name | Description |
|-------|-------------|-------------|
| `Ingredient` | Składnik | Base ingredients with unit_type |
| `Product` | Produkt | Menu items with prices |
| `ProductIngredient` | SkładnikProduktu | Links products to ingredients |
| `ExpenseCategory` | KategoriaWydatków | Hierarchical categories (max 3 levels) |
| `DailyRecord` | RaportDzienny | Daily open/close records |
| `InventorySnapshot` | StanMagazynowy | Inventory at day open/close |
| `SalesItem` | Sprzedaż | Sales transactions |
| `Transaction` | Transakcja | Financial transactions |

---

## API Design Standards

All new endpoints must follow:

```
Base: /api/v1/{resource}

GET    /{resource}           # List (with pagination)
GET    /{resource}/{id}      # Get single
POST   /{resource}           # Create
PUT    /{resource}/{id}      # Update
DELETE /{resource}/{id}      # Delete
```

Response format:
```json
{
  "data": {...},
  "message": "Sukces",
  "errors": []
}
```

Error messages in Polish.

---

## Code Standards

### Backend (Python/FastAPI)

- Use service layer for business logic
- Pydantic schemas for validation
- OpenAPI annotations on all endpoints
- Unit tests for all services
- Error messages in Polish

### Frontend (React/TypeScript)

- React Query for data fetching
- TailwindCSS with custom classes (.btn, .input, .card)
- Context API for shared state
- All UI labels in Polish

---

## Enforcement Commands

Use these commands to check compliance:

```bash
# Check specification coverage
python scripts/check-spec-coverage.py

# Create new feature scaffold
python scripts/new-feature.py {feature-name}
```

---

## Response Templates

### When No Specification Exists

```
Nie znalazłem specyfikacji dla tej funkcjonalności.

Zanim zacznę implementację, muszę utworzyć dokumentację:
1. Specyfikacja funkcjonalna (README.md)
2. Specyfikacja techniczna (TECHNICAL.md)
3. Scenariusze BDD (scenarios.feature)
4. Plan testów (TESTING.md)

Czy chcesz, żebym rozpoczął od utworzenia specyfikacji?
```

### When Specification Incomplete

```
Znalazłem specyfikację, ale brakuje następujących sekcji:
- [lista brakujących sekcji]

Czy chcesz, żebym uzupełnił brakujące elementy przed implementacją?
```

### When Ready to Implement

```
Specyfikacja jest kompletna i zatwierdzona.

Rozpoczynam implementację zgodnie z:
- docs/specs/{feature}/README.md
- docs/specs/{feature}/TECHNICAL.md

Czy mogę kontynuować?
```

---

## Summary

1. **ALWAYS** check for specification first
2. **NEVER** implement without approved spec
3. **ALWAYS** use Polish for UI and messages
4. **ALWAYS** reference existing models
5. **ALWAYS** follow API standards
6. **ALWAYS** write BDD scenarios before tests
