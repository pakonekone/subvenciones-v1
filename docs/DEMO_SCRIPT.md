# Demo Script - Sistema de Subvenciones con AI Analyst

## Pre-Demo Setup

### 1. Start Services
```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### 2. Verify Services
- Backend: http://localhost:8000/docs
- Frontend: http://localhost:3000

### 3. Ensure Test Data
```bash
# Check organization profile exists
curl -s -H "X-User-ID: demo-user" http://localhost:8000/api/v1/organization | jq .

# Check grants exist
curl -s "http://localhost:8000/api/v1/grants?limit=5" | jq '.grants | length'
```

---

## Demo Flow (15-20 min)

### Scene 1: Problem Statement (2 min)

**Narration**:
> "Las ONGs y fundaciones espanolas pierden miles de euros en subvenciones porque:
> 1. No encuentran las convocatorias a tiempo
> 2. No saben si son elegibles
> 3. El proceso de documentacion es complejo
>
> Fandit automatiza la captura, analisis y preparacion de subvenciones."

### Scene 2: Grant Discovery (3 min)

**Actions**:
1. Open http://localhost:3000
2. Show the grants table with existing grants
3. Click "Capturar" dropdown
4. Select "BDNS - Base Nacional"
5. Configure date range (last 7 days)
6. Show the filter keywords preview
7. Start capture and wait for results
8. Point out the new grants appearing

**Key Points**:
- Automatic nonprofit filtering
- Transparent keywords system
- Multiple sources (BDNS, BOE, PLACSP)

### Scene 3: Organization Profile (3 min)

**Actions**:
1. Click "Mi Organizacion" in navigation
2. Show the pre-filled form with "Fundacion Esperanza Digital"
3. Highlight:
   - Organization type
   - Sectors (checkboxes)
   - Regions (geographic scope)
   - Capabilities
4. Modify a sector (add or remove)
5. Save the profile

**Key Points**:
- One-time setup
- Data used for personalized analysis
- Structured fields for accurate matching

### Scene 4: AI Analyst Chat - Basic (4 min)

**Actions**:
1. Return to grants page
2. Click on a relevant grant (e.g., one with "accion social" sector)
3. Show the Agent Sidebar opens automatically
4. Notice the grant info displayed at top
5. Type first question:
   > "Explicame esta convocatoria en terminos sencillos"
6. Wait for AI response
7. Show the markdown formatting

**Key Points**:
- Sidebar opens automatically on grant selection
- Full grant context sent to AI
- Clean markdown responses

### Scene 5: AI Analyst Chat - Eligibility Analysis (5 min)

**Actions**:
1. Type second question:
   > "Somos elegibles para esta convocatoria?"
2. Wait for response showing:
   - Compatibility score
   - Matching sectors
   - Matching regions
   - Potential issues
3. Type follow-up:
   > "Que documentacion necesitamos preparar?"
4. Show the AI's structured response

**Key Points**:
- Organization profile automatically included
- Personalized eligibility analysis
- Actionable next steps

### Scene 6: Advanced Features (3 min)

**Actions**:
1. Show quick filters (Nonprofit, High Budget)
2. Demonstrate search functionality
3. Show the export to Excel option
4. Briefly show Google Sheets integration column

**Key Points**:
- Rich filtering capabilities
- Export for offline work
- Integration with existing workflows

---

## Demo Questions to Prepare For

### Technical
1. "How does the AI know about our organization?"
   > The organization profile is sent with every chat request, giving the AI full context.

2. "What AI model powers the analysis?"
   > We use N8n to orchestrate calls to Claude or GPT-4, depending on configuration.

3. "How accurate is the eligibility analysis?"
   > It's a decision support tool. The AI analyzes public criteria but final eligibility depends on reviewing full bases.

### Business
1. "How often are grants updated?"
   > BDNS and BOE are checked on-demand. Can be scheduled for automatic daily updates.

2. "Can multiple users share an organization profile?"
   > Current demo uses simple user IDs. Production would have proper auth with shared org access.

3. "What about GDPR/data privacy?"
   > All data stays in your infrastructure. N8n can be self-hosted. No external data sharing.

---

## Backup Scenarios

### If N8n is slow:
> "The AI is analyzing the full context. In production, we'd optimize response times with caching and model selection."

### If capture returns no results:
> "No new grants match our nonprofit filters for this date range. Let me expand the dates..."

### If chat fails:
> "Let me check the N8n webhook connection. Meanwhile, I can show you the grant details panel..."

---

## Key Messages

1. **Save Time**: Automatic capture from multiple sources
2. **Never Miss**: Transparent filtering shows exactly what's being captured
3. **Know Immediately**: AI tells you if you're eligible in seconds
4. **Act Fast**: Structured recommendations and deadline tracking
5. **Stay Organized**: Export to Excel, Google Sheets integration

---

## Post-Demo Actions

1. Offer to:
   - Configure their own organization profile
   - Run a live capture with their criteria
   - Show the N8n workflow (for technical audience)

2. Collect feedback on:
   - Missing sectors/regions in profile
   - Additional AI capabilities they'd want
   - Integration needs (CRM, project management)
