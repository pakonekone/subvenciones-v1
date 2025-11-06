# Sistema de Subvenciones v1.0 - Arquitectura y Flujos

## Diagrama de Arquitectura General

```mermaid
graph TB
    subgraph "Frontend - React + Vite"
        UI[Interface de Usuario]
        GT[Tabla de Subvenciones]
        CD[Diálogo de Captura]
        FK[Gestor de Filtros]
        AN[Dashboard Analytics]
    end

    subgraph "Backend - FastAPI"
        subgraph "API Layer"
            API_G[/api/v1/grants]
            API_C[/api/v1/capture]
            API_W[/api/v1/webhook]
            API_F[/api/v1/filters]
            API_A[/api/v1/analytics]
        end

        subgraph "Service Layer"
            BDNS_S[BDNS Service]
            BOE_S[BOE Service]
            PDF_S[PDF Processor]
            N8N_S[N8n Service]
        end

        subgraph "Shared Modules"
            BDNS_API[BDNS API Client]
            BOE_API[BOE API Client]
            FILTERS[Filters & Keywords]
        end
    end

    subgraph "Database"
        PG[(PostgreSQL)]
    end

    subgraph "External APIs"
        BDNS_EXT[BDNS API<br/>Base Nacional]
        BOE_EXT[BOE API<br/>Boletín Oficial]
    end

    subgraph "Integration Layer"
        N8N[N8n Workflow<br/>AI Analysis]
        SHEETS[Google Sheets<br/>Export]
    end

    UI --> GT
    UI --> CD
    UI --> FK
    UI --> AN

    GT --> API_G
    CD --> API_C
    FK --> API_F
    AN --> API_A

    API_G --> PG
    API_C --> BDNS_S
    API_C --> BOE_S
    API_W --> PG
    API_F --> FILTERS
    API_A --> PG

    BDNS_S --> BDNS_API
    BDNS_S --> FILTERS
    BDNS_S --> PG

    BOE_S --> BOE_API
    BOE_S --> PDF_S
    BOE_S --> FILTERS
    BOE_S --> PG

    BDNS_API --> BDNS_EXT
    BOE_API --> BOE_EXT

    API_G --> N8N_S
    N8N_S --> N8N
    N8N --> API_W
    N8N --> SHEETS
    SHEETS --> API_W
```

## Flujo 1: Captura de Subvenciones BDNS

```mermaid
sequenceDiagram
    participant U as Usuario
    participant FE as Frontend
    participant API as FastAPI
    participant BDNS_S as BDNS Service
    participant BDNS_API as BDNS API Client
    participant BDNS_EXT as BDNS Externa
    participant FILTERS as Filtros
    participant DB as PostgreSQL

    U->>FE: Configura captura (rango fechas)
    FE->>FE: Muestra preview de filtros<br/>(11 keywords nonprofit)
    U->>FE: Inicia captura
    FE->>API: POST /api/v1/capture/bdns<br/>{fecha_desde, fecha_hasta, max_results}
    API->>BDNS_S: capture_by_date_range()

    BDNS_S->>BDNS_API: search_grants(fecha, fecha, max)
    BDNS_API->>BDNS_EXT: GET /ayudas<br/>fechaDesde=dd/MM/yyyy
    BDNS_EXT-->>BDNS_API: Lista de convocatorias
    BDNS_API-->>BDNS_S: Grants JSON

    loop Para cada grant
        BDNS_S->>BDNS_API: get_grant_detail(id_convocatoria)
        BDNS_API->>BDNS_EXT: GET /ayudas/{id}
        BDNS_EXT-->>BDNS_API: Detalles completos
        BDNS_API-->>BDNS_S: Grant detallado

        BDNS_S->>FILTERS: apply_nonprofit_filters()
        FILTERS-->>BDNS_S: is_nonprofit, confidence

        BDNS_S->>DB: INSERT grant<br/>(source='BDNS')
    end

    BDNS_S-->>API: {captured: N, filtered: M}
    API-->>FE: Resultado captura
    FE-->>U: "N subvenciones capturadas"
```

## Flujo 2: Captura de Subvenciones BOE

