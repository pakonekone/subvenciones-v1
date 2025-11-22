# 🏛️ Sistema de Subvenciones v1.0

**Sistema profesional de captura, análisis y gestión de subvenciones públicas españolas**

Sistema full-stack que automatiza la búsqueda y gestión de ayudas y subvenciones del BOE (Boletín Oficial del Estado) y BDNS (Base de Datos Nacional de Subvenciones), con integración de inteligencia artificial para análisis y seguimiento bidireccional de exportaciones a Google Sheets.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-00a393?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-61dafb?logo=react)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5+-3178c6?logo=typescript)](https://www.typescriptlang.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-336791?logo=postgresql)](https://www.postgresql.org)

---

## 🎯 Características Principales

### ✅ Captura Automatizada
- **BDNS**: Búsqueda por rango de fechas preciso (fecha_desde → fecha_hasta)
- **BOE**: Procesamiento automático de PDFs con extracción de contenido
- **Filtrado inteligente**: 11 keywords para organizaciones sin ánimo de lucro + 44 keywords de subvenciones
- **Vista previa de filtros**: Transparencia total - ves qué criterios se aplican antes de capturar

### 🔍 Sistema de Filtros Transparente
- **Endpoint de filtros**: `/api/v1/filters/*` expone todos los keywords activos
- **Gestor de Keywords**: Modal con 3 tabs para visualizar filtros (BDNS Nonprofit, BOE Grants, BOE Nonprofit)
- **Preview en captura**: Información clara de qué keywords se usarán antes de iniciar

### 📊 Gestión Inteligente
- **Tabla avanzada**: Ordenación, filtrado, búsqueda full-text
- **Filtros múltiples**: Presupuesto, fechas, regiones, sectores, tipo de beneficiario
- **Clasificación nonprofit**: Confianza automática basada en keywords
- **Score de relevancia**: Informativo (no filtra grants, solo informa)

### 🤖 Integración N8n Bidireccional
- **Análisis AI**: Envía grants a N8n para evaluación de prioridad y valor estratégico
- **Callbacks de análisis**: Recibe y actualiza prioridad/valor de cada subvención
- **Tracking de exportación**: Sistema de webhooks bidireccional para seguir estado de Google Sheets

### 📈 Seguimiento de Exportaciones a Google Sheets
- **Columna "Exportado"** con indicadores visuales:
  - ✅ **Verde con enlace**: Exportado exitosamente a Google Sheets (clickeable)
  - ⏳ **Ámbar**: Enviado a N8n, procesando
  - ➖ **Gris**: No enviado aún
- **Metadatos completos**: URL de sheet, ID de fila, timestamp de exportación
- **Callback automático**: N8n confirma export exitoso vía webhook

### 📅 Gestión de Plazos
- **Fechas de publicación**: Columna sortable para visibilidad temporal
- **Cálculo de plazos**: Sistema para calcular días hábiles hasta deadline
- **Manejo de casos especiales**: "Hasta agotar presupuesto", "Revisar Bases"

---

## 🚀 Quick Start

### Requisitos Previos
- Python 3.11+
- Node.js 18+
- Docker (para PostgreSQL)
- Git

### 1. Clonar Repositorio
```bash
git clone https://github.com/pakonekone/subvenciones-v1.git
cd subvenciones-v1
```

### 2. Setup Backend
```bash
cd backend

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus valores (ver sección Configuración)

# Iniciar base de datos
docker-compose up -d db

# Ejecutar migraciones
alembic upgrade head

# Iniciar servidor backend
uvicorn app.main:app --reload
```

El backend estará disponible en `http://localhost:8000`
- **API Docs interactiva**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 3. Setup Frontend
```bash
# En nueva terminal
cd frontend

# Instalar dependencias
npm install

# Iniciar servidor de desarrollo
npm run dev
```

El frontend estará disponible en `http://localhost:3000`

---

## 🔧 Configuración

### Variables de Entorno Backend (`backend/.env`)

```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/subvenciones

# N8n Integration
N8N_WEBHOOK_URL=https://your-n8n-instance.com/webhook/grants-analysis

# API Limits
BDNS_MAX_RESULTS=50
BOE_MAX_RESULTS=100

# Filtering (informativo, no excluye grants)
MIN_RELEVANCE_SCORE=0.0

# CORS (frontend URL)
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Logging
LOG_LEVEL=INFO
```

### PostgreSQL

El sistema usa **puerto 5433** (no el estándar 5432) para evitar conflictos:
```yaml
# docker-compose.yml
services:
  db:
    image: postgres:16
    ports:
      - "5433:5432"  # Host:Container
    environment:
      POSTGRES_DB: subvenciones
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
```

---

## 📖 Uso del Sistema

### 1. Capturar Subvenciones BDNS

1. Abre la aplicación en `http://localhost:3000`
2. Click en **"Capturar Subvenciones"**
3. Selecciona tab **"BDNS"**
4. Configura rango de fechas:
   - **Fecha desde**: 2025-01-01
   - **Fecha hasta**: 2025-01-31
   - **Max resultados**: 50 (1-100)
5. **Previsualiza filtros**: Se mostrarán los 11 keywords nonprofit activos
6. Click **"Iniciar Captura"**
7. Espera proceso (puede tomar minutos según volumen)

**Resultado**: Subvenciones nonprofit capturadas y almacenadas en BD.

### 2. Capturar Subvenciones BOE

1. Tab **"BOE"** en diálogo de captura
2. Configura:
   - **Días hacia atrás**: 7 (últimos 7 días)
   - **Max resultados**: 20
3. **Previsualiza filtros**: 44 keywords de grants + nonprofit keywords
4. Click **"Iniciar Captura"**

**Resultado**: PDFs descargados, procesados, texto extraído, relevancia calculada.

### 3. Filtrar y Buscar

**Filtros rápidos** (botones superiores):
- Solo Nonprofit
- Presupuesto ≥ 500k€
- Fuente (BDNS/BOE)

**Búsqueda**:
- Busca en título, organismo, descripción

**Filtros avanzados** (panel lateral):
- Rango presupuesto: €500,000 - €5,000,000
- Fechas de solicitud: desde/hasta
- Regiones: Andalucía, Madrid, Cataluña...
- Sectores: Cultura, Medio Ambiente, Social...

### 4. Enviar a N8n para Análisis

1. Selecciona grants (checkbox)
2. Click **"Enviar a N8n"** (botón superior)
3. Sistema envía grants a webhook N8n
4. N8n procesa con AI y devuelve:
   - **Priority**: high/medium/low
   - **Strategic Value**: 0-10

**Callback automático**: N8n llama a `/api/v1/webhook/callback` para actualizar grants.

### 5. Seguimiento de Exportación a Google Sheets

**Proceso completo**:
1. Grants enviados a N8n (paso 4)
2. N8n ejecuta workflow:
   - Analiza con AI
   - Exporta a Google Sheets
   - **Nodo HTTP Request adicional**: Llama a `/api/v1/webhook/callback/sheets`
3. Backend actualiza:
   - `google_sheets_exported = true`
   - `google_sheets_url = "https://docs.google.com/..."`
   - `google_sheets_row_id = "123"`
   - `google_sheets_exported_at = timestamp`

**En la UI**:
- ✅ **Verde + enlace**: Click para abrir Google Sheet
- ⏳ **Ámbar**: Enviado, esperando confirmación
- ➖ **Gris**: No enviado

### 6. Ver Detalles de Grant

- Click en cualquier fila de la tabla
- Se abre panel lateral con:
  - Metadata completa
  - Descripción expandida
  - Enlaces a documentos
  - Análisis N8n (si disponible)
  - Estado de exportación

### 7. Gestionar Keywords de Filtros

1. Click **"Gestionar Filtros"**
2. Modal con 3 tabs:
   - **BDNS Nonprofit** (11 keywords)
   - **BOE Grants** (44 keywords)
   - **BOE Nonprofit** (compartido con BDNS)
3. Visualiza keywords activos
4. (Futuro) Edita y guarda cambios

---

## 🏗️ Arquitectura

### Stack Tecnológico

**Backend**:
- **FastAPI** 0.104+ - Framework API REST moderno
- **PostgreSQL** 16 - Base de datos relacional
- **SQLAlchemy** 2.0+ - ORM
- **Alembic** - Migraciones de BD
- **Pydantic** 2.0+ - Validación de datos
- **pdfplumber** + **PyPDF2** - Procesamiento de PDFs

**Frontend**:
- **React** 18 + **TypeScript** 5
- **Vite** - Build tool ultra-rápido
- **TanStack Table** v8 - Tablas avanzadas
- **TanStack Query** v5 - Data fetching y caching
- **Tailwind CSS** 3 - Utility-first CSS
- **shadcn/ui** - Componentes accesibles

**Infraestructura**:
- **Docker** - Containerización (PostgreSQL)
- **N8n** - Workflow automation & AI
- **Google Sheets API** - Exportación y tracking

### Flujos Principales

Ver **[ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md)** para diagramas completos con Mermaid de:
1. Arquitectura general del sistema
2. Flujo de captura BDNS
3. Flujo de captura BOE con PDFs
4. Flujo de filtrado y consulta
5. Flujo bidireccional N8n + Google Sheets

### Estructura de Directorios

```
subvenciones-v1/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # Endpoints FastAPI
│   │   │   ├── grants.py    # CRUD grants
│   │   │   ├── capture.py   # BDNS capture
│   │   │   ├── capture_boe.py
│   │   │   ├── webhook.py   # N8n bidireccional
│   │   │   ├── filters.py   # Keywords transparency
│   │   │   └── analytics.py
│   │   ├── models/          # SQLAlchemy models
│   │   │   └── grant.py     # 43+ campos
│   │   ├── services/        # Lógica de negocio
│   │   │   ├── bdns_service.py
│   │   │   ├── boe_service.py
│   │   │   ├── pdf_processor.py
│   │   │   └── n8n_service.py
│   │   ├── shared/          # Módulos reutilizables (de v0)
│   │   │   ├── bdns_api.py
│   │   │   ├── boe_api.py
│   │   │   └── filters.py   # Keywords definidos
│   │   ├── database.py
│   │   ├── config.py
│   │   └── main.py
│   ├── tests/
│   ├── migrations/          # Alembic
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── GrantsTable.tsx
│   │   │   ├── GrantDetailDrawer.tsx
│   │   │   ├── CaptureConfigDialog.tsx
│   │   │   ├── FilterKeywordsManager.tsx
│   │   │   ├── AdvancedFilterPanel.tsx
│   │   │   └── ui/          # shadcn/ui
│   │   ├── pages/
│   │   │   └── GrantsPage.tsx
│   │   ├── types.ts
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
│
├── docker-compose.yml
├── ARCHITECTURE_DIAGRAM.md   # Diagramas visuales
├── CLAUDE.md                 # Guía para Claude Code
├── DEPLOYMENT.md             # Deploy a Railway
├── TODO.md                   # Roadmap
└── README.md                 # Este archivo
```

---

## 📊 Modelo de Datos

### Grant (Tabla Principal)

Almacena todas las subvenciones con 43+ campos:

**Identificación**:
- `id` (PK)
- `source` - "BDNS" | "BOE"
- `code` - Código oficial (ej: BDNS-123456)

**Información básica**:
- `title`, `description`
- `department` - Organismo convocante
- `publication_date` - Fecha de publicación

**Plazos**:
- `application_start_date`
- `application_end_date`

**Presupuesto**:
- `total_budget` (float)
- `currency` (default: "EUR")

**Clasificación**:
- `beneficiary_types` (JSONB)
- `sectors` (JSONB)
- `regions` (JSONB)

**Nonprofit**:
- `is_nonprofit` (boolean)
- `nonprofit_confidence` (0.0-1.0)

**Documentación**:
- `pdf_url`, `pdf_content`, `pdf_markdown`
- `relevance_score` (informativo)

**N8n Analysis**:
- `priority` - "high" | "medium" | "low" | null
- `strategic_value` (float 0-10)

**Google Sheets Tracking** (nuevos campos 2025-10-20):
- `google_sheets_exported` (boolean, indexed)
- `google_sheets_exported_at` (datetime)
- `google_sheets_row_id` (string)
- `google_sheets_url` (text, clickeable en UI)

**Metadata**:
- `created_at`, `updated_at`

---

## 🔌 API Endpoints

### Grants
- `GET /api/v1/grants` - Listar con filtros
  - Query params: `skip`, `limit`, `source`, `is_nonprofit`, `min_budget`, `search`, `start_date_from`, `end_date_from`, `sectors[]`, `regions[]`, `google_sheets_exported`
- `GET /api/v1/grants/{id}` - Detalle por ID
- `DELETE /api/v1/grants/{id}` - Eliminar grant
- `DELETE /api/v1/grants/bulk` - Eliminar múltiples

### Capture
- `POST /api/v1/capture/bdns` - Capturar BDNS
  - Body: `{fecha_desde, fecha_hasta, max_results}`
- `POST /api/v1/capture/boe` - Capturar BOE
  - Body: `{days_back, max_results}`

### Webhooks (N8n Integration)
- `POST /api/v1/webhook/send` - Enviar grants a N8n
  - Body: `{grant_ids: [1,2,3]}`
- `POST /api/v1/webhook/callback` - Recibir análisis de N8n
  - Body: `{grant_id, priority, strategic_value}`
- `POST /api/v1/webhook/callback/sheets` - Recibir confirmación export Google Sheets
  - Body: `{grant_id, status, sheets_url, row_id, error_message}`

### Filters (Transparency)
- `GET /api/v1/filters/bdns` - 11 nonprofit keywords
- `GET /api/v1/filters/boe` - 44 grant + nonprofit keywords
- `GET /api/v1/filters/summary` - Resumen completo

### Analytics
- `GET /api/v1/analytics/summary` - Métricas dashboard

### Exports
- `POST /api/v1/exports/excel` - Generar Excel
  - Body: `{grant_ids: [1,2,3]}`

**Documentación interactiva**: http://localhost:8000/docs

---

## 🧪 Testing

```bash
cd backend

# Ejecutar todos los tests
pytest

# Con coverage
pytest --cov=app --cov-report=html

# Solo tests de API
pytest tests/test_api/

# Solo tests de servicios
pytest tests/test_services/

# Verbose
pytest -v -s
```

### Estructura de Tests
```
backend/tests/
├── test_api/
│   ├── test_grants.py
│   ├── test_capture.py
│   ├── test_webhook.py
│   └── test_filters.py
├── test_services/
│   ├── test_bdns_service.py
│   ├── test_boe_service.py
│   └── test_pdf_processor.py
└── conftest.py  # Fixtures compartidos
```

---

## 🚀 Deployment

Ver **[DEPLOYMENT.md](DEPLOYMENT.md)** para guía completa de deployment a Railway.

**Quick deploy checklist**:
- [ ] PostgreSQL 16+ provisionado
- [ ] Variables de entorno configuradas
- [ ] Migraciones ejecutadas (`alembic upgrade head`)
- [ ] N8n webhook URL configurada
- [ ] CORS origins incluye dominio de producción
- [ ] Frontend build (`npm run build`)
- [ ] Health check endpoint activo (`/health`)

---

## 🔐 Seguridad

- **CORS**: Solo orígenes permitidos en `CORS_ORIGINS`
- **SQL Injection**: Protegido por SQLAlchemy ORM
- **Validación**: Pydantic valida todos los inputs
- **Secrets**: Nunca commitear `.env` (está en `.gitignore`)
- **N8n Webhooks**: Considerar autenticación (API keys, tokens)

---

## 🐛 Troubleshooting

### PostgreSQL no inicia
```bash
# Verificar puerto
docker ps | grep postgres

# Ver logs
docker-compose logs -f db

# Si puerto 5433 está ocupado, cambiar en docker-compose.yml
```

### Migraciones fallan
```bash
# Resetear BD (CUIDADO: borra datos)
docker-compose down -v
docker-compose up -d db
alembic upgrade head
```

### Frontend no conecta a backend
```bash
# Verificar proxy en vite.config.ts
server: {
  proxy: {
    '/api': 'http://localhost:8000'
  }
}

# Verificar CORS en backend .env
CORS_ORIGINS=http://localhost:3000
```

### PDFs no se procesan
```bash
# Instalar dependencias de PDF
pip install pdfplumber PyPDF2

# Verificar logs
# Error común: PDFs protegidos o corruptos
```

### N8n webhooks no funcionan
```bash
# Verificar URL en .env
N8N_WEBHOOK_URL=https://...

# Probar con curl
curl -X POST https://your-n8n.com/webhook/test \
  -H "Content-Type: application/json" \
  -d '{"test": true}'

# Verificar configuración de callbacks en N8n workflow
```

---

## 📚 Recursos Adicionales

### Documentación Oficial de Fuentes
- [BDNS API](https://www.pap.hacienda.gob.es/bdnstrans/) - Base de Datos Nacional de Subvenciones
- [BOE API](https://boe.es/datosabiertos/) - Boletín Oficial del Estado

### Documentación del Proyecto
- [ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md) - Diagramas Mermaid de flujos
- [CLAUDE.md](CLAUDE.md) - Guía para desarrollo con Claude Code
- [DEPLOYMENT.md](DEPLOYMENT.md) - Deploy a Railway
- [TODO.md](TODO.md) - Roadmap y próximas features

### Stack
- [FastAPI Docs](https://fastapi.tiangolo.com)
- [React Docs](https://react.dev)
- [TanStack Table](https://tanstack.com/table/latest)
- [shadcn/ui](https://ui.shadcn.com)

---

## 🗺️ Roadmap

### ✅ Completado (v1.0)
- [x] Captura BDNS con rango de fechas
- [x] Captura BOE con procesamiento de PDFs
- [x] Sistema de filtros transparente
- [x] Integración bidireccional N8n
- [x] Tracking de exportación Google Sheets
- [x] Columna "Exportado" con indicadores visuales
- [x] Filtros avanzados (budget, dates, regions, sectors)
- [x] Relevance score informativo (no filtra)

### 🔄 En Progreso (v1.1)
- [ ] Edición de keywords desde UI
- [ ] Auto-refresh polling (actualización automática de estados)
- [ ] Excel export mejorado con cálculo de plazos españoles
- [ ] Testing automatizado completo

### 🎯 Futuro (v1.2+)
- [ ] Notificaciones push de nuevas subvenciones
- [ ] Dashboard analytics avanzado
- [ ] Sistema de alertas personalizadas
- [ ] Multi-tenant (múltiples organizaciones)
- [ ] API pública para integraciones

Ver **[TODO.md](TODO.md)** para lista detallada y prioridades.

---

## 👥 Contribuir

Desarrollado para automatización de captura y análisis de subvenciones públicas españolas.

### Development Workflow
1. Fork del repositorio
2. Crear branch (`git checkout -b feature/nueva-feature`)
3. Commits siguiendo conventional commits
4. Tests pasando (`pytest`)
5. PR a `main`

### Code Style
- **Backend**: Black + Ruff + MyPy
- **Frontend**: ESLint + Prettier
- **Commits**: Conventional Commits

---

## 📄 Licencia

Proyecto privado. Todos los derechos reservados.

---

## 🙏 Agradecimientos

- **BDNS** y **BOE** por proporcionar APIs públicas
- **N8n** por la plataforma de automatización
- **FastAPI**, **React**, y todo el ecosistema open-source

---

**Made with ❤️ for efficient grant opportunity management**

Para soporte o preguntas, ver [TODO.md](TODO.md) o documentación en `ARCHITECTURE_DIAGRAM.md`.
