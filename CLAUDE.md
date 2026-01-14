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
- `grant.py` - Core Grant model with 47+ fields supporting both BOE and BDNS sources
  - Stores grant metadata, dates, budget, beneficiary types, sectors, regions
  - Includes N8n analysis results (priority, strategic_value)
  - Supports nonprofit classification with confidence scores
  - **Google Sheets tracking**: `google_sheets_exported`, `google_sheets_exported_at`, `google_sheets_row_id`, `google_sheets_url`
  - **BDNS Document Processing**: `bdns_documents` (JSON), `bdns_documents_processed`, `bdns_documents_processed_at`, `bdns_documents_content`, `bdns_documents_combined_text`
- `organization_profile.py` - **NEW** Organization profile for eligibility matching
  - Stores organization data: name, CIF, type, sectors, regions, capabilities
  - Used by AI agent to provide personalized eligibility analysis
  - Method `to_n8n_payload()` serializes for AI context

**`app/api/v1/`** - FastAPI route handlers
- `grants.py` - CRUD operations for grants (list with filters, get by ID, delete, bulk operations)
  - `GET /{grant_id}/documents` - Get BDNS document metadata and processing status
  - `POST /{grant_id}/documents/process` - Trigger on-demand PDF text extraction
- `capture.py` - BDNS capture with **date range selection** (fecha_desde/fecha_hasta)
- `capture_boe.py` - BOE capture with PDF processing
- `webhook.py` - **AI Chat Analyst**: Interactive chat for analyzing grants using N8n workflow.
  - Send grants to N8n for AI analysis
  - Receive analysis callbacks (priority, strategic_value)
  - Receive Google Sheets export callbacks (tracking webhook)
- **PLACSP Integration**: Full integration with Public Sector Contracting Platform.
  - Atom feed capture with pagination and deep linking.
  - Robust XML parsing (CODICE/Atom) with `html_url` extraction.
  - Configurable filters with persistence (`filter_profiles.json`).
  - [Technical Documentation](docs/PLACSP/technical_documentation.md)
- `filters.py` - **Filter transparency endpoints** (expose BDNS/BOE keywords)
- `analytics.py` - Dashboard metrics and statistics
- `endpoints/exports.py` - Excel export functionality
- `organization.py` - **NEW** Organization profile CRUD endpoints
  - `GET /api/v1/organization` - Get current user's profile
  - `POST /api/v1/organization` - Create/update profile
  - `GET /api/v1/organization/options` - Get form options (sectors, regions, capabilities)

**`app/services/`** - Business logic layer
- `bdns_service.py` - Wraps BDNS API client, filters by nonprofit keywords, stores to DB
- `bdns_document_service.py` - **NEW** On-demand PDF extraction for BDNS documents
  - Downloads PDFs from BDNS URLs, extracts text using PDFProcessor
  - Stores extracted content in `bdns_documents_content` (per-document) and `bdns_documents_combined_text`
  - Automatically integrates with AI chatbot via `to_n8n_payload()`
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
  - Integrates AgentSidebar for persistent AI chat
  - Checks for organization profile on mount
- `GrantDetailPage.tsx` - Dedicated grant detail page with URL routing (`/grants/:id`)
  - Full grant information with modular components
  - Includes BDNS document list with on-demand processing
  - AgentSidebar integration for AI chat
- `OrganizationPage.tsx` - Organization profile form
  - Complete form with sectors, regions, capabilities checkboxes
  - Loads predefined options from backend
  - Auto-saves to database

**`src/components/`** - React components
- `GrantsTable.tsx` - Data table with sorting, filtering, selection
  - **New "Exportado" column** with visual indicators (✅/⏳/➖)
  - **Publication date column** for timeline visibility
- `GrantDetailDrawer.tsx` - Slide-out panel with full grant details (includes DocumentsList)
- `grant/` - Modular grant components:
  - `GrantHeader.tsx`, `GrantInfoGrid.tsx`, `GrantTimeline.tsx`, `GrantLinks.tsx`
  - `DocumentsList.tsx` - **NEW** BDNS document list with download links and processing button
