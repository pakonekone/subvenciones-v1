# Documentación Técnica: Integración PLACSP

## Visión General
Este documento detalla la implementación de la integración con la Plataforma de Contratación del Sector Público (PLACSP) para la captura y gestión de licitaciones. El sistema consume el feed Atom de licitaciones, extrae información relevante, aplica filtros configurables y presenta los datos en la interfaz de usuario.

## Arquitectura

### 1. Ingesta de Datos (Backend)
*   **Fuente**: Feed Atom de PLACSP (`https://contrataciondelestado.es/sindicacion/...`).
*   **Parser**: `CODICEParser` (`backend/app/shared/codice_parser.py`)
    *   Parsea XML/Atom utilizando `xml.etree.ElementTree`.
    *   Maneja namespaces complejos de CODICE y Atom.
    *   Extrae metadatos clave: Título, Importe, CPV, Enlaces (PDF y HTML), Fechas.
    *   **Mejora Clave**: Extracción robusta de `html_url` buscando directamente etiquetas `atom:link`.

*   **Servicio**: `PLACSPService` (`backend/app/services/placsp_service.py`)
    *   Orquesta la descarga y procesado de páginas del feed.
    *   Gestiona la paginación (detectando enlaces 'next').
    *   Implementa lógica de "Días hacia atrás" (`days_back`) para capturas incrementales.
    *   Persiste los datos en la base de datos PostgreSQL.

### 2. Sistema de Filtrado
*   **Motor**: `GrantFilter` (`backend/app/shared/filters.py`)
    *   Sistema basado en perfiles y reglas (Include, Exclude, Regex).
    *   **Persistencia**: Los perfiles se guardan en `filter_profiles.json`.
    *   **Perfil PLACSP**: Perfil específico `test_placsp` que filtra por palabras clave en título y resumen.
*   **API**:
    *   `GET /api/v1/filters/placsp`: Recupera keywords actuales.
    *   `POST /api/v1/filters/placsp`: Actualiza y guarda keywords en disco.

### 3. Modelo de Datos
La entidad `Grant` (`backend/app/models/grant.py`) se ha extendido con campos específicos:
*   `source`: "PLACSP"
*   `placsp_folder_id`: Identificador del expediente.
*   `html_url`: Enlace a la publicación oficial en la web de PLACSP.
*   `pdf_url`: Enlace directo a los pliegos (si disponible).
*   `contract_type`: Tipo de contrato (Suministros, Servicios, etc.).
*   `cpv_codes`: Lista de códigos CPV.

### 4. Frontend (React)
*   **Configuración de Captura**: `CaptureConfigDialog.tsx`
    *   Adaptado para mostrar opciones específicas de PLACSP cuando se selecciona esa fuente.
    *   Muestra resumen de filtros activos.
*   **Gestión de Filtros**: `FilterKeywordsManager.tsx`
    *   Nueva pestaña "PLACSP" para añadir/eliminar palabras clave.
    *   Conectado a la API para persistencia real.
*   **Visualización**: `GrantDetailDrawer.tsx`
    *   Botón "Ver Publicación Oficial (PLACSP)" usando `html_url`.
    *   Visualización de campos específicos (CPV, Tipo de contrato).

## Flujos Principales

### Captura de Licitaciones
1.  Usuario inicia captura desde UI seleccionando "PLACSP".
2.  Backend (`capture_placsp.py` / `PLACSPService`) descarga el feed Atom.
3.  Se iteran las entradas y se parsean con `CODICEParser`.
4.  Se aplica `GrantFilter` con el perfil `test_placsp`.
5.  Si pasa el filtro, se guarda/actualiza en la BD (`Grant`).
6.  Se actualiza el campo `html_url` para asegurar acceso a la fuente original.

### Edición de Filtros
1.  Usuario abre "Configuración de Captura" -> "Ver/Editar".
2.  Frontend carga keywords desde `GET /api/v1/filters/placsp`.
3.  Usuario modifica la lista y guarda.
4.  Frontend envía `POST /api/v1/filters/placsp`.
5.  Backend actualiza el objeto `GrantFilter` en memoria y sobrescribe `filter_profiles.json`.

## Archivos Clave
*   `backend/app/services/placsp_service.py`: Lógica de negocio principal.
*   `backend/app/shared/codice_parser.py`: Parser XML especializado.
*   `backend/app/shared/filters.py`: Motor de filtros y persistencia.
*   `backend/app/api/v1/filters.py`: Endpoints de gestión de filtros.
*   `frontend/src/components/CaptureConfigDialog.tsx`: UI de configuración.
