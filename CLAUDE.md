# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Sistema de Subvenciones v1.0** - Professional system for capturing and managing Spanish government grants from BOE (Official State Gazette) and BDNS (National Database of Grants) with N8n integration for AI analysis.

This is a full-stack application with FastAPI backend and React frontend, designed to automate grant discovery, filtering, and export for nonprofit organizations.

## Development Commands

### Backend (FastAPI)

```bash
# Setup
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Database setup
docker-compose up -d db                    # Start PostgreSQL
alembic upgrade head                       # Run migrations
alembic revision --autogenerate -m "msg"   # Create new migration

# Run server
uvicorn app.main:app --reload              # Development server on port 8000

# Testing
pytest                                     # Run all tests
pytest tests/test_api/                     # Run specific test directory
pytest -v                                  # Verbose output
pytest --cov=app                           # With coverage

# Code quality
black app/                                 # Format code
ruff check app/                            # Lint
mypy app/                                  # Type checking
```

### Frontend (React + Vite)

```bash
# Setup
cd frontend
npm install

# Run
npm run dev                                # Development server on port 3000
npm run build                              # Production build
npm run preview                            # Preview production build
```

### Docker

```bash
# From project root
docker-compose up -d db                    # Start PostgreSQL only
docker-compose down                        # Stop all services
docker-compose logs -f db                  # View database logs
```

## Architecture

### Backend Structure

The backend follows a layered architecture with clear separation of concerns:

**`app/models/`** - SQLAlchemy ORM models
- `grant.py` - Core Grant model with 43+ fields supporting both BOE and BDNS sources
  - Stores grant metadata, dates, budget, beneficiary types, sectors, regions
  - Includes N8n analysis results (priority, strategic_value)
  - Supports nonprofit classification with confidence scores

**`app/api/v1/`** - FastAPI route handlers
- `grants.py` - CRUD operations for grants (list with filters, get by ID, delete)
- `capture.py` - Endpoints to trigger BDNS capture with date range selection
- `capture_boe.py` - Endpoints to trigger BOE capture with PDF processing
- `webhook.py` - N8n integration endpoints (send grants, receive callbacks from Google Sheets)
- `filters.py` - **NEW** - Expose filter keywords for transparency (BDNS/BOE)
- `analytics.py` - Dashboard metrics and statistics
- `endpoints/exports.py` - Excel export functionality

**`app/services/`** - Business logic layer
- `bdns_service.py` - Wraps BDNS API client, filters by nonprofit keywords, stores to DB
- `boe_service.py` - Wraps BOE API client, processes PDF content
- `pdf_processor.py` - Extracts text and markdown from PDF documents
- `n8n_service.py` - Basic webhook sender
- `n8n_service_enhanced.py` - Advanced N8n integration with queue management

**`app/shared/`** - Reusable modules (migrated from v0 project)
- `bdns_api.py` - BDNS API client with search and detail fetching
- `bdns_models.py` - Pydantic models for BDNS responses
- `boe_api.py` - BOE API client
- `filters.py` - Nonprofit and sector relevance filters
- `n8n_webhook.py` - Enhanced N8n webhook with retry logic

**`app/database.py`** - SQLAlchemy session management
**`app/config.py`** - Pydantic Settings for environment configuration

### Frontend Structure

**`src/pages/`** - Page components
- `GrantsPage.tsx` - Main grants table and capture controls

**`src/components/`** - React components
- `GrantsTable.tsx` - Data table with sorting, filtering, selection
- `GrantDetailDrawer.tsx` - Slide-out panel with full grant details
- `AdvancedFilterPanel.tsx` - Budget range, date range, region/sector filters
- `CaptureConfigDialog.tsx` - Configure BDNS/BOE capture parameters
- `Analytics.tsx` - Dashboard with charts and statistics
- `ui/` - shadcn/ui components (Button, Dialog, Select, etc.)

**`src/types.ts`** - TypeScript interfaces matching backend models

### Data Flow

1. **Capture**: BDNS/BOE APIs → `bdns_service.py`/`boe_service.py` → Grant model → PostgreSQL
2. **Filtering**: Services apply nonprofit keywords and minimum budget thresholds
3. **Frontend**: React → FastAPI → PostgreSQL (with pagination, filters)
4. **N8n Integration**: Selected grants → N8n webhook → AI analysis → Update grant priority
5. **Export**: Grants → Excel with calculated deadlines → Download

## Key Concepts

### Grant Sources

The system supports two data sources, distinguished by the `source` field:
- **"BDNS"** - Grants from National Database (most complete metadata)
- **"BOE"** - Grants from Official Gazette (requires PDF processing)

