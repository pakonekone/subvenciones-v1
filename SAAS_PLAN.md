# Plan de Transformación a SaaS Multi-tenant
## Sistema de Subvenciones v1.0 → v2.0 SaaS

**Fecha**: 2025-11-28
**Objetivo**: Convertir el sistema actual en un SaaS multi-tenant con modelo Freemium

---

## Decisiones Estratégicas Confirmadas

| Aspecto | Decisión | Razón |
|---------|----------|-------|
| **Modelo de Pricing** | Freemium (Free → Pro → Enterprise) | Maximizar usuarios, conversión gradual |
| **N8n Strategy** | Managed por nosotros (workflows centralizados) | Mayor control, mejor UX, escalable |
| **Migración de Datos** | Fresh start (eliminar grants actuales) | Simplicidad, sin deuda técnica |
| **Sistema de Auth** | Supabase (auth + RLS integrado) | Reduce tiempo 30%, Row Level Security nativo |

---

## Arquitectura del Sistema SaaS

### Stack Tecnológico Final

**Backend**:
- FastAPI 0.104+ (mantener)
- Supabase Postgres (reemplaza PostgreSQL local)
- Supabase Auth (JWT, email verification)
- Stripe para billing
- N8n Cloud (managed workflows)

**Frontend**:
- React 18 + TypeScript (mantener)
- Supabase Client (`@supabase/supabase-js`)
- React Router v6 (nuevo - routing protegido)
- Stripe Checkout (nuevo - payments)

**Infraestructura**:
- Backend: Railway / Render
- Frontend: Vercel
- Database: Supabase (managed Postgres)
- N8n: N8n Cloud
- Email: Supabase Auth (built-in)

### Modelo de Datos Multi-tenant

```mermaid
erDiagram
    ORGANIZATION ||--o{ PROFILE : has
    ORGANIZATION ||--o{ GRANT : owns
    ORGANIZATION ||--o| SUBSCRIPTION : has
    PROFILE }o--|| SUPABASE_USER : links

    ORGANIZATION {
        uuid id PK
        string name
        string slug UK
        string tier "free|pro|enterprise"
        json n8n_config
        json settings
        timestamp created_at
    }

    PROFILE {
        uuid id PK
        uuid user_id FK
        uuid organization_id FK
        string role "admin|member|viewer"
        timestamp joined_at
    }

    GRANT {
        uuid id PK
        uuid organization_id FK "TENANT ISOLATION"
        string source
        string title
        float budget_amount
        boolean is_nonprofit
        timestamp created_at
    }

    SUBSCRIPTION {
        uuid id PK
        uuid organization_id FK
        string tier
        string status
        string stripe_customer_id
        string stripe_subscription_id
    }
```

---

## Fase 1: Migración a Supabase (Semanas 1-2)

### Objetivos
- Reemplazar PostgreSQL local por Supabase Postgres
- Implementar autenticación con Supabase Auth
- Crear modelos base de multi-tenancy

### Backend - Configuración Supabase

**1.1. Crear proyecto Supabase**
```bash
# En Supabase Dashboard (https://supabase.com)
1. Crear nuevo proyecto: "subvenciones-saas"
2. Región: Europe (Frankfurt o similar)
3. Database password: generar segura
4. Obtener:
   - Project URL
   - Anon public key
   - Service role key
   - Database connection string
```

**1.2. Actualizar configuración Backend**

Archivo: `backend/app/config.py`
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Supabase
    supabase_url: str
    supabase_anon_key: str
    supabase_service_key: str
    database_url: str  # Supabase Postgres connection

    # JWT (Supabase maneja esto, pero necesitamos validar)
    supabase_jwt_secret: str

    # Stripe
    stripe_secret_key: str
    stripe_publishable_key: str
    stripe_webhook_secret: str

    # Frontend
    frontend_url: str = "http://localhost:3000"

    # Existing
    cors_origins: list[str]
    log_level: str = "INFO"
```

Archivo: `backend/.env`
```bash
# Supabase
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGc...
SUPABASE_SERVICE_KEY=eyJhbGc...
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.xxxxx.supabase.co:5432/postgres

# Supabase JWT Secret (de Supabase Dashboard > Settings > API)
SUPABASE_JWT_SECRET=your-jwt-secret

# Stripe (obtener de stripe.com)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Frontend
FRONTEND_URL=http://localhost:3000

# Existing
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
LOG_LEVEL=INFO
```

**1.3. Cliente Supabase**

Archivo: `backend/app/supabase.py` (NUEVO)
```python
from supabase import create_client, Client
from app.config import settings

supabase: Client = create_client(
    settings.supabase_url,
    settings.supabase_service_key  # Service key para admin operations
)

def get_supabase() -> Client:
    """Dependency para obtener cliente Supabase"""
    return supabase
```

**1.4. Eliminar Docker PostgreSQL local**

Archivo: `docker-compose.yml`
```yaml
# ELIMINAR la sección de PostgreSQL
# Ya no necesitamos PostgreSQL local
# Supabase maneja la base de datos

# Mantener solo si tienes otros servicios
version: '3.8'
services:
  # db: ELIMINAR
```

### Backend - Modelos Multi-tenant

**1.5. Modelo Organization**

Archivo: `backend/app/models/organization.py` (NUEVO)
```python
from sqlalchemy import Column, String, DateTime, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.database import Base

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False, index=True)
    tier = Column(String, default="free")  # free, pro, enterprise

    # N8n configuration per tenant
    n8n_webhook_url = Column(String, nullable=True)
    n8n_workflow_id = Column(String, nullable=True)

    # Organization settings
    settings = Column(JSON, default={})
    # Example settings:
    # {
    #   "min_relevance_score": 0.3,
    #   "bdns_max_results": 50,
    #   "custom_filters": [...],
    #   "google_sheets_template_id": "..."
    # }

    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    grants = relationship("Grant", back_populates="organization")
    profiles = relationship("Profile", back_populates="organization")
    subscription = relationship("Subscription", back_populates="organization", uselist=False)
