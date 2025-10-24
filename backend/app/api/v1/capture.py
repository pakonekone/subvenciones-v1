"""
Capture endpoints - Trigger BDNS grant capture
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional

from app.database import get_db
from app.services import BDNSService

router = APIRouter()


class CaptureRequest(BaseModel):
    """Request para capturar grants de BDNS"""
    days_back: Optional[int] = Field(None, ge=1, le=90, description="Días hacia atrás para buscar (deprecated)")
    date_from: Optional[str] = Field(None, description="Fecha desde (YYYY-MM-DD)")
    date_to: Optional[str] = Field(None, description="Fecha hasta (YYYY-MM-DD)")
    max_results: int = Field(default=50, ge=1, le=100, description="Máximo número de resultados")


class CaptureResponse(BaseModel):
    """Response de captura de grants"""
    success: bool
    message: str
    stats: dict


@router.post("/bdns", response_model=CaptureResponse)
async def capture_bdns_grants(
    request: CaptureRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Captura grants de BDNS con filtro nonprofit

    Este endpoint:
    1. Busca convocatorias en BDNS en el rango de fechas especificado
    2. Filtra por organizaciones sin ánimo de lucro
    3. Guarda en PostgreSQL
    4. Retorna estadísticas de captura
    """
    try:
        bdns_service = BDNSService(db)

        # Determinar el método de captura
        if request.date_from and request.date_to:
            # Usar rango de fechas
            stats = bdns_service.capture_by_date_range(
                date_from=request.date_from,
                date_to=request.date_to,
                max_results=request.max_results
            )
        elif request.days_back:
            # Usar días hacia atrás (deprecated pero soportado)
            stats = bdns_service.capture_recent_grants(
                days_back=request.days_back,
                max_results=request.max_results
            )
        else:
            # Por defecto, buscar grants de hoy
            from datetime import date
            today = date.today().isoformat()
            stats = bdns_service.capture_by_date_range(
                date_from=today,
                date_to=today,
                max_results=request.max_results
            )

        return CaptureResponse(
            success=True,
            message=f"Captura completada: {stats['total_new']} nuevos grants",
            stats=stats
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error capturando grants: {str(e)}"
        )


@router.get("/bdns/status")
async def get_capture_status(db: Session = Depends(get_db)):
    """
    Obtiene el estado actual de la captura BDNS
    
    Retorna:
    - Total grants en BD
    - Grants abiertos
    - Grants no enviados a N8n
    """
    from app.models import Grant
    
    total = db.query(Grant).filter(Grant.source == "BDNS").count()
    open_grants = db.query(Grant).filter(
        Grant.source == "BDNS",
        Grant.is_open == True
    ).count()
    unsent = db.query(Grant).filter(
        Grant.source == "BDNS",
        Grant.sent_to_n8n == False
    ).count()
    
    return {
        "total_grants": total,
        "open_grants": open_grants,
        "unsent_to_n8n": unsent,
        "source": "BDNS"
    }
