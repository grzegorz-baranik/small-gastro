# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## CRITICAL: Specification-Driven Workflow

**BEFORE writing ANY implementation code, you MUST follow the documentation-first approach.**

### Workflow Phases

1. **Specification Phase** (REQUIRED before coding)
   - Check if spec exists: `docs/specs/{feature-name}/`
   - If missing, create using: `python scripts/new-feature.py {feature-name}`
   - Complete all required documents:
     - `README.md` - Functional specification
     - `TECHNICAL.md` - Technical design
     - `scenarios.feature` - BDD scenarios
     - `TESTING.md` - Test plan

2. **Review & Approval**
   - Get user approval before implementation
   - Update spec status to "Zatwierdzony"

3. **Implementation**
   - Only after spec approval
   - Follow technical design
   - Write tests matching BDD scenarios

### Quick Commands

```bash
# Create new feature structure
python scripts/new-feature.py <feature-name>

# Check specification coverage
python scripts/check-spec-coverage.py

# List existing features
python scripts/new-feature.py --list
```

### Response When No Spec Exists

```
Nie znalazłem specyfikacji dla tej funkcjonalności.
Zanim zacznę implementację, muszę utworzyć dokumentację.
Czy chcesz, żebym rozpoczął od utworzenia specyfikacji?
```

See `CLAUDE_CODE_INSTRUCTIONS.md` for complete protocol details.

---

## Project: small-gastro

A web application for managing a small food business (kebab, burger, etc.) with:
- **Frontend**: React + TypeScript + Vite + TailwindCSS
- **Backend**: Python FastAPI + SQLAlchemy
- **Database**: PostgreSQL
- **Language**: Polish (all UI labels)
- **Currency**: PLN (Polish Zloty)

## Features

1. **Menu Management** - Products with prices, linked ingredients (by weight or count)
2. **Financial Tracking** - Expenses (hierarchical categories) and Revenue with payment methods
3. **Daily Operations** - Open/close day with inventory snapshots, sales recording
4. **Dashboard** - Income, expenses, profit, discrepancy warnings

## Commands

```bash
# Development with Docker (PostgreSQL only)
docker compose -f docker-compose.dev.yml up -d

# Backend
cd backend
pip install -r requirements.txt
alembic upgrade head                    # Apply migrations
uvicorn app.main:app --reload           # Start dev server (port 8000)

# Frontend
cd frontend
npm install
npm run dev                             # Start dev server (port 5173)

# Production (Full Docker Stack)
docker compose up -d                    # Start all services
docker compose logs -f                  # Follow logs
```

## Worktree Workflow (MANDATORY)

**IMPORTANT: When asked to work on any new feature, fix, or refactor, ALWAYS use git worktrees. Do NOT just create a branch in the main repo.**

### Steps:
1. Create worktree with new branch:
   ```bash
   git worktree add -b <branch-name> ../small-gastro-worktrees/<branch-name> main
   ```
2. Navigate to the worktree:
   ```bash
   cd ../small-gastro-worktrees/<branch-name>
   ```
3. Work there independently (all commits stay on that branch)

### Branch naming convention:
- `feature-<name>` - New features
- `fix-<name>` - Bug fixes
- `refactor-<name>` - Code refactoring

### Why worktrees:
- Allows parallel work on multiple features without stashing
- Main repo stays clean on main branch
- Each feature has its own isolated working directory

## Project Structure

```
small-gastro/
├── docs/
│   ├── specs/               # Feature specifications (REQUIRED before coding)
│   │   └── {feature-name}/
│   │       ├── README.md    # Functional specification
│   │       ├── TECHNICAL.md # Technical design
│   │       ├── TESTING.md   # Test plan
│   │       └── scenarios.feature  # BDD scenarios
│   ├── adrs/                # Architecture Decision Records
│   └── templates/           # Specification templates
├── scripts/
│   ├── new-feature.py       # Create new feature scaffold
│   └── check-spec-coverage.py  # Verify spec completeness
├── tests/
│   └── features/            # BDD feature files (Gherkin)
├── backend/
│   ├── app/
│   │   ├── api/v1/          # FastAPI routers (endpoints)
│   │   ├── core/            # Database connection, config
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   └── services/        # Business logic
│   ├── alembic/             # Database migrations
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/             # API client functions
│   │   ├── components/      # React components
│   │   ├── context/         # React context (DailyRecordContext)
│   │   ├── pages/           # Page components
│   │   ├── types/           # TypeScript types
│   │   └── utils/           # Utility functions (formatters)
│   └── package.json
├── docker-compose.yml       # Production config
└── docker-compose.dev.yml   # Development config (DB only)
```

## Key Patterns

### Backend
- **Services return data directly** - No complex Result types, keep it simple
- **SQLAlchemy 2.0** - Use declarative models with relationships
- **Pydantic schemas** - Separate Create/Update/Response schemas
- **Polish error messages** - All API errors in Polish

### Frontend
- **React Query** - For data fetching and caching
- **TailwindCSS** - Utility-first styling with custom `.btn`, `.input`, `.card` classes
- **Context API** - For shared state (DailyRecordContext for current day status)
- **Polish UI** - All labels, buttons, messages in Polish

## Database Models

| Model | Description |
|-------|-------------|
| `Ingredient` | Skladniki with unit_type (weight/count) |
| `Product` | Produkty with price |
| `ProductIngredient` | Junction table linking products to ingredients |
| `ExpenseCategory` | Hierarchical expense categories (max 3 levels) |
| `DailyRecord` | Daily open/close records |
| `InventorySnapshot` | Ingredient quantities at day open/close |
| `SalesItem` | Sales transactions for products |
| `Transaction` | Financial transactions (expense/revenue) |

## API Endpoints

- `GET/POST /api/v1/ingredients` - Ingredient CRUD
- `GET/POST /api/v1/products` - Product CRUD with ingredients
- `GET/POST /api/v1/categories` - Expense category hierarchy
- `GET/POST /api/v1/daily-records` - Open/close day operations
- `GET/POST /api/v1/sales` - Sales recording
- `GET/POST /api/v1/transactions` - Financial transactions
- `GET /api/v1/dashboard/*` - Dashboard data and warnings

## Environment Variables

### Backend (.env)
```
DATABASE_URL=postgresql://user:password@localhost:5432/small_gastro
CORS_ORIGINS=http://localhost:5173
```

### Frontend (.env)
```
VITE_API_BASE_URL=http://localhost:8000/api/v1
```