### Nonprofit Filtering

The `bdns_service.py` automatically filters grants using keyword matching:
- Checks beneficiary types, sectors, and title for nonprofit indicators
- Keywords: "fundación", "asociación", "ONG", "entidad sin ánimo", etc.
- Sets `is_nonprofit=True` and `nonprofit_confidence` (0.0-1.0)

### Date Handling and Deadlines

**Critical for Excel export feature:**
- `application_start_date` and `application_end_date` are stored as DateTime
- Excel export must calculate business days remaining until deadline
- Handle three cases:
  1. Specific end date → calculate working days (exclude weekends, Spanish holidays)
  2. "Hasta agotar presupuesto" in title → return "N/A - Hasta agotar"
  3. No deadline info → return "Revisar Bases"

### Database Configuration

PostgreSQL runs on **port 5433** (not default 5432) to avoid conflicts:
- Connection string: `postgresql://postgres:postgres@localhost:5433/subvenciones`
- Docker container name: `subvenciones-db`
- Alembic migrations are in `backend/app/migrations/`

### N8n Integration

Two approaches available:
1. **Basic** (`n8n_service.py`) - Simple POST to webhook URL
2. **Enhanced** (`n8n_service_enhanced.py`) - Queue, retry logic, delivery tracking

N8n webhook receives grants and returns AI analysis (priority, strategic_value).

## Important Patterns

### Service Layer Pattern

Services are the single source of truth for business logic:
- API endpoints call service methods (thin controllers)
- Services handle database transactions
- Services integrate with external APIs (BDNS, BOE, N8n)

Example:
```python
# In API endpoint
@router.post("/capture/bdns")
def capture_bdns(params: CaptureRequest, db: Session = Depends(get_db)):
    service = BDNSService(db)
    result = service.capture_recent_grants(days_back=params.days_back)
    return result
```

### Filter Architecture

The backend supports rich filtering on grants:
- **Query params**: `skip`, `limit`, `source`, `is_nonprofit`, `min_budget`
- **Date ranges**: `start_date_from`, `start_date_to`, `end_date_from`, `end_date_to`
- **Search**: `search` (full-text across title, department)
- **Arrays**: `sectors`, `regions`, `beneficiary_types` (JSON field filtering)

Filters are applied in `app/api/v1/grants.py` via SQLAlchemy query building.

### Frontend API Communication

Vite proxy configuration handles API calls:
- Frontend runs on `http://localhost:3000`
- Backend runs on `http://localhost:8000`
- `/api/*` requests are proxied to backend (see `vite.config.ts`)
- Use relative URLs: `fetch('/api/v1/grants')` in frontend code

## Testing Strategy

Tests are structured in `backend/tests/`:
- `test_api/` - Endpoint integration tests
- `test_services/` - Service unit tests

Use FastAPI TestClient for API testing:
```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
response = client.get("/api/v1/grants")
```

## Common Gotchas

1. **Port conflicts**: PostgreSQL runs on 5433, not 5432
2. **Database URL**: Alembic uses port 5432 in `alembic.ini` - must match docker-compose port mapping
3. **CORS**: Frontend origins must be in `CORS_ORIGINS` env var (comma-separated)
4. **PDF Processing**: Requires `pdfplumber` and `PyPDF2` - can be memory intensive
5. **BDNS Date Format**: API expects `dd/MM/yyyy` format, not ISO format
6. **Nonprofit Keywords**: Defined in `shared/filters.py` - case-insensitive matching
7. **Excel Export**: Not yet implemented - this is the highest priority missing feature

## Environment Variables

Key variables (see `backend/.env.example`):
- `DATABASE_URL` - PostgreSQL connection string
- `N8N_WEBHOOK_URL` - N8n webhook endpoint for grant analysis
- `BDNS_MAX_RESULTS` - Limit for BDNS API queries (default: 50)
- `MIN_RELEVANCE_SCORE` - Threshold for grant relevance (0.0-1.0)
- `CORS_ORIGINS` - Allowed frontend origins (comma-separated)
- `LOG_LEVEL` - Logging verbosity (DEBUG, INFO, WARNING, ERROR)

## Next Priority Features

Based on STATUS.md, the highest priority unimplemented features are:

1. **Excel Export Service** - Generate professional Excel files with calculated deadlines
2. **Advanced Filtering UI** - Budget ranges, date ranges, sector/region multi-select
3. **BOE Capture Integration** - Reuse `shared/boe_api.py` for BOE grant capture
4. **Grant Detail View** - Modal/drawer with complete metadata and documents

When implementing these, follow the existing service layer pattern and maintain consistency with the current architecture.
