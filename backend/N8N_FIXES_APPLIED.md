# ✅ Correcciones Aplicadas al Workflow N8n

## 🔍 Problema Original

El workflow inicial no extraía correctamente los datos del webhook porque:
1. Los datos llegaban en `body` del webhook, no en el nivel raíz
2. Las fechas ISO (`2025-11-04T00:00:00`) no se estaban formateando para el Excel
3. Se perdía información valiosa

**Ejemplo de problema**:
```json
// Webhook recibía:
{
  "body": {
    "application_end_date": "2025-11-04T00:00:00",
    "budget_amount": 12000
  }
}

// Pero el código buscaba:
$json.application_end_date  // ❌ undefined
$json.budget_amount         // ❌ undefined
```

## ✅ Soluciones Implementadas

### 1. Nuevo Nodo: Extract Body (Nodo 2)

**Ubicación**: Entre Webhook y Calculate Dates

**Función**: Extrae el objeto `body` del webhook y lo convierte en el objeto raíz.

**Código**:
```javascript
return [$json.body];
```

**Resultado**:
- Input: `{ body: { application_end_date: "2025-11-04T00:00:00" } }`
- Output: `{ application_end_date: "2025-11-04T00:00:00" }` ✅

### 2. Mejora: Calculate & Format Dates (Nodo 3)

**Cambios**:
- ✅ Detecta fechas ISO (`YYYY-MM-DD` o `YYYY-MM-DDTHH:MM:SS`)
- ✅ Formatea a `DD/MM/YYYY` para el Excel
- ✅ Calcula "20 días hábiles" si es necesario
- ✅ Formatea también la fecha de publicación

**Ejemplo con el grant real**:
```
Input:
  application_end_date: "2025-11-04T00:00:00"
  publication_date: "2025-10-17T00:00:00"

Output:
  calculated_end_date: "04/11/2025"
  original_end_date: "04/11/2025"
  formatted_pub_date: "17/10/2025"
```

### 3. Actualización: Map to Sheet Columns (Nodo 4)

**Cambios**:
- ✅ Usa `$json.formatted_pub_date` (ya formateado)
- ✅ Usa `$json.calculated_end_date` (ya formateado)
- ✅ Maneja casos donde `bdns_code` puede venir de diferentes lugares
- ✅ Mejora la construcción del link BDNS

**Mejora del Link BDNS**:
```javascript
// Antes:
'https://www.infosubvenciones.es/.../{ bdns_code }'

// Ahora (maneja múltiples fuentes):
$json.metadata?.bdns_code || $json.bdns_code || $json.id.replace('BDNS-', '')
```

## 📊 Resultado con el Grant Real

**Input del Webhook** (BDNS-863217):
```json
{
  "id": "BDNS-863217",
  "source": "BDNS",
  "title": "EXTRACTO DE LA CONVOCATORIA...",
  "department": "OROPESA DEL MAR/ORPESA",
  "publication_date": "2025-10-17T00:00:00",
  "application_end_date": "2025-11-04T00:00:00",
  "budget_amount": 12000,
  "bdns_code": "863217",
  "metadata": {
    "bdns_code": "863217",
    "regulatory_base_url": "www.oropesadelmar.es"
  }
}
```

**Output en Google Sheets**:

| Fuente | Código | Subvencionador | Título | Fecha Pub | Fecha Fin Original | Fecha Fin Calculada | Montante | Link Principal | Link PDF | Sede |
|--------|--------|----------------|--------|-----------|-------------------|---------------------|----------|---------------|----------|------|
| BDNS | 863217 | OROPESA DEL MAR/ORPESA | EXTRACTO DE LA CONVOCATORIA... | 17/10/2025 | 04/11/2025 | 04/11/2025 | 12.000 € | https://www.infosubvenciones.es/.../863217 | www.oropesadelmar.es | No disponible |

## 🎯 Workflow Actualizado

**6 Nodos** (antes eran 5):

