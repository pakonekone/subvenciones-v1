# 📊 Estado Actual del Proyecto - Subvenciones v1.0

## ✅ LO QUE YA FUNCIONA (Completado Hoy)

### Backend Core
- ✅ **FastAPI Application** funcionando en puerto 8000
- ✅ **PostgreSQL Database** en Docker (puerto 5433)
- ✅ **SQLAlchemy ORM** con modelo Grant completo (43 campos)
- ✅ **CORS Middleware** configurado para frontend
- ✅ **Config Management** con Pydantic Settings + .env
- ✅ **Database Migrations** - Tabla grants creada y funcionando

### Servicios Implementados
- ✅ **BDNSService** - Captura grants desde BDNS API
  - Búsqueda con filtros
  - Filtrado por nonprofit keywords
  - Fetch de detalles completos
  - Manejo correcto de field mappings
- ✅ **N8nService** - Wrapper básico para webhooks N8n
- ✅ **Shared Modules** - bdns_api.py y bdns_models.py copiados y funcionando

### API Endpoints Funcionando
- ✅ `GET /api/v1/grants` - Listar grants con paginación y filtros
- ✅ `GET /api/v1/grants/{id}` - Obtener grant por ID
- ✅ `POST /api/v1/capture/bdns` - Capturar grants de BDNS
- ✅ `POST /api/v1/webhook/send` - Enviar grants a N8n
- ✅ `GET /api/v1/health` - Health check

### Frontend React
- ✅ **Vite + React + TypeScript** configurado
- ✅ **Tabla de Grants** con datos en tiempo real
- ✅ **Botones de Captura** funcionando
- ✅ **Botón Enviar a N8n** con selección múltiple
- ✅ **Proxy Vite** configurado para API

### Database
- ✅ **PostgreSQL 15** en Docker
- ✅ **2 Grants Capturados** como prueba:
  - BDNS-863193: Congreso Microbiología (€2,500)
  - BDNS-863197: Cronistas Oficiales (€6,000)

### Arquitectura
- ✅ Separación Backend/Frontend funcional
- ✅ Docker Compose para PostgreSQL
- ✅ Hot-reload en desarrollo (backend y frontend)

---

## ❌ LO QUE FALTA - PRIORIZADO

### 🔴 PRIORIDAD CRÍTICA

#### 1. Export Excel Service ⭐⭐⭐⭐⭐
**URGENTE**: El principal valor del sistema v1.0
```python
# Necesitamos crear:
app/services/excel_service.py
  ├─ generate_bdns_nonprofit_excel()
  ├─ calculate_deadline() con 3 casos:
  │   1. Plazo específico → calcular días hábiles
  │   2. "Hasta agotar presupuesto" → N/A
  │   3. Sin información → revisar PDF
  ├─ add_business_days() - cálculo preciso
  └─ Estilos profesionales (openpyxl)
```

**Endpoint necesario**:
```
POST /api/v1/exports/bdns-excel
{
  "grant_ids": ["BDNS-863193", "BDNS-863197"],
  "include_closed": false
}
→ Returns: Excel file download
```

**Campos críticos del Excel**:
- Código BDNS
- Título Convocatoria
- Organismo Convocante
- Importe Total
- **Fecha Inicio** ⭐
- **Fecha Fin** ⭐
- **Días para Presentar** ⭐ (cálculo complejo)
- Beneficiarios
- Sectores
- Región
- URL Bases Reguladoras
- Estado (Abierta/Cerrada)

#### 2. Filtro Avanzado de Grants
Actualmente solo hay búsqueda básica. Necesitamos:
```typescript
// Frontend: src/components/grants/GrantFilters.tsx
- Rango de fechas
- Rango de presupuesto (€10k-€100k)
- Filtro por organismo
- Filtro por sector
- Filtro por región
- Búsqueda por texto
- Estado: Abierta/Cerrada
```

#### 3. Captura BOE (Además de BDNS)
**Reutilizar del proyecto original**:
```python
# Copiar y adaptar:
boe_project/capture_grants.py → app/services/boe_service.py
boe_project/pdf_processor.py → app/services/pdf_service.py

# Endpoint:
POST /api/v1/capture/boe
{
  "date": "2025-10-18",  # opcional, default=today
  "process_pdfs": true
}
```

### 🟡 PRIORIDAD ALTA

#### 4. Vista Detallada de Grant
Modal/Página con toda la información:
```typescript
// src/components/grants/GrantDetailModal.tsx
- Toda la metadata
- Documentos adjuntos
- Anuncios oficiales
- Botón "Descargar PDF"
- Botón "Abrir en BDNS"
```

#### 5. Dashboard Analytics
Métricas importantes (inspirado en BOE Dashboard):
```typescript
// src/pages/Analytics.tsx
📊 Gráficos:
- Grants capturados por día (últimos 30 días)
- Distribución por presupuesto
- Top 10 organismos convocantes
- Distribución por región
- Grants abiertos vs cerrados
```

#### 6. N8n Cloud Integration Mejorada
```python
# app/services/n8n_service.py - Mejorar
- Retry logic con exponential backoff
- Queue management (webhook_queue.db)
- Verificación de entrega
- Logs estructurados de envíos
```

