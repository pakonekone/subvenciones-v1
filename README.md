# 🏛️ Sistema de Subvenciones v1.0

**Sistema profesional de captura y gestión de subvenciones de BOE y BDNS con integración N8n**

## 🚀 Quick Start

```bash
# 1. Setup backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your configuration

# 3. Start database
docker-compose up -d db

# 4. Run migrations
alembic upgrade head

# 5. Start backend
uvicorn app.main:app --reload

# 6. Setup frontend (new terminal)
cd frontend
npm install
npm run dev
```

## 📋 Features

### ✅ Implementado
- **Excel BDNS Nonprofit** con cálculo automático de fechas límite
- Captura automática BOE y BDNS con selección precisa de fechas
- **Sistema de filtros transparente** - visualiza y edita keywords antes de captura
- Filtros avanzados (nonprofit, montante ≥500k, fechas)
- **Integración bidireccional con Google Sheets** - tracking de exports con webhooks
- Integración N8n para análisis AI
- API REST completa con endpoints de filtros
- UI profesional con React + TanStack Table
- **Columna "Exportado"** con indicadores visuales de estado

### 🔄 En progreso
- Deploy automatizado Railway
- Testing automatizado
- Documentación API completa

## 🏗️ Arquitectura

```
subvenciones-v1/
├── backend/          # FastAPI + PostgreSQL
│   ├── app/          # Application code
│   ├── shared/       # Reutilizado de v0 (BOE/BDNS APIs)
│   └── tests/        # Unit & integration tests
│
├── frontend/         # React + TypeScript + Vite
│   └── src/
│
└── docs/             # Documentation
```

## 🎯 Excel BDNS - Feature Principal

Genera datos para enviar a n8n y desde ahí crearemos google sheet profesional con:
- ✅ Código BDNS
- ✅ Subvencionador (organismo)
- ✅ Título convocatoria
- ✅ Fecha publicación
- ✅ **Fecha límite calculada** (convierte "20 días hábiles" → fecha exacta)
- ✅ Montante económico (≥500,000€)
- ✅ Links (BDNS oficial, PDF, tramitación)

## 📊 Tecnologías

### Backend
- **FastAPI** - API REST framework
- **PostgreSQL** - Database
- **SQLAlchemy** - ORM
- **Alembic** - Migrations
- **Pydantic** - Validation
- **openpyxl** - Excel generation

### Frontend
- **React 18** + **TypeScript**
- **Vite** - Build tool
- **TanStack Table** - Data tables
- **TanStack Query** - Data fetching
- **Tailwind CSS** - Styling
- **shadcn/ui** - Component library

### Integración
- **N8n** - Workflow automation & AI analysis
- **BOE API** - Official gazette data
- **BDNS API** - National grants database

## 🔗 Links

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432

## 📚 Documentation

- [API Documentation](docs/API.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Migration from v0](docs/MIGRATION.md)
- [Architecture](docs/ARCHITECTURE.md)

## 👥 Team

Desarrollado para automatización de captura y análisis de subvenciones públicas españolas.

---

**Made with ❤️ for efficient grant opportunity management**
