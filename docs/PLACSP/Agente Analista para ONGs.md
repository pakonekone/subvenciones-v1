Plan: Agente Analista Inteligente para ONGs/Fundaciones

     Resumen Ejecutivo

     Transformar el chatbot actual en un Agente Analista que conoce el perfil de la organización del 
     usuario y puede evaluar automáticamente la elegibilidad para cada convocatoria, generar documentos y
      emitir alertas proactivas.

     Usuario objetivo: ONGs, Fundaciones, Asociaciones (comportamiento similar a PYME)

     Simplificación clave: Una organización por usuario, no múltiples clientes.

     ---
     Jobs To Be Done

     JTBD Principal

     "Cuando veo una nueva convocatoria, quiero saber en segundos si mi organización puede aplicar y qué 
     requisitos cumplimos o no."

     JTBD Secundarios

     1. Evaluación de elegibilidad
     "Preguntarle al agente '¿Podemos aplicar a esta convocatoria?' y recibir análisis de requisitos 
     cumplidos/pendientes."
     2. Generación de documentos
     "Que el agente genere un borrador de memoria técnica adaptado a nuestro perfil y los requisitos de 
     la convocatoria."
     3. Alertas proactivas
     "Que el sistema me avise: 'Nueva convocatoria con 85% de match para tu organización'."

     ---
     Arquitectura Simplificada

     Modelo de Datos

     ┌─────────────────────┐
     │  OrganizationProfile │  ← UNO por usuario (user_id)
     ├─────────────────────┤
     │  name               │
     │  cif                │
     │  organization_type  │  (fundacion, asociacion, ong, cooperativa)
     │  sectors[]          │  (accion_social, educacion, medioambiente...)
     │  regions[]          │  (ES41, ES30...)
     │  annual_budget      │
     │  employee_count     │
     │  founding_year      │
     │  capabilities[]     │  (gestion_proyectos_ue, atencion_menores...)
     │  statutes_summary   │  (resumen AI de estatutos)
     │  activity_summary   │  (qué hacemos, misión)
     └─────────────────────┘
              │
              ▼
     ┌─────────────────────┐
     │  GrantApplication   │  ← Histórico de aplicaciones
     ├─────────────────────┤
     │  grant_id           │
     │  status             │  (draft, submitted, approved, rejected)
     │  match_score        │
     │  eligibility_analysis│
     │  amount_requested   │
     │  amount_granted     │
     └─────────────────────┘

     Backend: Nuevo Modelo

     # backend/app/models/organization_profile.py

     class OrganizationProfile(Base):
         __tablename__ = "organization_profiles"

         id = Column(UUID, primary_key=True, default=uuid.uuid4)
         user_id = Column(String, unique=True, index=True)  # Un perfil por usuario

         # Datos básicos
         name = Column(String, nullable=False)
         cif = Column(String)
         organization_type = Column(String)  # fundacion, asociacion, ong, cooperativa

         # Perfil para matching
         sectors = Column(JSON, default=list)       # ["accion_social", "educacion"]
         regions = Column(JSON, default=list)       # ["ES41", "ES30"]
         annual_budget = Column(Float)              # Presupuesto anual
         employee_count = Column(Integer)
         founding_year = Column(Integer)

         # Capacidades (para matching)
         capabilities = Column(JSON, default=list)  # ["proyectos_europeos", "menores"]

         # Resúmenes AI
         statutes_summary = Column(Text)            # De qué va la organización
         activity_summary = Column(Text)            # Qué hacemos, misión

         created_at = Column(DateTime, default=datetime.utcnow)
         updated_at = Column(DateTime, onupdate=datetime.utcnow)

     ---
     Flujo del Sistema

     1. Configuración de Perfil (Formulario)

     Página /mi-organizacion con formulario tradicional:

     ┌─────────────────────────────────────────┐
     │  Mi Organización                         │
     ├─────────────────────────────────────────┤
     │                                          │
     │  Nombre: [Fundación Ejemplo_______]      │
     │  CIF:    [G12345678_______________]      │
     │  Tipo:   [Fundación ▼]                   │
     │                                          │
     │  Sectores de actividad:                  │
     │  [✓] Acción Social  [✓] Educación        │
     │  [ ] Medioambiente  [ ] Cultura          │
     │  [ ] Salud          [ ] Cooperación      │
     │                                          │
     │  Regiones donde operamos:                │
     │  [✓] Madrid  [✓] Cataluña  [ ] Andalucía │
     │                                          │
     │  Presupuesto anual: [500.000 €]          │
     │  Año de fundación:  [2015]               │
     │  Nº empleados:      [12]                 │
     │                                          │
     │  Descripción/Misión:                     │
     │  [Textarea - qué hace la organización]   │
     │                                          │
     │  [Guardar]                               │
     └─────────────────────────────────────────┘

     2. Uso Normal (Con perfil configurado)

     Usuario selecciona una convocatoria
             │
             ▼
     ┌─────────────────────────────────────────┐
     │  AGENTE (sidebar):                       │
     │                                          │
     │  "He analizado esta convocatoria para   │
     │   Fundación Ejemplo:"                    │
     │                                          │
     │   Match: 87% ✅ RECOMENDADO APLICAR      │
     │                                          │
     │   ✅ Tipo beneficiario: Fundación        │
     │   ✅ Sector: Acción Social               │
     │   ✅ Ámbito: Nacional                    │
     │   ⚠️ Requiere: Certificado Hacienda     │
     │                                          │
     │   [Generar memoria técnica]              │
     │   [Ver análisis completo]                │
     └─────────────────────────────────────────┘

     ---
     Implementación

     Fase 1: Perfil de Organización (Sprint 1)

     Backend:
     - Modelo OrganizationProfile + migración
     - CRUD: GET/POST/PUT /api/v1/organization
     - Validación: un perfil por user_id

     Frontend:
     - OrganizationProfileForm.tsx - Formulario de perfil
     - Página /mi-organizacion con el formulario
     - Link en navegación: "Mi Organización"

     Archivos:
     backend/app/models/organization_profile.py (nuevo)
     backend/app/api/v1/organization.py (nuevo)
     backend/alembic/versions/005_organization_profile.py (nuevo)
     frontend/src/pages/OrganizationPage.tsx (nuevo)
     frontend/src/components/OrganizationProfileForm.tsx (nuevo)

     Fase 2: Agente con Contexto (Sprint 2)

     Backend:
     - Modificar n8n_service.py para incluir perfil de organización en payload
     - Nuevo endpoint: POST /api/v1/agent/analyze-eligibility
     - Calcular match score: perfil vs requisitos de convocatoria

     Payload enriquecido a N8n:
     {
         "organization": {
             "name": "Fundación Ejemplo",
             "type": "fundacion",
             "sectors": ["accion_social", "educacion"],
             "regions": ["ES41"],
             "annual_budget": 500000,
             "capabilities": ["proyectos_europeos", "menores"],
             "statutes_summary": "Organización dedicada a..."
         },
         "grant": { ... },  # Ya existe
         "chat": { message, history }
     }

     Frontend:
     - AgentSidebar.tsx - Panel lateral persistente
     - EligibilityBadge.tsx - Badge de match score en tabla
     - Auto-análisis al seleccionar convocatoria

     Fase 3: UI del Agente Protagonista (Sprint 2-3)

     Layout con sidebar persistente:
     ┌────────────────────────────────────────────────────────────┐
     │  Header: Logo | Grants | Mi Organización | [Avatar]        │
     ├──────────────────────────────────────┬─────────────────────┤
     │                                      │                     │
     │   CONTENIDO PRINCIPAL                │   AGENTE SIDEBAR    │
     │   (Tabla de grants)                  │   (300px fijo)      │
     │                                      │                     │
     │   ┌──────────────────────────────┐   │   ┌───────────────┐ │
     │   │ ✅ 87% Convocatoria A        │──▶│   │ Análisis de   │ │
     │   │ ⚠️ 62% Convocatoria B        │   │   │ Fundación X   │ │
     │   │ ❌ 23% Convocatoria C        │   │   │ vs Conv. A    │ │
     │   └──────────────────────────────┘   │   │               │ │
     │                                      │   │ [Chat input]  │ │
     │                                      │   └───────────────┘ │
     └──────────────────────────────────────┴─────────────────────┘

     Componentes:
     // frontend/src/components/agent/
     AgentSidebar.tsx       // Container del panel lateral
     AgentChat.tsx          // Chat con historial
     MatchScoreBadge.tsx    // Badge 87% ✅ en tabla
     EligibilityReport.tsx  // Análisis detallado expandible
     QuickActions.tsx       // "Generar memoria", "Ver bases"

     Fase 4: Generación de Documentos (Sprint 3)

     Backend:
     - Endpoint: POST /api/v1/agent/generate-document
     - Tipos: memoria_tecnica, presupuesto, carta_presentacion
     - Storage en Cloudflare R2

     N8n:
     - Workflow de generación con contexto de organización + convocatoria
     - Plantillas base para cada tipo de documento

     Frontend:
     - DocumentGenerator.tsx - Selector de tipo + preview
     - Descarga en PDF/DOCX

     Fase 5: Alertas Inteligentes (Sprint 4)

     Backend:
     - Modificar AlertService para calcular match con perfil
     - Scoring automático de nuevas convocatorias
     - Email: "Nueva convocatoria con 89% de match"

     Frontend:
     - Notificación in-app de nuevos matches
     - Dashboard de "Recomendadas para ti"

     ---
     Prompt del Agente

     # System Prompt - Agente Analista de Subvenciones

     Eres un analista experto en subvenciones españolas. Ayudas a organizaciones
     (ONGs, fundaciones, asociaciones) a encontrar y aplicar a convocatorias relevantes.

     ## Contexto que recibes:
     - **organization**: Perfil de la organización del usuario (tipo, sectores, capacidades)
     - **grant**: Convocatoria actual seleccionada (si hay)
     - **chat.history**: Conversación previa

     ## Tu personalidad:
     - **Proactivo**: Ofrece análisis sin que te lo pidan
     - **Preciso**: Cita artículos específicos de la convocatoria
     - **Práctico**: Enfócate en acciones concretas
     - **Empático**: Entiendes las limitaciones de recursos de las ONGs

     ## Tus capacidades:
     1. **Análisis de elegibilidad**: Cruza perfil de org vs requisitos
     2. **Recomendaciones**: "Esta convocatoria encaja porque..."
     3. **Generación de documentos**: Borradores de memoria técnica
     4. **Búsqueda**: Encuentra convocatorias por criterios

     ## Formato de respuestas:
     - Usa markdown estructurado
     - Incluye indicadores visuales: ✅ cumple, ⚠️ verificar, ❌ no cumple
     - Sé conciso pero completo
     - Termina con acción sugerida

     ## Ejemplo de análisis automático:
     "He analizado la convocatoria del MITECO para **[Nombre Organización]**:

     **Match: 87%** ✅ Recomendado aplicar

     ### Requisitos cumplidos (7/9):
     ✅ Tipo de beneficiario: Fundación
     ✅ Sector: Medioambiente (tu especialidad)
     ✅ Ámbito territorial: Nacional
     ✅ Antigüedad: >3 años (fundada en 2018)
     ...

     ### Pendiente de verificar (2/9):
     ⚠️ Certificado de estar al corriente con Hacienda
     ⚠️ Seguro de responsabilidad civil

     ### Siguiente paso:
     ¿Quieres que genere un borrador de memoria técnica?"

     ---
     Archivos Críticos a Modificar

     | Archivo                                 | Cambio                         |
     |-----------------------------------------|--------------------------------|
     | backend/app/models/__init__.py          | Exportar OrganizationProfile   |
     | backend/app/api/v1/__init__.py          | Registrar router organization  |
     | backend/app/services/n8n_service.py     | Incluir org profile en payload |
     | frontend/src/App.tsx                    | Layout con AgentSidebar        |
     | frontend/src/components/GrantsTable.tsx | Columna de match score         |

     ---
     Decisiones Técnicas

     | Decisión     | Opción              | Justificación       |
     |--------------|---------------------|---------------------|
     | Auth         | Header X-User-ID    | Simple para demo    |
     | Storage docs | Cloudflare R2       | Gratuito, escala    |
     | UI Agente    | Sidebar persistente | Máximo impacto      |
     | Multitenancy | NO                  | Una org por usuario |

     ---
     Orden de Implementación Sugerido

     1. Modelo OrganizationProfile + migración + CRUD básico
     2. Formulario de perfil en frontend
     3. Modificar payload N8n para incluir organización
     4. AgentSidebar - UI básica del panel lateral
     5. Match score - Cálculo y visualización en tabla
     6. Prompt engineering del agente en N8n
     7. Generación de documentos (si hay tiempo)
     8. Alertas inteligentes (si hay tiempo)

     ---
     MVP para Demo

     Mínimo viable impactante:
     1. Usuario configura perfil de su organización
     2. Al ver lista de grants, ve badge de match score
     3. Al seleccionar un grant, el sidebar muestra análisis automático
     4. Puede chatear con el agente para profundizar
     5. (Bonus) Generar borrador de memoria técnica