```

**1.6. Modelo Profile**

Archivo: `backend/app/models/profile.py` (NUEVO)
```python
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.database import Base

class Profile(Base):
    """
    Links Supabase Auth users to Organizations
    """
    __tablename__ = "profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Link to Supabase Auth user (auth.users table)
    user_id = Column(UUID(as_uuid=True), unique=True, nullable=False, index=True)

    # Organization membership
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)

    # Role within organization
    role = Column(String, default="member")  # admin, member, viewer

    # Metadata
    joined_at = Column(DateTime, default=datetime.utcnow)
    last_seen_at = Column(DateTime, nullable=True)

    # Relationships
    organization = relationship("Organization", back_populates="profiles")
```

**1.7. Modelo Subscription**

Archivo: `backend/app/models/subscription.py` (NUEVO)
```python
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.database import Base

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)

    # Stripe integration
    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)

    # Subscription details
    tier = Column(String, default="free")  # free, pro, enterprise
    status = Column(String, default="active")  # active, canceled, past_due

    # Billing period
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)

    # Usage tracking (for free tier limits)
    grants_captured_this_month = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    organization = relationship("Organization", back_populates="subscription")
```

**1.8. Actualizar modelo Grant**

Archivo: `backend/app/models/grant.py`
```python
# Agregar al modelo existente:

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID

class Grant(Base):
    __tablename__ = "grants"

    # Existing fields...

    # NUEVO: Multi-tenant isolation
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id"),
        nullable=False,
        index=True  # Critical for query performance
    )

    # NUEVO: Track who created the grant
    created_by_user_id = Column(UUID(as_uuid=True), nullable=True)

    # Relationship
    organization = relationship("Organization", back_populates="grants")
```

**1.9. Migración Alembic**

```bash
cd backend

# Generar migración
alembic revision --autogenerate -m "Add multi-tenant models: Organization, Profile, Subscription, update Grant"

# Revisar migración generada en backend/migrations/versions/

# Aplicar migración
alembic upgrade head
```

### Frontend - Supabase Auth

**1.10. Instalar dependencias**

```bash
cd frontend

npm install @supabase/supabase-js
npm install react-router-dom
npm install @stripe/stripe-js @stripe/react-stripe-js
```

**1.11. Cliente Supabase**

Archivo: `frontend/src/lib/supabase.ts` (NUEVO)
```typescript
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error('Missing Supabase environment variables')
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// Types
export interface User {
  id: string
  email: string
  user_metadata?: {
    full_name?: string
  }
}

export interface Profile {
  id: string
  user_id: string
  organization_id: string
  role: 'admin' | 'member' | 'viewer'
  joined_at: string
}

export interface Organization {
  id: string
  name: string
  slug: string
  tier: 'free' | 'pro' | 'enterprise'
  settings: Record<string, any>
}
```

Archivo: `frontend/.env`
```bash
VITE_SUPABASE_URL=https://xxxxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGc...
VITE_API_URL=http://localhost:8000
VITE_STRIPE_PUBLISHABLE_KEY=pk_test_...
```

**1.12. Auth Context**

Archivo: `frontend/src/contexts/AuthContext.tsx` (NUEVO)
```typescript
import { createContext, useContext, useEffect, useState } from 'react'
import { User, Session } from '@supabase/supabase-js'
import { supabase, Profile, Organization } from '@/lib/supabase'

interface AuthContextType {
  user: User | null
  profile: Profile | null
  organization: Organization | null
  session: Session | null
  loading: boolean
  signIn: (email: string, password: string) => Promise<void>
  signUp: (email: string, password: string, organizationName: string) => Promise<void>
  signOut: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [profile, setProfile] = useState<Profile | null>(null)
  const [organization, setOrganization] = useState<Organization | null>(null)
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session)
      setUser(session?.user ?? null)
      if (session?.user) {
        loadUserProfile(session.user.id)
      } else {
        setLoading(false)
      }
    })

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session)
      setUser(session?.user ?? null)
      if (session?.user) {
        loadUserProfile(session.user.id)
      } else {
        setProfile(null)
        setOrganization(null)
        setLoading(false)
      }
    })

    return () => subscription.unsubscribe()
  }, [])

  async function loadUserProfile(userId: string) {
    try {
      // Fetch profile
      const { data: profile, error: profileError } = await supabase
        .from('profiles')
        .select('*')
        .eq('user_id', userId)
        .single()

      if (profileError) throw profileError
      setProfile(profile)

      // Fetch organization
      const { data: org, error: orgError } = await supabase
        .from('organizations')
        .select('*')
        .eq('id', profile.organization_id)
        .single()

      if (orgError) throw orgError
      setOrganization(org)
    } catch (error) {
      console.error('Error loading profile:', error)
    } finally {
      setLoading(false)
    }
  }

  const signIn = async (email: string, password: string) => {
    const { error } = await supabase.auth.signInWithPassword({
      email,
      password,
    })
    if (error) throw error
  }

  const signUp = async (email: string, password: string, organizationName: string) => {
    // Sign up user in Supabase Auth
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: {
          organization_name: organizationName,
        },
      },
    })
    if (error) throw error

    // Create organization and profile via backend API
    // (Backend handles this in a database trigger or API endpoint)
  }

  const signOut = async () => {
    const { error } = await supabase.auth.signOut()
    if (error) throw error
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        profile,
        organization,
        session,
        loading,
        signIn,
        signUp,
        signOut,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
```

**1.13. Login Page**

Archivo: `frontend/src/pages/LoginPage.tsx` (NUEVO)
```typescript
import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'

export function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { signIn } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await signIn(email, password)
      navigate('/app')
    } catch (err: any) {
      setError(err.message || 'Error al iniciar sesión')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Iniciar Sesión</CardTitle>
          <CardDescription>
            Accede a tu cuenta de Sistema de Subvenciones
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="p-3 text-sm text-red-500 bg-red-50 rounded">
                {error}
              </div>
            )}

            <div>
              <label htmlFor="email" className="block text-sm font-medium mb-1">
                Email
              </label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoFocus
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium mb-1">
                Contraseña
              </label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Cargando...' : 'Iniciar Sesión'}
            </Button>

            <p className="text-sm text-center text-gray-600">
              ¿No tienes cuenta?{' '}
              <Link to="/register" className="text-blue-600 hover:underline">
                Regístrate gratis
              </Link>
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
```

**1.14. Register Page**

Archivo: `frontend/src/pages/RegisterPage.tsx` (NUEVO)
```typescript
import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'

