# N8n Chat Agent Setup Guide

## Overview

This document explains how to configure the N8n workflow for the AI Analyst Chat feature with organization context.

## Current Webhook

```
N8N_CHAT_WEBHOOK_URL=https://nokodo10.app.n8n.cloud/webhook/caddb366-b911-42ff-93b3-8c34c9976300
```

## Payload Structure

The backend sends the following payload to N8n:

```json
{
  "grant": {
    "id": "uuid-string",
    "title": "Subvenciones para proyectos de accion social...",
    "source": "BDNS",
    "department": "Ministerio de Derechos Sociales",
    "budget_amount": 500000.0,
    "budget_text": "500.000 euros",
    "application_start_date": "2026-01-01T00:00:00",
    "application_end_date": "2026-03-31T23:59:59",
    "is_open": true,
    "sectors": ["accion_social", "educacion"],
    "regions": ["ES30", "nacional"],
    "beneficiary_types": ["fundaciones", "asociaciones", "ongs"],
    "url": "https://www.pap.hacienda.gob.es/bdnstrans/...",
    "bdns_id": "123456",
    "summary": "Extracted summary...",
    "requirements": "Extracted requirements..."
  },
  "organization": {
    "name": "Fundacion Esperanza Digital",
    "type": "fundacion",
    "cif": "G12345678",
    "sectors": ["accion_social", "educacion", "tecnologia"],
    "regions": ["ES30", "ES51", "nacional"],
    "annual_budget": 850000.0,
    "employee_count": 25,
    "founding_year": 2015,
    "capabilities": ["proyectos_europeos", "formacion", "insercion_laboral", "voluntariado"],
    "description": "Fundacion dedicada a reducir la brecha digital..."
  },
  "chat": {
    "message": "Somos elegibles para esta convocatoria?",
    "history": [
      {"role": "user", "content": "Hola"},
      {"role": "assistant", "content": "Hola! Soy tu analista..."}
    ]
  }
}
```

**Note**: `organization` will be `null` if the user hasn't configured their profile.

## Recommended N8n Workflow

### Node 1: Webhook (Trigger)

- **Type**: Webhook
- **HTTP Method**: POST
- **Path**: `/grant-chat` or use the UUID path
- **Response Mode**: "Respond to Webhook" at the end
- **Authentication**: None (or add API key for production)

### Node 2: Set Context Variables

Extract and format the data for the AI:

```javascript
// Code node to prepare context
const grant = $json.grant;
const org = $json.organization;
const chat = $json.chat;

// Format grant info
const grantContext = `
## CONVOCATORIA
- Titulo: ${grant.title}
- Organo: ${grant.department || 'No especificado'}
- Presupuesto: ${grant.budget_text || grant.budget_amount + ' EUR'}
- Plazo: ${grant.application_start_date} a ${grant.application_end_date}
- Estado: ${grant.is_open ? 'ABIERTA' : 'CERRADA'}
- Sectores: ${(grant.sectors || []).join(', ')}
- Regiones: ${(grant.regions || []).join(', ')}
- Beneficiarios: ${(grant.beneficiary_types || []).join(', ')}
- URL: ${grant.url}
${grant.summary ? '\nResumen: ' + grant.summary : ''}
${grant.requirements ? '\nRequisitos: ' + grant.requirements : ''}
`;

// Format org info
let orgContext = '';
if (org) {
  orgContext = `
## ORGANIZACION DEL USUARIO
- Nombre: ${org.name}
- Tipo: ${org.type}
- CIF: ${org.cif || 'No proporcionado'}
- Sectores: ${(org.sectors || []).join(', ')}
- Regiones: ${(org.regions || []).join(', ')}
- Presupuesto anual: ${org.annual_budget ? org.annual_budget + ' EUR' : 'No especificado'}
- Empleados: ${org.employee_count || 'No especificado'}
- Ano fundacion: ${org.founding_year || 'No especificado'}
- Capacidades: ${(org.capabilities || []).join(', ')}
- Descripcion: ${org.description || 'No proporcionada'}
`;
} else {
  orgContext = `
## ORGANIZACION DEL USUARIO
No se ha configurado el perfil de la organizacion.
Solicita al usuario que configure su perfil en "Mi Organizacion" para un analisis personalizado.
`;
}

return {
  grantContext,
  orgContext,
  userMessage: chat.message,
  chatHistory: chat.history || []
};
```

### Node 3: AI Agent (Claude/GPT-4)

**System Prompt**:

