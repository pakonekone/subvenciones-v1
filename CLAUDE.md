# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Sistema de Subvenciones v1.0** - Professional full-stack system for capturing and managing Spanish government grants from BOE (Official State Gazette) and BDNS (National Database of Grants) with N8n integration for AI analysis and Google Sheets export tracking.

This is a production-ready application with FastAPI backend and React frontend, designed to automate grant discovery, intelligent filtering, AI analysis, and bidirectional export tracking for nonprofit organizations.

## Documentation

- **[ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md)** - Complete system architecture with Mermaid diagrams showing all flows
- **[README.md](README.md)** - User-facing documentation and quick start guide
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment guide for Railway
- **[TODO.md](TODO.md)** - Current feature roadmap and priorities

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

See [ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md) for complete visual diagrams of all system flows.

### Backend Structure

The backend follows a layered architecture with clear separation of concerns:

**`app/models/`** - SQLAlchemy ORM models
- `grant.py` - Core Grant model with 43+ fields supporting both BOE and BDNS sources
  - Stores grant metadata, dates, budget, beneficiary types, sectors, regions
  - Includes N8n analysis results (priority, strategic_value)
  - Supports nonprofit classification with confidence scores
  - **Google Sheets tracking**: `google_sheets_exported`, `google_sheets_exported_at`, `google_sheets_row_id`, `google_sheets_url`

**`app/api/v1/`** - FastAPI route handlers
- `grants.py` - CRUD operations for grants (list with filters, get by ID, delete, bulk operations)
- `capture.py` - BDNS capture with **date range selection** (fecha_desde/fecha_hasta)
- `capture_boe.py` - BOE capture with PDF processing
- `webhook.py` - **Bidirectional N8n integration**:
  - Send grants to N8n for AI analysis
  - Receive analysis callbacks (priority, strategic_value)
  - Receive Google Sheets export callbacks (tracking webhook)
- `filters.py` - **Filter transparency endpoints** (expose BDNS/BOE keywords)
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
- `boe_api.py` - BOE API client with PDF processing
- `filters.py` - **11 BDNS nonprofit keywords + 44 BOE grant keywords**
- `n8n_webhook.py` - Enhanced N8n webhook with retry logic

**`app/database.py`** - SQLAlchemy session management
**`app/config.py`** - Pydantic Settings for environment configuration

### Frontend Structure

**`src/pages/`** - Page components
- `GrantsPage.tsx` - Main grants table and capture controls

**`src/components/`** - React components
- `GrantsTable.tsx` - Data table with sorting, filtering, selection
  - **New "Exportado" column** with visual indicators (✅/⏳/➖)
  - **Publication date column** for timeline visibility
- `GrantDetailDrawer.tsx` - Slide-out panel with full grant details
- `AdvancedFilterPanel.tsx` - Budget range, date range, region/sector filters
- `CaptureConfigDialog.tsx` - Configure BDNS/BOE capture with **filter preview**
- `FilterKeywordsManager.tsx` - **NEW** - Modal with 3 tabs to view/edit filter keywords
- `Analytics.tsx` - Dashboard with charts and statistics
- `ui/` - shadcn/ui components (Button, Dialog, Select, etc.)

**`src/types.ts`** - TypeScript interfaces matching backend models

### Data Flow

1. **Capture**: BDNS/BOE APIs → Services (with transparent filtering) → Grant model → PostgreSQL
2. **Filtering**: Services apply nonprofit keywords (visible via `/api/v1/filters/*`)
3. **Frontend**: React → FastAPI → PostgreSQL (with pagination, rich filters)
4. **N8n Analysis**: Selected grants → N8n webhook → AI analysis → Callback updates grant
5. **Google Sheets Export**: N8n → Sheets → Callback webhook → Update grant tracking fields
6. **Export**: Grants → Excel with calculated deadlines → Download

## Key Concepts

### Grant Sources

The system supports two data sources, distinguished by the `source` field:
- **"BDNS"** - Grants from National Database (most complete metadata)
- **"BOE"** - Grants from Official Gazette (requires PDF processing)

