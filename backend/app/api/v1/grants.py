"""
Grants endpoints - List and filter grants
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime

from app.database import get_db
from app.models import Grant

router = APIRouter()


class GrantListItem(BaseModel):
    """Item de grant para listado"""
    id: str
    source: str
    title: str
    department: Optional[str]
    publication_date: Optional[datetime]
    application_start_date: Optional[datetime]
    application_end_date: Optional[datetime]
    budget_amount: Optional[float]
    is_nonprofit: bool
    is_open: bool
    sent_to_n8n: bool
    bdns_code: Optional[str]
    nonprofit_confidence: Optional[float]
    beneficiary_types: Optional[List]
    sectors: Optional[List]
    regions: Optional[List]
    purpose: Optional[str]
    regulatory_base_url: Optional[str]
    electronic_office: Optional[str]
    google_sheets_exported: bool = False
    google_sheets_url: Optional[str] = None

    class Config:
        from_attributes = True


class GrantDetail(BaseModel):
    """Detalle completo de un grant"""
    id: str
    source: str
    title: str
    department: Optional[str]
    publication_date: Optional[datetime]
    application_start_date: Optional[datetime]
    application_end_date: Optional[datetime]
    budget_amount: Optional[float]
    is_nonprofit: bool
    is_open: bool
    sent_to_n8n: bool
    sent_to_n8n_at: Optional[datetime]
    bdns_code: Optional[str]
    nonprofit_confidence: Optional[float]
    beneficiary_types: Optional[List]
    sectors: Optional[List]
    regions: Optional[List]
    purpose: Optional[str]
    regulatory_base_url: Optional[str]
    electronic_office: Optional[str]
    captured_at: Optional[datetime]
    google_sheets_exported: bool = False
    google_sheets_exported_at: Optional[datetime] = None
    google_sheets_row_id: Optional[str] = None
    google_sheets_url: Optional[str] = None

    class Config:
        from_attributes = True


class GrantsListResponse(BaseModel):
    """Response de listado de grants"""
    total: int
    grants: List[GrantListItem]


@router.get("", response_model=GrantsListResponse)
async def list_grants(
    # Filtros básicos
    source: Optional[str] = Query(None, description="Filtrar por fuente: BOE o BDNS"),
    is_open: Optional[bool] = Query(None, description="Filtrar por estado abierto/cerrado"),
    is_nonprofit: Optional[bool] = Query(None, description="Filtrar por nonprofit"),
    sent_to_n8n: Optional[bool] = Query(None, description="Filtrar por enviado a N8n"),

    # Filtros de búsqueda
    search: Optional[str] = Query(None, description="Búsqueda en título y descripción"),
    department: Optional[str] = Query(None, description="Filtrar por organismo"),

    # Filtros de fecha
    date_field: str = Query("application_end_date", description="Campo de fecha para filtrar (application_end_date, publication_date, captured_at)"),
    date_from: Optional[str] = Query(None, description="Fecha desde (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Fecha hasta (YYYY-MM-DD)"),

    # Filtros de presupuesto
    budget_min: Optional[float] = Query(None, ge=0, description="Presupuesto mínimo"),
    budget_max: Optional[float] = Query(None, ge=0, description="Presupuesto máximo"),

    # Filtros de confianza
    confidence_min: Optional[float] = Query(None, ge=0, le=1, description="Confianza nonprofit mínima"),

    # Paginación y ordenamiento
    limit: int = Query(50, ge=1, le=500, description="Número máximo de resultados"),
    offset: int = Query(0, ge=0, description="Offset para paginación"),
    sort_by: str = Query("application_end_date", description="Campo para ordenar"),
    order: str = Query("asc", description="Orden: asc o desc"),
    db: Session = Depends(get_db)
):
    """
    Lista grants con filtros avanzados
    """
    from datetime import datetime

    query = db.query(Grant)

    # Filtros básicos
    if source:
        query = query.filter(Grant.source == source.upper())
    if is_open is not None:
        query = query.filter(Grant.is_open == is_open)
    if is_nonprofit is not None:
        query = query.filter(Grant.is_nonprofit == is_nonprofit)
    if sent_to_n8n is not None:
        query = query.filter(Grant.sent_to_n8n == sent_to_n8n)

    # Búsqueda de texto
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Grant.title.ilike(search_pattern)) |
            (Grant.purpose.ilike(search_pattern))
        )

    if department:
        dept_pattern = f"%{department}%"
        query = query.filter(Grant.department.ilike(dept_pattern))

    # Filtros de fecha dinámicos
    date_column = getattr(Grant, date_field, Grant.application_end_date)
    
    if date_from:
        try:
            from_date = datetime.strptime(date_from, "%Y-%m-%d")
            query = query.filter(date_column >= from_date)
        except ValueError:
            pass

    if date_to:
        try:
            to_date = datetime.strptime(date_to, "%Y-%m-%d")
            query = query.filter(date_column <= to_date)
        except ValueError:
            pass

    # Filtros de presupuesto
    if budget_min is not None:
        query = query.filter(Grant.budget_amount >= budget_min)

    if budget_max is not None:
        query = query.filter(Grant.budget_amount <= budget_max)

    # Filtro de confianza
    if confidence_min is not None:
        query = query.filter(Grant.nonprofit_confidence >= confidence_min)

    # Contar total
    total = query.count()

    # Ordenar
    sort_column = getattr(Grant, sort_by, Grant.application_end_date)
    if order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))

    # Paginación
    grants = query.offset(offset).limit(limit).all()
    
    return GrantsListResponse(
        total=total,
        grants=[GrantListItem.model_validate(g) for g in grants]
    )


@router.get("/{grant_id}", response_model=GrantDetail)
async def get_grant_detail(
    grant_id: str,
    db: Session = Depends(get_db)
):
    """
    Obtiene el detalle completo de un grant específico
    """
    grant = db.query(Grant).filter(Grant.id == grant_id).first()
    
    if not grant:
        raise HTTPException(status_code=404, detail=f"Grant {grant_id} not found")
    
    return GrantDetail.model_validate(grant)


@router.get("/bdns/open")
async def get_open_bdns_grants(
    days_ahead: int = Query(30, ge=1, le=365, description="Días hacia adelante"),
    db: Session = Depends(get_db)
):
    """
    Obtiene grants BDNS abiertos que cierran en los próximos N días
    """
    from app.services import BDNSService

    bdns_service = BDNSService(db)
    grants = bdns_service.get_grants_by_deadline(days_ahead=days_ahead)

    return {
        "total": len(grants),
        "grants": [GrantListItem.model_validate(g) for g in grants]
    }


@router.delete("/{grant_id}")
async def delete_grant(
    grant_id: str,
    db: Session = Depends(get_db)
):
    """
    Elimina un grant por su ID
    """
    grant = db.query(Grant).filter(Grant.id == grant_id).first()

    if not grant:
        raise HTTPException(status_code=404, detail=f"Grant {grant_id} not found")

    db.delete(grant)
    db.commit()

    return {
        "success": True,
        "message": f"Grant {grant_id} eliminado correctamente"
    }


class ChatRequest(BaseModel):
    """Request para el chat con AI"""
    message: str
    history: List[Dict[str, str]] = []


@router.post("/{grant_id}/chat")
async def chat_with_grant(
    grant_id: str,
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Envía un mensaje al analista AI sobre un grant específico
    """
    from app.services.n8n_service import N8nService
    
    service = N8nService(db)
    result = await service.send_chat_message(
        grant_id=grant_id,
        message=request.message,
        history=request.history
    )
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Error en el chat AI"))
        
    return result
