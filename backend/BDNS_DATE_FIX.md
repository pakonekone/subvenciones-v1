# ✅ BDNS Date Parsing Fix

## 🔍 Problema Identificado

Las fechas de convocatorias BDNS llegaban como `null` a la base de datos, aunque en la web de BDNS aparecían correctamente.

**Ejemplo**:
- Web BDNS mostraba: "Fecha de inicio: 31/12/2024, Fecha de finalización: 31/12/2025"
- Base de datos tenía: `application_start_date: null`, `application_end_date: null`

## ❌ Causa Raíz

El código en `bdns_service.py` tenía varios problemas:

### 1. Manejo silencioso de errores
```python
# Código ANTERIOR (INCORRECTO):
if detail.fechaFinSolicitud:
    try:
        application_end_date = datetime.strptime(detail.fechaFinSolicitud, "%Y-%m-%d").date()
    except:
        pass  # ❌ Silencia todos los errores
```

**Problema**: Si el formato de fecha no era exactamente `YYYY-MM-DD`, el parsing fallaba silenciosamente y la fecha quedaba como `None`.

### 2. Formato único esperado

El código solo intentaba parsear en formato `YYYY-MM-DD` (ISO), pero la API de BDNS puede devolver fechas en diferentes formatos:
- `DD/MM/YYYY` (formato español)
- `YYYY-MM-DD` (ISO)
- `YYYY-MM-DDTHH:MM:SS` (ISO con hora)

### 3. Sin logging

No había ningún log que indicara:
- Qué valor raw venía de la API
- Qué formato se intentó parsear
- Por qué falló el parsing

## ✅ Solución Implementada

### 1. Parser robusto con múltiples formatos

```python
def parse_bdns_date(date_str: str, field_name: str):
    if not date_str:
        return None

    # Try multiple date formats
    formats = [
        "%Y-%m-%d",     # YYYY-MM-DD (ISO format)
        "%d/%m/%Y",     # DD/MM/YYYY (Spanish format)
        "%Y-%m-%dT%H:%M:%S",  # ISO with time
        "%Y-%m-%d %H:%M:%S"   # SQL datetime format
    ]

    for fmt in formats:
        try:
            result = datetime.strptime(date_str, fmt).date()
            logger.debug(f"✅ Parsed {field_name}: {date_str} → {result} using format {fmt}")
            return result
        except ValueError:
            continue

    # If no format worked, log the error
    logger.warning(f"⚠️ Could not parse {field_name}: '{date_str}' - tried formats: {formats}")
    return None
```

### 2. Logging detallado

```python
# Parse dates with debug logging
logger.info(f"📅 Parsing dates for BDNS-{detail.codigoBDNS}")
logger.debug(f"   Raw fechaRecepcion: {detail.fechaRecepcion}")
logger.debug(f"   Raw fechaInicioSolicitud: {detail.fechaInicioSolicitud}")
logger.debug(f"   Raw fechaFinSolicitud: {detail.fechaFinSolicitud}")

publication_date = parse_bdns_date(detail.fechaRecepcion, "fechaRecepcion")
application_start_date = parse_bdns_date(detail.fechaInicioSolicitud, "fechaInicioSolicitud")
application_end_date = parse_bdns_date(detail.fechaFinSolicitud, "fechaFinSolicitud")
```

### 3. Aplicado en ambos métodos

- `_create_grant()`: Cuando se captura un grant nuevo
- `_update_grant()`: Cuando se actualiza un grant existente

## 📊 Resultado Esperado

Ahora cuando la API de BDNS devuelva las fechas:

```json
{
  "fechaInicioSolicitud": "31/12/2024",
  "fechaFinSolicitud": "31/12/2025"
}
```

El sistema:
1. ✅ Intentará parsear con formato DD/MM/YYYY (éxito)
2. ✅ Logueará: "✅ Parsed fechaInicioSolicitud: 31/12/2024 → 2024-12-31 using format %d/%m/%Y"
3. ✅ Guardará correctamente en la base de datos
4. ✅ Enviará fechas válidas a N8n

## 🔧 Testing

Para verificar que el fix funciona:

1. Captura nuevos grants BDNS:
```bash
# Desde la UI o API
POST /api/v1/grants/capture/bdns
```

2. Revisa los logs:
```bash
tail -f logs/app.log | grep "📅 Parsing dates"
```

3. Verifica que las fechas aparezcan en la base de datos:
```sql
SELECT id, application_start_date, application_end_date
FROM grants
WHERE source = 'BDNS'
ORDER BY captured_at DESC
LIMIT 5;
```

4. Envía un grant a N8n y verifica que las fechas lleguen correctamente:
```bash
# Las fechas deben aparecer en el payload como:
{
  "application_end_date": "2025-12-31T00:00:00",
  "metadata": {
    "application_start_date": "2024-12-31",
    "application_end_date": "2025-12-31"
  }
}
```

## 🎯 Impacto en Google Sheets Export

Con este fix, el workflow N8n ahora recibirá:

```json
{
  "application_end_date": "2025-12-31T00:00:00",  // ✅ Ya no null
  "publication_date": "2025-10-17T00:00:00"        // ✅ Ya no null
}
```

Y el nodo "Calculate & Format Dates" podrá:
- ✅ Detectar el formato ISO
- ✅ Formatear a DD/MM/YYYY para el Excel
- ✅ Mostrar "31/12/2025" en lugar de "No especificado"

## 📝 Archivos Modificados

- `/backend/app/services/bdns_service.py`:
  - Método `_create_grant()` (líneas 159-197)
  - Método `_update_grant()` (líneas 263-293)

## ⚠️ Nota Importante

Si después de este fix las fechas **aún** llegan como `null`, significa que:

1. **La API de BDNS no devuelve esas fechas** para esa convocatoria específica
2. Los campos `fechaInicioSolicitud` y `fechaFinSolicitud` vienen vacíos o `null` desde la API
3. Esto es normal para algunas convocatorias que no tienen fechas límite definidas

En ese caso, el workflow de N8n manejará correctamente el null mostrando "No especificado" en el Excel.

## 🚀 Próximos Pasos

Si las fechas siguen llegando como `null` después de este fix:

1. Verificar los logs para ver qué valor raw llega de la API
2. Hacer un test manual con el BDNS API client:
```python
from shared.bdns_api import BDNSAPIClient
client = BDNSAPIClient()
detail = client.get_convocatoria_detail("863019")
print(detail.fechaInicioSolicitud)
print(detail.fechaFinSolicitud)
```

3. Si la API no devuelve las fechas, investigar si hay que llamar a otro endpoint o usar otros campos