### Filter Transparency System (2025-10-19/20)

**Critical architectural decision**: All filtering logic is now exposed through transparent endpoints.

**Backend Endpoints** (`app/api/v1/filters.py`):
- `GET /api/v1/filters/bdns` - Returns 11 nonprofit keywords used in BDNS filtering
- `GET /api/v1/filters/boe` - Returns 44 grant keywords + nonprofit keywords for BOE
- `GET /api/v1/filters/summary` - Returns comprehensive filter summary with counts

**Frontend Components**:
- `FilterKeywordsManager.tsx` - Modal with 3 tabs (BDNS Nonprofit, BOE Grants, BOE Nonprofit)
- `CaptureConfigDialog.tsx` - Shows filter preview before capture

**Keywords are defined in** `app/shared/filters.py`:
- BDNS: 11 nonprofit keywords (fundación, asociación, ONG, etc.)
- BOE: 44 grant keywords (subvención, ayuda, beca, etc.) + nonprofit keywords

### Relevance Score Handling

**IMPORTANT**: As of 2025-10-20, `relevance_score` is **informational only** and does NOT exclude grants.

Previously, BOE grants with `relevance_score < 0.3` were filtered out. Now:
- All identified grants are captured regardless of score
- Score is displayed for user decision-making
- Users can filter by score in the UI if desired

### Date Range Selection for BDNS

Replaced "días hacia atrás" parameter with precise date range selection:

**Backend** (`app/services/bdns_service.py`):
- Method: `capture_by_date_range(date_from: str, date_to: str, max_results: int)`
- Accepts ISO format (YYYY-MM-DD), converts to BDNS format (dd/MM/yyyy)
- Limits: min 1 result, max 100 results per capture

**Frontend** (`CaptureConfigDialog.tsx`):
- Date pickers for precise range selection
- Default: today's date for both from/to
- User can select historical ranges

### Google Sheets Export Tracking (Bidirectional Webhooks)

**Database Schema** (`grant.py` lines 91-95):
```python
google_sheets_exported = Column(Boolean, default=False, index=True)
google_sheets_exported_at = Column(DateTime, nullable=True)
google_sheets_row_id = Column(String, nullable=True)
google_sheets_url = Column(Text, nullable=True)
```

**Backend Endpoint** (`webhook.py` lines 186-260):
- `POST /api/v1/webhook/callback/sheets` - Receives callbacks from N8n
- Payload: `{grant_id, status, sheets_url, row_id, error_message}`
- Updates grant record with export status and timestamp

**Frontend** (`GrantsTable.tsx`):
- New "Exportado" column with visual indicators:
  - ✅ Green Google Sheets icon + clickable link (successfully exported)
  - ⏳ Amber clock icon (sent to N8n, processing)
  - ➖ Gray dash (not sent yet)

**N8n Configuration** (see TODO.md):
- Requires adding HTTP Request node AFTER Google Sheets node
- Calls callback endpoint to confirm successful export
- Separate from "Respond to Webhook" (two different HTTP communications)

### Nonprofit Filtering

Services automatically filter grants using keyword matching:
- Checks beneficiary types, sectors, and title for nonprofit indicators
- Keywords defined in `shared/filters.py` (case-insensitive matching)
- Sets `is_nonprofit=True` and `nonprofit_confidence` (0.0-1.0)
- Users can see active keywords before capture

### Date Handling and Deadlines

**Critical for Excel export feature:**
- `application_start_date` and `application_end_date` are stored as DateTime
- Excel export calculates business days remaining until deadline
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

**Two-way webhook system**:

1. **Outbound** - Send grants for analysis (`n8n_service.py`):
   - Basic: Simple POST to webhook URL
   - Enhanced: Queue, retry logic, delivery tracking