```mermaid
sequenceDiagram
    participant U as Usuario
    participant FE as Frontend
    participant API as FastAPI
    participant BOE_S as BOE Service
    participant BOE_API as BOE API Client
    participant BOE_EXT as BOE Externa
    participant PDF_S as PDF Processor
    participant FILTERS as Filtros
    participant DB as PostgreSQL

    U->>FE: Configura captura BOE<br/>(días hacia atrás)
    FE->>FE: Preview filtros<br/>(44 keywords + nonprofit)
    U->>FE: Inicia captura
    FE->>API: POST /api/v1/capture/boe<br/>{days_back, max_results}
    API->>BOE_S: capture_recent_grants()

    BOE_S->>BOE_API: search_boe_grants(days_back)
    BOE_API->>BOE_EXT: Búsqueda por keywords
    BOE_EXT-->>BOE_API: Resultados BOE
    BOE_API-->>BOE_S: Lista grants

    loop Para cada grant con PDF
        BOE_S->>BOE_API: get_pdf_url(id)
        BOE_API-->>BOE_S: PDF URL

        BOE_S->>PDF_S: extract_text_from_pdf(url)
        PDF_S->>BOE_EXT: Download PDF
        BOE_EXT-->>PDF_S: PDF bytes
        PDF_S->>PDF_S: Extract text<br/>(pdfplumber)
        PDF_S-->>BOE_S: Texto extraído

        BOE_S->>FILTERS: calculate_relevance_score()
        FILTERS-->>BOE_S: relevance_score (0-1)
        Note over BOE_S: Score es informativo<br/>NO filtra grants

        BOE_S->>FILTERS: apply_nonprofit_filters()
        FILTERS-->>BOE_S: is_nonprofit, confidence

        BOE_S->>DB: INSERT grant<br/>(source='BOE')
    end

    BOE_S-->>API: {captured: N, processed_pdfs: M}
    API-->>FE: Resultado captura
    FE-->>U: "N subvenciones BOE capturadas"
```

## Flujo 3: Consulta y Filtrado de Subvenciones

```mermaid
sequenceDiagram
    participant U as Usuario
    participant FE as Frontend
    participant API as FastAPI
    participant DB as PostgreSQL

    U->>FE: Abre página de subvenciones
    FE->>API: GET /api/v1/grants?skip=0&limit=50
    API->>DB: SELECT * FROM grants<br/>ORDER BY created_at DESC
    DB-->>API: Lista grants
    API-->>FE: {items: [...], total: N}
    FE-->>U: Tabla con subvenciones

    U->>FE: Aplica filtros avanzados<br/>(budget, dates, regions, sectors)
    FE->>API: GET /api/v1/grants?<br/>min_budget=10000&<br/>regions=["Madrid"]&<br/>start_date_from=2025-01-01
    API->>DB: SELECT con WHERE clauses<br/>+ JSON operators
    DB-->>API: Grants filtrados
    API-->>FE: Resultados filtrados
    FE-->>U: Tabla actualizada

    U->>FE: Ordena por presupuesto
    FE->>FE: Sort local (ya tiene datos)
    FE-->>U: Tabla reordenada

    U->>FE: Click en grant
    FE->>FE: Abre GrantDetailDrawer
    FE-->>U: Panel detalle completo
```

## Flujo 4: Integración N8n y Google Sheets (Bidireccional)

```mermaid
sequenceDiagram
    participant U as Usuario
    participant FE as Frontend
    participant API as FastAPI
    participant DB as PostgreSQL
    participant N8N as N8n Workflow
    participant AI as AI Analysis
    participant SHEETS as Google Sheets

    U->>FE: Selecciona grants
    U->>FE: Click "Enviar a N8n"
    FE->>API: POST /api/v1/webhook/send<br/>{grant_ids: [1,2,3]}

    loop Para cada grant
        API->>DB: SELECT grant WHERE id=X
        DB-->>API: Grant data
        API->>N8N: POST webhook<br/>{grant JSON}

        N8N->>AI: Analyze grant
        AI-->>N8N: {priority, strategic_value}

        N8N->>API: POST /api/v1/webhook/callback<br/>{grant_id, priority, value}
        API->>DB: UPDATE grant<br/>SET priority=X, strategic_value=Y
        DB-->>API: Updated
        API-->>N8N: 200 OK

        N8N->>SHEETS: Add row to sheet
        SHEETS-->>N8N: {row_id, sheets_url}

        N8N->>API: POST /api/v1/webhook/callback/sheets<br/>{grant_id, status, sheets_url, row_id}
        API->>DB: UPDATE grant<br/>SET google_sheets_exported=true,<br/>google_sheets_url=...,<br/>google_sheets_exported_at=NOW()
        DB-->>API: Updated
        API-->>N8N: 200 OK
    end

    API-->>FE: {processed: 3}
    FE-->>U: "3 subvenciones enviadas"

    Note over FE: Frontend polling cada 30s
    FE->>API: GET /api/v1/grants (refresh)
    API->>DB: SELECT grants
    DB-->>API: Grants actualizados
    API-->>FE: Grants con estados
    FE-->>U: Iconos actualizados:<br/>✅ Exportado + link<br/>⏳ Procesando<br/>➖ No enviado
```

## Flujo 5: Gestión Transparente de Filtros

