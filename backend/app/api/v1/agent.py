"""
Agent endpoints - AI-powered document generation and analysis
"""
import os
import httpx
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Literal
from datetime import datetime

from app.database import get_db
from app.models import Grant
from app.models.organization_profile import OrganizationProfile

router = APIRouter()

# N8n Document Generator webhook URL
N8N_DOCUMENT_WEBHOOK_URL = os.getenv("N8N_DOCUMENT_WEBHOOK_URL", "")


class DocumentGenerationRequest(BaseModel):
    """Request to generate a document"""
    grant_id: str
    document_type: Literal["memoria_tecnica", "carta_presentacion", "checklist"]
    instructions: Optional[str] = None


class DocumentResponse(BaseModel):
    """Response from document generation"""
    success: bool
    document_type: str
    title: Optional[str] = None
    google_doc_url: Optional[str] = None
    google_doc_id: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None


@router.post("/generate-document", response_model=DocumentResponse)
async def generate_document(
    request: DocumentGenerationRequest,
    x_user_id: str = Header(..., alias="X-User-ID", description="User ID for organization profile"),
    db: Session = Depends(get_db)
):
    """
    Generate a document (memoria técnica, carta de presentación, etc.)
    using AI agent with Google Docs integration.

    Requires:
    - X-User-ID header with user ID that has an organization profile
    - N8N_DOCUMENT_WEBHOOK_URL environment variable configured
    """
    # Validate N8n webhook URL
    if not N8N_DOCUMENT_WEBHOOK_URL:
        raise HTTPException(
            status_code=503,
            detail="Document generation service not configured. Set N8N_DOCUMENT_WEBHOOK_URL."
        )

    # Get organization profile
    organization = db.query(OrganizationProfile).filter(
        OrganizationProfile.user_id == x_user_id
    ).first()

    if not organization:
        raise HTTPException(
            status_code=404,
            detail="Organization profile not found. Please configure your organization first."
        )

    # Get grant
    grant = db.query(Grant).filter(Grant.id == request.grant_id).first()

    if not grant:
        raise HTTPException(
            status_code=404,
            detail=f"Grant {request.grant_id} not found"
        )

    # Build payload for N8n
    payload = {
        "action": "generate_document",
        "document_type": request.document_type,
        "user_instructions": request.instructions,
        "organization": organization.to_n8n_payload(),
        "grant": {
            "id": grant.id,
            "title": grant.title,
            "source": grant.source,
            "department": grant.department,
            "purpose": grant.purpose,
            "budget_amount": grant.budget_amount,
            "application_start_date": grant.application_start_date.isoformat() if grant.application_start_date else None,
            "application_end_date": grant.application_end_date.isoformat() if grant.application_end_date else None,
            "beneficiary_types": grant.beneficiary_types,
            "sectors": grant.sectors,
            "regions": grant.regions,
            "regulatory_base_url": grant.regulatory_base_url,
            "html_url": grant.html_url,
        }
    }

    # Call N8n webhook
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                N8N_DOCUMENT_WEBHOOK_URL,
                json=payload,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code != 200:
                return DocumentResponse(
                    success=False,
                    document_type=request.document_type,
                    error=f"N8n returned status {response.status_code}"
                )

            result = response.json()

            # Handle different response formats
            if isinstance(result, dict):
                # Check for document info
                doc_url = result.get("google_doc_url") or result.get("doc_url") or result.get("url")
                doc_id = result.get("google_doc_id") or result.get("doc_id") or result.get("documentId")
                title = result.get("title") or result.get("document_title")
                message = result.get("message") or result.get("output")

                return DocumentResponse(
                    success=True,
                    document_type=request.document_type,
                    title=title,
                    google_doc_url=doc_url,
                    google_doc_id=doc_id,
                    message=message
                )
            else:
                return DocumentResponse(
                    success=True,
                    document_type=request.document_type,
                    message=str(result)
                )

    except httpx.TimeoutException:
        return DocumentResponse(
            success=False,
            document_type=request.document_type,
            error="Document generation timed out. The AI agent may still be working - check Google Drive."
        )
    except Exception as e:
        return DocumentResponse(
            success=False,
            document_type=request.document_type,
            error=str(e)
        )


@router.get("/document-types")
async def get_document_types():
    """
    Get available document types for generation
    """
    return {
        "types": [
            {
                "id": "memoria_tecnica",
                "name": "Memoria Técnica",
                "description": "Documento completo con justificación, objetivos, metodología, presupuesto e indicadores",
                "estimated_time": "2-3 minutos"
            },
            {
                "id": "carta_presentacion",
                "name": "Carta de Presentación",
                "description": "Carta formal presentando la organización y su interés en la convocatoria",
                "estimated_time": "1 minuto"
            },
            {
                "id": "checklist",
                "name": "Checklist de Documentación",
                "description": "Lista de documentos requeridos con instrucciones para obtenerlos",
                "estimated_time": "30 segundos"
            }
        ]
    }
