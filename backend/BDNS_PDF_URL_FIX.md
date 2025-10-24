# ✅ BDNS PDF URL Capture Fix

## 🔍 Problema Identificado

Los grants de BDNS **NO estaban capturando las URLs de los PDFs**, solo se guardaba `regulatory_base_url` (bases reguladoras).

**Impacto**:
- No se podía acceder al PDF del extracto publicado en el BOE
- Faltaba información importante en el payload enviado a N8n
- El workflow de Google Sheets no tenía el link al PDF principal

## ❌ Antes (Incompleto)

```python
grant = Grant(
    # ... otros campos
    regulatory_base_url=detail.urlBasesReguladoras,  # Solo bases reguladoras
    # ❌ pdf_url = None
    # ❌ html_url = None
)
```

**Resultado**: `pdf_url` y `html_url` quedaban como `null` en la base de datos.

## ✅ Solución Implementada

### 1. Extracción de URLs desde `anuncios`

La API de BDNS incluye un campo `anuncios` que contiene información sobre las publicaciones en el BOE:

```python
# Extract PDF URL from announcements (anuncios)
pdf_url = None
html_url = None
if detail.anuncios and len(detail.anuncios) > 0:
    # Get the first announcement's URL (usually the BOE PDF)
    first_announcement = detail.anuncios[0]
    if first_announcement.url:
        pdf_url = first_announcement.url
        # Also try to construct HTML version
        if 'boe.es' in first_announcement.url and 'pdf' in first_announcement.url.lower():
            # Convert PDF URL to HTML URL
            # e.g., https://boe.es/boe/dias/2024/01/15/pdfs/BOE-A-2024-12345.pdf
            # to: https://boe.es/diario_boe/txt.php?id=BOE-A-2024-12345
            if first_announcement.cve:
                html_url = f"https://boe.es/diario_boe/txt.php?id={first_announcement.cve}"

logger.debug(f"   PDF URL: {pdf_url}")
logger.debug(f"   HTML URL: {html_url}")
```

### 2. Guardado en el Grant

```python
grant = Grant(
    # ... otros campos
    pdf_url=pdf_url,  # ✅ URL del PDF del BOE
    html_url=html_url,  # ✅ URL HTML del BOE
    regulatory_base_url=detail.urlBasesReguladoras,  # Bases reguladoras
    electronic_office=detail.sedeElectronica,  # Sede electrónica
)
```

### 3. Aplicado en ambos métodos

- `_create_grant()`: Para nuevos grants
- `_update_grant()`: Para grants existentes

## 📊 Estructura de datos BDNS

**`anuncios`** (Lista de BDNSAnnouncement):
```json
{
  "anuncios": [
    {
      "numAnuncio": 123456,
      "titulo": "EXTRACTO DE LA CONVOCATORIA...",
      "url": "https://boe.es/boe/dias/2024/01/15/pdfs/BOE-A-2024-12345.pdf",
      "cve": "BOE-A-2024-12345",
      "desDiarioOficial": "BOE",
      "datPublicacion": "2024-01-15"
    }
  ]
}
```

## 🎯 Resultado Esperado

Ahora cuando se captura un grant BDNS:

### Base de Datos
```sql
SELECT
  id,
  pdf_url,
  html_url,
  regulatory_base_url
FROM grants
WHERE source = 'BDNS'
LIMIT 1;
```

**Resultado**:
```
id: BDNS-863212
pdf_url: https://boe.es/boe/dias/2024/01/15/pdfs/BOE-A-2024-12345.pdf
html_url: https://boe.es/diario_boe/txt.php?id=BOE-A-2024-12345
regulatory_base_url: https://www.ejemplo.gob.es/bases-reguladoras.pdf
```

### Payload a N8n

```json
{
  "id": "BDNS-863212",
  "source": "BDNS",
  "pdf_url": "https://boe.es/boe/dias/2024/01/15/pdfs/BOE-A-2024-12345.pdf",
  "html_url": "https://boe.es/diario_boe/txt.php?id=BOE-A-2024-12345",
  "metadata": {
    "regulatory_base_url": "https://www.ejemplo.gob.es/bases-reguladoras.pdf",
    "electronic_office": "https://sede.gob.es/ejemplo"
  }
}
```