- `AdvancedFilterPanel.tsx` - Budget range, date range, region/sector filters
- `CaptureConfigDialog.tsx` - Configure BDNS/BOE capture with **filter preview**
- `FilterKeywordsManager.tsx` - Modal with 3 tabs to view/edit filter keywords
- `Analytics.tsx` - Dashboard with charts and statistics
- `agent/AgentSidebar.tsx` - **NEW** Persistent AI analyst sidebar
  - Opens from right side when grant selected
  - Shows organization profile warning if not configured
  - Contains GrantChat for interactive AI chat
- `GrantChat.tsx` - Chat interface for AI analyst
- `ui/` - shadcn/ui components (Button, Dialog, Select, Checkbox, Textarea, etc.)

**`src/types.ts`** - TypeScript interfaces matching backend models
- `Grant` - Main grant interface with all fields including BDNS documents
- `BDNSDocument`, `BDNSDocumentContent` - BDNS document metadata and extracted content
- `OrganizationProfile`, `ProfileOption`, `ProfileOptions` - Organization profile interfaces

### Data Flow

1. **Capture**: BDNS/BOE APIs → Services (with transparent filtering) → Grant model → PostgreSQL
2. **Filtering**: Services apply nonprofit keywords (visible via `/api/v1/filters/*`)
3. **Frontend**: React → FastAPI → PostgreSQL (with pagination, rich filters)
4. **Document Processing**: User triggers → BDNSDocumentService downloads PDFs → PDFProcessor extracts text → Stored in grant
5. **N8n Analysis**: Selected grants → N8n webhook (includes document content) → AI analysis → Callback updates grant
6. **Google Sheets Export**: N8n → Sheets → Callback webhook → Update grant tracking fields
7. **Export**: Grants → Excel with calculated deadlines → Download

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

### BDNS Document Processing (2026-01-14)

**Purpose**: Extract text content from BDNS PDF attachments (bases reguladoras, anexos) for AI analysis.

**Architecture Decision**: On-demand processing (not during capture) to avoid slow captures and unnecessary processing.

**Database Schema** (`grant.py`):
```python
bdns_documents = Column(JSON)                    # Document metadata captured during BDNS fetch
bdns_documents_processed = Column(Boolean)       # Processing status flag
bdns_documents_processed_at = Column(DateTime)   # When processed
bdns_documents_content = Column(JSON)            # Per-document extraction results
bdns_documents_combined_text = Column(Text)      # All documents combined for AI
```

**Document URL Format**:
```
https://www.infosubvenciones.es/bdnstrans/GE/es/convocatoria/{bdns_code}/document/{doc_id}
```

**Service** (`bdns_document_service.py`):
- `process_grant_documents(grant_id)` - Downloads and processes all PDFs for a grant
- Uses existing `PDFProcessor` for text extraction
- Stores results per-document and combined

**API Endpoints** (`grants.py`):
- `GET /api/v1/grants/{id}/documents` - Get document metadata and processing status
- `POST /api/v1/grants/{id}/documents/process` - Trigger PDF processing

**Frontend** (`DocumentsList.tsx`):
- Shows document list with download links
- Processing status badge (Procesado/Pendiente)
- "Procesar documentos" button triggers extraction
- Success/error feedback

**AI Integration** (`to_n8n_payload()`):
- Extracted text automatically appended to `pdf_content_text` field
- Added under section "CONTENIDO DE DOCUMENTOS ADJUNTOS"
- Limited to 30,000 chars to avoid payload size issues
- No prompt changes needed - agent receives content automatically

### Organization Profile System (2026-01-12)

**Purpose**: Enable personalized eligibility analysis by storing organization data.