2. **Inbound Callbacks** - Receive results:
   - **Analysis callback**: N8n returns AI analysis (priority, strategic_value)
   - **Sheets callback**: N8n confirms successful Google Sheets export with URL and row ID

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
    result = service.capture_by_date_range(
        date_from=params.fecha_desde,
        date_to=params.fecha_hasta,
        max_results=params.max_results
    )
    return result
```

### Filter Architecture

The backend supports rich filtering on grants:
- **Query params**: `skip`, `limit`, `source`, `is_nonprofit`, `min_budget`
- **Date ranges**: `start_date_from`, `start_date_to`, `end_date_from`, `end_date_to`
- **Search**: `search` (full-text across title, department)
- **Arrays**: `sectors`, `regions`, `beneficiary_types` (JSON field filtering)
- **Export status**: `google_sheets_exported` (boolean filter)

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
5. **BDNS Date Format**: API expects `dd/MM/yyyy` format, backend converts from ISO
6. **Nonprofit Keywords**: Defined in `shared/filters.py` - case-insensitive matching
7. **Relevance Score**: Now informational only, does NOT filter grants
8. **N8n Callbacks**: Two separate webhooks (analysis + sheets) - don't confuse with "Respond to Webhook"

## Environment Variables

Key variables (see `backend/.env.example`):
- `DATABASE_URL` - PostgreSQL connection string
- `N8N_WEBHOOK_URL` - N8n webhook endpoint for grant analysis
- `BDNS_MAX_RESULTS` - Limit for BDNS API queries (default: 50)
- `MIN_RELEVANCE_SCORE` - Informational threshold (default: 0.0, no filtering)
- `CORS_ORIGINS` - Allowed frontend origins (comma-separated)
- `LOG_LEVEL` - Logging verbosity (DEBUG, INFO, WARNING, ERROR)

## Current Feature Status (2025-10-20)

### ✅ Fully Implemented

1. **Filter Transparency System**
   - Expose all keywords via API endpoints
   - FilterKeywordsManager UI component
   - Preview filters before capture

2. **Date Range Selection for BDNS**
   - Precise fecha_desde/fecha_hasta selection
   - ISO to BDNS format conversion
   - 1-100 results limit

3. **Google Sheets Export Tracking**
   - Database fields for tracking
   - Bidirectional webhook callbacks
   - Visual indicators in UI (✅/⏳/➖)

4. **Publication Date Column**
   - Sortable column in GrantsTable
   - Timeline visibility

5. **Advanced Filtering**
   - Budget ranges, date ranges, regions, sectors
   - Full-text search
   - Nonprofit classification

6. **N8n Integration**
   - Send grants for AI analysis
   - Receive priority/strategic_value callbacks
   - Queue management (enhanced version)

7. **BOE + BDNS Capture**
   - Automatic PDF processing
   - Nonprofit keyword filtering
   - Relevance scoring (informational)

### 🔄 In Progress (see TODO.md)

1. **Excel Export Enhancement**
   - Professional formatting
   - Calculated deadlines with Spanish holidays

2. **Filter Keyword Editing**
   - UI for modifying keywords
   - Persistence layer

3. **Auto-refresh Polling**
   - Background grant updates
   - Real-time status changes

## Next Priority Features

Based on TODO.md, the highest priority features are:

1. **Enhanced Excel Export** - Professional formatting with calculated business days
2. **Keyword Editor** - Allow users to modify filter keywords via UI
3. **Auto-refresh System** - Polling for grant updates without manual refresh
4. **Advanced Analytics** - Deeper insights into grant patterns and success rates

When implementing these, follow the existing service layer pattern and maintain consistency with the current architecture. See ARCHITECTURE_DIAGRAM.md for visual representation of all flows.

## Migration Notes

This project evolved from `subvenciones-v0`. Key differences:
- v0: Script-based capture → v1: Full-stack web application
- v0: Manual Excel → v1: Automated export + Google Sheets tracking
- v0: Hidden filters → v1: Transparent filter system
- v0: One-way N8n → v1: Bidirectional webhooks

The `app/shared/` directory contains battle-tested modules from v0 (BDNS API, BOE API, filters) that were proven in production.
