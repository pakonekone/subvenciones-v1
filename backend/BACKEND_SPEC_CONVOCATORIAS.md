# Especificación Técnica Backend - Módulo Convocatorias (Grants)

**Proyecto:** Subvenciones v1.0 - Sistema de Gestión de Subvenciones
**Fecha:** 2025-10-18
**Versión:** 1.0
**Autor:** Especificación basada en frontend implementado

---

## 📋 Tabla de Contenidos

1. [Visión General del Sistema](#visión-general-del-sistema)
2. [Arquitectura](#arquitectura)
3. [API Endpoints](#api-endpoints)
4. [Modelo de Datos](#modelo-de-datos)
5. [Schemas Pydantic](#schemas-pydantic)
6. [Lógica de Negocio](#lógica-de-negocio)
7. [Integración N8n](#integración-n8n)
8. [Base de Datos](#base-de-datos)
9. [Testing](#testing)
10. [Ejemplos de Uso](#ejemplos-de-uso)

---

## 🎯 Visión General del Sistema

### Propósito
Sistema automatizado para capturar, filtrar, almacenar y enviar información sobre subvenciones españolas desde dos fuentes principales:
- **BDNS** (Base de Datos Nacional de Subvenciones)
- **BOE** (Boletín Oficial del Estado)

### Flujo de Datos
```
┌─────────────┐
│ BDNS API    │──┐
└─────────────┘  │
                 │    ┌──────────────┐      ┌─────────────┐      ┌──────────┐
                 ├───→│ FastAPI      │─────→│ PostgreSQL  │←────→│ Frontend │
                 │    │ Backend      │      │ Database    │      │ React    │
┌─────────────┐  │    └──────────────┘      └─────────────┘      └──────────┘
│ BOE API     │──┘           │
└─────────────┘              │
                             ↓
                    ┌─────────────────┐
                    │ N8n Cloud       │
                    │ (AI Analysis)   │
                    └─────────────────┘
```

### Tecnologías
- **Framework:** FastAPI 0.104+
- **Base de Datos:** PostgreSQL 15+ (puerto 5433)
- **ORM:** SQLAlchemy 2.0+
- **Validación:** Pydantic 2.0+
- **HTTP Client:** HTTPX (async)
- **Migraciones:** Scripts Python personalizados

---

## 🏗️ Arquitectura

### Estructura de Directorios
```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── grants.py          # Endpoints de grants
│   │       ├── capture_bdns.py    # Captura BDNS
│   │       ├── capture_boe.py     # Captura BOE
│   │       ├── webhook.py         # Integración N8n
│   │       └── analytics.py       # Analytics dashboard
│   ├── models/
│   │   ├── grant.py              # Modelo Grant
│   │   └── webhook_history.py    # Modelo WebhookHistory
│   ├── services/
│   │   ├── bdns_service.py       # Lógica BDNS
│   │   ├── boe_service.py        # Lógica BOE
│   │   └── n8n_service_enhanced.py  # Servicio N8n con retry
│   ├── migrations/               # Scripts de migración
│   ├── config.py                 # Configuración
│   ├── database.py               # Setup DB
│   └── main.py                   # App principal
├── .env                          # Variables de entorno
└── requirements.txt
```

### Capas de la Aplicación
1. **API Layer** (`app/api/v1/`) - Endpoints REST
2. **Service Layer** (`app/services/`) - Lógica de negocio
3. **Data Layer** (`app/models/`) - Modelos SQLAlchemy
4. **Integration Layer** - APIs externas (BDNS, BOE, N8n)

---

## 🔌 API Endpoints

### Base URL
```
http://localhost:8000/api/v1
```

---

### 1. **Grants Management**

#### **1.1. GET /api/v1/grants**
Lista grants con filtros avanzados y paginación.

**Query Parameters:**
```python
# Filtros de búsqueda
search: str | None           # Búsqueda full-text en title, purpose
department: str | None       # Filtro por organismo (LIKE)

# Filtros de fechas (application_end_date)
date_from: str | None        # ISO date (YYYY-MM-DD)
date_to: str | None          # ISO date (YYYY-MM-DD)

# Filtros de presupuesto
budget_min: float | None     # Presupuesto mínimo en €
budget_max: float | None     # Presupuesto máximo en €

# Filtros de confianza
confidence_min: float | None # Confianza mínima (0.0 - 1.0)

# Filtros booleanos
is_open: bool | None         # Estado de convocatoria
is_nonprofit: bool | None    # Filtro nonprofit (generalmente true)
sent_to_n8n: bool | None     # Enviado a N8n

# Filtros de fuente
source: str | None           # "BDNS" o "BOE"

# Paginación
limit: int = 100             # Límite de resultados (max 1000)
offset: int = 0              # Offset para paginación
```

**Response 200:**
```json
{
  "total": 245,
  "grants": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "source": "BDNS",
      "title": "Subvenciones para proyectos de innovación social",
      "department": "Ministerio de Inclusión, Seguridad Social y Migraciones",
      "publication_date": "2025-01-15T00:00:00",
      "application_start_date": "2025-02-01T00:00:00",
      "application_end_date": "2025-03-31T00:00:00",
      "budget_amount": 500000.00,
      "is_nonprofit": true,
      "is_open": true,
      "sent_to_n8n": false,
      "bdns_code": "745392",
      "boe_id": null,
      "nonprofit_confidence": 0.95,
      "beneficiary_types": ["Asociaciones", "Fundaciones", "ONG"],
      "sectors": ["Servicios sociales", "Innovación social"],
      "regions": ["Nacional"],
      "purpose": "Fomentar proyectos innovadores en el ámbito social...",
      "regulatory_base_url": "https://www.boe.es/...",
      "electronic_office": "https://sede.inclusion.gob.es"
    }
  ]
}
```

**Lógica de Filtrado:**
- **search**: Full-text search usando PostgreSQL `to_tsvector` (español) en `title` y `purpose`
- **department**: Case-insensitive LIKE `%{department}%`
- **date_from/date_to**: Filtra por `application_end_date` (fecha límite)
- **Filtros combinados**: AND lógico entre todos los filtros activos

**Errores:**
- `400`: Parámetros inválidos
- `500`: Error interno del servidor

---

#### **1.2. GET /api/v1/grants/{grant_id}**
Obtiene detalles completos de un grant específico.

**Path Parameters:**
- `grant_id`: UUID del grant

**Response 200:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "source": "BDNS",
  "title": "Subvenciones para proyectos de innovación social",
  "department": "Ministerio de Inclusión, Seguridad Social y Migraciones",
  "publication_date": "2025-01-15T00:00:00",
  "application_start_date": "2025-02-01T00:00:00",
  "application_end_date": "2025-03-31T00:00:00",
  "budget_amount": 500000.00,
  "is_nonprofit": true,
  "is_open": true,
  "sent_to_n8n": false,
  "sent_to_n8n_at": null,
  "bdns_code": "745392",
  "boe_id": null,
  "nonprofit_confidence": 0.95,
  "beneficiary_types": ["Asociaciones", "Fundaciones", "ONG"],
  "sectors": ["Servicios sociales", "Innovación social"],
  "regions": ["Nacional"],
  "purpose": "Fomentar proyectos innovadores en el ámbito social que promuevan la inclusión y el bienestar de colectivos vulnerables...",
  "regulatory_base_url": "https://www.boe.es/diario_boe/txt.php?id=BOE-A-2025-12345",
  "electronic_office": "https://sede.inclusion.gob.es",
  "created_at": "2025-01-16T10:30:00",
  "updated_at": "2025-01-16T10:30:00"
}
```

**Errores:**
- `404`: Grant no encontrado
- `500`: Error interno

---

#### **1.3. POST /api/v1/grants**
Crea un grant manualmente (para testing o importaciones manuales).

**Request Body:**
```json
{
  "source": "MANUAL",
  "title": "Ayudas a startups tecnológicas",
  "department": "CDTI",
  "publication_date": "2025-01-20",
  "application_start_date": "2025-02-01",
  "application_end_date": "2025-04-30",
  "budget_amount": 1000000.00,
  "is_nonprofit": false,
  "beneficiary_types": ["Startups", "PYMEs"],
  "sectors": ["Tecnología", "I+D"],
  "regions": ["Madrid", "Barcelona"],
  "purpose": "Financiación para startups tecnológicas en fase seed",
  "regulatory_base_url": "https://www.cdti.es/...",
  "electronic_office": "https://sede.cdti.es"
}
```

**Response 201:**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "source": "MANUAL",
  "title": "Ayudas a startups tecnológicas",
  ...
}
```

**Validaciones:**
- `title`: Requerido, min 10 caracteres
- `source`: Requerido
- `budget_amount`: >= 0 si se proporciona
- `application_end_date`: Debe ser posterior a `application_start_date`

**Errores:**
- `400`: Validación fallida
- `500`: Error creando grant

---

#### **1.4. PUT /api/v1/grants/{grant_id}**
Actualiza un grant existente (actualización parcial permitida).

**Request Body:** (todos los campos opcionales)
```json
{
  "is_nonprofit": true,
  "nonprofit_confidence": 0.85,
  "sent_to_n8n": true
}
```

**Response 200:** Grant completo actualizado

**Errores:**
- `404`: Grant no encontrado
- `400`: Validación fallida
- `500`: Error actualizando

---

#### **1.5. DELETE /api/v1/grants/{grant_id}**
Elimina un grant de la base de datos.

**Response 200:**
```json
{
  "message": "Grant deleted successfully",
  "grant_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Errores:**
- `404`: Grant no encontrado
- `500`: Error eliminando

---

#### **1.6. GET /api/v1/grants/stats**
Estadísticas básicas rápidas (sin parámetros de tiempo).

**Response 200:**
```json
{
  "total_grants": 1245,
  "nonprofit_grants": 892,
  "open_grants": 234,
  "sent_to_n8n": 156,
  "total_budget": 45678900.00,
  "sources": {
    "BDNS": 1100,
    "BOE": 145
  }
}
```

---

### 2. **Capture Endpoints**

#### **2.1. POST /api/v1/capture/bdns**
Captura grants desde la API de BDNS.

**Request Body:**
```json
{
  "days_back": 7,           // Días hacia atrás desde hoy (default: 7)
  "max_results": 50         // Máximo de resultados (default: 50)
}
```

**Response 200:**
```json
{
  "success": true,
  "message": "Captura BDNS exitosa",
  "stats": {
    "total_fetched": 50,
    "total_new": 12,
    "total_updated": 5,
    "total_nonprofit": 8,
    "total_skipped": 33
  },
  "processing_time_seconds": 5.2
}
```

**Lógica:**
1. Query BDNS API para grants de los últimos `days_back` días
2. Para cada grant:
   - Si no existe (`bdns_code` único): crear nuevo
   - Si existe: actualizar campos
3. Aplicar filtro nonprofit automáticamente
4. Calcular `nonprofit_confidence` basado en keywords

**Errores:**
- `400`: Parámetros inválidos (days_back > 365, max_results > 1000)
- `503`: BDNS API no disponible
- `500`: Error en procesamiento

---

#### **2.2. POST /api/v1/capture/boe**
Captura grants desde BOE usando keyword detection.

**Request Body:**
```json
{
  "target_date": "2025-01-20",  // Fecha del BOE (ISO format)
  "min_relevance": 0.3          // Score mínimo (0.0 - 1.0, default: 0.3)
}
```

**Response 200:**
```json
{
  "success": true,
  "message": "Captura BOE exitosa",
  "stats": {
    "total_scanned": 250,      // Documentos escaneados
    "total_new": 8,            // Nuevos grants creados
    "total_updated": 2,        // Grants actualizados
    "total_skipped": 240,      // Documentos sin keywords
    "avg_relevance": 0.67
  },
  "processing_time_seconds": 12.5
}
```

**Lógica:**
1. Obtener sumario del BOE para `target_date`
2. Para cada documento, calcular `relevance_score`:
   - Detección de keywords: "subvención", "ayuda", "convocatoria", "beca", etc.
   - Peso por sección: I (alta), III (media), V.A y V.B (alta)
   - Score = (keywords_found / total_keywords) * section_weight
3. Si `relevance_score >= min_relevance`:
   - Crear grant con ID formato `BOE-A-YYYY-XXXXX`
   - Extraer información del título y descripción
   - NO nonprofit por defecto (requiere validación manual o AI)
4. Deduplicación por `boe_id`

**Keywords BOE (30+ palabras clave):**
```python
GRANT_KEYWORDS = [
    'subvención', 'subvenciones', 'ayuda', 'ayudas',
    'beca', 'becas', 'convocatoria', 'convocatorias',
    'fondos next generation', 'startup', 'startups',
    'pyme', 'pymes', 'pequeñas y medianas empresas',
    'innovación', 'i+d+i', 'investigación',
    'desarrollo tecnológico', 'economía circular',
    'sostenibilidad', 'energías renovables',
    'transformación digital', 'digitalización',
    'formación', 'empleo', 'emprendimiento',
    'asociaciones', 'fundaciones', 'ong',
    'tercer sector', 'sin ánimo de lucro',
    'economía social', 'cooperativas'
]
```

**Secciones BOE Relevantes:**
- I. Disposiciones generales (peso: 1.2)
- III. Otras disposiciones (peso: 1.0)
- V.A. Anuncios - Contratación del Sector Público (peso: 1.1)
- V.B. Anuncios - Otros anuncios oficiales (peso: 1.0)

**Errores:**
- `400`: target_date inválida o futura
- `503`: BOE API no disponible
- `500`: Error en procesamiento

---

### 3. **Webhook N8n Integration**

#### **3.1. POST /api/v1/webhook/send**
Envía uno o múltiples grants a N8n Cloud para análisis AI.

**Request Body:**
```json
{
  "grant_ids": [
    "550e8400-e29b-41d4-a716-446655440000",
    "660e8400-e29b-41d4-a716-446655440001"
  ]
}
```

**Response 200:**
```json
{
  "success": true,
  "message": "2/2 grants enviados exitosamente",
  "results": {
    "total": 2,
    "successful": 2,
    "failed": 0,
    "errors": []
  }
}
```

**Lógica:**
1. Validar que N8N_WEBHOOK_URL esté configurado
2. Para cada grant_id:
   - Obtener grant de DB
   - Crear payload N8n (ver sección [Integración N8n](#integración-n8n))
   - Enviar POST a webhook con retry logic
   - Crear registro en `webhook_history`
   - Si éxito: marcar `sent_to_n8n = true`, `sent_to_n8n_at = now()`
3. Devolver estadísticas de envío

**Retry Logic (N8nServiceEnhanced):**
- **Max retries:** 3
- **Backoff:** Exponencial (2s, 4s, 8s, 16s, 32s, max 60s)
- **Retry en:** HTTP 5xx (server errors)
- **No retry en:** HTTP 4xx (client errors)
- **Tracking:** Todos los intentos en `webhook_history`

**Errores:**
- `400`: No grant_ids proporcionados o IDs inválidos
- `503`: N8n webhook URL no configurado
- `500`: Error enviando (detalles en response)

---

#### **3.2. POST /api/v1/webhook/send/{grant_id}**
Shortcut para enviar un único grant.

**Path Parameters:**
- `grant_id`: UUID del grant

**Response 200:**
```json
{
  "success": true,
  "message": "Grant 550e8400... enviado a N8n",
  "results": {
    "grant_id": "550e8400-e29b-41d4-a716-446655440000",
    "status_code": 200,
    "response_time_ms": 245,
    "history_id": 123
  }
}
```

**Errores:**
- `404`: Grant no encontrado
- `503`: N8n no configurado
- `500`: Error enviando

---

#### **3.3. POST /api/v1/webhook/resend-failed**
Reintenta enviar grants que fallaron anteriormente.

**Query Parameters:**
```python
limit: int = 10  # Máximo de grants a reintentar
```

**Response 200:**
```json
{
  "success": true,
  "message": "Reintentando envío de 5 grants",
  "results": {
    "total": 5,
    "successful": 3,
    "failed": 2,
    "errors": [
      {
        "grant_id": "550e8400-...",
        "error": "Timeout after 30s",
        "attempt": 3
      }
    ]
  }
}
```

**Lógica:**
1. Query `webhook_history` con `status = 'retrying'` y `next_retry_at <= now()`
2. Limitar a `limit` registros
3. Para cada grant, ejecutar `send_grant_with_retry()`
4. Actualizar `webhook_history` con resultados

**Errores:**
- `500`: Error en reintento

---

#### **3.4. GET /api/v1/webhook/unsent**
Lista grants que no han sido enviados a N8n.

**Query Parameters:**
```python
limit: int = 50  # Límite de resultados
```

**Response 200:**
```json
{
  "total": 12,
  "grants": [
    {
      "id": "550e8400-...",
      "title": "Subvenciones para...",
      "source": "BDNS",
      "created_at": "2025-01-20T10:30:00"
    }
  ]
}
```

**Lógica:**
- Query grants con `sent_to_n8n = false`
- Ordenar por `created_at DESC`

---

#### **3.5. GET /api/v1/webhook/test**
Prueba la conectividad con N8n webhook.

**Response 200:**
```json
{
  "success": true,
  "message": "N8n webhook conectado correctamente",
  "webhook_url": "https://franco-n8n.app.n8n.cloud/webhook/...",
  "response_time_ms": 156,
  "status_code": 200
}
```

**Lógica:**
1. Enviar payload de prueba a N8n:
```json
{
  "test": true,
  "message": "Connectivity test from backend",
  "timestamp": "2025-01-20T10:30:00"
}
```
2. Validar respuesta

**Errores:**
- `503`: N8n no configurado o no responde
- `500`: Error de conectividad

---

### 4. **Analytics Endpoints**

#### **4.1. GET /api/v1/analytics/overview**
Dashboard completo de analytics con métricas agregadas.

**Query Parameters:**
```python
days: int = 30  # Período de análisis (min: 1, max: 365)
```

**Response 200:**
```json
{
  "total_grants": 245,
  "total_budget": 125678900.00,
  "nonprofit_grants": 180,
  "open_grants": 45,
  "sent_to_n8n": 120,
  "avg_confidence": 0.78,

  "grants_by_source": [
    {
      "source": "BDNS",
      "count": 200,
      "total_budget": 100000000.00,
      "nonprofit_count": 160,
      "open_count": 38,
      "sent_to_n8n_count": 95
    },
    {
      "source": "BOE",
      "count": 45,
      "total_budget": 25678900.00,
      "nonprofit_count": 20,
      "open_count": 7,
      "sent_to_n8n_count": 25
    }
  ],

  "grants_by_date": [
    {
      "date": "2025-01-20",
      "count": 12,
      "total_budget": 5600000.00
    }
  ],

  "budget_distribution": [
    {
      "range": "< 10K €",
      "count": 45,
      "total_budget": 280000.00
    },
    {
      "range": "10K - 50K €",
      "count": 78,
      "total_budget": 2450000.00
    },
    {
      "range": "50K - 100K €",
      "count": 34,
      "total_budget": 2890000.00
    },
    {
      "range": "100K - 500K €",
      "count": 52,
      "total_budget": 15600000.00
    },
    {
      "range": "500K - 1M €",
      "count": 23,
      "total_budget": 17800000.00
    },
    {
      "range": "> 1M €",
      "count": 13,
      "total_budget": 86658900.00
    }
  ],

  "top_departments": [
    {
      "department": "Ministerio de Trabajo y Economía Social",
      "count": 45,
      "total_budget": 34500000.00,
      "avg_budget": 766666.67
    }
  ]
}
```

**Lógica SQL:**
```sql
-- Total grants en período
SELECT COUNT(*), SUM(budget_amount), AVG(nonprofit_confidence)
FROM grants
WHERE created_at >= NOW() - INTERVAL '{days} days'

-- Grants por fuente
SELECT source, COUNT(*), SUM(budget_amount),
       SUM(CASE WHEN is_nonprofit THEN 1 ELSE 0 END) as nonprofit_count,
       SUM(CASE WHEN is_open THEN 1 ELSE 0 END) as open_count,
       SUM(CASE WHEN sent_to_n8n THEN 1 ELSE 0 END) as sent_count
FROM grants
WHERE created_at >= NOW() - INTERVAL '{days} days'
GROUP BY source

-- Grants por día (para gráfico timeline)
SELECT DATE(created_at) as date, COUNT(*), SUM(budget_amount)
FROM grants
WHERE created_at >= NOW() - INTERVAL '{days} days'
GROUP BY DATE(created_at)
ORDER BY date

-- Distribución de presupuesto
SELECT
  CASE
    WHEN budget_amount < 10000 THEN '< 10K €'
    WHEN budget_amount < 50000 THEN '10K - 50K €'
    WHEN budget_amount < 100000 THEN '50K - 100K €'
    WHEN budget_amount < 500000 THEN '100K - 500K €'
    WHEN budget_amount < 1000000 THEN '500K - 1M €'
    ELSE '> 1M €'
  END as range,
  COUNT(*), SUM(budget_amount)
FROM grants
WHERE created_at >= NOW() - INTERVAL '{days} days'
  AND budget_amount IS NOT NULL
GROUP BY range

-- Top 10 departamentos
SELECT department, COUNT(*),
       SUM(budget_amount) as total,
       AVG(budget_amount) as avg
FROM grants
WHERE created_at >= NOW() - INTERVAL '{days} days'
  AND department IS NOT NULL
GROUP BY department
ORDER BY total DESC
LIMIT 10
```

**Errores:**
- `400`: days inválido (< 1 o > 365)
- `500`: Error en query

---

#### **4.2. GET /api/v1/analytics/trends**
Tendencias temporales para una métrica específica.

**Query Parameters:**
```python
metric: str       # "count" | "budget" | "confidence"
days: int = 30    # Período
grouping: str = "day"  # "day" | "week" | "month"
```

**Response 200:**
```json
{
  "metric": "count",
  "grouping": "day",
  "data": [
    {
      "period": "2025-01-20",
      "value": 12
    },
    {
      "period": "2025-01-21",
      "value": 8
    }
  ]
}
```

**Errores:**
- `400`: Parámetros inválidos
- `500`: Error en query

---

## 💾 Modelo de Datos

### Tabla: `grants`

```sql
CREATE TABLE grants (
    -- Identificadores
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source VARCHAR NOT NULL,                    -- "BDNS" | "BOE" | "MANUAL"
    bdns_code VARCHAR,                          -- Código BDNS (único si source=BDNS)
    boe_id VARCHAR,                             -- ID BOE formato BOE-A-YYYY-XXXXX

    -- Información básica
    title TEXT NOT NULL,
    department VARCHAR,                         -- Organismo convocante
    purpose TEXT,                               -- Finalidad/objeto de la convocatoria

    -- Fechas
    publication_date TIMESTAMP,                 -- Fecha publicación BOE/BDNS
    application_start_date TIMESTAMP,           -- Inicio plazo solicitud
    application_end_date TIMESTAMP,             -- Fin plazo solicitud (DEADLINE)

    -- Presupuesto
    budget_amount NUMERIC(15, 2),               -- Presupuesto en €

    -- Clasificación
    is_nonprofit BOOLEAN DEFAULT false,         -- ¿Dirigida a nonprofit?
    nonprofit_confidence NUMERIC(3, 2),         -- Confianza 0.00 - 1.00
    beneficiary_types TEXT[],                   -- ["Asociaciones", "Fundaciones", ...]
    sectors TEXT[],                             -- ["Tecnología", "Medio ambiente", ...]
    regions TEXT[],                             -- ["Madrid", "Barcelona", "Nacional"]

    -- Estado
    is_open BOOLEAN DEFAULT true,               -- ¿Convocatoria abierta?

    -- N8n Integration
    sent_to_n8n BOOLEAN DEFAULT false,
    sent_to_n8n_at TIMESTAMP,

    -- URLs
    regulatory_base_url TEXT,                   -- URL bases reguladoras
    electronic_office TEXT,                     -- URL sede electrónica

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT unique_bdns_code UNIQUE (bdns_code),
    CONSTRAINT unique_boe_id UNIQUE (boe_id),
    CONSTRAINT valid_confidence CHECK (nonprofit_confidence >= 0 AND nonprofit_confidence <= 1),
    CONSTRAINT valid_dates CHECK (
        application_end_date IS NULL OR
        application_start_date IS NULL OR
        application_end_date >= application_start_date
    )
);

-- Indexes para performance
CREATE INDEX idx_grants_source ON grants(source);
CREATE INDEX idx_grants_created_at ON grants(created_at);
CREATE INDEX idx_grants_is_nonprofit ON grants(is_nonprofit);
CREATE INDEX idx_grants_is_open ON grants(is_open);
CREATE INDEX idx_grants_sent_to_n8n ON grants(sent_to_n8n);
CREATE INDEX idx_grants_application_end_date ON grants(application_end_date);
CREATE INDEX idx_grants_bdns_code ON grants(bdns_code);
CREATE INDEX idx_grants_boe_id ON grants(boe_id);

-- Full-text search (español)
CREATE INDEX idx_grants_search ON grants
USING GIN(to_tsvector('spanish', coalesce(title, '') || ' ' || coalesce(purpose, '')));
```

### Tabla: `webhook_history`

```sql
CREATE TABLE webhook_history (
    id SERIAL PRIMARY KEY,
    grant_id VARCHAR NOT NULL,                  -- UUID del grant
    attempt_number INTEGER DEFAULT 1,           -- Número de intento (1-3)
    max_retries INTEGER DEFAULT 3,
    status VARCHAR NOT NULL,                    -- 'pending' | 'success' | 'failed' | 'retrying'
    http_status_code INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP,
    next_retry_at TIMESTAMP,
    response_body JSONB,
    error_message TEXT,
    error_type VARCHAR,
    webhook_url TEXT NOT NULL,
    payload JSONB,
    response_time_ms FLOAT
);

CREATE INDEX idx_webhook_history_grant_id ON webhook_history(grant_id);
CREATE INDEX idx_webhook_history_created_at ON webhook_history(created_at);
CREATE INDEX idx_webhook_history_next_retry_at ON webhook_history(next_retry_at);
CREATE INDEX idx_webhook_history_status ON webhook_history(status);
```

---

## 📦 Schemas Pydantic

### Grant Schemas

```python
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class GrantBase(BaseModel):
    """Base schema con campos comunes"""
    source: str = Field(..., pattern="^(BDNS|BOE|MANUAL)$")
    title: str = Field(..., min_length=10, max_length=500)
    department: Optional[str] = None
    purpose: Optional[str] = None
    publication_date: Optional[datetime] = None
    application_start_date: Optional[datetime] = None
    application_end_date: Optional[datetime] = None
    budget_amount: Optional[float] = Field(None, ge=0)
    is_nonprofit: bool = False
    nonprofit_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    beneficiary_types: Optional[List[str]] = None
    sectors: Optional[List[str]] = None
    regions: Optional[List[str]] = None
    is_open: bool = True
    regulatory_base_url: Optional[str] = None
    electronic_office: Optional[str] = None

    @validator('application_end_date')
    def validate_dates(cls, v, values):
        if v and 'application_start_date' in values and values['application_start_date']:
            if v < values['application_start_date']:
                raise ValueError('application_end_date must be after application_start_date')
        return v

class GrantCreate(GrantBase):
    """Schema para creación"""
    pass

class GrantUpdate(BaseModel):
    """Schema para actualización (todos opcionales)"""
    title: Optional[str] = Field(None, min_length=10)
    department: Optional[str] = None
    purpose: Optional[str] = None
    budget_amount: Optional[float] = Field(None, ge=0)
    is_nonprofit: Optional[bool] = None
    nonprofit_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    beneficiary_types: Optional[List[str]] = None
    sectors: Optional[List[str]] = None
    regions: Optional[List[str]] = None
    is_open: Optional[bool] = None
    sent_to_n8n: Optional[bool] = None
    regulatory_base_url: Optional[str] = None
    electronic_office: Optional[str] = None

class GrantResponse(GrantBase):
    """Schema para respuesta"""
    id: UUID
    bdns_code: Optional[str] = None
    boe_id: Optional[str] = None
    sent_to_n8n: bool
    sent_to_n8n_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class GrantsListResponse(BaseModel):
    """Schema para lista paginada"""
    total: int
    grants: List[GrantResponse]
```

### Capture Schemas

```python
class BDNSCaptureRequest(BaseModel):
    days_back: int = Field(7, ge=1, le=365)
    max_results: int = Field(50, ge=1, le=1000)

class BOECaptureRequest(BaseModel):
    target_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    min_relevance: float = Field(0.3, ge=0.0, le=1.0)

    @validator('target_date')
    def validate_target_date(cls, v):
        from datetime import datetime
        try:
            date = datetime.fromisoformat(v)
            if date > datetime.now():
                raise ValueError('target_date cannot be in the future')
            return v
        except ValueError:
            raise ValueError('Invalid date format, use YYYY-MM-DD')

class CaptureResponse(BaseModel):
    success: bool
    message: str
    stats: dict
    processing_time_seconds: float
```

### Webhook Schemas

```python
class SendToN8nRequest(BaseModel):
    grant_ids: List[str] = Field(..., min_items=1)

    @validator('grant_ids')
    def validate_grant_ids(cls, v):
        from uuid import UUID
        for grant_id in v:
            try:
                UUID(grant_id)
            except ValueError:
                raise ValueError(f'Invalid UUID: {grant_id}')
        return v

class SendToN8nResponse(BaseModel):
    success: bool
    message: str
    results: dict
```

### Analytics Schemas

```python
class AnalyticsOverview(BaseModel):
    total_grants: int
    total_budget: float
    nonprofit_grants: int
    open_grants: int
    sent_to_n8n: int
    avg_confidence: float
    grants_by_source: List[dict]
    grants_by_date: List[dict]
    budget_distribution: List[dict]
    top_departments: List[dict]
```

---

## 🧠 Lógica de Negocio

### Cálculo de `is_nonprofit`

**Para BDNS:**
```python
def calculate_nonprofit_confidence(grant_data: dict) -> tuple[bool, float]:
    """
    Calcula si un grant es nonprofit basado en keywords

    Returns:
        (is_nonprofit, confidence_score)
    """
    NONPROFIT_KEYWORDS = [
        'sin ánimo de lucro', 'sin animo de lucro',
        'fundaciones', 'fundación',
        'asociaciones', 'asociación',
        'ong', 'ongs', 'organización no gubernamental',
        'tercer sector', 'economía social',
        'cooperativas', 'cooperativa',
        'entidades sin fines de lucro',
        'entidades no lucrativas'
    ]

    # Concatenar todos los textos relevantes
    text = ' '.join([
        grant_data.get('title', ''),
        grant_data.get('purpose', ''),
        ' '.join(grant_data.get('beneficiary_types', []))
    ]).lower()

    # Contar keywords encontradas
    found_keywords = sum(1 for kw in NONPROFIT_KEYWORDS if kw in text)

    # Calcular confidence
    confidence = min(found_keywords / 3.0, 1.0)  # 3+ keywords = 100% confidence

    # Si confidence >= 0.5, marcar como nonprofit
    is_nonprofit = confidence >= 0.5

    return is_nonprofit, round(confidence, 2)
```

**Para BOE:**
```python
def calculate_boe_relevance(document: dict) -> float:
    """
    Calcula relevance score para documento BOE

    Args:
        document: {
            'title': str,
            'summary': str,
            'section': str  # "I", "III", "V.A", "V.B"
        }

    Returns:
        float: Score 0.0 - 1.0
    """
    GRANT_KEYWORDS = [
        'subvención', 'subvenciones', 'ayuda', 'ayudas',
        'beca', 'becas', 'convocatoria', 'convocatorias',
        'fondos next generation', 'startup', 'pyme',
        # ... 30+ keywords
    ]

    SECTION_WEIGHTS = {
        'I': 1.2,
        'III': 1.0,
        'V.A': 1.1,
        'V.B': 1.0
    }

    # Concatenar título y sumario
    text = (document['title'] + ' ' + document.get('summary', '')).lower()

    # Contar keywords
    found_keywords = sum(1 for kw in GRANT_KEYWORDS if kw in text)

    # Calcular base score
    base_score = found_keywords / len(GRANT_KEYWORDS)

    # Aplicar peso de sección
    section_weight = SECTION_WEIGHTS.get(document['section'], 0.5)

    # Score final
    score = min(base_score * section_weight, 1.0)

    return round(score, 2)
```

### Cálculo de `is_open`

```python
def is_grant_open(grant: Grant) -> bool:
    """
    Determina si una convocatoria está abierta

    Rules:
    - Si no hay application_end_date: True (abierta indefinidamente)
    - Si application_end_date > now(): True
    - Si application_end_date <= now(): False
    """
    from datetime import datetime

    if not grant.application_end_date:
        return True

    return grant.application_end_date > datetime.now()
```

**Auto-update:** Ejecutar diariamente (cron job):
```python
# Actualizar estado de grants cerradas
db.execute(
    "UPDATE grants SET is_open = false "
    "WHERE application_end_date <= NOW() AND is_open = true"
)
```

---

## 🔗 Integración N8n

### Payload Formato

```python
def grant_to_n8n_payload(grant: Grant) -> dict:
    """
    Convierte Grant a formato N8n
    """
    return {
        "id": str(grant.id),
        "source": grant.source,
        "bdns_code": grant.bdns_code,
        "boe_id": grant.boe_id,

        # Información básica
        "title": grant.title,
        "department": grant.department,
        "purpose": grant.purpose,

        # Fechas
        "publication_date": grant.publication_date.isoformat() if grant.publication_date else None,
        "application_start_date": grant.application_start_date.isoformat() if grant.application_start_date else None,
        "application_end_date": grant.application_end_date.isoformat() if grant.application_end_date else None,

        # Presupuesto
        "budget_amount": float(grant.budget_amount) if grant.budget_amount else None,

        # Clasificación
        "is_nonprofit": grant.is_nonprofit,
        "nonprofit_confidence": float(grant.nonprofit_confidence) if grant.nonprofit_confidence else None,
        "beneficiary_types": grant.beneficiary_types or [],
        "sectors": grant.sectors or [],
        "regions": grant.regions or [],

        # Estado
        "is_open": grant.is_open,

        # URLs
        "regulatory_base_url": grant.regulatory_base_url,
        "electronic_office": grant.electronic_office,

        # Metadata
        "created_at": grant.created_at.isoformat(),

        # N8n puede usar este timestamp para tracking
        "sent_at": datetime.now().isoformat()
    }
```

### N8n Service Enhanced

```python
import asyncio
import httpx
from datetime import datetime, timedelta

class N8nServiceEnhanced:
    """
    Servicio N8n con retry logic y webhook history
    """

    def __init__(self, db: Session):
        self.db = db
        self.webhook_url = settings.n8n_webhook_url
        self.max_retries = 3
        self.base_delay = 2  # seconds
        self.max_delay = 60  # seconds

    def _calculate_retry_delay(self, attempt: int) -> int:
        """Exponential backoff: 2^(attempt-1) seconds"""
        delay = self.base_delay * (2 ** (attempt - 1))
        return min(delay, self.max_delay)

    def _calculate_next_retry_at(self, attempt: int) -> datetime:
        """Calculate next retry timestamp"""
        delay = self._calculate_retry_delay(attempt)
        return datetime.now() + timedelta(seconds=delay)

    async def send_grant_with_retry(
        self,
        grant_id: str,
        max_retries: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Send grant to N8n with retry logic

        Args:
            grant_id: Grant UUID
            max_retries: Override default max retries

        Returns:
            {
                "success": bool,
                "grant_id": str,
                "attempt": int,
                "status_code": int,
                "response_time_ms": float,
                "history_id": int,
                "error": str (if failed)
            }
        """
        max_retries = max_retries or self.max_retries
        grant = self.db.query(Grant).filter(Grant.id == grant_id).first()

        if not grant:
            return {"success": False, "error": f"Grant {grant_id} not found"}

        payload = grant_to_n8n_payload(grant)

        # Create webhook history record
        history = WebhookHistory(
            grant_id=grant_id,
            attempt_number=1,
            max_retries=max_retries,
            status='pending',
            webhook_url=self.webhook_url,
            payload=payload
        )
        self.db.add(history)
        self.db.commit()

        # Attempt sending with retries
        for attempt in range(1, max_retries + 1):
            try:
                start_time = time.time()

                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        self.webhook_url,
                        json=payload,
                        headers={"Content-Type": "application/json"}
                    )

                    response_time_ms = (time.time() - start_time) * 1000
                    response.raise_for_status()

                    # SUCCESS
                    grant.sent_to_n8n = True
                    grant.sent_to_n8n_at = datetime.now()
                    self.db.commit()

                    history.status = 'success'
                    history.http_status_code = response.status_code
                    history.sent_at = datetime.now()
                    history.response_body = response.json() if response.text else None
                    history.response_time_ms = response_time_ms
                    self.db.commit()

                    return {
                        "success": True,
                        "grant_id": grant_id,
                        "attempt": attempt,
                        "status_code": response.status_code,
                        "response_time_ms": response_time_ms,
                        "history_id": history.id
                    }

            except httpx.HTTPStatusError as e:
                # HTTP error (4xx, 5xx)
                history.attempt_number = attempt
                history.http_status_code = e.response.status_code
                history.error_message = str(e)
                history.error_type = 'http_status_error'

                # Retry on 5xx only
                if attempt < max_retries and e.response.status_code >= 500:
                    history.status = 'retrying'
                    history.next_retry_at = self._calculate_next_retry_at(attempt)
                    self.db.commit()

                    delay = self._calculate_retry_delay(attempt)
                    await asyncio.sleep(delay)
                else:
                    # 4xx or max retries
                    history.status = 'failed'
                    self.db.commit()

                    return {
                        "success": False,
                        "grant_id": grant_id,
                        "attempt": attempt,
                        "error": str(e),
                        "status_code": e.response.status_code,
                        "history_id": history.id
                    }

            except (httpx.RequestError, httpx.TimeoutException) as e:
                # Network error or timeout
                history.attempt_number = attempt
                history.error_message = str(e)
                history.error_type = type(e).__name__

                if attempt < max_retries:
                    history.status = 'retrying'
                    history.next_retry_at = self._calculate_next_retry_at(attempt)
                    self.db.commit()

                    delay = self._calculate_retry_delay(attempt)
                    await asyncio.sleep(delay)
                else:
                    history.status = 'failed'
                    self.db.commit()

                    return {
                        "success": False,
                        "grant_id": grant_id,
                        "attempt": attempt,
                        "error": str(e),
                        "history_id": history.id
                    }

        # Should not reach here
        return {
            "success": False,
            "grant_id": grant_id,
            "error": "Max retries exceeded"
        }
```

---

## 🗄️ Base de Datos

### Configuración

**PostgreSQL Connection:**
```python
# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql://user:password@localhost:5433/subvenciones_db"
    n8n_webhook_url: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
```

**.env:**
```bash
DATABASE_URL=postgresql://franco:password@localhost:5433/subvenciones_db
N8N_WEBHOOK_URL=https://franco-n8n.app.n8n.cloud/webhook/YOUR_WEBHOOK_ID
```

### Migraciones

**Crear tabla grants:**
```python
# app/migrations/create_grants_table.py
from sqlalchemy import create_engine, text
from app.config import settings

def run_migration():
    engine = create_engine(settings.database_url)

    with engine.connect() as conn:
        # Check if table exists
        result = conn.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name='grants'
        """))

        if result.fetchone() is None:
            # Create table (SQL from modelo de datos section)
            conn.execute(text("""
                CREATE TABLE grants (
                    -- [Full SQL here]
                );

                -- Create indexes
                CREATE INDEX idx_grants_source ON grants(source);
                -- [All indexes]
            """))

            conn.commit()
            print("✅ grants table created")
        else:
            print("⚠️  grants table already exists")

if __name__ == "__main__":
    run_migration()
```

**Agregar boe_id column:**
```python
# app/migrations/add_boe_id.py
def run_migration():
    conn.execute(text("ALTER TABLE grants ADD COLUMN boe_id VARCHAR"))
    conn.execute(text("CREATE UNIQUE INDEX idx_grants_boe_id ON grants(boe_id)"))
    conn.commit()
```

### Full-Text Search (Español)

```sql
-- Crear índice GIN para búsqueda full-text
CREATE INDEX idx_grants_search ON grants
USING GIN(to_tsvector('spanish', coalesce(title, '') || ' ' || coalesce(purpose, '')));

-- Query de ejemplo
SELECT * FROM grants
WHERE to_tsvector('spanish', coalesce(title, '') || ' ' || coalesce(purpose, ''))
      @@ to_tsquery('spanish', 'innovación & tecnología');
```

**En SQLAlchemy:**
```python
from sqlalchemy import func

# Search query
search_term = "innovación tecnología"
query = db.query(Grant).filter(
    func.to_tsvector('spanish',
        func.coalesce(Grant.title, '') + ' ' + func.coalesce(Grant.purpose, '')
    ).op('@@')(
        func.to_tsquery('spanish', search_term)
    )
)
```

---

## ✅ Testing

### Casos de Prueba Críticos

**1. Crear Grant:**
```bash
curl -X POST http://localhost:8000/api/v1/grants \
  -H "Content-Type: application/json" \
  -d '{
    "source": "MANUAL",
    "title": "Test Grant - Ayudas a asociaciones",
    "department": "Test Department",
    "budget_amount": 50000,
    "is_nonprofit": true,
    "beneficiary_types": ["Asociaciones"]
  }'
```

**2. Listar Grants con Filtros:**
```bash
curl "http://localhost:8000/api/v1/grants?is_nonprofit=true&budget_min=10000&budget_max=100000&limit=20"
```

**3. Capturar BDNS:**
```bash
curl -X POST http://localhost:8000/api/v1/capture/bdns \
  -H "Content-Type: application/json" \
  -d '{"days_back": 7, "max_results": 20}'
```

**4. Capturar BOE:**
```bash
curl -X POST http://localhost:8000/api/v1/capture/boe \
  -H "Content-Type: application/json" \
  -d '{"target_date": "2025-01-20", "min_relevance": 0.3}'
```

**5. Enviar a N8n:**
```bash
curl -X POST http://localhost:8000/api/v1/webhook/send \
  -H "Content-Type: application/json" \
  -d '{"grant_ids": ["550e8400-e29b-41d4-a716-446655440000"]}'
```

**6. Analytics:**
```bash
curl "http://localhost:8000/api/v1/analytics/overview?days=30"
```

### Datos de Prueba

```python
# app/tests/fixtures.py
import pytest
from app.models import Grant
from uuid import uuid4

@pytest.fixture
def sample_grant(db):
    grant = Grant(
        id=uuid4(),
        source="BDNS",
        title="Subvención de Prueba para Asociaciones",
        department="Ministerio de Pruebas",
        bdns_code="TEST123",
        budget_amount=75000.00,
        is_nonprofit=True,
        nonprofit_confidence=0.90,
        beneficiary_types=["Asociaciones", "Fundaciones"],
        sectors=["Social", "Tecnología"],
        regions=["Nacional"],
        is_open=True
    )
    db.add(grant)
    db.commit()
    return grant
```

---

## 📚 Ejemplos de Uso

### Frontend Integration

**Listar Grants con Filtros:**
```typescript
const loadGrants = async (filters: FilterValues) => {
  const params = new URLSearchParams()
  params.append('is_nonprofit', 'true')
  params.append('limit', '100')

  if (filters.search) params.append('search', filters.search)
  if (filters.department) params.append('department', filters.department)
  if (filters.dateFrom) params.append('date_from', filters.dateFrom)
  if (filters.dateTo) params.append('date_to', filters.dateTo)
  if (filters.budgetMin) params.append('budget_min', filters.budgetMin)
  if (filters.budgetMax) params.append('budget_max', filters.budgetMax)
  if (filters.confidenceMin) {
    params.append('confidence_min', (parseFloat(filters.confidenceMin) / 100).toString())
  }
  if (filters.isOpen !== 'all') params.append('is_open', filters.isOpen)
  if (filters.sentToN8n !== 'all') params.append('sent_to_n8n', filters.sentToN8n)

  const response = await fetch(`/api/v1/grants?${params.toString()}`)
  const data = await response.json()
  return data.grants
}
```

**Enviar a N8n:**
```typescript
const sendToN8n = async (grantIds: string[]) => {
  const response = await fetch('/api/v1/webhook/send', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ grant_ids: grantIds })
  })

  if (response.status === 503) {
    const error = await response.json()
    alert(`N8n no configurado: ${error.detail}`)
    return
  }

  if (!response.ok) {
    throw new Error('Error enviando a N8n')
  }

  return await response.json()
}
```

---

## 🚀 Deployment Checklist

### Pre-Producción
- [ ] Variables de entorno configuradas (.env)
- [ ] PostgreSQL 15+ instalado (puerto 5433)
- [ ] Migraciones ejecutadas
- [ ] Indexes creados
- [ ] N8N_WEBHOOK_URL configurado y validado
- [ ] BDNS API key configurada (si requerida)
- [ ] Tests end-to-end pasando

### Configuración Producción
```bash
# .env production
DATABASE_URL=postgresql://user:secure_password@db.example.com:5432/subvenciones_prod
N8N_WEBHOOK_URL=https://production-n8n.app.n8n.cloud/webhook/SECURE_ID
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### Monitoring
- [ ] Logs configurados (INFO level mínimo)
- [ ] Webhook history monitoreado diariamente
- [ ] Alertas configuradas para:
  - Webhook delivery failures > 10%
  - Database connection errors
  - API response time > 2s
  - Capture errors

### Cronjobs Recomendados
```bash
# Captura diaria BDNS (lunes a viernes 8:00 AM)
0 8 * * 1-5 curl -X POST http://localhost:8000/api/v1/capture/bdns -H "Content-Type: application/json" -d '{"days_back": 1, "max_results": 100}'

# Captura diaria BOE (lunes a viernes 9:00 AM)
0 9 * * 1-5 curl -X POST http://localhost:8000/api/v1/capture/boe -H "Content-Type: application/json" -d '{"target_date": "$(date +%Y-%m-%d)", "min_relevance": 0.3}'

# Reintentar webhooks fallidos (cada 6 horas)
0 */6 * * * curl -X POST http://localhost:8000/api/v1/webhook/resend-failed?limit=20

# Actualizar estado is_open (diario a medianoche)
0 0 * * * psql -d subvenciones_prod -c "UPDATE grants SET is_open = false WHERE application_end_date <= NOW() AND is_open = true"
```

---

## 📖 Referencias

### APIs Externas
- **BDNS API:** https://www.infosubvenciones.es/bdnstrans/doc/swagger
- **BOE API:** https://www.boe.es/datosabiertos/
- **N8n Webhooks:** https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.webhook/

### Documentación Técnica
- FastAPI: https://fastapi.tiangolo.com/
- SQLAlchemy 2.0: https://docs.sqlalchemy.org/
- Pydantic: https://docs.pydantic.dev/
- PostgreSQL Full-Text Search: https://www.postgresql.org/docs/current/textsearch.html

---

## ✉️ Contacto y Soporte

**Desarrollador Frontend:** Franco
**Especificación creada:** 2025-10-18
**Versión Backend Requerida:** Python 3.13+, FastAPI 0.104+, PostgreSQL 15+

---

**Notas Finales:**
1. Todos los endpoints deben incluir documentación OpenAPI automática (FastAPI)
2. CORS debe estar configurado para frontend en http://localhost:3000
3. Rate limiting recomendado: 100 requests/minuto por IP
4. Logs deben incluir request_id para tracking
5. Respuestas deben incluir headers CORS apropiados
6. Validación de input debe ser exhaustiva (Pydantic)
7. Transacciones DB deben usar rollback en caso de error
8. N8n webhook debe tener timeout de 30 segundos
9. Webhook history debe limpiarse después de 90 días (opcional)
10. Full-text search debe usar configuración 'spanish' de PostgreSQL

---

**Estado del Proyecto:**
- ✅ Frontend completamente implementado (React + TypeScript)
- ⏳ Backend en desarrollo (esta especificación)
- ✅ Database schema definido
- ✅ N8n workflow configurado
- ⏳ Testing pendiente
- ⏳ Deploy a producción pendiente

---

*Esta especificación cubre el 100% de la funcionalidad implementada en el frontend y proporciona todos los detalles necesarios para que un desarrollador backend implemente el sistema completo sin ambigüedades.*