**Database Model** (`organization_profile.py`):
```python
class OrganizationProfile(Base):
    __tablename__ = "organization_profiles"
    id = Column(UUID, primary_key=True)
    user_id = Column(String, unique=True, index=True)  # Simple auth via X-User-ID header
    name = Column(String, nullable=False)
    cif = Column(String, nullable=True)
    organization_type = Column(String)  # fundacion, asociacion, ong, cooperativa, empresa
    sectors = Column(JSON)  # ["accion_social", "educacion", "tecnologia", ...]
    regions = Column(JSON)  # ["ES30", "ES51", "nacional", ...]
    annual_budget = Column(Float)
    employee_count = Column(Integer)
    founding_year = Column(Integer)
    capabilities = Column(JSON)  # ["proyectos_europeos", "formacion", ...]
    description = Column(Text)
```

**Predefined Options** (`/api/v1/organization/options`):
- **Organization Types**: Fundacion, Asociacion, ONG, Cooperativa, Empresa/PYME
- **16 Sectors**: Accion Social, Educacion, Medioambiente, Cultura, Salud, Cooperacion, etc.
- **20 Regions**: All Spanish autonomous communities + "Nacional"
- **12 Capabilities**: Proyectos europeos, Atencion menores/mayores, Formacion, etc.

**Authentication**: Simple header-based (`X-User-ID: demo-user`)

### AI Analyst Chat (Enhanced 2026-01-12)

**Interactive Chat System with Organization Context**:
- **Frontend**:
  - `GrantChat` component for chat interface
  - `AgentSidebar` - Persistent sidebar that opens when grant is selected
  - Shows warning if organization profile not configured
- **Backend**: Proxy endpoint `POST /api/v1/grants/{id}/chat`
  - Accepts `user_id` query parameter to fetch organization profile
  - Includes organization data in N8n payload for personalized analysis
- **N8n Integration**:
  - Dedicated webhook: `N8N_CHAT_WEBHOOK_URL`
  - **Enhanced Payload Structure**:
    ```json
    {
      "grant": {
        "id": "uuid",
        "title": "Subvencion para...",
        "budget_amount": 500000,
        "sectors": ["educacion"],
        "regions": ["ES30"],
        "beneficiary_types": ["fundaciones"],
        ...
      },
      "organization": {
        "name": "Fundacion Esperanza Digital",
        "type": "fundacion",
        "sectors": ["accion_social", "educacion"],
        "regions": ["ES30", "ES51"],
        "capabilities": ["proyectos_europeos", "formacion"],
        "annual_budget": 850000,
        ...
      },
      "chat": {
        "message": "Somos elegibles para esta convocatoria?",
        "history": [...]
      }
    }
    ```
  - Response: `{ output: "Markdown text..." }`
- **Flow**: User message → Backend (fetch org profile) → N8n Webhook → AI Agent (with grant + org context) → Response → Frontend UI

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
9. **BDNS Document URLs**: Must use `/GE/es/convocatoria/{bdns_code}/document/{id}` format, NOT `/api/documento/{id}`

## Environment Variables

Key variables (see `backend/.env.example`):
- `DATABASE_URL` - PostgreSQL connection string
- `N8N_WEBHOOK_URL` - N8n webhook endpoint for grant analysis
- `N8N_CHAT_WEBHOOK_URL` - N8n webhook for interactive chat agent
- `BDNS_MAX_RESULTS` - Limit for BDNS API queries (default: 50)
- `MIN_RELEVANCE_SCORE` - Informational threshold (default: 0.0, no filtering)
- `CORS_ORIGINS` - Allowed frontend origins (comma-separated)
- `LOG_LEVEL` - Logging verbosity (DEBUG, INFO, WARNING, ERROR)

## Current Feature Status (2026-01-14)

### ✅ Fully Implemented

1. **BDNS Document Processing (2026-01-14)**
   - On-demand PDF extraction from BDNS attachments
   - DocumentsList UI component with processing status
   - Automatic integration with AI chatbot
   - Displayed in both GrantDetailDrawer and GrantDetailPage