export function RegisterPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [organizationName, setOrganizationName] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { signUp } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await signUp(email, password, organizationName)
      navigate('/app/onboarding')
    } catch (err: any) {
      setError(err.message || 'Error al crear cuenta')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Crear Cuenta</CardTitle>
          <CardDescription>
            Empieza gratis - no requiere tarjeta de crédito
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="p-3 text-sm text-red-500 bg-red-50 rounded">
                {error}
              </div>
            )}

            <div>
              <label htmlFor="organization" className="block text-sm font-medium mb-1">
                Nombre de Organización
              </label>
              <Input
                id="organization"
                type="text"
                value={organizationName}
                onChange={(e) => setOrganizationName(e.target.value)}
                placeholder="Mi Fundación"
                required
                autoFocus
              />
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium mb-1">
                Email
              </label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="tu@email.com"
                required
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium mb-1">
                Contraseña
              </label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Mínimo 8 caracteres"
                required
                minLength={8}
              />
            </div>

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Creando cuenta...' : 'Crear Cuenta Gratis'}
            </Button>

            <p className="text-sm text-center text-gray-600">
              ¿Ya tienes cuenta?{' '}
              <Link to="/login" className="text-blue-600 hover:underline">
                Inicia sesión
              </Link>
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
```

---

## Fase 2: Multi-tenancy Core (Semanas 3-4)

### Objetivos
- Implementar Row Level Security en Supabase
- Actualizar todos los endpoints con filtrado por organización
- Proteger todas las rutas con autenticación

### Backend - Row Level Security

**2.1. Configurar RLS en Supabase**

En Supabase SQL Editor, ejecutar:

```sql
-- Enable RLS on all multi-tenant tables
ALTER TABLE grants ENABLE ROW LEVEL SECURITY;
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;

-- Helper function to get current user's organization_id
CREATE OR REPLACE FUNCTION auth.current_user_organization_id()
RETURNS UUID AS $$
  SELECT organization_id
  FROM public.profiles
  WHERE user_id = auth.uid()
$$ LANGUAGE SQL STABLE;

-- Policy: Users can only see grants from their organization
CREATE POLICY "org_isolation_grants" ON grants
  FOR ALL
  USING (organization_id = auth.current_user_organization_id());

-- Policy: Users can see their own organization
CREATE POLICY "users_see_own_org" ON organizations
  FOR SELECT
  USING (id = auth.current_user_organization_id());

-- Policy: Admins can update their organization
CREATE POLICY "admins_update_org" ON organizations
  FOR UPDATE
  USING (
    id = auth.current_user_organization_id()
    AND EXISTS (
      SELECT 1 FROM profiles
      WHERE user_id = auth.uid()
      AND role = 'admin'
    )
  );

-- Policy: Users can see profiles in their organization
CREATE POLICY "users_see_org_profiles" ON profiles
  FOR SELECT
  USING (organization_id = auth.current_user_organization_id());

-- Policy: Users can see their organization's subscription
CREATE POLICY "users_see_org_subscription" ON subscriptions
  FOR SELECT
  USING (organization_id = auth.current_user_organization_id());
```

**2.2. Auth Dependencies**

Archivo: `backend/app/api/dependencies.py` (NUEVO)
```python
from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from app.database import get_db
from app.config import settings
from app.models.profile import Profile
from app.models.organization import Organization

async def get_current_user(
    authorization: str = Header(...),
    db: Session = Depends(get_db)
) -> dict:
    """
    Validates Supabase JWT token and returns user info
    """
    try:
        # Extract token from "Bearer <token>"
        scheme, token = authorization.split()
        if scheme.lower() != 'bearer':
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")

        # Verify JWT with Supabase JWT secret
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated"
        )

        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        return {
            "user_id": user_id,
            "email": payload.get("email"),
            "role": payload.get("role")
        }
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header")


async def get_current_profile(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Profile:
    """
    Gets the Profile for the current user
    """
    profile = db.query(Profile).filter(
        Profile.user_id == current_user["user_id"]
    ).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    return profile


async def get_current_organization(
    profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db)
) -> Organization:
    """
    Gets the Organization for the current user
    """
    organization = db.query(Organization).filter(
        Organization.id == profile.organization_id
    ).first()

    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")

    if not organization.is_active:
        raise HTTPException(status_code=403, detail="Organization is inactive")

    return organization


async def require_admin(
    profile: Profile = Depends(get_current_profile)
) -> Profile:
    """
    Ensures current user has admin role
    """
    if profile.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")

    return profile
```

**2.3. Actualizar endpoints de Grants**

Archivo: `backend/app/api/v1/grants.py`
```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.api.dependencies import get_current_organization
from app.models.grant import Grant
from app.models.organization import Organization

router = APIRouter()

