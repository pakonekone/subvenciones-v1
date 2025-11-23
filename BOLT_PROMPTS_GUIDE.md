# 🚀 Guía de Prompts para Bolt.new: SaaS de Subvenciones

## 📋 Índice
1. [Estrategia General](#estrategia-general)
2. [Prompts Paso a Paso](#prompts-paso-a-paso)
3. [Tech Stack Recomendado](#tech-stack-recomendado)
4. [Best Practices de Bolt](#best-practices-de-bolt)
5. [Checklist Pre-Comercialización](#checklist-pre-comercialización)

---

## 🎯 Estrategia General

### Enfoque de Desarrollo en Bolt.new

**Principios Clave:**
- ✅ **Incrementalidad**: Construir en 10 fases progresivas
- ✅ **Especificidad**: Prompts detallados con tech stack explícito
- ✅ **Validación**: Probar cada fase antes de avanzar
- ✅ **Contexto**: Usar prompts de proyecto para mantener consistencia

**Ventajas de Bolt para SaaS:**
- Scaffolding ultra-rápido (0 a MVP en horas)
- Integración nativa con Supabase (auth + DB)
- Deploy automático en Netlify/Vercel
- Stripe integration lista para pagos

---

## 📝 Prompts Paso a Paso

### 🔧 **PROMPT GLOBAL DEL PROYECTO** (Configurar primero)

**Acción**: En Bolt.new, ir a Settings → Project Prompt y pegar esto:

```markdown
You are building a professional SaaS platform for managing Spanish government grants (subvenciones).

CRITICAL REQUIREMENTS:
- Target users: Nonprofit organizations in Spain
- Must be production-ready and commercially viable
- Professional UI/UX with modern design (shadcn/ui)
- Multi-tenant architecture ready
- Internationalization support (Spanish primary, English secondary)
- Mobile-responsive design mandatory
- Performance-optimized (Core Web Vitals)

TECH STACK (ALWAYS USE):
- Frontend: React 18 + TypeScript + Vite
- UI: Tailwind CSS + shadcn/ui components
- Backend: Supabase (PostgreSQL + Auth + Storage)
- State Management: Zustand
- Forms: React Hook Form + Zod validation
- API Integration: TanStack Query (React Query)
- Date handling: date-fns
- Charts: Recharts
- Deployment: Netlify

CODE STYLE:
- TypeScript strict mode enabled
- ESLint + Prettier configured
- Modular component architecture
- Custom hooks for reusable logic
- Error boundaries for resilience
- Accessibility (ARIA labels, keyboard navigation)

IMPORTANT:
- Never skip error handling
- Always add loading states
- Include empty states with CTAs
- Add toast notifications for user feedback
- Implement optimistic UI updates
- Follow GDPR compliance for data handling
```

---

### **FASE 1: Scaffolding Base + Autenticación**

**Prompt:**
```
Create the foundation for a multi-tenant SaaS platform for managing Spanish government grants. This is a commercial product targeting nonprofit organizations.

PROJECT STRUCTURE:
1. Initialize a React + TypeScript + Vite project
2. Install and configure Tailwind CSS
3. Set up shadcn/ui with these components: Button, Card, Dialog, Form, Input, Label, Select, Table, Tabs, Toast, Avatar, DropdownMenu
4. Create folder structure:
   - /src/components/ui (shadcn components)
   - /src/components/auth (authentication components)
   - /src/components/layout (Header, Sidebar, Footer)
   - /src/pages (Dashboard, Login, Register, Settings)
   - /src/lib (utilities, Supabase client)
   - /src/hooks (custom hooks)
   - /src/types (TypeScript interfaces)
   - /src/stores (Zustand stores)

SUPABASE INTEGRATION:
1. Configure Supabase client with environment variables
2. Implement authentication system:
   - Email/password registration with email confirmation
   - Magic link login option
   - Google OAuth integration
   - Password reset flow
   - Protected routes with auth guard
3. Create authentication UI:
   - Modern login page with organization branding
   - Registration page with terms acceptance
   - Email verification page
   - Password reset page

USER EXPERIENCE:
- Add animated transitions between auth states
- Show loading spinners during auth operations
- Display toast notifications for success/errors
- Include "Remember me" functionality
- Add "Privacy Policy" and "Terms of Service" footer links

STYLING:
- Professional color scheme: Primary blue (#0066CC), Secondary green (#10B981)
- Clean, minimalist design
- Mobile-first responsive layout
- Dark mode toggle in header

OUTPUT:
A fully functional authentication system ready for user registration.
```

---

### **FASE 2: Database Schema + Multi-Tenancy**

**Prompt:**
```
Set up the Supabase database schema for a multi-tenant grants management SaaS. Each organization should have isolated data.

DATABASE TABLES (create SQL in Supabase):

1. **organizations** table:
   - id (uuid, primary key)
   - name (text, required)
   - slug (text, unique, for custom URLs)
   - logo_url (text, nullable)
   - plan_tier (enum: 'free', 'pro', 'enterprise')
   - max_users (integer, default 5)
   - created_at (timestamp)
   - subscription_status (enum: 'trial', 'active', 'cancelled')
   - trial_ends_at (timestamp)

2. **profiles** table (extends auth.users):
   - id (uuid, references auth.users)
   - organization_id (uuid, references organizations)
   - role (enum: 'owner', 'admin', 'member', 'viewer')
   - full_name (text)
   - avatar_url (text)
   - email_notifications (boolean, default true)
   - created_at (timestamp)

3. **grants** table:
   - id (uuid, primary key)
   - organization_id (uuid, references organizations) [CRITICAL for multi-tenancy]
   - title (text, required)
   - source (enum: 'BDNS', 'BOE')
   - grant_code (text, unique per source)
   - publishing_department (text)
   - application_start_date (date)
   - application_end_date (date)
   - total_budget (numeric)
   - sectors (jsonb array)
   - regions (jsonb array)
   - beneficiary_types (jsonb array)
   - is_nonprofit (boolean, default false)
   - nonprofit_confidence (numeric, 0-1)
   - relevance_score (numeric, 0-1)
   - ai_priority (text, enum: 'high', 'medium', 'low')
   - ai_strategic_value (text)
   - summary (text, AI-generated)
   - pdf_url (text)
   - pdf_content (text)
   - google_sheets_exported (boolean, default false)
   - google_sheets_url (text)
   - status (enum: 'new', 'reviewing', 'applying', 'applied', 'rejected', 'awarded')
   - assigned_to (uuid, references profiles)
   - notes (text)
   - created_at (timestamp)
   - updated_at (timestamp)

4. **grant_activities** table (audit log):
   - id (uuid, primary key)
   - grant_id (uuid, references grants)
   - user_id (uuid, references profiles)
   - action_type (enum: 'created', 'status_changed', 'assigned', 'note_added', 'exported')
   - details (jsonb)
   - created_at (timestamp)

5. **filter_keywords** table (customizable per organization):
   - id (uuid, primary key)
   - organization_id (uuid, references organizations)
   - keyword_type (enum: 'bdns_nonprofit', 'boe_grants', 'custom')
   - keyword (text)
   - is_active (boolean, default true)

ROW-LEVEL SECURITY (RLS) POLICIES:
- Enable RLS on all tables except 'organizations'
- Grants: Users can only access grants from their organization
- Profiles: Users can only see profiles from their organization
- Filter keywords: Isolated by organization_id

CREATE INDEXES:
- grants.organization_id
- grants.status
- grants.application_end_date
- grants.is_nonprofit
- grants.created_at

FRONTEND INTEGRATION:
1. Create TypeScript interfaces matching these tables in /src/types/database.ts
2. Build Zustand store for organization context
3. Create custom hooks:
   - useCurrentOrganization()
   - useCurrentUser()
   - useGrants() with filters
4. Add middleware to automatically inject organization_id in all queries

OUTPUT:
Complete database schema with RLS policies, TypeScript types, and React hooks ready to use.
```

---

### **FASE 3: Dashboard Principal + Tabla de Subvenciones**

**Prompt:**
```
Build the main dashboard with a professional grants table using TanStack Table and shadcn/ui.

DASHBOARD LAYOUT:
1. Top navigation bar:
   - Organization logo + name
   - Search bar (global grant search)
   - Notifications bell icon with badge
   - User avatar with dropdown menu
   - Dark mode toggle

2. Left sidebar (collapsible on mobile):
   - Dashboard (home icon)
   - Subvenciones (folder icon) - active
   - Calendario (calendar icon)
   - Analíticas (chart icon)
   - Configuración (settings icon)
   - Ayuda (help icon)

3. Main content area:
   - Page header: "Subvenciones" with action buttons
   - Quick stats cards (4 cards in a row):
     * Total grants captured this month
     * Grants expiring in 7 days (red alert)
     * Average relevance score
     * Total budget available
   - Filters panel (collapsible):
     * Source (BDNS/BOE multi-select)
     * Status dropdown
     * Budget range slider (0-500k€)
     * Date range picker (application deadline)
     * "Solo para ONG" checkbox
     * Clear all filters button
   - Action toolbar:
     * "Capturar Nuevas" button (primary, opens modal)
     * "Exportar a Excel" button
     * "Enviar a N8n" button (bulk action)
     * Bulk selection count badge
   - Grants table with advanced features

GRANTS TABLE FEATURES:
- Columns:
  1. Checkbox (bulk selection)
  2. Estado (status badge with color coding)
  3. Título (with source badge, truncate at 60 chars)
  4. Organismo (department name)
  5. Presupuesto (formatted currency, sortable)
  6. Fecha límite (days remaining badge, sortable)
  7. Prioridad IA (chip: Alta/Media/Baja)
  8. Exportado (✅/⏳/➖ icons)
  9. Acciones (3-dot menu: Ver, Editar, Eliminar, Exportar)

- Table interactions:
  * Click row to open detail drawer (slide from right)
  * Sortable columns (click header)
  * Row hover effect
  * Sticky header on scroll
  * Pagination (10/25/50/100 per page)
  * Loading skeleton during fetch
  * Empty state: "No se encontraron subvenciones" with CTA

- Real-time updates:
  * Use TanStack Query with 30-second refetch interval
  * Optimistic UI updates on status change
  * Toast notification on new grants

RESPONSIVE DESIGN:
- Desktop (>1024px): Full layout with sidebar
- Tablet (768-1023px): Collapsed sidebar, icons only
- Mobile (<767px): Bottom navigation, card view instead of table

STATE MANAGEMENT:
- Zustand store for:
  * Selected grant IDs (bulk actions)
  * Active filters
  * Sort configuration
  * Pagination state

PERFORMANCE:
- Virtual scrolling for large datasets (use @tanstack/react-virtual)
- Debounced search (300ms)
- Cached queries with React Query

OUTPUT:
A production-ready dashboard with fully interactive grants table.
```

---

### **FASE 4: Captura de Subvenciones (BDNS + BOE)**

**Prompt:**
```
Implement the grant capture system that fetches grants from external APIs (BDNS and BOE) and stores them in Supabase.

FRONTEND COMPONENTS:

1. **CaptureConfigDialog** (Modal component):
   - Tabs for "BDNS" and "BOE"

   BDNS Tab:
   - Date range picker (from/to) with smart defaults (last 30 days)
   - Max results slider (1-100)
   - Preview section showing active filter keywords
   - "Vista previa de filtros" expandable card:
     * Display 11 BDNS nonprofit keywords as chips
     * Link to edit keywords (opens FilterKeywordsManager)
   - "Capturar" button (primary, disabled during fetch)
   - Progress bar during capture

   BOE Tab:
   - Date range picker
   - Max results slider (1-50)
   - BOE section selector (dropdown: "Sección 3 - Subvenciones", etc.)
   - Preview of 44 grant keywords
   - "Procesar PDFs automáticamente" checkbox
   - Estimated time warning (PDFs take longer)
   - "Capturar" button

2. **FilterKeywordsManager** (Separate modal):
   - 3 tabs: "BDNS ONG", "BOE Subvenciones", "Personalizados"
   - Each tab shows keyword chips with remove (X) button
   - "Añadir keyword" input with + button
   - Save button (updates organization's filter_keywords table)
   - Restore defaults button

BACKEND INTEGRATION (Supabase Edge Functions):

Create 2 Edge Functions:

**Function 1: capture-bdns-grants**
```typescript
// This runs on Supabase Edge (Deno runtime)
// Calls BDNS API: https://www.infosubvenciones.es/bdnstrans/busquedasPublicas/busquedaGlobal.html

Input: {
  organizationId,
  dateFrom,
  dateTo,
  maxResults
}

Process:
1. Fetch from BDNS API with date range
2. Get organization's filter keywords from filter_keywords table
3. For each grant result:
   - Check if title/beneficiaries match nonprofit keywords
   - Calculate nonprofit_confidence (0-1 based on matches)
   - Assign relevance_score (informational only, don't filter)
4. Insert grants into 'grants' table with organization_id
5. Create activity log entry

Output: {
  captured: number,
  filtered: number,
  errors: string[]
}
```

**Function 2: capture-boe-grants**
```typescript
// Calls BOE API: https://www.boe.es/datosabiertos/

Input: {
  organizationId,
  dateFrom,
  dateTo,
  section,
  processPDFs
}

Process:
1. Search BOE by date range and section
2. Get organization's BOE grant keywords
3. For each result:
   - Match title against 44 grant keywords
   - If processPDFs=true:
     * Download PDF from BOE
     * Extract text using PDF parsing
     * Store in pdf_content field
   - Calculate relevance_score
4. Insert grants with organization_id

Output: {
  captured: number,
  pdfsProcessed: number,
  errors: string[]
}
```

FRONTEND LOGIC:
1. On "Capturar" click:
   - Validate date range (max 90 days)
   - Show loading state with progress indicator
   - Call Supabase Edge Function
   - Stream progress updates (use Server-Sent Events if possible)
   - On success:
     * Show success toast: "✅ 23 subvenciones capturadas"
     * Invalidate grants query (React Query)
     * Close modal
   - On error:
     * Show error details in modal
     * Allow retry

2. Filter preview:
   - Fetch current keywords from filter_keywords table
   - Display count: "11 palabras clave activas"
   - Make keywords editable inline

SMART DEFAULTS:
- BDNS date range: Last 30 days
- BOE date range: Last 7 days
- Max results: 50 for BDNS, 20 for BOE
- Process PDFs: OFF by default (warn about time)

ERROR HANDLING:
- Network timeout (30s)
- Rate limiting from APIs
- Duplicate grants (check grant_code)
- Invalid date ranges

OUTPUT:
Complete capture system with real-time progress and intelligent filtering.
```

---

### **FASE 5: Detalle de Subvención + Gestión de Estado**

**Prompt:**
```
Create a comprehensive grant detail view with status management and activity tracking.

GRANT DETAIL DRAWER (Slide-in from right, 60% viewport width):

HEADER SECTION:
- Grant title (truncate with tooltip on hover)
- Source badge (BDNS/BOE with icon)
- Close button (X)
- Action buttons row:
  * "Cambiar estado" dropdown
  * "Asignar a" user selector
  * "Exportar a Sheets" button
  * "Copiar enlace" button
  * "Eliminar" button (destructive, confirm dialog)

CONTENT TABS:
1. **Overview**:
   - Grant code (copyable)
   - Publishing department with logo (if available)
   - Budget: Large formatted number (€ 150.000)
   - Application dates:
     * Start: fecha + relative time (e.g., "hace 3 días")
     * End: fecha + countdown timer (e.g., "Quedan 12 días")
     * Business days calculator (exclude weekends + Spanish holidays)
   - Nonprofit classification:
     * Is nonprofit: Yes/No badge
     * Confidence: Progress bar (0-100%)
   - Sectors (multi-select chips)
   - Regions (map visualization with highlighted regions)
   - Beneficiary types (icon + label list)
   - Relevance score: Star rating (0-5 stars, informational)

2. **AI Analysis**:
   - Priority level: Large chip (Alta/Media/Baja) with explanation
   - Strategic value: Text paragraph from N8n AI analysis
   - Summary: AI-generated grant summary
   - "Regenerar análisis" button (calls N8n webhook)
   - Last analyzed: timestamp

3. **Documents**:
   - PDF viewer (if pdf_url exists):
     * Embedded PDF with zoom controls
     * Download PDF button
     * Extract text button (shows pdf_content in modal)
   - BOE/BDNS links (external)
   - "Subir documento adicional" button (Supabase Storage)

4. **Activity Log**:
   - Timeline of all actions:
     * Created by [user] on [date]
     * Status changed to [status] by [user]
     * Assigned to [user] by [user]
     * Note added by [user]
     * Exported to Sheets on [date]
   - "Añadir nota" text area at top

5. **Notes & Comments**:
   - Rich text editor (use Tiptap or similar)
   - Internal notes (not exported)
   - Mention other users (@username)
   - Attach files from Supabase Storage

STATUS MANAGEMENT:
- Status options: New, Reviewing, Applying, Applied, Rejected, Awarded
- Status change creates activity log entry
- Status badge color coding:
  * New: Gray
  * Reviewing: Blue
  * Applying: Yellow
  * Applied: Purple
  * Rejected: Red
  * Awarded: Green

ASSIGNMENT SYSTEM:
- Dropdown showing all organization members
- Avatar + name display
- Unassign option
- Email notification to assigned user (optional)

REAL-TIME COLLABORATION:
- Use Supabase Realtime subscriptions
- Show "User X is viewing this grant" indicator
- Optimistic updates for status/assignment changes

MOBILE OPTIMIZATION:
- Drawer becomes full-screen modal on mobile
- Tabs become accordion sections
- Simplified action buttons (overflow menu)

KEYBOARD SHORTCUTS:
- ESC: Close drawer
- Ctrl+E: Change status
- Ctrl+A: Assign
- Ctrl+N: Add note

OUTPUT:
A feature-rich grant detail view rivaling commercial project management tools.
```

---

### **FASE 6: Integración con N8n (AI Analysis + Webhooks)**

**Prompt:**
```
Implement bidirectional N8n webhook integration for AI-powered grant analysis and Google Sheets export tracking.

ARCHITECTURE:
```
Frontend → Supabase Edge Function → N8n Workflow → Callback to Supabase
                                         ↓
                                   (AI Analysis via OpenAI)
                                   (Google Sheets Export)
```

SUPABASE EDGE FUNCTIONS:

**Function: send-to-n8n**
```typescript
// Triggered manually or automatically on new grants

Input: { grantIds: string[], action: 'analyze' | 'export' }

Process:
1. Fetch grant details from database
2. Format payload for N8n webhook
3. Send POST to N8N_WEBHOOK_URL (from env)
4. Mark grants as "processing" in database
5. Return tracking ID

Payload format:
{
  "action": "analyze" | "export",
  "grants": [
    {
      "id": "uuid",
      "title": "string",
      "department": "string",
      "budget": number,
      "sectors": string[],
      "deadline": "ISO date",
      "pdf_content": "string",
      "callback_url": "https://[project].supabase.co/functions/v1/n8n-callback"
    }
  ],
  "organization_id": "uuid"
}
```

**Function: n8n-callback** (receives results)
```typescript
// Webhook endpoint for N8n to send results back

Input (from N8n):
{
  "grant_id": "uuid",
  "action": "analyze" | "export",

  // For analysis:
  "priority": "high" | "medium" | "low",
  "strategic_value": "string",
  "summary": "string",

  // For export:
  "sheets_url": "string",
  "row_id": "string",
  "status": "success" | "error",
  "error_message": "string"
}

Process:
1. Validate webhook signature (security)
2. Update grant record:
   - If analysis: Update ai_priority, ai_strategic_value, summary
   - If export: Update google_sheets_exported, google_sheets_url, google_sheets_row_id
3. Create activity log entry
4. Trigger real-time update to frontend (Supabase Realtime)
5. Send browser notification if user is online

Return: { success: true }
```

FRONTEND COMPONENTS:

**N8nAnalysisButton**:
- Button in grants table and detail drawer
- Bulk action for multiple grants
- Shows loading state: "Analizando... (2/5)"
- Disables if already analyzed recently
- Tooltip: "Analizar con IA" on hover

**SheetsExportButton**:
- Visual states:
  * Not exported: "Exportar a Sheets" (green button)
  * Processing: ⏳ amber spinner
  * Exported: ✅ green checkmark + clickable link
- Bulk export modal:
  * Select template (dropdown)
  * Preview first 3 rows
  * "Exportar [X] subvenciones" button

**WebhookStatus** (component in settings):
- Shows N8n webhook health:
  * Last successful call
  * Total calls today
  * Error rate
- Test webhook button
- View webhook logs (last 50 calls)

N8N WORKFLOW STRUCTURE (Document for user):
```
1. Webhook Trigger (receives from Supabase)
2. IF node: Check action type

   Branch A: Analyze
   3a. OpenAI Node: Generate analysis
   4a. Format response
   5a. HTTP Request: Send to callback URL

   Branch B: Export to Sheets
   3b. Google Sheets Node: Append row
   4b. Get Sheet URL + Row ID
   5b. HTTP Request: Send to callback URL

6. Respond to Webhook (200 OK)
```

SECURITY:
- Validate webhook signatures using shared secret
- Rate limiting: Max 100 grants per minute
- Store N8N_WEBHOOK_URL in Supabase secrets (not .env)
- Encrypt sensitive data in transit

ERROR HANDLING:
- Retry logic: 3 attempts with exponential backoff
- Dead letter queue for failed webhooks
- Admin notification on 5+ consecutive failures
- User-friendly error messages

REAL-TIME UPDATES:
- Subscribe to grant changes:
  ```typescript
  supabase
    .channel('grants')
    .on('postgres_changes',
      { event: 'UPDATE', schema: 'public', table: 'grants' },
      payload => {
        // Update UI with new ai_priority, sheets_url, etc.
      }
    )
    .subscribe()
  ```

OUTPUT:
Complete N8n integration with real-time feedback and robust error handling.
```

---

### **FASE 7: Analíticas + Dashboard Metrics**

**Prompt:**
```
Build a comprehensive analytics dashboard with charts, KPIs, and insights using Recharts.

ANALYTICS PAGE LAYOUT:

TOP KPI CARDS (4 cards responsive grid):
1. **Total Grants YTD**:
   - Large number (e.g., 247)
   - Trend indicator: +12% vs last month (green/red arrow)
   - Mini line chart (last 6 months)

2. **Total Budget Available**:
   - Formatted currency: €12.4M
   - Average grant size: €50k
   - Largest grant: €500k (with link)

3. **Grants Expiring Soon**:
   - Count of grants ending in <7 days
   - Urgency indicator (red if >5)
   - "View all" link

4. **Win Rate**:
   - Percentage: 23% (Awarded / Applied)
   - Comparison to industry average
   - Trend: +5% vs last quarter

CHARTS SECTION (2-column grid):

**Chart 1: Grants Captured Over Time**
- Type: Area chart (Recharts AreaChart)
- X-axis: Last 12 months
- Y-axis: Number of grants
- Two data series:
  * BDNS (blue fill)
  * BOE (green fill)
- Stacked view
- Tooltip showing exact numbers + date
- Legend with toggle to show/hide series

**Chart 2: Budget Distribution by Sector**
- Type: Pie chart with customized labels
- Data: Sum of total_budget grouped by sectors
- Colors: Palette of 8 distinct colors
- Labels: Sector name + percentage
- Interactive: Click slice to filter grants table
- Center text: "Total: €X.XM"

**Chart 3: Grant Status Funnel**
- Type: Funnel chart (use Recharts custom shape)
- Stages: New → Reviewing → Applying → Applied → Awarded
- Show conversion rates between stages
- Color-coded by stage
- Click stage to see grants in that status

**Chart 4: AI Priority Distribution**
- Type: Horizontal bar chart
- 3 bars: High, Medium, Low priority
- Show count + percentage
- Click to filter main grants table

**Chart 5: Timeline of Application Deadlines**
- Type: Gantt-style timeline
- X-axis: Next 90 days
- Y-axis: Grant titles (top 20 by budget)
- Bars colored by priority
- Today indicator (vertical line)
- Hover: Show full grant details

**Chart 6: Nonprofit vs General Grants**
- Type: Donut chart
- Inner ring: Count of grants
- Outer ring: Total budget
- Legend with is_nonprofit filter

FILTERS PANEL (top of analytics page):
- Date range selector (preset: This month, Quarter, Year, Custom)
- Source filter (BDNS/BOE checkboxes)
- "Solo alta prioridad" toggle
- "Export report" button (PDF generation)

INSIGHTS SECTION (AI-powered):
- Card with "Key Insights" header
- 3-5 bullet points auto-generated:
  * "80% of high-priority grants are from BDNS"
  * "Average time to deadline decreased 15% this month"
  * "Education sector has 3x more budget than last quarter"
- "Refresh insights" button (calls OpenAI via N8n)

INTERACTIVE FEATURES:
- Click any chart element → Filter main grants table
- Sync filters across all charts (use Zustand)
- Download chart as PNG (Recharts built-in)
- Export data as CSV

PERFORMANCE:
- Lazy load charts (React.lazy)
- Use React Query to cache analytics data (5-minute stale time)
- Debounce filter changes (500ms)
- Virtual scrolling for large datasets

RESPONSIVE DESIGN:
- Desktop: 2-column chart grid
- Tablet: 1-column, full-width charts
- Mobile: Scroll horizontally for wide charts, simplified views

REAL-TIME UPDATES:
- Refetch analytics every 60 seconds
- Show "Updated X seconds ago" timestamp
- Pulse animation on data refresh

OUTPUT:
A stunning analytics dashboard that rivals enterprise BI tools like Tableau.
```

---

### **FASE 8: Exportación a Excel + Calendario**

**Prompt:**
```
Implement professional Excel export with calculated deadlines and a visual calendar of application dates.

EXCEL EXPORT FEATURE:

**ExcelExportDialog** component:
- Triggered from grants table "Exportar a Excel" button
- Modal with configuration options:

  Template selection:
  - [ ] Standard Report
  - [ ] Detailed Analysis (includes AI insights)
  - [ ] Compliance Checklist
  - [ ] Custom (user can select columns)

  Date calculations:
  - [x] Calculate business days to deadline (exclude weekends + Spanish holidays)
  - [x] Highlight grants expiring in <7 days (red row)

  Formatting:
  - [ ] Include charts (miniature versions from analytics)
  - [ ] Add organization logo as header
  - [x] Professional styling (borders, colors, frozen header)

  Filters:
  - Export only selected grants OR all filtered grants
  - Show preview: "Will export X grants"

**Backend Logic** (Supabase Edge Function: generate-excel):
```typescript
// Use SheetJS (xlsx) library for Excel generation

Input: {
  grantIds: string[],
  template: string,
  includeCharts: boolean
}

Process:
1. Fetch grant data from database
2. Calculate business days to deadline:
   - Load Spanish national holidays from holidays-es library
   - Exclude weekends (Saturday, Sunday)
   - Count remaining workdays
3. Format data for Excel:
   - Currency: €XX.XXX,XX (Spanish format)
   - Dates: DD/MM/YYYY
   - Percentages: XX,X%
4. Create Excel workbook:
   - Sheet 1: Grants list (formatted table)
   - Sheet 2: Summary statistics
   - Sheet 3: Charts (if includeCharts)
5. Apply styling:
   - Header row: Bold, blue background, white text
   - Frozen top row
   - Auto-width columns
   - Conditional formatting:
     * Red fill for deadline <7 days
     * Green fill for nonprofit grants
6. Return Excel file as Blob

Output: Excel file download
```

**Column structure**:
| Título | Organismo | Fuente | Presupuesto | Fecha Inicio | Fecha Límite | Días Hábiles | Prioridad IA | Estado | Sectores | Regiones |

**Advanced features**:
- Formulas in Excel: SUM of budgets, COUNT of grants per sector
- Pivot table sheet (optional)
- Data validation dropdowns for Status column

CALENDAR FEATURE:

**GrantsCalendar** component (new page):
- Use @fullcalendar/react library
- Month view by default (also Week and List views available)

**Calendar events**:
- Each grant is an event
- Event date = application_end_date
- Event color = AI priority:
  * High: Red
  * Medium: Orange
  * Low: Green
- Event title = Grant title (truncated)
- Click event → Open GrantDetailDrawer

**Calendar features**:
- "Today" button
- Navigation arrows (previous/next month)
- Mini calendar in sidebar
- Filter panel:
  * Show only high priority
  * Show only nonprofit
  * Source filter
- Export calendar to .ics file (for Google Calendar, Outlook)

**Deadline reminders**:
- Settings page option: "Email reminders"
  * 7 days before deadline
  * 3 days before deadline
  * 1 day before deadline
- Use Supabase Edge Function with cron trigger
- Send via email (use Resend or SendGrid)

BUSINESS DAYS CALCULATION:
```typescript
// Helper function (use date-fns + holidays-es)
import {
  differenceInBusinessDays,
  isWeekend,
  parseISO
} from 'date-fns';
import { getHolidays } from 'holidays-es';

function calculateBusinessDays(deadline: string): number {
  const today = new Date();
  const endDate = parseISO(deadline);
  const holidays = getHolidays(today.getFullYear());

  let businessDays = differenceInBusinessDays(endDate, today);

  // Subtract Spanish holidays
  holidays.forEach(holiday => {
    if (holiday.date >= today && holiday.date <= endDate) {
      businessDays--;
    }
  });

  return businessDays;
}
```

OUTPUT:
Professional Excel exports and interactive calendar for deadline management.
```

---

### **FASE 9: Sistema de Suscripciones (Stripe + Planes)**

**Prompt:**
```
Implement a complete subscription system with Stripe integration for SaaS monetization.

PRICING PLANS:

**Free Plan**:
- Max 5 users
- 50 grants/month capture limit
- Basic filters
- Excel export (no charts)
- Community support
- Price: €0/month

**Pro Plan** (Most popular):
- Max 20 users
- Unlimited grant capture
- Advanced filters + saved searches
- AI analysis (100 credits/month)
- Excel export with charts
- Google Sheets auto-export
- Email reminders
- Priority support
- Price: €99/month

**Enterprise Plan**:
- Unlimited users
- Unlimited everything
- Custom filter keywords
- API access
- White-label option
- Dedicated account manager
- SSO (SAML)
- Price: €499/month (custom pricing available)

STRIPE INTEGRATION:

**Supabase Edge Function: create-checkout-session**
```typescript
import Stripe from 'stripe';

Input: {
  priceId: string, // Stripe Price ID
  organizationId: string
}

Process:
1. Initialize Stripe with secret key (from env)
2. Create checkout session:
   - Mode: 'subscription'
   - Customer email: current user's email
   - Success URL: /settings/billing?success=true
   - Cancel URL: /settings/billing?canceled=true
   - Metadata: { organizationId }
3. Return session URL

Output: { url: 'https://checkout.stripe.com/...' }
```

**Stripe Webhook Handler** (Edge Function: stripe-webhook):
```typescript
// Handles events from Stripe

Events to handle:
1. checkout.session.completed:
   - Update organization.plan_tier
   - Set organization.subscription_status = 'active'
   - Create activity log

2. customer.subscription.updated:
   - Upgrade/downgrade plan
   - Update max_users limit

3. customer.subscription.deleted:
   - Set subscription_status = 'cancelled'
   - Downgrade to free plan
   - Email notification

4. invoice.payment_failed:
   - Set subscription_status = 'past_due'
   - Send warning email
   - Lock features after 7 days

Security: Verify webhook signature
```

FRONTEND COMPONENTS:

**PricingPage** (public, before login):
- 3-column responsive grid
- Plan cards with:
  * Plan name + badge (if popular)
  * Price (large, formatted)
  * Feature list with checkmarks
  * CTA button: "Empezar prueba gratis" / "Suscribirse"
- Toggle: Monthly / Annual (20% discount)
- FAQ section below
- Testimonials from real organizations

**BillingSettings** (inside app, /settings/billing):
- Current plan card:
  * Plan name + tier badge
  * Billing cycle (monthly/annual)
  * Next billing date
  * Usage metrics:
    - Users: 3/20
    - Grants captured this month: 127/unlimited
    - AI credits: 45/100
  * "Upgrade plan" / "Cancel subscription" buttons

- Payment method:
  * Card ending in XXXX (Stripe)
  * "Update card" button → Opens Stripe customer portal

- Billing history:
  * Table of invoices (last 12 months)
  * Download invoice PDF button

- Danger zone:
  * "Cancel subscription" (opens confirmation modal)
  * "Delete organization" (requires password)

**UsageLimitsIndicator** (shown across app):
- When approaching limits:
  * Toast notification: "⚠️ Has usado 45/50 capturas este mes"
  * Banner in dashboard
  * CTA to upgrade

**TrialBanner** (for new organizations):
- "🎉 Estás en periodo de prueba (quedan 12 días)"
- "Actualiza ahora y obtén 20% descuento"
- Dismissible

BILLING ENFORCEMENT:

**Middleware to check limits**:
```typescript
async function canCaptureGrants(organizationId: string): boolean {
  const org = await getOrganization(organizationId);

  if (org.plan_tier === 'free') {
    const capturedThisMonth = await countGrantsThisMonth(organizationId);
    return capturedThisMonth < 50;
  }

  return true; // Unlimited for paid plans
}
```

**Feature flags by plan**:
```typescript
const features = {
  free: ['basic_filters', 'excel_export'],
  pro: ['basic_filters', 'excel_export', 'ai_analysis', 'sheets_export', 'reminders'],
  enterprise: ['*'] // All features
};

function hasFeature(org: Organization, feature: string): boolean {
  return features[org.plan_tier].includes(feature) ||
         features[org.plan_tier].includes('*');
}
```

CUSTOMER PORTAL:
- Use Stripe Customer Portal (no custom UI needed)
- Allow users to:
  * Update payment method
  * Download invoices
  * Cancel subscription
  * View usage

ANALYTICS FOR ADMIN:
- MRR (Monthly Recurring Revenue)
- Churn rate
- LTV (Lifetime Value)
- Conversion rate (trial → paid)

OUTPUT:
Complete subscription system ready for commercial launch.
```

---

### **FASE 10: Optimización, SEO y Deploy**

**Prompt:**
```
Finalize the SaaS for production: performance optimization, SEO, security hardening, and deployment.

PERFORMANCE OPTIMIZATION:

1. **Code Splitting**:
   - Lazy load all routes:
     ```typescript
     const Dashboard = lazy(() => import('./pages/Dashboard'));
     const Analytics = lazy(() => import('./pages/Analytics'));
     ```
   - Lazy load heavy components (Calendar, Charts)
   - Use Suspense with loading skeletons

2. **Image Optimization**:
   - Convert all images to WebP format
   - Use responsive images (srcset)
   - Lazy load images below fold (use Intersection Observer)
   - Organization logos: max 200KB

3. **Bundle Optimization**:
   - Run `npm run build -- --analyze`
   - Tree-shake unused code
   - Move React Query to separate chunk
   - Compress with Brotli

4. **Caching Strategy**:
   - Set long cache headers for static assets (365 days)
   - Implement Service Worker for offline support
   - Use React Query's staleTime aggressively:
     * Grants list: 30 seconds
     * Analytics: 5 minutes
     * User profile: Infinity (until logout)

5. **Database Optimization**:
   - Add indexes to frequently queried columns
   - Use database connection pooling (Supabase Postgres)
   - Implement cursor-based pagination for large tables

SEO OPTIMIZATION:

**Meta tags** (use react-helmet-async):
```tsx
<Helmet>
  <title>Gestor de Subvenciones para ONG | GrantFlow</title>
  <meta name="description" content="Automatiza la búsqueda y gestión de subvenciones españolas. IA integrada, filtros inteligentes y exportación a Excel." />
  <meta property="og:title" content="GrantFlow - Gestión Inteligente de Subvenciones" />
  <meta property="og:description" content="Encuentra subvenciones de BDNS y BOE automáticamente" />
  <meta property="og:image" content="/og-image.png" />
  <meta property="og:type" content="website" />
  <meta name="twitter:card" content="summary_large_image" />

  {/* Structured data */}
  <script type="application/ld+json">
    {JSON.stringify({
      "@context": "https://schema.org",
      "@type": "SoftwareApplication",
      "name": "GrantFlow",
      "applicationCategory": "BusinessApplication",
      "offers": {
        "@type": "Offer",
        "price": "99",
        "priceCurrency": "EUR"
      }
    })}
  </script>
</Helmet>
```

**Landing page** (public, for SEO):
- Hero section with value proposition
- Features section (with keywords: "subvenciones BDNS", "ayudas BOE", etc.)
- Testimonials
- Pricing preview
- CTA: "Empieza gratis"

**Blog** (optional, for content marketing):
- Guides: "Cómo solicitar subvenciones para ONG"
- Use case stories
- Built with MDX (next-mdx-remote)

**robots.txt**:
```
User-agent: *
Allow: /
Disallow: /app/
Disallow: /settings/

Sitemap: https://grantflow.app/sitemap.xml
```

**sitemap.xml**:
- Auto-generated (use sitemap library)
- Include public pages only

SECURITY HARDENING:

1. **Content Security Policy**:
   ```typescript
   // In index.html
   <meta http-equiv="Content-Security-Policy"
         content="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' https://*.supabase.co https://api.stripe.com;">
   ```

2. **Environment Variables**:
   - Never expose secrets in frontend
   - Use Supabase Edge Function secrets for:
     * Stripe secret key
     * N8N webhook URL
     * OpenAI API key
   - Frontend only needs public keys

3. **Rate Limiting**:
   - Supabase: Enable rate limiting on Edge Functions (100 req/min per IP)
   - Login attempts: Max 5 per 15 minutes
   - Grant capture: Max 3 per minute

4. **Input Validation**:
   - Use Zod schemas for all forms
   - Sanitize user input (prevent XSS)
   - SQL injection protection (use parameterized queries)

5. **Authentication Security**:
   - Require email verification
   - Strong password policy (min 8 chars, 1 number, 1 symbol)
   - Optional 2FA (TOTP via Supabase)
   - Auto-logout after 7 days of inactivity

MONITORING & ANALYTICS:

1. **Error Tracking**:
   - Integrate Sentry:
     ```typescript
     Sentry.init({
       dsn: "...",
       environment: import.meta.env.MODE,
       tracesSampleRate: 0.1
     });
     ```
   - Error boundaries with Sentry reporting

2. **User Analytics**:
   - PostHog or Plausible (GDPR-compliant)
   - Track events:
     * Grant captured
     * Export to Excel
     * Subscription upgrade
     * Feature usage
   - Avoid tracking PII

3. **Performance Monitoring**:
   - Lighthouse CI in GitHub Actions
   - Core Web Vitals thresholds:
     * LCP < 2.5s
     * FID < 100ms
     * CLS < 0.1
   - Alert on degradation

DEPLOYMENT (Netlify):

1. **Build Configuration** (netlify.toml):
   ```toml
   [build]
     publish = "dist"
     command = "npm run build"

   [build.environment]
     NODE_VERSION = "20"

   [[redirects]]
     from = "/*"
     to = "/index.html"
     status = 200

   [[headers]]
     for = "/*"
     [headers.values]
       X-Frame-Options = "DENY"
       X-Content-Type-Options = "nosniff"
       Referrer-Policy = "strict-origin-when-cross-origin"
   ```

2. **Environment Variables** (Netlify dashboard):
   - VITE_SUPABASE_URL
   - VITE_SUPABASE_ANON_KEY
   - VITE_STRIPE_PUBLISHABLE_KEY

3. **Custom Domain**:
   - Set up: www.grantflow.app
   - Enable HTTPS (automatic with Netlify)
   - Configure DNS (A record to Netlify)

4. **Preview Deployments**:
   - Automatic for all Pull Requests
   - Use Netlify branch deploys for staging

FINAL CHECKS:

- [ ] Run Lighthouse audit (score >90 on all metrics)
- [ ] Test on mobile devices (iOS Safari, Android Chrome)
- [ ] Cross-browser testing (Chrome, Firefox, Safari, Edge)
- [ ] Load testing (simulate 100 concurrent users)
- [ ] Accessibility audit (WCAG AA compliance)
- [ ] GDPR compliance:
  * Privacy policy page
  * Cookie consent banner
  * Data export/delete features
- [ ] Terms of Service page
- [ ] Contact page with support form

LAUNCH CHECKLIST:

- [ ] Domain purchased and configured
- [ ] SSL certificate active
- [ ] Monitoring dashboards set up
- [ ] Stripe live mode enabled
- [ ] N8n workflows tested in production
- [ ] Backups configured (Supabase automatic backups)
- [ ] Status page (e.g., status.grantflow.app)
- [ ] Customer support system (Intercom or Crisp chat)
- [ ] Email sequences for onboarding (Resend or SendGrid)
- [ ] Blog post announcing launch
- [ ] Social media posts scheduled

OUTPUT:
A production-ready, commercially viable SaaS platform ready for paying customers.
```

---

## 🎨 Tech Stack Recomendado

### Frontend
- **Framework**: React 18 + TypeScript + Vite
- **UI Library**: shadcn/ui + Tailwind CSS
- **State Management**: Zustand (simple, performant)
- **Data Fetching**: TanStack Query (React Query v5)
- **Forms**: React Hook Form + Zod
- **Charts**: Recharts
- **Tables**: TanStack Table v8
- **Calendar**: FullCalendar
- **Date Handling**: date-fns + holidays-es
- **PDF Viewer**: react-pdf
- **Rich Text**: Tiptap (if needed for notes)

### Backend
- **Database**: Supabase PostgreSQL
- **Auth**: Supabase Auth (email/password, magic links, OAuth)
- **Storage**: Supabase Storage (for PDFs, logos)
- **Functions**: Supabase Edge Functions (Deno runtime)
- **Realtime**: Supabase Realtime subscriptions

### External Services
- **Payments**: Stripe (subscriptions + customer portal)
- **Automation**: N8n (self-hosted or cloud)
- **Email**: Resend or SendGrid
- **Analytics**: PostHog (GDPR-compliant) or Plausible
- **Error Tracking**: Sentry
- **Monitoring**: Better Uptime or Uptime Robot

### Deployment
- **Frontend**: Netlify (or Vercel)
- **Backend**: Supabase Cloud
- **CDN**: Cloudflare (for assets)

---

## 💡 Best Practices de Bolt

### ✅ DO's

1. **Start with Global Prompt**: Configure project-level instructions first
2. **Be Extremely Specific**: Mention exact libraries, color codes, component names
3. **Build Incrementally**: One phase at a time, test before moving on
4. **Use Enhance Prompt**: Click the ✨ icon before submitting complex prompts
5. **Target Files**: Right-click files to focus Bolt's attention
6. **Show Examples**: Include code snippets of desired output
7. **Define Success Criteria**: "Output should include X, Y, Z"

### ❌ DON'Ts

1. **Avoid Vague Requests**: "Make it better" → Specify what to improve
2. **Don't Overload**: Break 200-line prompts into 3-4 smaller ones
3. **Don't Skip Testing**: Verify each phase works before proceeding
4. **Don't Assume Context**: Bolt doesn't remember previous sessions (use project prompts)
5. **Don't Rush**: Quality > Speed. Better to iterate than rebuild.

### 🔥 Pro Tips

- **Use "Continue"**: If Bolt stops mid-generation, just say "continue from where you stopped"
- **Reference Previous Work**: "Using the GrantsTable component we built, add..."
- **Ask for Explanations**: "Explain the N8n integration flow you just implemented"
- **Request Alternatives**: "Show me 2 approaches for handling file uploads"
- **Leverage Templates**: Ask Bolt to create reusable templates (e.g., "Create a standard API error handler")

---

## ✅ Checklist Pre-Comercialización

### Legal & Compliance
- [ ] Privacy Policy página (GDPR-compliant)
- [ ] Terms of Service página
- [ ] Cookie consent banner (uses cookies-consent library)
- [ ] Data export feature (user can download all their data)
- [ ] Data deletion feature (GDPR right to be forgotten)
- [ ] Refund policy (clear, fair)

### Marketing Assets
- [ ] Logo profesional (SVG + PNG)
- [ ] Favicon set (multiple sizes)
- [ ] OG images para social sharing
- [ ] Screenshots para landing page
- [ ] Demo video (2-3 minutos)
- [ ] Case study (1 real customer)

### Documentation
- [ ] User guide / Knowledge base
- [ ] API documentation (if offering API access)
- [ ] Video tutorials (YouTube channel)
- [ ] FAQ page
- [ ] Changelog page (show product updates)

### Support System
- [ ] In-app chat (Crisp or Intercom)
- [ ] Help center (searchable articles)
- [ ] Email support address (support@grantflow.app)
- [ ] Ticket system (for Enterprise)
- [ ] Response time SLA (24h for Pro, 4h for Enterprise)

### Onboarding
- [ ] Welcome email sequence (5 emails over 2 weeks)
- [ ] In-app product tour (use Shepherd.js or Intro.js)
- [ ] Quick start checklist (shown in dashboard)
- [ ] Sample data (pre-populate 5 demo grants)
- [ ] Video walkthroughs linked from UI

### Monitoring & Alerts
- [ ] Uptime monitoring (Better Uptime)
- [ ] Error tracking configured (Sentry)
- [ ] Performance monitoring (Lighthouse CI)
- [ ] Conversion funnel tracking (PostHog)
- [ ] Alert for critical errors (Slack/email)
- [ ] Daily metrics email (MRR, new signups, churn)

### Security Audit
- [ ] Penetration testing (hire professional if budget allows)
- [ ] Dependency audit (`npm audit`)
- [ ] Secrets rotation policy
- [ ] Backup testing (can you restore from backup?)
- [ ] Disaster recovery plan documented

### Launch Strategy
- [ ] Beta tester group (10-20 organizations)
- [ ] Launch on Product Hunt (prepare for launch day)
- [ ] LinkedIn posts (founder's personal account)
- [ ] Paid ads campaign (Google Ads, Meta Ads)
- [ ] SEO-optimized blog content (10 articles pre-launch)
- [ ] Partnerships with nonprofit associations
- [ ] Press release (send to TechCrunch, etc.)

---

## 🚦 Orden de Ejecución

**Día 1**: Fases 1-2 (Auth + Database)
**Día 2**: Fases 3-4 (Dashboard + Capture)
**Día 3**: Fases 5-6 (Detail view + N8n)
**Día 4**: Fases 7-8 (Analytics + Export)
**Día 5**: Fase 9 (Subscriptions)
**Día 6**: Fase 10 (Optimization + Deploy)
**Día 7**: Testing + Polish

---

## 📚 Recursos Adicionales

**Documentación Oficial**:
- [Bolt.new Docs](https://support.bolt.new/)
- [Supabase Docs](https://supabase.com/docs)
- [shadcn/ui Components](https://ui.shadcn.com/)
- [TanStack Query](https://tanstack.com/query/latest)

**Bolt Community**:
- [Bolt Discord](https://discord.com/invite/stackblitz)
- [Bolters.io Community Guide](https://bolters.io/)

**Inspiration**:
- [Real SaaS built with Bolt](https://softwareontheroad.com/no-code-saas-mvp-bolt-new-guide)

---

## 🎯 Ejemplo de Prompt Completo (Fase 1)

Para que veas cómo se ve un prompt listo para Bolt:

```
Create the foundation for "GrantFlow", a multi-tenant SaaS platform for managing Spanish government grants targeting nonprofit organizations.

TECH STACK:
- React 18 + TypeScript + Vite
- Tailwind CSS 3.4
- shadcn/ui components
- Supabase for backend (auth + database)
- Zustand for state management

INITIAL SETUP:
1. Initialize Vite project with React-TS template
2. Install dependencies:
   - @supabase/supabase-js
   - @radix-ui/react-* (via shadcn/ui)
   - tailwindcss
   - zustand
   - react-router-dom
   - zod
   - react-hook-form

3. Configure Tailwind with custom theme:
   - Primary color: #0066CC (blue)
   - Secondary color: #10B981 (green)
   - Font: Inter from Google Fonts

4. Install shadcn/ui and add these components:
   - Button, Card, Dialog, Form, Input, Label, Select, Toast

PROJECT STRUCTURE:
src/
├── components/
│   ├── ui/ (shadcn components)
│   ├── auth/
│   │   ├── LoginForm.tsx
│   │   ├── RegisterForm.tsx
│   │   └── AuthGuard.tsx
│   └── layout/
│       ├── Header.tsx
│       └── Footer.tsx
├── pages/
│   ├── LoginPage.tsx
│   ├── RegisterPage.tsx
│   └── DashboardPage.tsx
├── lib/
│   ├── supabase.ts (client initialization)
│   └── utils.ts
├── hooks/
│   └── useAuth.ts
├── stores/
│   └── authStore.ts (Zustand)
└── types/
    └── index.ts

SUPABASE CONFIGURATION:
1. Create supabase client in lib/supabase.ts:
   - Use environment variables for SUPABASE_URL and SUPABASE_ANON_KEY
   - Export typed client

2. Create useAuth hook:
   - signUp(email, password)
   - signIn(email, password)
   - signOut()
   - user state
   - loading state

3. Create AuthGuard component:
   - Redirects to /login if not authenticated
   - Shows loading spinner while checking auth

AUTHENTICATION UI:

LoginForm component:
- Email input with validation
- Password input with show/hide toggle
- "Recordarme" checkbox
- "Iniciar sesión" button (primary)
- "¿Olvidaste tu contraseña?" link
- "¿No tienes cuenta? Regístrate" link
- Google login button (secondary)
- Error message display with toast

RegisterForm component:
- Organization name input
- Email input
- Password input (with strength indicator)
- Confirm password input
- "Acepto los términos y condiciones" checkbox
- "Crear cuenta" button
- "¿Ya tienes cuenta? Inicia sesión" link

PAGES:

LoginPage:
- Centered card with logo
- LoginForm component
- Footer with privacy links
- Background gradient (blue to green)

RegisterPage:
- Similar layout to LoginPage
- RegisterForm component

DashboardPage:
- Protected by AuthGuard
- Header with user avatar + logout
- Placeholder content: "Dashboard próximamente"

ENVIRONMENT SETUP:
Create .env.local file structure:
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_anon_key

ROUTING:
- / → Redirect to /dashboard if authenticated, else /login
- /login → LoginPage
- /register → RegisterPage
- /dashboard → DashboardPage (protected)

STYLING REQUIREMENTS:
- Mobile-first responsive design
- Smooth transitions (200ms ease)
- Focus states for accessibility
- Loading states for all async actions
- Toast notifications for errors/success

OUTPUT CHECKLIST:
✅ User can register with email/password
✅ User receives verification email
✅ User can log in after verification
✅ Protected routes work correctly
✅ Logout functionality works
✅ UI is professional and responsive
✅ No console errors

Please create this foundation and confirm when ready to proceed to Phase 2 (Database Schema).
```

---

## 🎬 ¡Listo para Empezar!

Con esta guía, tienes todo lo necesario para construir un SaaS profesional en Bolt.new.

**Recuerda**:
1. Configura el **Project Prompt** primero
2. Ejecuta las fases **secuencialmente**
3. **Prueba cada fase** antes de continuar
4. **Ajusta los prompts** según las respuestas de Bolt
5. **No te saltes** la Fase 10 (optimization)

**¡Éxito con tu SaaS!** 🚀