```mermaid
sequenceDiagram
    participant U as Usuario
    participant FE as Frontend
    participant API as FastAPI
    participant FILTERS as Filters Module

    U->>FE: Click "Ver Filtros"
    FE->>API: GET /api/v1/filters/summary
    API->>FILTERS: get_all_keywords()
    FILTERS-->>API: {bdns: [...], boe_grants: [...], boe_nonprofit: [...]}
    API-->>FE: Filter summary + counts

    FE->>FE: Abre FilterKeywordsManager
    FE-->>U: Modal con 3 tabs:<br/>- BDNS Nonprofit (11)<br/>- BOE Grants (44)<br/>- BOE Nonprofit

    U->>FE: Tab "BDNS Nonprofit"
    FE->>API: GET /api/v1/filters/bdns
    API->>FILTERS: get_bdns_nonprofit_keywords()
    FILTERS-->>API: 11 keywords
    API-->>FE: Keywords list
    FE-->>U: Lista editable

    U->>FE: Tab "BOE Grants"
    FE->>API: GET /api/v1/filters/boe
    API->>FILTERS: get_boe_grant_keywords() +<br/>get_nonprofit_keywords()
    FILTERS-->>API: 44 grant + nonprofit keywords
    API-->>FE: Combined list
    FE-->>U: Keywords agrupados

    Note over U,FE: Antes de capturar
    U->>FE: Abre diálogo captura
    FE->>API: GET /api/v1/filters/summary
    API-->>FE: Active filters
    FE-->>U: Preview: "Se usarán 11 keywords<br/>para filtrar organizaciones"
```

## Modelo de Datos: Grant

```mermaid
erDiagram
    GRANT {
        int id PK
        string source "BDNS|BOE"
        string title
        text description
        string department
        datetime publication_date
        datetime application_start_date
        datetime application_end_date
        float total_budget
        string currency
        jsonb beneficiary_types
        jsonb sectors
        jsonb regions
        boolean is_nonprofit
        float nonprofit_confidence
        string priority "null|high|medium|low"
        float strategic_value
        text pdf_url
        text pdf_content
        text pdf_markdown
        float relevance_score
        boolean google_sheets_exported
        datetime google_sheets_exported_at
        string google_sheets_row_id
        text google_sheets_url
        datetime created_at
        datetime updated_at
    }
```

## Componentes Clave del Sistema

### Backend Services

1. **BDNS Service** (`bdns_service.py`)
   - Captura por rango de fechas
   - Filtrado automático por keywords nonprofit
   - Conversión formato fechas (ISO → dd/MM/yyyy)
   - Límites: 1-100 resultados por captura

2. **BOE Service** (`boe_service.py`)
   - Búsqueda por días hacia atrás
   - Procesamiento de PDFs
   - Cálculo de relevance_score (informativo)
   - Filtrado nonprofit + grant keywords

3. **PDF Processor** (`pdf_processor.py`)
   - Extracción con pdfplumber
   - Generación de markdown
   - Manejo de errores de encoding

4. **N8n Service** (`n8n_service.py` / `n8n_service_enhanced.py`)
   - Envío webhook básico
   - Versión mejorada: queue + retry + tracking

### Frontend Components

1. **GrantsTable** (`GrantsTable.tsx`)
   - Tabla con sorting local
   - Columnas: título, fuente, presupuesto, fechas, nonprofit, exportado
   - Selección múltiple para acciones batch
   - Indicadores visuales de estado de export

2. **CaptureConfigDialog** (`CaptureConfigDialog.tsx`)
   - Tabs para BDNS/BOE
   - BDNS: date pickers (from/to)
   - BOE: días hacia atrás
   - Preview de filtros activos

3. **FilterKeywordsManager** (`FilterKeywordsManager.tsx`)
   - 3 tabs: BDNS Nonprofit, BOE Grants, BOE Nonprofit
   - Vista de keywords activos
   - Edición futura

4. **GrantDetailDrawer** (`GrantDetailDrawer.tsx`)
   - Panel lateral con metadata completa
   - Visualización de análisis N8n
   - Links a PDFs y Google Sheets

### Shared Modules

1. **Filters** (`shared/filters.py`)
   - 11 keywords BDNS nonprofit
   - 44 keywords BOE grants
   - Lógica de matching case-insensitive
   - Cálculo de confidence scores

2. **BDNS API Client** (`shared/bdns_api.py`)
   - Wrapper de API BDNS
   - Búsqueda y detalle
   - Conversión de modelos Pydantic

3. **BOE API Client** (`shared/boe_api.py`)
   - Búsqueda en BOE
   - Descarga de PDFs
   - Parsing de XML/JSON

## Decisiones Arquitectónicas Clave

1. **Relevance Score es Informativo**: No filtra grants, solo informa al usuario
2. **Puerto PostgreSQL 5433**: Evita conflictos con otras instancias
3. **Filtros Transparentes**: Usuario ve y entiende qué criterios se aplican
4. **Webhooks Bidireccionales**: N8n → Backend (análisis) y N8n → Backend (export confirmación)
5. **Service Layer Pattern**: Lógica de negocio separada de API endpoints
6. **Vite Proxy**: Frontend y backend en puertos distintos con proxy transparente

## Próximos Pasos Sugeridos

1. Implementar export a Excel con cálculo de plazos
2. Permitir edición de keywords desde UI
3. Integrar notificaciones de nuevas subvenciones
4. Dashboard de analytics mejorado
5. Sistema de alertas personalizadas