@router.get("/grants")
async def list_grants(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    organization: Organization = Depends(get_current_organization),  # NEW
    db: Session = Depends(get_db)
):
    """
    List grants - automatically filtered by user's organization
    """
    query = db.query(Grant).filter(
        Grant.organization_id == organization.id  # TENANT ISOLATION
    )

    total = query.count()
    grants = query.offset(skip).limit(limit).all()

    return {
        "items": grants,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/grants/{grant_id}")
async def get_grant(
    grant_id: str,
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """
    Get single grant - verify it belongs to user's organization
    """
    grant = db.query(Grant).filter(
        Grant.id == grant_id,
        Grant.organization_id == organization.id  # TENANT ISOLATION
    ).first()

    if not grant:
        raise HTTPException(status_code=404, detail="Grant not found")

    return grant


@router.delete("/grants/{grant_id}")
async def delete_grant(
    grant_id: str,
    organization: Organization = Depends(get_current_organization),
    profile: Profile = Depends(require_admin),  # Only admins can delete
    db: Session = Depends(get_db)
):
    """
    Delete grant - only admins, verify ownership
    """
    grant = db.query(Grant).filter(
        Grant.id == grant_id,
        Grant.organization_id == organization.id
    ).first()

    if not grant:
        raise HTTPException(status_code=404, detail="Grant not found")

    db.delete(grant)
    db.commit()

    return {"message": "Grant deleted successfully"}
```

**2.4. Actualizar endpoints de Captura**

Archivo: `backend/app/api/v1/capture.py`
```python
from app.api.dependencies import get_current_organization, get_current_profile

@router.post("/capture/bdns")
async def capture_bdns(
    request: CaptureBDNSRequest,
    organization: Organization = Depends(get_current_organization),
    profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db)
):
    """
    Capture BDNS grants for current organization
    """
    # Check tier limits
    if organization.tier == "free":
        # Check if exceeded monthly limit
        current_month_count = db.query(Grant).filter(
            Grant.organization_id == organization.id,
            Grant.created_at >= datetime.now().replace(day=1)
        ).count()

        if current_month_count >= 100:  # Free tier limit
            raise HTTPException(
                status_code=403,
                detail="Monthly grant limit reached. Upgrade to Pro for unlimited captures."
            )

    service = BDNSService(db, organization_id=organization.id)
    result = service.capture_by_date_range(
        date_from=request.fecha_desde,
        date_to=request.fecha_hasta,
        max_results=request.max_results,
        created_by_user_id=profile.user_id  # Track who created
    )

    return result
```

**Similar para BOE capture y todos los demás endpoints**

### Frontend - Protected Routing

**2.5. Router con protección**

Archivo: `frontend/src/App.tsx`
```typescript
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from '@/contexts/AuthContext'
import { LoginPage } from '@/pages/LoginPage'
import { RegisterPage } from '@/pages/RegisterPage'
import { GrantsPage } from '@/pages/GrantsPage'
import { AnalyticsPage } from '@/pages/AnalyticsPage'
import { SettingsPage } from '@/pages/SettingsPage'
import { TeamPage } from '@/pages/TeamPage'
import { BillingPage } from '@/pages/BillingPage'
import { OnboardingPage } from '@/pages/OnboardingPage'
import { AppLayout } from '@/components/AppLayout'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()

  if (loading) {
    return <div>Loading...</div>
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* Protected app routes */}
          <Route
            path="/app"
            element={
              <ProtectedRoute>
                <AppLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="/app/grants" replace />} />
            <Route path="grants" element={<GrantsPage />} />
            <Route path="analytics" element={<AnalyticsPage />} />
            <Route path="settings" element={<SettingsPage />} />
            <Route path="team" element={<TeamPage />} />
            <Route path="billing" element={<BillingPage />} />
            <Route path="onboarding" element={<OnboardingPage />} />
          </Route>

          {/* Redirect root to app */}
          <Route path="/" element={<Navigate to="/app" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
```

**2.6. App Layout con Navbar**

Archivo: `frontend/src/components/AppLayout.tsx` (NUEVO)
```typescript
import { Outlet } from 'react-router-dom'
import { Navbar } from './Navbar'

export function AppLayout() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <main className="container mx-auto py-6">
        <Outlet />
      </main>
    </div>
  )
}
```

**2.7. Navbar con user info**

Archivo: `frontend/src/components/Navbar.tsx` (NUEVO)
```typescript
import { Link } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { Button } from './ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from './ui/dropdown-menu'

export function Navbar() {
  const { user, organization, signOut } = useAuth()

  return (
    <nav className="bg-white shadow">
      <div className="container mx-auto px-4 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-8">
          <Link to="/app/grants" className="text-xl font-bold">
            Sistema de Subvenciones
          </Link>

          <div className="flex space-x-4">
            <Link to="/app/grants" className="text-gray-700 hover:text-gray-900">
              Subvenciones
            </Link>
            <Link to="/app/analytics" className="text-gray-700 hover:text-gray-900">
              Analytics
            </Link>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          {organization && (
            <div className="text-sm text-gray-600">
              {organization.name}
              <span className="ml-2 px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">
                {organization.tier.toUpperCase()}
              </span>
            </div>
          )}

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm">
                {user?.email}
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel>Mi Cuenta</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem asChild>
                <Link to="/app/settings">Configuración</Link>
              </DropdownMenuItem>
              <DropdownMenuItem asChild>
                <Link to="/app/team">Equipo</Link>
              </DropdownMenuItem>
              <DropdownMenuItem asChild>
                <Link to="/app/billing">Facturación</Link>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => signOut()}>
                Cerrar Sesión
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </nav>
  )
}
```

---

## Fase 3: N8n Multi-tenant (Semanas 5-6)

### Objetivos
- Configurar N8n Cloud para workflows por organización
- Implementar creación automática de workflows vía API
- Configurar Google Sheets OAuth por tenant

### Backend - N8n Workflow Manager

**3.1. N8n API Client**

Archivo: `backend/app/services/n8n_api_client.py` (NUEVO)
```python
import requests
from typing import Dict, Any
from app.config import settings

