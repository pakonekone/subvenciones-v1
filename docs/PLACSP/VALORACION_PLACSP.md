# Evaluación Técnica: Integración de PLACSP (Plataforma de Contratación del Sector Público)

## 1. Resumen Ejecutivo
La integración de la PLACSP es **totalmente viable** y encaja con la arquitectura actual del sistema. A diferencia de BDNS (API REST) y BOE (Scraping/API + PDF), PLACSP utiliza un estándar de sindicación (**Atom Feeds**) con un formato de datos estructurado (**CODICE XML**).

Esto permitirá una captura de datos más robusta y estructurada que el BOE, pero requiere una lógica de parseo XML más compleja debido a la profundidad del estándar CODICE.

## 2. Análisis de la Fuente (PLACSP)

### Mecanismo de Acceso
- **Protocolo**: Atom Syndication Format (RFC 4287).
- **Endpoint**: URLs de feeds públicos (ej. Licitaciones, Contratos Menores).
- **Paginación**: Enlaces `first`, `last`, `next`, `prev` (RFC 5005). Esto facilita recorrer el histórico.
- **Actualizaciones**: Incremental. Se debe rastrear el timestamp `updated` para capturar solo lo nuevo.

### Formato de Datos
- **Estándar**: XML siguiendo esquemas CODICE.
- **Riqueza de Datos**: Muy alta. Incluye:
  - Presupuesto base y valor estimado.
  - CPV (Common Procurement Vocabulary).
  - Fechas clave (presentación ofertas, apertura plicas).
  - Ubicación de ejecución (NUTS).
  - Criterios de adjudicación.
  - Enlaces a pliegos (PDFs).

## 3. Estrategia de Integración

### Arquitectura Backend
Se propone seguir el patrón de diseño existente (Service + Client), añadiendo un módulo específico para XML complejo.

1.  **`PLACSPClient` (`app/shared/placsp_client.py`)**:
    - Manejo de la navegación de feeds Atom (paginación).
    - Descarga de XMLs.
    - Detección de entradas eliminadas (`<at:deleted-entry>`).

2.  **`CODICEParser` (`app/shared/codice_parser.py`)**:
    - **Nuevo componente crítico**.
    - Responsable de traducir el XML complejo de CODICE a nuestro modelo plano de `Grant`.
    - Mapeo de campos:
        - `Grant.budget_amount` <- `Importe base`
        - `Grant.application_end_date` <- `Fecha fin presentación ofertas`
        - `Grant.regions` <- `Lugar de ejecución`

3.  **`PLACSPService` (`app/services/placsp_service.py`)**:
    - Orquestador similar a `BDNSService`.
    - Lógica de "Captura Incremental": Guardar la última fecha de actualización procesada para no re-leer todo el feed.
    - Filtrado: Aplicar los mismos filtros de keywords (Nonprofit) sobre el `Objeto del Contrato` y `Descripción`.

### Impacto en Base de Datos (`Grant` Model)
El modelo actual `Grant` es muy versátil, pero las Licitaciones (Tenders) tienen matices diferentes a las Subvenciones.

**Cambios sugeridos:**
- **Nuevo Source**: `source = "PLACSP"`.
- **Nuevos Campos (Opcionales pero recomendados)**:
    - `cpv_codes`: Array de strings (para códigos CPV).
    - `contract_type`: "Servicios", "Suministros", "Obras" (mapeado a `convocatoria_type`).
    - `tender_value_estimated`: Valor estimado del contrato (a veces difiere del presupuesto base).

### Impacto en Frontend
- **Capture Dialog**: Nueva pestaña "PLACSP" o "Licitaciones".
- **Filtros**: Añadir selectores para "Tipo de Contrato" (Obras, Servicios, etc.) si se decide extraer ese dato.

## 4. Retos y Consideraciones
1.  **Volumen de Datos**: Los feeds de PLACSP pueden ser muy voluminosos. La estrategia de "solo nuevos" es crítica.
2.  **Complejidad XML**: El esquema CODICE tiene muchas variantes. Se recomienda empezar mapeando los campos core (Título, Importe, Fechas, PDF) e iterar.
3.  **Diferencia Semántica**: Una "Licitación" no es exactamente una "Subvención".
    - *Mitigación*: El sistema ya filtra por "Nonprofit". Muchas licitaciones del tercer sector (servicios sociales, gestión de centros) son de interés y encajan en el modelo de negocio.

## 5. Plan de Trabajo Detallado

### Fase 1: Core Backend (Cliente y Parser)
**Objetivo**: Capacidad de descargar y entender los datos de PLACSP.

1.  **Dependencias**:
    - Verificar librerías para XML (probablemente `lxml` o `xml.etree.ElementTree` ya incluidas en Python o `feedparser` si facilita Atom).
2.  **Implementar `PLACSPClient`**:
    - Método `fetch_feed(url)`: Descarga el Atom feed.
    - Método `get_next_page(feed)`: Extrae el enlace "next" para paginación.
    - Método `download_entry_xml(link)`: Descarga el XML específico de una licitación (si no viene embebido completo).
3.  **Implementar `CODICEParser`**:
    - Crear clase para parsear el XML de CODICE.
    - Mapeo inicial de campos clave:
        - `id` (Identificador licitación)
        - `title` (Objeto del contrato)
        - `budget_amount` (Valor estimado / Presupuesto base)
        - `application_end_date` (Fecha fin presentación)
        - `pdf_url` (Link a pliegos)
        - `cpv` (Códigos CPV - opcional en v1)
        - `place` (Lugar de ejecución - opcional en v1)

### Fase 2: Servicio y Persistencia
**Objetivo**: Integrar los datos en el sistema existente.

1.  **Actualizar Modelo `Grant`**:
    - Confirmar si se necesitan campos nuevos o se reutilizan los existentes (ej. `bdns_code` vs `source_id`).
    - Decisión: Usar `id` como identificador único (ej. "PLACSP-12345").
2.  **Implementar `PLACSPService`**:
    - Método `capture_recent(days_back)`:
        - Iterar feeds desde "ahora" hacia atrás hasta cubrir `days_back`.
        - Por cada entry:
            - Parsear XML.
            - **Filtrado**: Aplicar `check_nonprofit` (reutilizar lógica de `BDNSService` o `filters.py`).
            - Si es relevante -> Guardar/Actualizar en DB.
3.  **Endpoint API**:
    - Crear `POST /api/v1/capture/placsp`.
    - Parámetros: `days_back` (default 1), `max_pages` (seguridad).

### Fase 3: Frontend y Visualización
**Objetivo**: Que el usuario pueda lanzar la captura y ver resultados.

1.  **Actualizar `CaptureConfigDialog.tsx`**:
    - Añadir tab "PLACSP".
    - Configuración: "Días hacia atrás" (similar a BOE).
    - Botón "Iniciar Captura".
2.  **Verificación en Tabla**:
    - Asegurar que los grants de source "PLACSP" se renderizan bien en `GrantsTable`.
    - Verificar enlaces a PDFs y detalles.

### Fase 4: Testing y Refinamiento
1.  **Pruebas Unitarias**:
    - Testear parser con XMLs de ejemplo (descargar algunos manualmente).
2.  **Pruebas de Integración**:
    - Ejecutar captura real y verificar datos en BD.
3.  **Ajuste de Filtros**:
    - Revisar si los keywords actuales de nonprofit funcionan bien con los textos de PLACSP.