#### 7. Procesamiento PDF (Si queremos capturar BOE)
```python
# app/services/pdf_service.py
- Descargar PDFs de BOE
- Extraer texto con pdfplumber/PyPDF2
- Markdown conversion
- Buscar deadlines/amounts en texto
```

### 🟢 PRIORIDAD MEDIA

#### 8. Búsqueda y Filtros Avanzados UI
- Filtros sticky (guardar en localStorage)
- "Mis filtros guardados"
- Export filtrados a Excel

#### 9. Gestión de Duplicados
```python
# Detectar grants duplicados:
- Mismo código BDNS
- Título similar (fuzzy matching)
- Merge automático de información
```

#### 10. Notificaciones In-App
```typescript
// Toast notifications para:
- Captura exitosa
- Error en captura
- Envío a N8n exitoso
- Nueva grant disponible
```

#### 11. Auth & User Management (Opcional)
Si varios usuarios van a usar el sistema:
```
- Login simple (email + password)
- Roles: Admin, Viewer
- Histórico de acciones por usuario
```

### ⚪ PRIORIDAD BAJA

#### 12. Deployment
```yaml
# Railway / Render / Fly.io
- Dockerfile backend
- Dockerfile frontend (build estático)
- docker-compose.prod.yml
- CI/CD con GitHub Actions
```

#### 13. Tests
```python
# backend/tests/
- test_bdns_service.py
- test_excel_service.py ⭐
- test_endpoints.py
```

#### 14. Logs & Monitoring
```python
# Structured logging
- JSON logs
- Log rotation
- Sentry integration (errores)
```

---

## 🎯 ROADMAP SUGERIDO

### Sprint 1 (Hoy - Funcionalidad Core)
1. ✅ ~~Setup básico backend + frontend~~
2. ✅ ~~Captura BDNS funcionando~~
3. ⏳ **Excel Export Service** ← HACER AHORA
4. ⏳ **Filtros básicos mejorados**

### Sprint 2 (Mañana - Captura BOE)
1. Integrar captura BOE
2. PDF processing
3. Merge BOE + BDNS data

### Sprint 3 (Día 3 - UX Mejorada)
1. Vista detallada de grants
2. Dashboard analytics
3. Búsqueda avanzada

### Sprint 4 (Día 4 - Polish)
1. N8n queue management
2. Notificaciones
3. Error handling mejorado

### Sprint 5 (Día 5-6 - Deploy)
1. Dockerización completa
2. Deploy a Railway
3. Testing end-to-end

---

## 📦 FUNCIONALIDADES DEL BOE PROJECT QUE PODEMOS REUTILIZAR

### Alta Prioridad
- ✅ `bdns_api.py` - Ya copiado y funcionando
- ✅ `bdns_models.py` - Ya copiado y funcionando
- ⏳ `capture_grants.py` - **Necesitamos adaptar para captura BOE**
- ⏳ `pdf_processor.py` - **Para extraer info de PDFs**
- ⏳ `n8n_webhook.py` - **Mejorar queue management**
- ⏳ `filters.py` - **Filtros de relevancia por sector**

### Media Prioridad
- `boe_api.py` - Cliente BOE completo
- `models.py` - Pydantic models de BOE
- `boe_to_n8n.py` - Orchestrator completo

### Baja Prioridad
- `boe_dashboard.py` - Streamlit (no necesitamos, ya tenemos React)

---

## 🔥 SIGUIENTE PASO INMEDIATO

**CREAR: `app/services/excel_service.py`**

Este es el valor diferencial del sistema v1.0. Sin Excel Export, el sistema no cumple su propósito principal.

```python
# Pseudocódigo de lo que necesitamos:

def generate_bdns_nonprofit_excel(grant_ids: List[str]) -> bytes:
    # 1. Fetch grants from database
    grants = db.query(Grant).filter(Grant.id.in_(grant_ids)).all()

    # 2. Create Excel workbook
    wb = openpyxl.Workbook()
    ws = wb.active

    # 3. Headers con estilo
    headers = [
        "Código BDNS", "Título", "Organismo",
        "Importe Total", "Fecha Inicio", "Fecha Fin",
        "Días para Presentar", "Beneficiarios", ...
    ]

    # 4. Calcular deadline para cada grant ⭐⭐⭐
    for grant in grants:
        dias_restantes = calculate_deadline(
            fecha_fin=grant.application_end_date,
            fecha_inicio=grant.application_start_date,
            titulo=grant.title  # Para detectar "hasta agotar"
        )

    # 5. Aplicar estilos profesionales
    # 6. Return bytes

def calculate_deadline(fecha_fin, fecha_inicio, titulo) -> str:
    # CASO 1: Fecha fin específica → calcular días hábiles
    if fecha_fin:
        return str(calculate_business_days_remaining(fecha_fin))

    # CASO 2: "Hasta agotar presupuesto"
    if "agotar" in titulo.lower():
        return "N/A - Hasta agotar"

    # CASO 3: Sin info
    return "Revisar Bases"

def calculate_business_days_remaining(fecha_fin: date) -> int:
    # Contar días hábiles desde hoy hasta fecha_fin
    # Excluir sábados, domingos y festivos españoles
    ...
```

¿Quieres que empiece por el Excel Service ahora?