### Google Sheets

El workflow N8n ahora puede usar:
- **Link Principal**: `pdf_url` (extracto del BOE)
- **Link PDF**: `regulatory_base_url` (bases reguladoras)

## 📝 Tipos de URLs en BDNS

| Campo | Descripción | Ejemplo |
|-------|-------------|---------|
| `pdf_url` | PDF del extracto publicado en el BOE | https://boe.es/boe/dias/.../pdfs/BOE-A-2024-12345.pdf |
| `html_url` | Versión HTML del extracto en el BOE | https://boe.es/diario_boe/txt.php?id=BOE-A-2024-12345 |
| `regulatory_base_url` | Bases reguladoras completas | https://www.organismo.gob.es/bases.pdf |
| `electronic_office` | Sede electrónica para solicitudes | https://sede.gob.es/organismo |

## ⚠️ Casos Especiales

### Grant sin anuncios

Si `detail.anuncios` es `null` o está vacío:
- `pdf_url` = `null`
- `html_url` = `null`
- `regulatory_base_url` = aún disponible (desde `detail.urlBasesReguladoras`)

Esto es normal para grants que no se han publicado en el BOE aún o que solo tienen bases reguladoras.

### PDF no es del BOE

Si el PDF viene de otra fuente (no boe.es):
- `pdf_url` = URL del PDF (cualquier dominio)
- `html_url` = `null` (solo se genera para boe.es)

## 🧪 Testing

### 1. Capturar nuevo grant BDNS

```bash
# Desde la UI
POST /api/v1/capture/bdns
```

### 2. Verificar logs

```bash
tail -f logs/app.log | grep "PDF URL"
```

**Output esperado**:
```
2025-10-18 01:00:00 - DEBUG - PDF URL: https://boe.es/boe/dias/2024/01/15/pdfs/BOE-A-2024-12345.pdf
2025-10-18 01:00:00 - DEBUG - HTML URL: https://boe.es/diario_boe/txt.php?id=BOE-A-2024-12345
```

### 3. Verificar base de datos

```sql
SELECT
  id,
  pdf_url IS NOT NULL as has_pdf,
  html_url IS NOT NULL as has_html
FROM grants
WHERE source = 'BDNS'
ORDER BY captured_at DESC
LIMIT 10;
```

### 4. Enviar a N8n y verificar

El payload ahora debe incluir:
```json
{
  "pdf_url": "https://boe.es/...",
  "html_url": "https://boe.es/diario_boe/...",
  "metadata": {
    "regulatory_base_url": "..."
  }
}
```

## 📈 Mejoras Futuras

### Múltiples anuncios

Actualmente tomamos el primer anuncio (`detail.anuncios[0]`). Si hay múltiples publicaciones (BOE, DOCV, etc.), podríamos:
- Priorizar el BOE sobre otros boletines
- Guardar todos los anuncios en un array JSON

### Documentos adjuntos

BDNS también tiene `detail.documentos` con documentos adicionales. Podríamos capturar:
```python
if detail.documentos:
    # Construir URLs para descargar documentos
    for doc in detail.documentos:
        doc_url = f"https://www.infosubvenciones.es/bdnstrans/api/documento/{doc.id}"
```

### Validación de URLs

Añadir validación para verificar que las URLs son accesibles:
```python
import requests

if pdf_url:
    try:
        response = requests.head(pdf_url, timeout=5)
        if response.status_code != 200:
            logger.warning(f"PDF URL not accessible: {pdf_url}")
    except:
        pass
```

## 🎉 Beneficio

Con este fix:
- ✅ **PDFs accesibles** - Link directo al extracto del BOE
- ✅ **Múltiples formatos** - PDF y HTML disponibles
- ✅ **Datos completos en N8n** - Todo el contexto para análisis
- ✅ **Google Sheets completo** - Links funcionales para el equipo

El equipo de proyectos ahora puede acceder directamente al PDF del extracto oficial desde el Excel.

## 📁 Archivos Modificados

- `/backend/app/services/bdns_service.py`:
  - Método `_create_grant()` (líneas 216-234, 269-270)
  - Método `_update_grant()` (líneas 331-340, 353-356)
