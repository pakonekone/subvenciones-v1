"""
Organization Profile API endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models import OrganizationProfile

router = APIRouter()


# Pydantic models
class OrganizationProfileCreate(BaseModel):
    name: str
    cif: Optional[str] = None
    organization_type: Optional[str] = None  # fundacion, asociacion, ong, cooperativa, empresa
    sectors: Optional[List[str]] = []
    regions: Optional[List[str]] = []
    annual_budget: Optional[float] = None
    employee_count: Optional[int] = None
    founding_year: Optional[int] = None
    capabilities: Optional[List[str]] = []
    description: Optional[str] = None


class OrganizationProfileUpdate(BaseModel):
    name: Optional[str] = None
    cif: Optional[str] = None
    organization_type: Optional[str] = None
    sectors: Optional[List[str]] = None
    regions: Optional[List[str]] = None
    annual_budget: Optional[float] = None
    employee_count: Optional[int] = None
    founding_year: Optional[int] = None
    capabilities: Optional[List[str]] = None
    description: Optional[str] = None


class OrganizationProfileResponse(BaseModel):
    id: str
    user_id: str
    name: str
    cif: Optional[str]
    organization_type: Optional[str]
    sectors: List[str]
    regions: List[str]
    annual_budget: Optional[float]
    employee_count: Optional[int]
    founding_year: Optional[int]
    capabilities: List[str]
    description: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


def get_user_id(x_user_id: Optional[str] = Header(None, alias="X-User-ID")) -> str:
    """
    Get user ID from header. In production with auth, this would validate a JWT.
    For now, we use a simple header-based approach.
    If no header provided, use a default anonymous user.
    """
    return x_user_id or "anonymous"


@router.get("", response_model=Optional[OrganizationProfileResponse])
def get_organization_profile(
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """
    Get the organization profile for the current user.
    Returns null if no profile exists yet.
    """
    profile = db.query(OrganizationProfile).filter(
        OrganizationProfile.user_id == user_id
    ).first()

    if not profile:
        return None

    return profile.to_dict()


@router.post("", response_model=OrganizationProfileResponse)
def create_or_update_organization_profile(
    data: OrganizationProfileCreate,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """
    Create or update the organization profile for the current user.
    If a profile already exists, it will be updated.
    """
    # Check if profile exists
    profile = db.query(OrganizationProfile).filter(
        OrganizationProfile.user_id == user_id
    ).first()

    if profile:
        # Update existing
        profile.name = data.name
        profile.cif = data.cif
        profile.organization_type = data.organization_type
        profile.sectors = data.sectors or []
        profile.regions = data.regions or []
        profile.annual_budget = data.annual_budget
        profile.employee_count = data.employee_count
        profile.founding_year = data.founding_year
        profile.capabilities = data.capabilities or []
        profile.description = data.description
    else:
        # Create new
        profile = OrganizationProfile(
            user_id=user_id,
            name=data.name,
            cif=data.cif,
            organization_type=data.organization_type,
            sectors=data.sectors or [],
            regions=data.regions or [],
            annual_budget=data.annual_budget,
            employee_count=data.employee_count,
            founding_year=data.founding_year,
            capabilities=data.capabilities or [],
            description=data.description
        )
        db.add(profile)

    db.commit()
    db.refresh(profile)

    return profile.to_dict()


@router.put("", response_model=OrganizationProfileResponse)
def update_organization_profile(
    data: OrganizationProfileUpdate,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """
    Partially update the organization profile.
    Only updates fields that are provided.
    """
    profile = db.query(OrganizationProfile).filter(
        OrganizationProfile.user_id == user_id
    ).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Organization profile not found. Create one first.")

    # Update only provided fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(profile, field, value)

    db.commit()
    db.refresh(profile)

    return profile.to_dict()


@router.delete("")
def delete_organization_profile(
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """Delete the organization profile for the current user."""
    profile = db.query(OrganizationProfile).filter(
        OrganizationProfile.user_id == user_id
    ).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Organization profile not found")

    db.delete(profile)
    db.commit()

    return {"status": "deleted", "user_id": user_id}


# Predefined options for frontend dropdowns
ORGANIZATION_TYPES = [
    {"value": "fundacion", "label": "Fundación"},
    {"value": "asociacion", "label": "Asociación"},
    {"value": "ong", "label": "ONG"},
    {"value": "cooperativa", "label": "Cooperativa"},
    {"value": "empresa", "label": "Empresa/PYME"},
]

SECTORS = [
    {"value": "accion_social", "label": "Acción Social"},
    {"value": "educacion", "label": "Educación"},
    {"value": "medioambiente", "label": "Medioambiente"},
    {"value": "cultura", "label": "Cultura"},
    {"value": "salud", "label": "Salud"},
    {"value": "cooperacion", "label": "Cooperación Internacional"},
    {"value": "deporte", "label": "Deporte"},
    {"value": "investigacion", "label": "Investigación"},
    {"value": "empleo", "label": "Empleo y Formación"},
    {"value": "vivienda", "label": "Vivienda"},
    {"value": "igualdad", "label": "Igualdad"},
    {"value": "infancia", "label": "Infancia y Juventud"},
    {"value": "mayores", "label": "Personas Mayores"},
    {"value": "discapacidad", "label": "Discapacidad"},
    {"value": "migracion", "label": "Migración"},
    {"value": "tecnologia", "label": "Tecnología e Innovación"},
]

REGIONS = [
    {"value": "ES11", "label": "Galicia"},
    {"value": "ES12", "label": "Asturias"},
    {"value": "ES13", "label": "Cantabria"},
    {"value": "ES21", "label": "País Vasco"},
    {"value": "ES22", "label": "Navarra"},
    {"value": "ES23", "label": "La Rioja"},
    {"value": "ES24", "label": "Aragón"},
    {"value": "ES30", "label": "Madrid"},
    {"value": "ES41", "label": "Castilla y León"},
    {"value": "ES42", "label": "Castilla-La Mancha"},
    {"value": "ES43", "label": "Extremadura"},
    {"value": "ES51", "label": "Cataluña"},
    {"value": "ES52", "label": "Comunidad Valenciana"},
    {"value": "ES53", "label": "Islas Baleares"},
    {"value": "ES61", "label": "Andalucía"},
    {"value": "ES62", "label": "Murcia"},
    {"value": "ES63", "label": "Ceuta"},
    {"value": "ES64", "label": "Melilla"},
    {"value": "ES70", "label": "Canarias"},
    {"value": "nacional", "label": "Nacional (toda España)"},
]

CAPABILITIES = [
    {"value": "proyectos_europeos", "label": "Gestión de proyectos europeos"},
    {"value": "atencion_menores", "label": "Atención a menores"},
    {"value": "atencion_mayores", "label": "Atención a personas mayores"},
    {"value": "formacion", "label": "Formación y capacitación"},
    {"value": "insercion_laboral", "label": "Inserción laboral"},
    {"value": "voluntariado", "label": "Gestión de voluntariado"},
    {"value": "sensibilizacion", "label": "Campañas de sensibilización"},
    {"value": "investigacion", "label": "Investigación"},
    {"value": "asistencia_juridica", "label": "Asistencia jurídica"},
    {"value": "atencion_psicologica", "label": "Atención psicológica"},
    {"value": "emergencias", "label": "Respuesta a emergencias"},
    {"value": "desarrollo_comunitario", "label": "Desarrollo comunitario"},
]


@router.get("/options")
def get_profile_options():
    """
    Get predefined options for organization profile form.
    Used by frontend to populate dropdowns.
    """
    return {
        "organization_types": ORGANIZATION_TYPES,
        "sectors": SECTORS,
        "regions": REGIONS,
        "capabilities": CAPABILITIES,
    }
