"""
N8n Service - Wrapper para enviar grants a N8n Cloud
N8n se encarga de: Excel generation, date calculations, AI analysis
"""
import sys
import httpx
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models import Grant
from app.config import get_settings

settings = get_settings()


class N8nService:
    """Service for sending grants to N8n Cloud"""
    
    def __init__(self, db: Session):
        self.db = db
        self.webhook_url = settings.n8n_webhook_url
        
        if not self.webhook_url:
            raise ValueError("N8N_WEBHOOK_URL not configured in settings")
    
    async def send_grant(self, grant_id: str) -> Dict[str, Any]:
        """
        Envía un grant a N8n Cloud con el payload completo
        
        Args:
            grant_id: ID del grant a enviar
            
        Returns:
            Dict con resultado del envío
        """
        grant = self.db.query(Grant).filter(Grant.id == grant_id).first()
        
        if not grant:
            return {
                "success": False,
                "error": f"Grant {grant_id} not found"
            }
        
        # Usar el método to_n8n_payload() del modelo
        payload = grant.to_n8n_payload()
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                
                # Marcar como enviado
                grant.sent_to_n8n = True
                grant.sent_to_n8n_at = datetime.now()
                self.db.commit()
                
                return {
                    "success": True,
                    "grant_id": grant_id,
                    "webhook_status": response.status_code,
                    "response": response.json() if response.text else None
                }
                
        except httpx.HTTPError as e:
            return {
                "success": False,
                "grant_id": grant_id,
                "error": str(e),
                "error_type": "http_error"
            }
        except Exception as e:
            return {
                "success": False,
                "grant_id": grant_id,
                "error": str(e),
                "error_type": "unknown_error"
            }
    
    async def send_multiple_grants(self, grant_ids: list[str]) -> Dict[str, Any]:
        """
        Envía múltiples grants a N8n (batch)
        
        Args:
            grant_ids: Lista de IDs de grants
            
        Returns:
            Dict con estadísticas del envío
        """
        results = {
            "total": len(grant_ids),
            "successful": 0,
            "failed": 0,
            "errors": []
        }
        
        for grant_id in grant_ids:
            result = await self.send_grant(grant_id)
            
            if result["success"]:
                results["successful"] += 1
            else:
                results["failed"] += 1
                results["errors"].append({
                    "grant_id": grant_id,
                    "error": result.get("error", "Unknown error")
                })
        
        return results
    
    async def resend_failed_grants(self, limit: int = 10) -> Dict[str, Any]:
        """
        Reintenta enviar grants que fallaron anteriormente
        
        Args:
            limit: Máximo número de grants a reintentar
            
        Returns:
            Dict con estadísticas del reintento
        """
        # Buscar grants que no se han enviado
        failed_grants = self.db.query(Grant).filter(
            Grant.sent_to_n8n == False,
            Grant.is_nonprofit == True
        ).limit(limit).all()
        
        grant_ids = [g.id for g in failed_grants]
        
        if not grant_ids:
            return {
                "message": "No failed grants to resend",
                "total": 0
            }
        
        return await self.send_multiple_grants(grant_ids)
    
    def get_unsent_grants(self, limit: int = 50) -> list[Grant]:
        """
        Obtiene grants que aún no se han enviado a N8n
        
        Args:
            limit: Máximo número de resultados
            
        Returns:
            Lista de grants no enviados
        """
        return self.db.query(Grant).filter(
            Grant.sent_to_n8n == False,
            Grant.is_nonprofit == True,
            Grant.is_open == True
        ).order_by(Grant.application_end_date.asc()).limit(limit).all()
    
    async def test_webhook_connectivity(self) -> Dict[str, Any]:
        """
        Prueba la conectividad con el webhook de N8n
        
        Returns:
            Dict con resultado del test
        """
        test_payload = {
            "test": True,
            "message": "Test from subvenciones-v1 backend",
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self.webhook_url,
                    json=test_payload,
                    headers={"Content-Type": "application/json"}
                )
                
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "webhook_url": self.webhook_url,
                    "response": response.json() if response.text else None
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "webhook_url": self.webhook_url
            }
