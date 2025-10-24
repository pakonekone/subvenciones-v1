# 📊 Guía Completa: Exportación Automática a Google Sheets desde N8n Cloud

## 🎯 Objetivo

Configurar un workflow en N8n Cloud que reciba grants filtrados desde la UI (sin ánimo de lucro + presupuesto ≥500k€) y los exporte automáticamente a Google Sheets para el equipo de proyectos.

**Beneficio**: Ahorra horas de búsqueda manual en Fandit, centralizando la información en un Excel accesible.

---

## 📋 Tabla de Contenidos

1. [Preparación: Google Sheets](#1-preparación-google-sheets)
2. [Configuración: N8n Cloud](#2-configuración-n8n-cloud)
3. [Importación del Workflow](#3-importación-del-workflow)
4. [Configuración de Nodos](#4-configuración-de-nodos)
5. [Conexión con Backend](#5-conexión-con-backend)
6. [Prueba del Flujo](#6-prueba-del-flujo)
7. [Troubleshooting](#7-troubleshooting)

---

## 1. Preparación: Google Sheets

### 1.1 Crear Google Sheet

1. Ve a [Google Sheets](https://sheets.google.com)
2. Crea una nueva hoja llamada: **"Subvenciones Sin Ánimo Lucro"**
3. En la primera fila (Row 1), añade estos headers:

| A | B | C | D | E | F | G | H | I | J | K |
|---|---|---|---|---|---|---|---|---|---|---|
| Fuente | Código | Subvencionador | Título | Fecha Publicación | Fecha Fin Original | Fecha Fin Calculada | Montante Económico | Link Principal | Link PDF | Sede Electrónica |

### 1.2 Formatear Columnas

- **Columna E, F, G** (Fechas): Formato → Número → Fecha (`DD/MM/YYYY`)
- **Columna H** (Montante): Formato → Número → Moneda (`€`)
- **Columna I, J, K** (Links): Dejar como texto (N8n insertará URLs clickables)

### 1.3 Obtener ID del Sheet

La URL del Google Sheet es:
```
https://docs.google.com/spreadsheets/d/XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX/edit
```

Copia el ID (la parte `XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX`). Lo necesitarás en N8n.

---

## 2. Configuración: N8n Cloud

### 2.1 Acceder a N8n Cloud

1. Ve a [N8n Cloud](https://n8n.cloud)
2. Inicia sesión con tu cuenta
3. Ve a **Workflows** → **New Workflow**

### 2.2 Configurar Credenciales de Google Sheets

1. En N8n, ve a **Credentials** (menú lateral)
2. Click en **Add Credential**
3. Busca **"Google Sheets OAuth2 API"**
4. Click en **Connect my account**
5. Autoriza con tu cuenta de Google (la que tiene acceso al Sheet)
6. Guarda las credenciales con nombre: `Google Sheets - Subvenciones`

**Nota**: N8n Cloud maneja OAuth2 automáticamente, no necesitas crear credenciales manualmente.

---

## 3. Importación del Workflow

### 3.1 Descargar JSON del Workflow

El archivo `n8n_workflow_google_sheets.json` está en la raíz del proyecto.

### 3.2 Importar en N8n Cloud

1. En N8n Cloud, abre un workflow nuevo
2. Click en el menú **⋮** (tres puntos) arriba a la derecha
3. Selecciona **Import from File**
4. Sube el archivo `n8n_workflow_google_sheets.json`
5. El workflow se importará con 5 nodos:
   - Webhook
   - Calculate Dates
   - Map to Sheet Columns
   - Google Sheets
   - Respond to Webhook

---

## 4. Configuración de Nodos

### 4.1 Nodo 1: Webhook

**Propósito**: Recibir el payload desde el backend.

1. Click en el nodo **Webhook**
2. Configuración:
   - **HTTP Method**: `POST`
   - **Path**: `boe-grants-to-sheets` (o el que prefieras)
   - **Authentication**: None (puedes añadir header auth si quieres)
3. Copia la **Production URL** que aparece. Ejemplo:
   ```
   https://yourinstance.app.n8n.cloud/webhook/boe-grants-to-sheets
   ```
4. **Guarda esta URL** - la necesitarás para el backend

### 4.2 Nodo 2: Calculate Dates (Function)

**Propósito**: Calcular fechas relativas como "20 días hábiles" a fechas exactas.

Este nodo ya tiene el código JavaScript necesario. Revisa que:
- Detecta patrones: "X días hábiles", "X días naturales"
- Calcula fechas saltando fines de semana
- Maneja fechas ISO ya calculadas

**No necesitas cambiar nada aquí**, pero puedes revisar el código si quieres ajustar la lógica.

### 4.3 Nodo 3: Map to Sheet Columns (Set)

**Propósito**: Mapear campos del payload a columnas del Google Sheet.

Este nodo ya tiene el mapeo completo:
- `source` → Fuente
- `bdns_code` o `boe_id` → Código
- `department` → Subvencionador
- etc.

**No necesitas cambiar nada**, pero verifica que los nombres de campos coincidan con tu modelo Grant.

### 4.4 Nodo 4: Google Sheets

**Propósito**: Insertar la fila en Google Sheets.

1. Click en el nodo **Google Sheets**
2. Configuración:
   - **Credential**: Selecciona `Google Sheets - Subvenciones` (la que creaste)
   - **Operation**: `Append`
   - **Document**: Pega el **ID del Sheet** que copiaste en el paso 1.3
   - **Sheet**: `Sheet1` (o el nombre de tu hoja, por defecto es Sheet1)
   - **Options**:
     - ✅ **Use header row** (Row 1 tiene los headers)

### 4.5 Nodo 5: HTTP Request (Callback) - **CRÍTICO**

**Propósito**: Notificar al backend que el grant se exportó exitosamente a Google Sheets.

⚠️ **IMPORTANTE**: Este nodo es DIFERENTE de "Respond to Webhook". Es una llamada HTTP ADICIONAL.

1. **Añadir nuevo nodo HTTP Request** DESPUÉS del nodo Google Sheets
2. Configuración:
   - **Method**: `POST`
   - **URL**: `http://localhost:8000/api/v1/webhook/callback/sheets`
     - En producción: Usar URL pública del backend
   - **Authentication**: None (o añadir header auth si necesario)
   - **Body** (JSON):
     ```json
     {
       "grant_id": "{{ $json.Código }}",
       "status": "success",
       "sheets_url": "https://docs.google.com/spreadsheets/d/YOUR_SPREADSHEET_ID",
       "row_id": null,
       "error_message": null
     }
     ```

**¿Por qué es necesario este nodo?**
- "Respond to Webhook" solo responde a la petición HTTP ORIGINAL (Backend → N8n)
- Este callback hace una NUEVA petición HTTP (N8n → Backend) para actualizar el estado del grant
- Sin este callback, la UI nunca mostrará el icono verde de "exportado"

### 4.6 Nodo 6: Respond to Webhook

**Propósito**: Responder al webhook original del backend.

Este nodo ya está configurado para devolver:
```json
{
  "success": true,
  "message": "Grant exported to Google Sheets",
  "grant_id": "{{ $json.id }}"
}
```

**Orden correcto de nodos**:
```
1. Webhook (recibe grant)
   ↓
2. Calculate Dates
   ↓
3. Map to Sheet Columns
   ↓
4. Google Sheets - Append Row
   ↓
5. HTTP Request (CALLBACK - actualiza backend) ← NUEVO
   ↓
6. Respond to Webhook (cierra conexión original)
```

---

## 5. Conexión con Backend

### 5.1 Actualizar N8n Webhook URL en .env

En el archivo `.env` del backend:

```env
N8N_WEBHOOK_URL=https://yourinstance.app.n8n.cloud/webhook/boe-grants-to-sheets
```

Reemplaza con la URL real de tu webhook de N8n Cloud.

### 5.2 Verificar Endpoint de Envío

El backend ya tiene el endpoint `/api/v1/webhook/send` que envía grants a N8n.

Cuando el usuario hace clic en "Enviar a N8n" en la UI, el backend:
1. Recibe el `grant_id`
2. Obtiene el grant completo de la base de datos
3. Llama a `grant.to_n8n_payload()` para generar el payload
4. Envía POST a `N8N_WEBHOOK_URL` con el payload
5. Marca el grant como `sent_to_n8n=True`

**No necesitas cambiar código**, solo actualizar la URL del webhook.

---

## 6. Prueba del Flujo

### 6.1 Activar el Workflow en N8n

1. En N8n Cloud, en tu workflow
2. Click en el toggle **Inactive** → **Active** (arriba a la derecha)
3. El workflow ahora está escuchando webhooks

### 6.2 Probar desde la UI

1. Abre la UI del frontend: `http://localhost:5173`
2. Ve a la página de **Grants**
3. Filtra por:
   - ✅ **Sin ánimo de lucro**
   - **Presupuesto mínimo**: 500000
4. Selecciona un grant de la lista
5. Click en **"Enviar a N8n"** (o el botón equivalente)
6. Verifica en la consola del navegador que la petición fue exitosa

### 6.3 Verificar en Google Sheets

1. Abre tu Google Sheet
2. Deberías ver una nueva fila con los datos del grant:
   - Fuente (BDNS o BOE)
   - Código
   - Título
   - Fechas
   - Montante
   - Links clickables

### 6.4 Verificar en N8n Cloud

1. En N8n Cloud, ve a **Executions** (menú lateral)
2. Verifica que hay una ejecución reciente con estado **Success** ✅
3. Click en la ejecución para ver el detalle:
   - Webhook recibió el payload
   - Calculate Dates procesó las fechas
   - Google Sheets insertó la fila

---

## 7. Troubleshooting

### ❌ Error: "Authentication failed"

**Solución**:
1. Ve a Credentials en N8n
2. Reautoriza la cuenta de Google
3. Verifica que la cuenta tiene acceso al Google Sheet

### ❌ Error: "Sheet not found"

**Solución**:
1. Verifica que el **ID del Sheet** es correcto
2. Verifica que el nombre de la hoja es correcto (por defecto `Sheet1`)
3. Asegúrate de que la cuenta de Google de N8n tiene permisos de edición

### ❌ Error: "Webhook not responding"

**Solución**:
1. Verifica que el workflow está **Active** en N8n
2. Verifica que la URL del webhook en `.env` es correcta
3. Prueba el webhook manualmente con `curl`:
```bash
curl -X POST https://yourinstance.app.n8n.cloud/webhook/boe-grants-to-sheets \
  -H "Content-Type: application/json" \
  -d '{
    "id": "TEST-123",
    "source": "BDNS",
    "title": "Test Grant",
    "department": "Test Dept",
    "budget_amount": 600000
  }'
```

### ❌ Fechas no se calculan correctamente

**Solución**:
1. Revisa el nodo **Calculate Dates**
2. Verifica que el patrón regex detecta correctamente el texto:
   - "20 días hábiles desde publicación"
   - "15 días naturales"
3. Ajusta la lógica de cálculo si es necesario

### ❌ Duplicados en el Sheet

**Solución**:
El flujo actual hace **append** (añadir siempre). Si quieres evitar duplicados:
1. Añade un nodo **Google Sheets** antes del insert para buscar el código
2. Usa un nodo **If** para verificar si existe
3. Solo inserta si no existe

**Nota**: Esto ralentiza el proceso. Para urgencia, mejor append siempre y limpiar duplicados manualmente después.

---

## 📊 Estructura del Payload

El backend envía este payload a N8n:

```json
{
  "id": "BDNS-863212",
  "source": "BDNS",
  "type": "grant",
  "timestamp": "2025-10-18T01:00:00",

  "title": "Subvenciones para proyectos sociales",
  "description": "Convocatoria publicada por Ministerio X",
  "department": "Ministerio de Derechos Sociales",
  "section": "III. Otras disposiciones",

  "pdf_url": "https://www.infosubvenciones.es/.../pdf",
  "html_url": "https://boe.es/diario_boe/txt.php?id=BOE-A-2024-12345",
  "xml_url": "https://boe.es/diario_boe/xml.php?id=BOE-A-2024-12345",

  "pdf_content_text": "CONVOCATORIA BDNS - Título\n...",
  "pdf_content_markdown": "# Título\n...",

  "metadata": {
    "bdns_code": "863212",
    "bdns_id": 863212,
    "budget_amount": 600000,
    "application_start_date": "2025-01-15",
    "application_end_date": "2025-03-15",
    "is_open": true,
    "is_nonprofit": true,
    "nonprofit_confidence": 0.9,
    "beneficiary_types": ["Fundaciones", "Asociaciones"],
    "sectors": ["Acción Social"],
    "regions": ["ES41 - CASTILLA Y LEÓN"],
    "instruments": ["Subvención"],
    "funds": ["MRR"],
    "convocatoria_type": "Concurrencia competitiva",
    "purpose": "Financiar proyectos sociales...",
    "regulatory_base_url": "https://...",
    "electronic_office": "https://sede.gob.es/...",
    "state_aid_number": "SA.12345",
    "state_aid_url": "https://..."
  },

  "processing_info": {
    "captured_at": "2025-10-18T01:00:00",
    "estimated_relevance": 0.85,
    "pdf_processed": true,
    "extraction_method": "bdns_api",
    "data_type": "structured",
    "enriched": true
  },

  "bdns_code": "863212",
  "publication_date": "2025-01-15",
  "application_end_date": "2025-03-15",
  "budget_amount": 600000,
  "is_nonprofit": true,
  "electronic_office": "https://sede.gob.es/..."
}
```

N8n extrae de este payload:
- `source` → Fuente
- `metadata.bdns_code` o `id` → Código
- `department` → Subvencionador
- `title` → Título
- `publication_date` → Fecha Publicación
- `application_end_date` → Fecha Fin (a calcular si es relativa)
- `budget_amount` → Montante Económico
- `metadata.regulatory_base_url` o `pdf_url` → Link PDF
- `metadata.electronic_office` → Sede Electrónica

---

## 🎉 ¡Listo!

Ahora cada vez que el equipo de proyectos filtre grants en la UI y haga clic en "Enviar a N8n", los grants se exportarán automáticamente a Google Sheets.

**Resultado**: Excel actualizado en tiempo real sin tocar Fandit.

---

## 📝 Notas Adicionales

### Personalización del Sheet

Puedes añadir más columnas en Google Sheets:
- **Estado**: Para marcar "Revisado", "En progreso", etc.
- **Responsable**: Asignar quien trabaja cada grant
- **Notas**: Comentarios del equipo

N8n solo escribe las 11 columnas base. Las adicionales las gestionan manualmente.

### Automatización de Actualizaciones

Si quieres que N8n actualice grants existentes (en lugar de append):
1. Añade un nodo **Google Sheets Lookup** para buscar por código
2. Usa **If** para verificar si existe
3. Si existe: **Update Row**
4. Si no existe: **Append Row**

Esto es más lento pero evita duplicados.

### Notificaciones

Puedes añadir un nodo **Send Email** al final para notificar al equipo cuando se exporta un grant nuevo.

---

**¿Preguntas?** Revisa la sección de Troubleshooting o contacta al equipo técnico.

---

## 📊 Diagrama de Flujo Completo

### Flujo de Comunicación HTTP

```
┌─────────────────────────────────────────────────────────────┐
│                  FLUJO COMPLETO CON CALLBACK                │
└─────────────────────────────────────────────────────────────┘

1. Usuario selecciona grant en UI
   │
   ├──> Frontend hace POST /api/v1/webhook/send
        │
        └──> Backend obtiene grant de DB y envía a N8n
             │
             ├──> HTTP POST a N8n webhook URL
                  │
                  ▼
              ┌────────────────────────────────────┐
              │         N8n WORKFLOW               │
              ├────────────────────────────────────┤
              │ 1. Webhook (recibe payload)        │
              │ 2. Calculate Dates                 │
              │ 3. Map to Sheet Columns            │
              │ 4. Google Sheets - Append Row      │
              │                                    │
              │ ┌────────────────────────────────┐ │
              │ │  5. HTTP Request (CALLBACK)    │ │
              │ │  POST /callback/sheets         │ │
              │ │  ↓                             │ │
              │ └────────────────────────────────┘ │
              │                ↓                   │
              │    Backend actualiza:              │
              │    - google_sheets_exported=True   │
              │    - google_sheets_exported_at     │
              │    - google_sheets_url             │
              │                                    │
              │ 6. Respond to Webhook (cierra)     │
              └────────────────────────────────────┘
                               │
                               ▼
             Backend recibe respuesta {"success": true}
             │
             └──> Frontend muestra "Enviado exitosamente"

2. Frontend refresca tabla de grants
   │
   └──> GET /api/v1/grants
        │
        └──> Backend retorna grants con google_sheets_exported=true
             │
             └──> UI muestra icono verde Google Sheets con link
```

### Dos Comunicaciones HTTP Diferentes

**⚠️ CRÍTICO DE ENTENDER:**

1. **Comunicación Original** (Backend → N8n):
   - Backend envía grant a N8n
   - N8n procesa y **responde** con "Respond to Webhook"
   - Esta es una comunicación **síncrona** HTTP request/response

2. **Comunicación Callback** (N8n → Backend):
   - N8n hace una **nueva** petición HTTP al backend
   - Backend actualiza el estado del grant en la DB
   - Esta es una comunicación **asíncrona** independiente

```
Backend ────────────────────────────────> N8n
         (1) POST grant to webhook

Backend <──────────────────────────────── N8n
         (2) Respond to Webhook {"success": true}

Backend <──────────────────────────────── N8n
         (3) Callback POST /callback/sheets
         (Actualiza google_sheets_exported)
```

### Qué Pasa Sin el Callback

Sin el nodo HTTP Request de callback:

```
❌ SIN CALLBACK:
   1. Grant se envía a N8n ✅
   2. Grant se exporta a Google Sheets ✅
   3. Backend NO se entera de la exportación ❌
   4. UI sigue mostrando icono ámbar "procesando" ❌
   5. Usuario no sabe si se exportó exitosamente ❌
```

Con el callback configurado:

```
✅ CON CALLBACK:
   1. Grant se envía a N8n ✅
   2. Grant se exporta a Google Sheets ✅
   3. N8n notifica al backend vía callback ✅
   4. Backend actualiza google_sheets_exported=true ✅
   5. UI muestra icono verde con link a Sheets ✅
   6. Usuario puede hacer clic para ver el grant en Sheets ✅
```

---

**Última actualización**: 2025-10-20
**Cambios**: Añadida sección crítica sobre callback HTTP Request