```
Eres un experto analista de subvenciones espanol. Tu nombre es "Analista de Fandit".
Tu trabajo es ayudar a organizaciones sin animo de lucro a:
1. Entender convocatorias de subvenciones
2. Determinar su elegibilidad
3. Preparar la documentacion necesaria
4. Maximizar sus posibilidades de exito

CONTEXTO ACTUAL:
{{ $json.grantContext }}
{{ $json.orgContext }}

INSTRUCCIONES DE COMPORTAMIENTO:

1. ANALISIS DE ELEGIBILIDAD:
   - Compara sectores de la organizacion con los de la convocatoria
   - Compara regiones de operacion
   - Verifica tipo de beneficiario
   - Considera presupuesto y tamano de la organizacion

2. PUNTUACION DE COMPATIBILIDAD:
   Cuando te pregunten sobre elegibilidad, calcula una puntuacion:
   - 90-100%: Excelente match, cumple todos los requisitos
   - 70-89%: Buen match, cumple la mayoria
   - 50-69%: Match parcial, puede aplicar con limitaciones
   - 30-49%: Match debil, pocas posibilidades
   - 0-29%: No elegible

3. FORMATO DE RESPUESTA:
   - Usa Markdown para estructurar respuestas
   - Se conciso pero completo
   - Incluye siempre "siguientes pasos" cuando sea relevante
   - Si falta el perfil de organizacion, solicita que lo configuren

4. CAPACIDADES ESPECIALES:
   - Puedes explicar terminos tecnicos
   - Puedes sugerir documentacion necesaria
   - Puedes identificar fechas limite importantes
   - Puedes comparar con otras convocatorias similares

5. LIMITACIONES:
   - No inventes datos que no esten en el contexto
   - Si no sabes algo, dilo claramente
   - No hagas promesas sobre resultados de la solicitud

HISTORIAL DE CONVERSACION:
{{ $json.chatHistory }}

Responde al usuario de forma profesional y util.
```

**User Message**: `{{ $json.userMessage }}`

### Node 4: Format Response

```javascript
// Ensure response has correct format
const aiResponse = $json.response || $json.output || $json.text || '';

return {
  output: aiResponse
};
```

### Node 5: Respond to Webhook

- **Type**: Respond to Webhook
- **Response Body**: `{{ $json }}`
- **Response Headers**: `Content-Type: application/json`

## Testing the Workflow

### Test Payload (copy-paste into webhook test):

```json
{
  "grant": {
    "id": "test-123",
    "title": "Subvenciones para proyectos de accion social en el ambito de la infancia y juventud",
    "source": "BDNS",
    "department": "Ministerio de Derechos Sociales y Agenda 2030",
    "budget_amount": 2000000,
    "budget_text": "2.000.000 euros",
    "application_start_date": "2026-01-15T00:00:00",
    "application_end_date": "2026-02-28T23:59:59",
    "is_open": true,
    "sectors": ["accion_social", "infancia", "educacion"],
    "regions": ["nacional"],
    "beneficiary_types": ["fundaciones", "asociaciones", "ongs"],
    "url": "https://example.com/convocatoria",
    "summary": "Convocatoria destinada a financiar proyectos de atencion a menores en situacion de vulnerabilidad."
  },
  "organization": {
    "name": "Fundacion Esperanza Digital",
    "type": "fundacion",
    "cif": "G12345678",
    "sectors": ["accion_social", "educacion", "tecnologia"],
    "regions": ["ES30", "ES51", "nacional"],
    "annual_budget": 850000,
    "employee_count": 25,
    "founding_year": 2015,
    "capabilities": ["proyectos_europeos", "formacion", "insercion_laboral", "voluntariado"],
    "description": "Fundacion dedicada a reducir la brecha digital en colectivos vulnerables"
  },
  "chat": {
    "message": "Somos elegibles para esta convocatoria? Dame un analisis detallado.",
    "history": []
  }
}
```

## Expected Response Format

The workflow should return:

```json
{
  "output": "# Analisis de Elegibilidad\n\n## Puntuacion de Compatibilidad: 85%\n\n### Coincidencias Positivas\n- **Sectores**: Accion social y educacion coinciden perfectamente\n- **Ambito geografico**: Nacional - tu organizacion opera a nivel nacional\n- **Tipo de beneficiario**: Fundaciones estan incluidas\n\n### Puntos a Considerar\n- Tu enfoque en tecnologia podria ser un diferenciador positivo\n- El presupuesto de tu organizacion (850.000 EUR) es adecuado para gestionar proyectos de esta envergadura\n\n### Siguientes Pasos\n1. Revisar las bases completas de la convocatoria\n2. Preparar memoria de actividades de los ultimos 3 anos\n3. Documentar proyectos previos en el ambito de infancia\n\n**Fecha limite**: 28 de febrero de 2026"
}
```

## Troubleshooting

### Chat not responding
1. Check N8N_CHAT_WEBHOOK_URL is set correctly in backend `.env`
2. Verify webhook is active in N8n (not paused)
3. Check N8n execution logs for errors

### Organization not included
1. Ensure user has created organization profile
2. Verify X-User-ID header is being sent (default: "demo-user")
3. Check organization exists in database

### Response format issues
1. Ensure last node outputs `{ "output": "..." }` format
2. Check for JSON parsing errors in N8n
3. Verify Content-Type is application/json