class N8nAPIClient:
    """
    Client for N8n Cloud API
    Docs: https://docs.n8n.io/api/
    """

    def __init__(self):
        self.base_url = settings.n8n_api_url  # https://your-n8n.app.n8n.cloud/api/v1
        self.api_key = settings.n8n_api_key
        self.headers = {
            "X-N8N-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }

    def create_workflow(self, name: str, nodes: list, connections: dict) -> Dict[str, Any]:
        """Create a new workflow"""
        payload = {
            "name": name,
            "nodes": nodes,
            "connections": connections,
            "active": True
        }

        response = requests.post(
            f"{self.base_url}/workflows",
            json=payload,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def get_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow details"""
        response = requests.get(
            f"{self.base_url}/workflows/{workflow_id}",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def update_workflow(self, workflow_id: str, updates: dict) -> Dict[str, Any]:
        """Update workflow"""
        response = requests.patch(
            f"{self.base_url}/workflows/{workflow_id}",
            json=updates,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def delete_workflow(self, workflow_id: str):
        """Delete workflow"""
        response = requests.delete(
            f"{self.base_url}/workflows/{workflow_id}",
            headers=self.headers
        )
        response.raise_for_status()
```

**3.2. Workflow Template**

Archivo: `backend/app/services/n8n_templates.py` (NUEVO)
```python
from typing import Dict, Any

def get_grants_analysis_workflow_template(
    organization_id: str,
    webhook_path: str,
    callback_url: str,
    google_sheets_id: str
) -> Dict[str, Any]:
    """
    Returns N8n workflow definition for grants analysis

    Flow:
    1. Webhook receives grant data
    2. OpenAI analyzes grant
    3. Export to Google Sheets
    4. Callback to backend with results
    """

    return {
        "name": f"Grants Analysis - Org {organization_id[:8]}",
        "nodes": [
            {
                "parameters": {
                    "path": webhook_path,
                    "responseMode": "responseNode",
                    "options": {}
                },
                "name": "Webhook",
                "type": "n8n-nodes-base.webhook",
                "position": [250, 300],
                "webhookId": "",
                "typeVersion": 1
            },
            {
                "parameters": {
                    "model": "gpt-4",
                    "messages": {
                        "values": [
                            {
                                "role": "system",
                                "content": "Analiza esta subvención y determina: 1) Prioridad (high/medium/low), 2) Valor estratégico (0-10)"
                            },
                            {
                                "role": "user",
                                "content": "={{ JSON.stringify($json) }}"
                            }
                        ]
                    },
                    "options": {
                        "temperature": 0.3
                    }
                },
                "name": "OpenAI",
                "type": "n8n-nodes-base.openAi",
                "position": [450, 300],
                "typeVersion": 1
            },
            {
                "parameters": {
                    "operation": "append",
                    "sheetId": google_sheets_id,
                    "range": "A:Z",
                    "options": {}
                },
                "name": "Google Sheets",
                "type": "n8n-nodes-base.googleSheets",
                "position": [650, 300],
                "typeVersion": 2,
                "credentials": {
                    "googleSheetsOAuth2Api": {
                        "name": f"Org {organization_id[:8]} - Google Sheets"
                    }
                }
            },
            {
                "parameters": {
                    "url": f"{callback_url}/callback/sheets",
                    "method": "POST",
                    "bodyParametersJson": "={{ JSON.stringify({\n  \"grant_id\": $json.grant_id,\n  \"status\": \"success\",\n  \"sheets_url\": $json.spreadsheet_url,\n  \"row_id\": $json.row_index\n}) }}",
                    "options": {
                        "headers": {
                            "values": [
                                {
                                    "name": "Content-Type",
                                    "value": "application/json"
                                }
                            ]
                        }
                    }
                },
                "name": "Callback Backend",
                "type": "n8n-nodes-base.httpRequest",
                "position": [850, 300],
                "typeVersion": 3
            },
            {
                "parameters": {
                    "respondWith": "={{ JSON.stringify({ success: true }) }}",
                    "options": {}
                },
                "name": "Respond to Webhook",
                "type": "n8n-nodes-base.respondToWebhook",
                "position": [1050, 300],
                "typeVersion": 1
            }
        ],
        "connections": {
            "Webhook": {
                "main": [[{"node": "OpenAI", "type": "main", "index": 0}]]
            },
            "OpenAI": {
                "main": [[{"node": "Google Sheets", "type": "main", "index": 0}]]
            },
            "Google Sheets": {
                "main": [[{"node": "Callback Backend", "type": "main", "index": 0}]]
            },
            "Callback Backend": {
                "main": [[{"node": "Respond to Webhook", "type": "main", "index": 0}]]
            }
        }
    }
```

**3.3. Workflow Creation Service**

Archivo: `backend/app/services/n8n_workflow_manager.py` (NUEVO)
```python
from sqlalchemy.orm import Session
from app.models.organization import Organization
from app.services.n8n_api_client import N8nAPIClient
from app.services.n8n_templates import get_grants_analysis_workflow_template
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class N8nWorkflowManager:
    def __init__(self, db: Session):
        self.db = db
        self.client = N8nAPIClient()

    def create_workflow_for_organization(
        self,
        organization_id: str,
        google_sheets_id: str
    ) -> dict:
        """
        Create dedicated N8n workflow for an organization
        """
        org = self.db.query(Organization).filter(
            Organization.id == organization_id
        ).first()

        if not org:
            raise ValueError(f"Organization {organization_id} not found")

        # Generate unique webhook path
        webhook_path = f"/webhook/org-{organization_id}/grants-analysis"

        # Get workflow template
        workflow_def = get_grants_analysis_workflow_template(
            organization_id=str(organization_id),
            webhook_path=webhook_path,
            callback_url=settings.backend_url,
            google_sheets_id=google_sheets_id
        )

        # Create workflow in N8n
        try:
            result = self.client.create_workflow(
                name=workflow_def["name"],
                nodes=workflow_def["nodes"],
                connections=workflow_def["connections"]
            )

            workflow_id = result["id"]
            webhook_url = f"{settings.n8n_webhook_base_url}{webhook_path}"

            # Update organization with workflow info
            org.n8n_workflow_id = workflow_id
            org.n8n_webhook_url = webhook_url
            self.db.commit()

            logger.info(f"Created N8n workflow {workflow_id} for org {organization_id}")

            return {
                "workflow_id": workflow_id,
                "webhook_url": webhook_url
            }

        except Exception as e:
            logger.error(f"Error creating N8n workflow: {e}")
            raise
```

**3.4. Admin Endpoint para crear workflows**

Archivo: `backend/app/api/v1/admin.py` (NUEVO)
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.n8n_workflow_manager import N8nWorkflowManager
from app.api.dependencies import require_super_admin

router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/organizations/{org_id}/create-workflow")
async def create_n8n_workflow(
    org_id: str,
    google_sheets_id: str,
    admin: dict = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    """
    Create N8n workflow for an organization
    Requires super-admin privileges
    """
    manager = N8nWorkflowManager(db)
    result = manager.create_workflow_for_organization(
        organization_id=org_id,
        google_sheets_id=google_sheets_id
    )

    return result
```

### Frontend - N8n Setup Wizard

**3.5. Onboarding Page con N8n setup**

Archivo: `frontend/src/pages/OnboardingPage.tsx` (NUEVO)
```typescript
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card } from '@/components/ui/card'

export function OnboardingPage() {
  const [step, setStep] = useState(1)
  const [googleSheetsId, setGoogleSheetsId] = useState('')
  const [loading, setLoading] = useState(false)
  const { organization } = useAuth()
  const navigate = useNavigate()

  const handleSetupN8n = async () => {
    setLoading(true)
    try {
      // Call backend to create N8n workflow
      const response = await fetch(`/api/v1/organizations/me/setup-n8n`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ google_sheets_id: googleSheetsId })
      })

      if (!response.ok) throw new Error('Setup failed')

      navigate('/app/grants')
    } catch (error) {
      console.error('N8n setup error:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto py-12">
      <h1 className="text-3xl font-bold mb-8">Configuración Inicial</h1>

      {step === 1 && (
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">
            Paso 1: Conectar Google Sheets
          </h2>
          <p className="text-gray-600 mb-4">
            Necesitamos el ID de tu Google Sheet para exportar subvenciones.
          </p>

          <div className="mb-4">
            <label className="block text-sm font-medium mb-2">
              Google Sheets ID
            </label>
            <Input
              value={googleSheetsId}
              onChange={(e) => setGoogleSheetsId(e.target.value)}
              placeholder="1A2B3C4D5E6F7G8H9I0J..."
            />
            <p className="text-sm text-gray-500 mt-1">
              Encuéntralo en la URL de tu sheet: docs.google.com/spreadsheets/d/<strong>ID</strong>/edit
            </p>
          </div>

          <Button onClick={() => setStep(2)} disabled={!googleSheetsId}>
            Continuar
          </Button>
        </Card>
      )}

      {step === 2 && (
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">
            Paso 2: Configurar N8n
          </h2>
          <p className="text-gray-600 mb-4">
            Crearemos tu workflow personalizado de análisis de subvenciones.
          </p>

          <Button onClick={handleSetupN8n} disabled={loading}>
            {loading ? 'Configurando...' : 'Configurar N8n'}
          </Button>
        </Card>
      )}
    </div>
  )
}
```

---

## Fase 4: Freemium & Billing (Semanas 7-8)

### Objetivos
- Integrar Stripe para pagos
- Implementar tier limits (free vs pro)
- Crear páginas de pricing y billing

### Backend - Stripe Integration

**4.1. Stripe Webhooks Handler**

Archivo: `backend/app/api/v1/billing.py` (NUEVO)
```python
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
import stripe
from app.config import settings
from app.database import get_db
from app.models.subscription import Subscription
from app.models.organization import Organization

router = APIRouter(prefix="/billing", tags=["billing"])

stripe.api_key = settings.stripe_secret_key

@router.post("/create-checkout-session")
async def create_checkout_session(
    price_id: str,
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """
    Create Stripe Checkout session for Pro subscription
    """
    try:
        checkout_session = stripe.checkout.Session.create(
            customer_email=organization.admin_email,  # You'd need to add this field
            line_items=[{
                'price': price_id,  # Stripe Price ID for Pro tier
                'quantity': 1,
            }],
            mode='subscription',
            success_url=f"{settings.frontend_url}/app/billing?success=true",
            cancel_url=f"{settings.frontend_url}/app/billing?canceled=true",
            metadata={
                'organization_id': str(organization.id)
            }
        )

        return {"url": checkout_session.url}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle Stripe webhook events
    """
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle different event types
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        organization_id = session['metadata']['organization_id']

        # Create or update subscription
        subscription = db.query(Subscription).filter(
            Subscription.organization_id == organization_id
        ).first()

        if not subscription:
            subscription = Subscription(organization_id=organization_id)
            db.add(subscription)

        subscription.stripe_customer_id = session['customer']
        subscription.stripe_subscription_id = session['subscription']
        subscription.tier = 'pro'
        subscription.status = 'active'

        # Update organization tier
        org = db.query(Organization).filter(
            Organization.id == organization_id
        ).first()
        org.tier = 'pro'

        db.commit()

    elif event['type'] == 'customer.subscription.deleted':
        # Downgrade to free tier
        subscription_id = event['data']['object']['id']

        subscription = db.query(Subscription).filter(
            Subscription.stripe_subscription_id == subscription_id
        ).first()

        if subscription:
            subscription.tier = 'free'
            subscription.status = 'canceled'

            org = db.query(Organization).filter(
                Organization.id == subscription.organization_id
            ).first()
            org.tier = 'free'

            db.commit()

    return {"status": "success"}


@router.post("/create-portal-session")
async def create_portal_session(
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """
    Create Stripe Customer Portal session for managing subscription
    """
    subscription = db.query(Subscription).filter(
        Subscription.organization_id == organization.id
    ).first()

    if not subscription or not subscription.stripe_customer_id:
        raise HTTPException(status_code=404, detail="No subscription found")

    try:
        portal_session = stripe.billing_portal.Session.create(
            customer=subscription.stripe_customer_id,
            return_url=f"{settings.frontend_url}/app/billing",
        )

        return {"url": portal_session.url}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

**4.2. Tier Enforcement Middleware**

Archivo: `backend/app/middleware/tier_limits.py` (NUEVO)
```python
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.organization import Organization
from app.models.grant import Grant
from datetime import datetime

TIER_LIMITS = {
    "free": {
        "max_grants_per_month": 100,
        "max_users": 1,
        "max_captures_per_day": 5
    },
    "pro": {
        "max_grants_per_month": None,  # Unlimited
        "max_users": 5,
        "max_captures_per_day": None
    },
    "enterprise": {
        "max_grants_per_month": None,
        "max_users": None,
        "max_captures_per_day": None
    }
}

def check_capture_limit(organization: Organization, db: Session):
    """
    Check if organization can capture more grants
    Raises HTTPException if limit exceeded
    """
    limits = TIER_LIMITS[organization.tier]

    if limits["max_grants_per_month"] is not None:
        # Count grants this month
        first_day_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0)

        count = db.query(Grant).filter(
            Grant.organization_id == organization.id,
            Grant.created_at >= first_day_of_month
        ).count()

        if count >= limits["max_grants_per_month"]:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "Monthly grant limit reached",
                    "current_tier": organization.tier,
                    "limit": limits["max_grants_per_month"],
                    "upgrade_url": "/app/billing"
                }
            )
```

### Frontend - Pricing & Billing

**4.3. Pricing Page**

Archivo: `frontend/src/pages/PricingPage.tsx` (NUEVO)
```typescript
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Check } from 'lucide-react'

const TIERS = [
  {
    name: 'Free',
    price: '€0',
    description: 'Perfecto para empezar',
    features: [
      '100 subvenciones/mes',
      '1 usuario',
      'Filtros básicos',
      'Exportación manual',
      'Soporte por email'
    ],
    cta: 'Plan Actual',
    priceId: null
  },
  {
    name: 'Pro',
    price: '€49',
    period: '/mes',
    description: 'Para organizaciones activas',
    features: [
      'Subvenciones ilimitadas',
      '5 usuarios',
      'Filtros avanzados',
      'N8n + Google Sheets automático',
      'Análisis AI ilimitado',
      'Soporte prioritario'
    ],
    cta: 'Upgrade a Pro',
    priceId: 'price_xxx',  // Your Stripe Price ID
    popular: true
  },
  {
    name: 'Enterprise',
    price: 'Custom',
    description: 'Para grandes organizaciones',
    features: [
      'Todo de Pro',
      'Usuarios ilimitados',
      'SSO / SAML',
      'API access',
      'Soporte dedicado',
      'Custom integrations'
    ],
    cta: 'Contactar',
    priceId: null
  }
]

export function PricingPage() {
  const handleUpgrade = async (priceId: string) => {
    try {
      const response = await fetch('/api/v1/billing/create-checkout-session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ price_id: priceId })
      })

      const { url } = await response.json()
      window.location.href = url  // Redirect to Stripe Checkout
    } catch (error) {
      console.error('Checkout error:', error)
    }
  }

  return (
    <div className="py-12">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold mb-4">Planes y Precios</h1>
        <p className="text-xl text-gray-600">
          Elige el plan perfecto para tu organización
        </p>
      </div>

      <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
        {TIERS.map((tier) => (
          <Card
            key={tier.name}
            className={`p-8 ${tier.popular ? 'border-blue-500 border-2 relative' : ''}`}
          >
            {tier.popular && (
              <div className="absolute top-0 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
                <span className="bg-blue-500 text-white px-4 py-1 rounded-full text-sm">
                  Más popular
                </span>
              </div>
            )}

            <h3 className="text-2xl font-bold mb-2">{tier.name}</h3>
            <div className="mb-4">
              <span className="text-4xl font-bold">{tier.price}</span>
              {tier.period && <span className="text-gray-600">{tier.period}</span>}
            </div>
            <p className="text-gray-600 mb-6">{tier.description}</p>

            <ul className="space-y-3 mb-8">
              {tier.features.map((feature) => (
                <li key={feature} className="flex items-start">
                  <Check className="h-5 w-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                  <span>{feature}</span>
                </li>
              ))}
            </ul>

            <Button
              className="w-full"
              variant={tier.popular ? 'default' : 'outline'}
              onClick={() => tier.priceId && handleUpgrade(tier.priceId)}
              disabled={!tier.priceId}
            >
              {tier.cta}
            </Button>
          </Card>
        ))}
      </div>
    </div>
  )
}
```

**4.4. Billing Page**

Archivo: `frontend/src/pages/BillingPage.tsx` (NUEVO)
```typescript
import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'

export function BillingPage() {
  const { organization } = useAuth()
  const [subscription, setSubscription] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchSubscription()
  }, [])

  const fetchSubscription = async () => {
    try {
      const response = await fetch('/api/v1/organizations/me/subscription')
      const data = await response.json()
      setSubscription(data)
    } catch (error) {
      console.error('Error fetching subscription:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleManageSubscription = async () => {
    try {
      const response = await fetch('/api/v1/billing/create-portal-session', {
        method: 'POST'
      })
      const { url } = await response.json()
      window.location.href = url  // Redirect to Stripe Portal
    } catch (error) {
      console.error('Portal error:', error)
    }
  }

  if (loading) return <div>Loading...</div>

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-8">Facturación</h1>

      <div className="grid gap-6">
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">Plan Actual</h2>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-2xl font-bold capitalize">
                {organization?.tier}
              </p>
              {subscription?.status && (
                <p className="text-gray-600">Estado: {subscription.status}</p>
              )}
            </div>

            {organization?.tier !== 'free' && (
              <Button onClick={handleManageSubscription}>
                Gestionar Suscripción
              </Button>
            )}

            {organization?.tier === 'free' && (
              <Button onClick={() => window.location.href = '/pricing'}>
                Upgrade a Pro
              </Button>
            )}
          </div>
        </Card>

        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">Uso Este Mes</h2>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span>Subvenciones capturadas</span>
              <span className="font-semibold">
                {subscription?.grants_captured_this_month || 0}
                {organization?.tier === 'free' && ' / 100'}
              </span>
            </div>
            <div className="flex justify-between">
              <span>Usuarios activos</span>
              <span className="font-semibold">
                1 {organization?.tier === 'free' && ' / 1'}
              </span>
            </div>
          </div>
        </Card>
      </div>
    </div>
  )
}
```

---

## Fase 5: Polish & Launch (Semanas 9-10)

### Deploy & Documentation

**5.1. Deploy Backend a Railway**

```bash
# Crear railway.json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "restartPolicyType": "ON_FAILURE"
  }
}

# En Railway dashboard:
# 1. New Project → Deploy from GitHub
# 2. Add Supabase Postgres (ya configurado externamente)
# 3. Environment variables:
#    - DATABASE_URL (Supabase)
#    - SUPABASE_URL
#    - SUPABASE_ANON_KEY
#    - SUPABASE_SERVICE_KEY
#    - STRIPE_SECRET_KEY
#    - N8N_API_URL
#    - N8N_API_KEY
```

**5.2. Deploy Frontend a Vercel**

```bash
# En Vercel dashboard:
# 1. Import Git Repository
# 2. Framework: Vite
# 3. Build Command: npm run build
# 4. Output Directory: dist
# 5. Environment variables:
#    - VITE_SUPABASE_URL
#    - VITE_SUPABASE_ANON_KEY
#    - VITE_API_URL (Railway backend URL)
#    - VITE_STRIPE_PUBLISHABLE_KEY
```

**5.3. User Documentation**

Archivo: `docs/USER_GUIDE.md` (NUEVO)
```markdown
# Guía de Usuario - Sistema de Subvenciones SaaS

## Primeros Pasos

### 1. Registro
1. Ve a [app.subvenciones.com/register](https://app.subvenciones.com/register)
2. Ingresa nombre de tu organización, email y contraseña
3. Verifica tu email (revisa spam)

### 2. Onboarding
1. Crea un Google Sheet para exportar subvenciones
2. Copia el ID del sheet
3. Pégalo en el wizard de configuración

### 3. Capturar Subvenciones
1. Click "Capturar Subvenciones"
2. Selecciona BDNS o BOE
3. Configura fechas y filtros
4. Inicia captura

### 4. Análisis AI con N8n
1. Selecciona subvenciones
2. Click "Enviar a N8n"
3. Espera análisis (2-5 min)
4. Ve resultados en columna "Prioridad"

### 5. Upgrade a Pro
1. Ve a "Facturación"
2. Click "Upgrade a Pro"
3. Completa pago con Stripe
4. Disfruta features ilimitados

## Límites por Tier

| Feature | Free | Pro | Enterprise |
|---------|------|-----|------------|
| Grants/mes | 100 | ∞ | ∞ |
| Usuarios | 1 | 5 | ∞ |
| N8n Analysis | Manual | Auto | Auto + Custom |
| Soporte | Email | Priority | Dedicated |

## Preguntas Frecuentes

### ¿Cómo configuro Google Sheets OAuth?
[Tutorial detallado...]

### ¿Puedo cancelar en cualquier momento?
Sí, sin penalizaciones.

### ¿Qué pasa con mis datos si cancelo?
Se mantienen por 30 días, después se eliminan.
```

---

## Estimación Final de Tiempo

| Fase | Tareas Principales | Duración |
|------|-------------------|----------|
| **1. Migración Supabase** | Setup Supabase, nuevos modelos, auth frontend | 2 semanas |
| **2. Multi-tenancy** | RLS, actualizar endpoints, protected routing | 2 semanas |
| **3. N8n Multi-tenant** | API workflows, templates, setup wizard | 2 semanas |
| **4. Freemium & Billing** | Stripe, tier enforcement, pricing pages | 2 semanas |
| **5. Polish & Launch** | Deploy, docs, testing | 1-2 semanas |
| **TOTAL** | | **9-10 semanas** |

---

## Checklist Pre-Launch

### Backend
- [ ] Todos los endpoints protegidos con auth
- [ ] RLS configurado en todas las tablas
- [ ] Tier limits funcionando
- [ ] Stripe webhooks probados
- [ ] N8n workflows creados automáticamente
- [ ] Error handling robusto
- [ ] Logging configurado
- [ ] Health check endpoint

### Frontend
- [ ] Login/Register funcionales
- [ ] Protected routing
- [ ] Onboarding wizard
- [ ] Settings page
- [ ] Billing page con Stripe
- [ ] Team management
- [ ] Error boundaries
- [ ] Loading states

### Infraestructura
- [ ] Backend deployed (Railway)
- [ ] Frontend deployed (Vercel)
- [ ] DNS configurado
- [ ] SSL certificates
- [ ] Monitoring (Sentry, LogRocket)
- [ ] Backups database
- [ ] Email templates configurados

### Business
- [ ] Pricing definido
- [ ] Stripe products creados
- [ ] Terms of Service
- [ ] Privacy Policy
- [ ] Support email configurado
- [ ] Landing page marketing

---

## Próximos Pasos Inmediatos

1. ✅ Confirmar plan con stakeholders
2. Crear cuenta Supabase
3. Crear cuenta Stripe (test mode)
4. Iniciar Fase 1: Migración a Supabase
5. Setup CI/CD pipeline

---

**Fecha de inicio propuesta**: Inmediato
**Fecha de lanzamiento estimada**: 9-10 semanas desde inicio

Este plan está optimizado para tu stack y decisiones (Supabase, Freemium, N8n managed). ¿Apruebas para empezar la ejecución?
