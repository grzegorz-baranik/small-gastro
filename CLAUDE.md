# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## TL;DR - MANDATORY RULES (Read This First!)

| Rule | Requirement |
|------|-------------|
| **Running the app** | ALWAYS use `docker compose up -d` - NEVER use `uvicorn` or `npm run dev` directly |
| **Feature branches** | ALWAYS bump Docker ports before running (see Port Allocation table) |
| **Before starting Docker** | ALWAYS run `docker ps` first to check for port conflicts |
| **Before PR/Merge** | ALWAYS revert port changes back to defaults |
| **New features** | ALWAYS use git worktrees, not branches in main repo |
| **Clarifications** | ALWAYS use `/interview` skill - never assume |

---

## CRITICAL: Interview-First Workflow

**ALL agents MUST use the `/interview` skill (AskUserQuestion tool) for ANY clarification or decision point.**

### The Interview Skill is MANDATORY When:

1. **Requirements are vague** - User request lacks specific details
2. **Multiple approaches exist** - More than one valid implementation path
3. **Technical decisions needed** - Architecture, library, or pattern choices
4. **Functional ambiguity** - Business logic or user flow unclear
5. **A/B decision points** - Trade-offs between options need user input
6. **Before specification creation** - Always clarify before writing specs
7. **Before plan mode** - Always clarify before planning implementation

### Interview Protocol (ALL Agents)

Every clarification MUST use `AskUserQuestion` tool with:
- 2-4 clear, distinct options (radio buttons or checkboxes)
- Brief descriptions explaining each option
- User can always select "Other" for custom input

**NEVER assume. ALWAYS ask using structured questions.**

See `.claude/skills/interview.md` for question templates per agent type.

---

## Specification-Driven Workflow

**BEFORE writing ANY implementation code, you MUST follow the documentation-first approach.**

### Workflow Phases

1. **Interview Phase** (MANDATORY when requirements unclear)
   - Run `/interview` skill to clarify requirements
   - Uses structured questions with radio/multi-choice options
   - Covers: functional, technical, and A/B decisions
   - Ensures all ambiguities are resolved before planning

2. **Specification Phase** (REQUIRED before coding)
   - Check if spec exists: `docs/specs/{feature-name}/`
   - If missing, create using: `python scripts/new-feature.py {feature-name}`
   - Complete all required documents:
     - `README.md` - Functional specification
     - `TECHNICAL.md` - Technical design
     - `scenarios.feature` - BDD scenarios
     - `TESTING.md` - Test plan

3. **Review & Approval**
   - Get user approval before implementation
   - Update spec status to "Approved"

4. **Implementation**
   - Only after spec approval
   - Follow technical design
   - Write tests matching BDD scenarios

### Quick Commands

```bash
# Requirements interview (before planning)
/interview

# Create new feature structure
python scripts/new-feature.py <feature-name>

# Check specification coverage
python scripts/check-spec-coverage.py

# List existing features
python scripts/new-feature.py --list

# Create git worktree for new work
new-worktree <name> [type] [base]   # PowerShell or Bash alias
```

### Response When No Spec Exists

```
I couldn't find a specification for this feature.
Before I start implementation, I need to create documentation.
Would you like me to start by creating a specification?
```

See `CLAUDE_CODE_INSTRUCTIONS.md` for complete protocol details.

---

## Project: small-gastro

A web application for managing a small food business (kebab, burger, etc.) with:
- **Frontend**: React + TypeScript + Vite + TailwindCSS
- **Backend**: Python FastAPI + SQLAlchemy
- **Database**: PostgreSQL
- **Currency**: PLN (Polish Zloty)

### Language Policy

| Scope | Language |
|-------|----------|
| UI labels, buttons, messages (frontend) | Polish |
| API error messages (backend i18n) | Polish |
| Code (variables, functions, classes) | English |
| Comments and documentation | English |
| BDD scenarios (.feature files) | English |
| Git commits | English |
| Specification documents | English |

## Features

1. **Menu Management** - Products with prices, linked ingredients (by weight or count)
2. **Financial Tracking** - Expenses (hierarchical categories) and Revenue with payment methods
3. **Daily Operations** - Open/close day with inventory snapshots, sales recording
4. **Dashboard** - Income, expenses, profit, discrepancy warnings

## CRITICAL: Docker-First Execution (MANDATORY)

**NEVER run the application using local `uvicorn` or `npm run dev` directly on the host system!**

**ALL execution MUST go through Docker Compose. This is NON-NEGOTIABLE.**

### Why Docker-Only:
- Ensures consistent environment across all branches
- Enables port isolation for parallel feature development
- Prevents "works on my machine" issues
- Avoids polluting the host system with dependencies

### Running the Solution

```bash
# ALWAYS use Docker Compose - NEVER run uvicorn/npm directly!

# Step 1: Check for running containers from other branches
docker ps

# Step 2: If on a feature branch, bump ports FIRST (see Port Allocation below)

# Step 3: Start the full stack
docker compose up -d                    # Start all services (backend + frontend + db)
docker compose logs -f                  # Follow logs

# Step 4: Run migrations (inside container)
docker compose exec backend alembic upgrade head
```

### FORBIDDEN Commands (Never Use These)

```bash
# ❌ WRONG - Never run directly on host:
uvicorn app.main:app --reload           # FORBIDDEN
npm run dev                             # FORBIDDEN
python -m uvicorn ...                   # FORBIDDEN

# ✅ CORRECT - Always use Docker:
docker compose up -d                    # CORRECT
docker compose exec backend alembic upgrade head  # CORRECT
```