1. **Webhook - Receive Grant**
   - Recibe el POST desde el backend
   - Contiene todo en `body`

2. **Extract Body** ⭐ NUEVO
   - Extrae `body` al nivel raíz
   - Hace accesibles todos los campos

3. **Calculate & Format Dates**
   - Formatea fechas ISO a DD/MM/YYYY
   - Calcula fechas relativas si es necesario
   - Formatea fecha de publicación

4. **Map to Sheet Columns**
   - Mapea 11 campos al formato del sheet
   - Usa fechas ya formateadas
   - Maneja valores por defecto

5. **Google Sheets - Append Row**
   - Inserta fila en el sheet
   - Modo append (no verifica duplicados)

6. **Respond to Webhook**
   - Confirma éxito al backend
   - Devuelve ID del grant exportado

## 🔧 Testing con Grant Real

Para probar con el grant real (BDNS-863217):

```bash
curl -X POST https://tu-webhook-url/webhook/boe-grants-to-sheets \
  -H "Content-Type: application/json" \
  -d '{
    "id": "BDNS-863217",
    "source": "BDNS",
    "title": "EXTRACTO DE LA CONVOCATORIA DE LAS SUBVENCIONES PARA EL FOMENTO DE ACTIVIDADES QUE REALICEN ENTIDADES SOCIALES EN EL ÁMBITO MUNICIPAL POR CONCURRENCIA COMPETITIVA EN EL AÑO 2025",
    "department": "OROPESA DEL MAR/ORPESA - AYUNTAMIENTO DE OROPESA DEL MAR/ORPESA",
    "publication_date": "2025-10-17T00:00:00",
    "application_end_date": "2025-11-04T00:00:00",
    "budget_amount": 12000,
    "bdns_code": "863217",
    "is_nonprofit": true,
    "metadata": {
      "bdns_code": "863217",
      "regulatory_base_url": "www.oropesadelmar.es"
    }
  }'
```

**Resultado Esperado**:
- ✅ Fila añadida en Google Sheets
- ✅ Fechas formateadas: 17/10/2025 y 04/11/2025
- ✅ Montante: 12.000 €
- ✅ Link BDNS: https://www.infosubvenciones.es/bdnstrans/GE/es/convocatoria/863217

## 📝 Cambios en los Archivos

### n8n_workflow_google_sheets.json
- ✅ Añadido nodo "Extract Body" (posición 2)
- ✅ Actualizado Function para formatear fechas ISO
- ✅ Mejorado Map para manejar múltiples fuentes de datos
- ✅ Actualizado versionId a "2"

### Archivos Sin Cambios
- `N8N_GOOGLE_SHEETS_SETUP.md` - Documentación principal sigue válida
- `N8N_QUICK_REFERENCE.md` - Referencia rápida sigue válida

## ⚠️ Puntos de Atención

### Formateo de Montante Económico

El código usa `toLocaleString('es-ES')` que formatea automáticamente:
- 12000 → "12.000"
- 600000 → "600.000"

Añade " €" al final para claridad.

### Manejo de Nulls

Todos los campos tienen valores por defecto:
- Fechas sin valor: "No especificado"
- Links sin valor: "No disponible"
- Montante sin valor: "No especificado"

### Fechas en Múltiples Formatos

El código maneja:
- ✅ ISO completo: `2025-10-17T00:00:00`
- ✅ ISO corto: `2025-10-17`
- ✅ Texto relativo: "20 días hábiles desde publicación"
- ✅ Null/undefined: "No especificado"

## 🎉 Beneficio Final

Con estas correcciones:
- ✅ **Datos completos** - No se pierde información
- ✅ **Fechas legibles** - Formato DD/MM/YYYY para humanos
- ✅ **Links funcionales** - URLs correctas para BDNS y BOE
- ✅ **Montantes claros** - Formato monetario español

**El equipo de proyectos puede usar el Excel directamente sin transformaciones manuales.**