2. **Filter Transparency System**
   - Expose all keywords via API endpoints
   - FilterKeywordsManager UI component
   - Preview filters before capture

3. **Date Range Selection for BDNS**
   - Precise fecha_desde/fecha_hasta selection
   - ISO to BDNS format conversion
   - 1-100 results limit

4. **Google Sheets Export Tracking**
   - Database fields for tracking
   - Bidirectional webhook callbacks
   - Visual indicators in UI (✅/⏳/➖)

5. **Publication Date Column**
   - Sortable column in GrantsTable
   - Timeline visibility

6. **Advanced Filtering**
   - Budget ranges, date ranges, regions, sectors
   - Full-text search
   - Nonprofit classification

7. **N8n Integration**
   - Send grants for AI analysis
   - Receive priority/strategic_value callbacks
   - Queue management (enhanced version)

8. **BOE + BDNS Capture**
   - Automatic PDF processing
   - Nonprofit keyword filtering
   - Relevance scoring (informational)

9. **AI Analyst Chat with Organization Context (2026-01-12)**
   - Interactive chat with AI agent about specific grants
   - **Organization profile integration** - Agent knows user's organization
   - **Persistent AgentSidebar** - Opens automatically when grant selected
   - Context-aware eligibility analysis (grant + organization matching)
   - Markdown support for rich text responses
   - Warning shown if organization profile not configured

10. **Organization Profile System (2026-01-12)**
    - Database model with sectors, regions, capabilities
    - CRUD API endpoints with predefined options
    - Form UI with checkboxes for multi-select fields
    - Integrated with AI chat for personalized analysis

### 🔄 In Progress (see TODO.md)

1. **N8n Agent Prompt Engineering**
   - Optimize prompt for eligibility analysis
   - Add match score calculation logic
   - Implement document generation capabilities

2. **Eligibility Match Score Visualization**
   - Calculate match percentage in N8n
   - Display score in grants table
   - Color-coded compatibility indicator

## N8n Chat Agent Configuration

### Webhook Setup

The AI chat requires a dedicated N8n webhook workflow:

1. **Create Webhook Node**:
   - Method: POST
   - Path: `/grant-chat` (or custom)
   - Response Mode: "Last Node" (wait for AI response)

2. **Receive Payload**:
   ```json
   {
     "grant": { ... },        // Full grant data
     "organization": { ... }, // User's organization profile (or null)
     "chat": {
       "message": "User question",
       "history": [{"role": "user/assistant", "content": "..."}]
     }
   }
   ```

3. **AI Agent Node** (recommended):
   - Use Claude or GPT-4 with system prompt
   - Pass grant + organization as context
   - Return structured response

4. **Example System Prompt for Eligibility Analysis**:
   ```
   Eres un experto analista de subvenciones espanol. Tu trabajo es ayudar a organizaciones
   sin animo de lucro a determinar su elegibilidad para convocatorias de subvenciones.

   CONTEXTO DE LA CONVOCATORIA:
   {{$json.grant}}

   PERFIL DE LA ORGANIZACION:
   {{$json.organization}}

   INSTRUCCIONES:
   1. Analiza si la organizacion cumple con los requisitos de la convocatoria
   2. Identifica coincidencias en: sectores, regiones, tipo de beneficiario, presupuesto
   3. Senala requisitos que la organizacion NO cumple
   4. Da una puntuacion de compatibilidad (0-100%)
   5. Recomienda siguientes pasos si es elegible

   Responde de forma clara y estructurada en espanol.
   ```

5. **Response Format**:
   ```json
   {
     "output": "# Analisis de Elegibilidad\n\n## Compatibilidad: 85%\n\n..."
   }
   ```

### Environment Variable

Set in backend `.env`:
```
N8N_CHAT_WEBHOOK_URL=https://your-n8n-instance.app.n8n.cloud/webhook/grant-chat
```

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