### Development Workflow

```bash
# Start full stack
docker compose up -d

# View logs
docker compose logs -f
docker compose logs -f backend          # Backend only
docker compose logs -f frontend         # Frontend only

# Restart after code changes (if not using hot-reload)
docker compose restart backend
docker compose restart frontend

# Stop everything
docker compose down

# Rebuild after dependency changes
docker compose build --no-cache
docker compose up -d
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

### Branch Workflow

Before creating a PR:
1. Run `git fetch origin && git rebase origin/main`
2. Resolve any conflicts
3. Run tests
4. Push with `git push --force-with-lease`

Never merge without rebasing first.

## CRITICAL: Docker Port Management for Feature Branches (MANDATORY)

**When working on a feature branch, Docker ports MUST be isolated to avoid conflicts. This is MANDATORY - failure to follow this will cause port conflicts!**

### Pre-Flight Checklist (BEFORE `docker compose up`)

**ALWAYS perform these steps before starting Docker on ANY feature branch:**

1. **Check running containers:**
   ```bash
   docker ps
   ```

2. **If containers are running from other branches:**
   - Either stop them: `docker compose down` (in that branch's directory)
   - Or bump YOUR ports to avoid conflicts

3. **Bump port numbers in docker-compose.yml:**
   - Edit `docker-compose.yml` (or `docker-compose.dev.yml`)
   - Increment ALL exposed ports by the same offset
   - Update corresponding `.env` files if needed

### Port Allocation Strategy (MANDATORY)

| Branch | PostgreSQL | Backend | Frontend | VITE_API_BASE_URL |
|--------|------------|---------|----------|-------------------|
| main/master | 5432 | 8000 | 5173 | http://localhost:8000/api/v1 |
| feature-1 | 5433 | 8001 | 5174 | http://localhost:8001/api/v1 |
| feature-2 | 5434 | 8002 | 5175 | http://localhost:8002/api/v1 |
| feature-3 | 5435 | 8003 | 5176 | http://localhost:8003/api/v1 |
| ... | +1 | +1 | +1 | ... |

### Files to Update When Bumping Ports

```bash
# 1. docker-compose.yml - Update these port mappings:
#    - PostgreSQL: "5432:5432" -> "5433:5432"
#    - Backend: "8000:8000" -> "8001:8000"
#    - Frontend: "5173:5173" -> "5174:5173"

# 2. frontend/.env (or docker-compose environment):
#    VITE_API_BASE_URL=http://localhost:8001/api/v1

# 3. backend/.env (if DATABASE_URL uses localhost):
#    DATABASE_URL=postgresql://user:pass@localhost:5433/small_gastro
```

### Before PR/Merge (CRITICAL)

**IMPORTANT: Revert ALL port changes before creating a PR!**

1. Reset docker-compose port numbers to defaults (5432, 8000, 5173)
2. Reset VITE_API_BASE_URL to http://localhost:8000/api/v1
3. Only keep relevant Docker changes (new services, env vars, etc.)
4. Never merge branch-specific port numbers into main/master

```bash
# Review port changes before PR
git diff docker-compose*.yml
git diff frontend/.env

# Revert ONLY port-related changes, keep other modifications
```

### Quick Reference: Port Bump Commands

```bash
# Check what ports are in use
docker ps --format "table {{.Names}}\t{{.Ports}}"
netstat -an | findstr "LISTENING" | findstr "5432 8000 5173"

# Identify next available port offset
# If feature-1 uses +1, use +2 for your feature
```

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
- **i18n for API errors** - See Language Policy above

### CRITICAL: Enum Columns in SQLAlchemy

**ALWAYS use `EnumColumn()` helper for enum columns, NEVER use raw `Enum()`!**

```python
# CORRECT - Always use EnumColumn from database.py
from app.core.database import Base, EnumColumn

class MyModel(Base):
    status = Column(EnumColumn(MyStatusEnum), nullable=False)

# WRONG - Never use raw Enum!
from sqlalchemy import Enum as SQLEnum
status = Column(SQLEnum(MyStatusEnum), nullable=False)  # DON'T DO THIS!
```

**Why:** PostgreSQL enums store lowercase values ('open', 'closed'), but SQLAlchemy's default `Enum()` sends uppercase names ('OPEN', 'CLOSED'). This causes cryptic errors like:
```
invalid input value for enum: "OPEN"
```

The `EnumColumn()` helper in `app/core/database.py` handles this automatically.

### FastAPI Route Ordering

**Static routes MUST come BEFORE path parameter routes!**

```python
# CORRECT order:
@router.get("/status/open")     # Static route first
@router.get("/{record_id}")     # Path param route after

# WRONG order - causes 422 errors:
@router.get("/{record_id}")     # This catches "/status/open" as record_id="status"
@router.get("/status/open")     # Never reached!
```

### Frontend
- **React Query** - For data fetching and caching
- **TailwindCSS** - Utility-first styling with custom `.btn`, `.input`, `.card` classes
- **Context API** - For shared state (DailyRecordContext for current day status)
- **Polish UI** - All labels, buttons, messages in Polish

## Database Models

| Model | Description |
|-------|-------------|
| `Ingredient` | Ingredients with unit_type (weight/count) |
| `Product` | Products with price |
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
