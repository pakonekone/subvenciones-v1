"""
Webhook endpoints - Send grants to N8n
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from app.database import get_db
from app.services import N8nService

router = APIRouter()


class SendToN8nRequest(BaseModel):
    """Request para enviar grants a N8n"""
    grant_ids: List[str]


class SendToN8nResponse(BaseModel):
    """Response de envío a N8n"""
    success: bool
    message: str
    results: dict


@router.post("/send", response_model=SendToN8nResponse)
async def send_grants_to_n8n(
    request: SendToN8nRequest,
    db: Session = Depends(get_db)
):
    """
    Envía uno o más grants a N8n Cloud

    N8n se encarga de:
    - Generar Excel con todos los campos
    - Calcular días restantes hasta deadline
    - Análisis AI del contenido
    - Enviar notificaciones si es prioritario
    """
    if not request.grant_ids:
        raise HTTPException(status_code=400, detail="No grant IDs provided")

    try:
        # Check if N8n is configured
        from app.config import get_settings
        settings = get_settings()
        if not settings.n8n_webhook_url:
            raise HTTPException(
                status_code=503,
                detail="N8n webhook URL not configured. Set N8N_WEBHOOK_URL in environment variables."
            )

        n8n_service = N8nService(db)

        if len(request.grant_ids) == 1:
            # Single grant
            result = await n8n_service.send_grant(request.grant_ids[0])
            
            if not result["success"]:
                raise HTTPException(
                    status_code=500,
                    detail=f"Error enviando a N8n: {result.get('error')}"
                )
            
            return SendToN8nResponse(
                success=True,
                message=f"Grant {request.grant_ids[0]} enviado a N8n",
                results=result
            )
        else:
            # Multiple grants
            results = await n8n_service.send_multiple_grants(request.grant_ids)
            
            return SendToN8nResponse(
                success=results["failed"] == 0,
                message=f"{results['successful']}/{results['total']} grants enviados exitosamente",
                results=results
            )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error enviando a N8n: {str(e)}"
        )


@router.post("/send/{grant_id}", response_model=SendToN8nResponse)
async def send_single_grant_to_n8n(
    grant_id: str,
    db: Session = Depends(get_db)
):
    """
    Envía un único grant a N8n (shortcut endpoint)
    """
    try:
        n8n_service = N8nService(db)
        result = await n8n_service.send_grant(grant_id)
        
        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"Error enviando a N8n: {result.get('error')}"
            )
        
        return SendToN8nResponse(
            success=True,
            message=f"Grant {grant_id} enviado a N8n",
            results=result
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error enviando a N8n: {str(e)}"
        )


@router.post("/resend-failed")
async def resend_failed_grants(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Reintenta enviar grants que fallaron anteriormente
    """
    try:
        n8n_service = N8nService(db)
        results = await n8n_service.resend_failed_grants(limit=limit)
        
        return {
            "success": True,
            "message": f"Reintentando envío de {results.get('total', 0)} grants",
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reenviando grants: {str(e)}"
        )


@router.get("/unsent")
async def get_unsent_grants(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Lista grants que aún no se han enviado a N8n
    """
    try:
        n8n_service = N8nService(db)
        grants = n8n_service.get_unsent_grants(limit=limit)
        
        return {
            "total": len(grants),
            "grants": [g.to_dict() for g in grants]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo grants no enviados: {str(e)}"
        )


@router.get("/test")
async def test_n8n_webhook(db: Session = Depends(get_db)):
    """
    Prueba la conectividad con el webhook de N8n
    """
    try:
        n8n_service = N8nService(db)
        result = await n8n_service.test_webhook_connectivity()

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error probando webhook: {str(e)}"
        )


class N8nCallbackRequest(BaseModel):
    """Request de callback desde N8n después de exportar a Google Sheets"""
    grant_id: str
    status: str  # "success" | "error"
    row_id: Optional[str] = None
    sheets_url: Optional[str] = None
    error_message: Optional[str] = None


@router.post("/callback/sheets")
async def n8n_sheets_callback(
    request: N8nCallbackRequest,
    db: Session = Depends(get_db)
):
    """
    Recibe confirmación de N8n cuando un grant se exporta a Google Sheets

    N8n debe llamar este endpoint después de procesar el grant con:
    - grant_id: ID del grant procesado
    - status: "success" si se exportó correctamente, "error" si falló
    - row_id: ID de fila en Google Sheets (opcional)
    - sheets_url: URL directa a la fila en Sheets (opcional)
    - error_message: Mensaje de error si falló (opcional)

    Esto actualiza el estado del grant para mostrar el icono de Google Sheets en la UI.
    """
    from app.models import Grant
    from datetime import datetime

    # Buscar el grant
    grant = db.query(Grant).filter(Grant.id == request.grant_id).first()

    if not grant:
        raise HTTPException(
            status_code=404,
            detail=f"Grant {request.grant_id} not found"
        )

    # Actualizar según el estado
    if request.status == "success":
        grant.google_sheets_exported = True
        grant.google_sheets_exported_at = datetime.now()

        if request.row_id:
            grant.google_sheets_row_id = request.row_id

        if request.sheets_url:
            grant.google_sheets_url = request.sheets_url

        db.commit()

        return {
            "success": True,
            "message": f"Grant {request.grant_id} marcado como exportado a Google Sheets",
            "grant_id": request.grant_id,
            "sheets_url": request.sheets_url
        }

    elif request.status == "error":
        # Log del error pero no actualizar el estado
        # El grant permanece como "enviado pero no exportado"
        error_msg = request.error_message or "Unknown error"

        return {
            "success": False,
            "message": f"Error exportando grant {request.grant_id}: {error_msg}",
            "grant_id": request.grant_id,
            "error": error_msg
        }

    else:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status: {request.status}. Must be 'success' or 'error'"
        )
