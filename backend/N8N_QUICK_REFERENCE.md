# 🚀 Referencia Rápida: N8n → Google Sheets

## ✅ Checklist de Configuración

### Pre-requisitos
- [ ] Cuenta N8n Cloud activa
- [ ] Cuenta Google con acceso a Sheets
- [ ] Google Sheet creado con headers

### Pasos de Configuración (15 minutos)

1. **Google Sheets** (5 min)
   - [ ] Crear sheet "Subvenciones Sin Ánimo Lucro"
   - [ ] Añadir headers en Row 1 (11 columnas)
   - [ ] Copiar ID del sheet desde la URL
   - [ ] Formatear columnas (fechas, moneda)

2. **N8n Cloud** (10 min)
   - [ ] Importar `n8n_workflow_google_sheets.json`
   - [ ] Configurar credenciales Google OAuth2
   - [ ] Actualizar ID del sheet en nodo Google Sheets
   - [ ] Copiar URL del webhook
   - [ ] Activar workflow

3. **Backend** (2 min)
   - [ ] Actualizar `N8N_WEBHOOK_URL` en `.env`
   - [ ] Reiniciar servidor backend

4. **Prueba** (3 min)
   - [ ] Filtrar grants en UI
   - [ ] Enviar uno a N8n
   - [ ] Verificar fila en Google Sheets
   - [ ] Verificar ejecución en N8n

---

## 📊 Headers del Google Sheet

Copia y pega en Row 1:

```
Fuente | Código | Subvencionador | Título | Fecha Publicación | Fecha Fin Original | Fecha Fin Calculada | Montante Económico | Link Principal | Link PDF | Sede Electrónica
```

---

## 🔗 URLs Importantes

- **N8n Cloud**: https://n8n.cloud
- **Google Sheets**: https://sheets.google.com
- **Documentación Completa**: Ver `N8N_GOOGLE_SHEETS_SETUP.md`

---

## 🧪 Comandos de Prueba

### Probar webhook manualmente (bash/terminal):

```bash
# Reemplaza YOUR_WEBHOOK_URL con la URL real
curl -X POST https://yourinstance.app.n8n.cloud/webhook/boe-grants-to-sheets \
  -H "Content-Type: application/json" \
  -d '{
    "id": "TEST-123",
    "source": "BDNS",
    "title": "Subvención de Prueba",
    "department": "Ministerio de Test",
    "publication_date": "2025-01-15",
    "application_end_date": "2025-03-15",
    "budget_amount": 600000,
    "bdns_code": "TEST-123",
    "metadata": {
      "bdns_code": "TEST-123",
      "budget_amount": 600000,
      "regulatory_base_url": "https://example.com/pdf",
      "electronic_office": "https://sede.gob.es/test"
    }
  }'
```

**Resultado esperado**:
```json
{
  "success": true,
  "message": "Grant exported to Google Sheets",
  "grant_id": "TEST-123",
  "timestamp": "2025-10-18T01:00:00.000Z"
}
```

---

## 🎯 Filtros en la UI

Para obtener los grants correctos:

1. **Filtro 1**: Sin ánimo de lucro
   - Checkbox: ✅ "Sin ánimo de lucro"
   - Backend filtra: `is_nonprofit=true`

2. **Filtro 2**: Presupuesto ≥500k€
   - Input: "Presupuesto mínimo: 500000"
   - Backend filtra: `budget_amount>=500000`

**Resultado**: Solo grants que cumplan AMBOS filtros.

---

## 🔍 Verificación Post-Envío

### En la UI
- ✅ Mensaje de confirmación
- ✅ Grant marcado como "Enviado a N8n"
- ✅ Icono o badge visual

### En N8n Cloud
1. Ve a **Executions**
2. Última ejecución debe tener status **Success** ✅
3. Click para ver detalles:
   - Webhook: Payload recibido
   - Calculate Dates: Fechas procesadas
   - Map Columns: Campos mapeados
   - Google Sheets: Fila insertada

### En Google Sheets
- ✅ Nueva fila al final del sheet
- ✅ Todos los campos poblados
- ✅ Links clickables (azules)
- ✅ Fechas formateadas DD/MM/YYYY
- ✅ Montante con símbolo €

---

## ❌ Errores Comunes y Soluciones

| Error | Causa | Solución |
|-------|-------|----------|
| "Authentication failed" | Credenciales Google incorrectas | Reautorizar en N8n Credentials |
| "Sheet not found" | ID incorrecto | Verificar ID del sheet |
| "Webhook timeout" | Workflow no activo | Activar workflow en N8n |
| Duplicados en sheet | Append sin validación | Normal - limpiar manualmente |
| Fechas incorrectas | Patrón no reconocido | Ajustar regex en Function node |
| Montante "No especificado" | Grant sin budget_amount | Normal para grants sin presupuesto |

---

## 📞 Contacto

**Dudas técnicas**: Revisar `N8N_GOOGLE_SHEETS_SETUP.md` (guía completa)

**Workflow JSON**: `n8n_workflow_google_sheets.json`

---

## 🎉 Resultado Final

**Antes**:
- Buscar manualmente en Fandit
- Copiar datos uno por uno
- 2-3 horas por día

**Después**:
- Filtrar en UI (30 segundos)
- Click "Enviar a N8n" (1 segundo)
- Excel actualizado automáticamente
- **5-10 minutos por día** ✨

**Ahorro**: ~2 horas diarias = 10 horas semanales para el equipo de proyectos.
