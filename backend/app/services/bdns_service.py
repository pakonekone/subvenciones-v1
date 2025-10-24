"""
BDNS Service - Wrapper para captura de grants desde BDNS
con filtro de organizaciones sin ánimo de lucro
"""
import sys
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

# Import from shared modules (reused from v0)
sys.path.insert(0, '/Users/franconejosmengo/Projects/subvenciones-v1/backend')
from shared.bdns_api import BDNSAPIClient
from shared.bdns_models import BDNSConvocatoriaDetail

from app.models import Grant
from app.config import get_settings

settings = get_settings()


class BDNSService:
    """Service for capturing and filtering BDNS grants"""
    
    def __init__(self, db: Session):
        self.db = db
        self.bdns_client = BDNSAPIClient()
        
    def capture_recent_grants(
        self,
        days_back: int = 7,
        max_results: int = None
    ) -> Dict[str, Any]:
        """
        Captura grants recientes de BDNS y los filtra por nonprofit
        
        Args:
            days_back: Días hacia atrás para buscar
            max_results: Máximo número de resultados (usa config si no se especifica)
            
        Returns:
            Dict con estadísticas de captura
        """
        if max_results is None:
            max_results = settings.bdns_max_results

        fecha_desde = datetime.now() - timedelta(days=days_back)

        # Import BDNSSearchParams
        from shared.bdns_models import BDNSSearchParams

        # Crear parámetros de búsqueda
        params = BDNSSearchParams(
            fechaDesde=fecha_desde.strftime("%d/%m/%Y"),  # Formato dd/MM/yyyy
            pageSize=min(max_results, 100),  # Máximo 100 por página
            order="fechaRecepcion",
            direccion="desc"
        )

        # Buscar convocatorias recientes (summaries)
        response = self.bdns_client.search_convocatorias(params)
        summaries = response.content[:max_results]  # Limitar resultados

        stats = {
            "total_fetched": len(summaries),
            "total_nonprofit": 0,
            "total_new": 0,
            "total_updated": 0,
            "total_skipped": 0,
            "total_errors": 0
        }

        for summary in summaries:
            try:
                # Obtener detalle completo
                detail = self.bdns_client.get_convocatoria_detail(summary.numeroConvocatoria)

                if not detail:
                    stats["total_errors"] += 1
                    continue

                # Verificar si es nonprofit
                is_nonprofit, confidence = self._check_nonprofit(detail)

                if is_nonprofit:
                    stats["total_nonprofit"] += 1

                    # Verificar si ya existe
                    existing = self.db.query(Grant).filter(
                        Grant.bdns_code == detail.codigoBDNS
                    ).first()

                    if existing:
                        # Actualizar si hay cambios
                        if self._should_update(existing, detail):
                            self._update_grant(existing, detail, confidence)
                            stats["total_updated"] += 1
                        else:
                            stats["total_skipped"] += 1
                    else:
                        # Crear nuevo
                        self._create_grant(detail, confidence)
                        stats["total_new"] += 1
            except Exception as e:
                stats["total_errors"] += 1
                continue
                    
        self.db.commit()
        return stats

    def capture_by_date_range(
        self,
        date_from: str,
        date_to: str,
        max_results: int = None
    ) -> Dict[str, Any]:
        """
        Captura grants de BDNS por rango de fechas

        Args:
            date_from: Fecha desde en formato YYYY-MM-DD
            date_to: Fecha hasta en formato YYYY-MM-DD
            max_results: Máximo número de resultados

        Returns:
            Dict con estadísticas de captura
        """
        if max_results is None:
            max_results = settings.bdns_max_results

        # Convertir formato de fecha YYYY-MM-DD a dd/MM/yyyy para BDNS API
        from datetime import datetime
        date_from_obj = datetime.strptime(date_from, "%Y-%m-%d")
        date_to_obj = datetime.strptime(date_to, "%Y-%m-%d")

        # Import BDNSSearchParams
        from shared.bdns_models import BDNSSearchParams

        # Crear parámetros de búsqueda
        params = BDNSSearchParams(
            fechaDesde=date_from_obj.strftime("%d/%m/%Y"),  # Formato dd/MM/yyyy
            fechaHasta=date_to_obj.strftime("%d/%m/%Y"),    # Formato dd/MM/yyyy
            pageSize=min(max_results, 100),  # Máximo 100 por página
            order="fechaRecepcion",
            direccion="desc"
        )

        # Buscar convocatorias
        response = self.bdns_client.search_convocatorias(params)
        summaries = response.content[:max_results]  # Limitar resultados

        stats = {
            "total_fetched": len(summaries),
            "total_nonprofit": 0,
            "total_new": 0,
            "total_updated": 0,
            "total_skipped": 0,
            "total_errors": 0,
            "date_from": date_from,
            "date_to": date_to
        }

        for summary in summaries:
            try:
                # Obtener detalle completo
                detail = self.bdns_client.get_convocatoria_detail(summary.numeroConvocatoria)

                if not detail:
                    stats["total_errors"] += 1
                    continue

                # Verificar si es nonprofit
                is_nonprofit, confidence = self._check_nonprofit(detail)

                if is_nonprofit:
                    stats["total_nonprofit"] += 1

                    # Verificar si ya existe
                    existing = self.db.query(Grant).filter(
                        Grant.bdns_code == detail.codigoBDNS
                    ).first()

                    if existing:
                        # Actualizar si hay cambios
                        if self._should_update(existing, detail):
                            self._update_grant(existing, detail, confidence)
                            stats["total_updated"] += 1
                        else:
                            stats["total_skipped"] += 1
                    else:
                        # Crear nuevo
                        self._create_grant(detail, confidence)
                        stats["total_new"] += 1
            except Exception as e:
                stats["total_errors"] += 1
                continue

        self.db.commit()
        return stats

    def _check_nonprofit(self, detail: BDNSConvocatoriaDetail) -> tuple[bool, float]:
        """
        Verifica si una convocatoria es para organizaciones sin ánimo de lucro

        Returns:
            (is_nonprofit, confidence_score)
        """
        nonprofit_keywords = [
            "sin ánimo de lucro",
            "sin fines de lucro",
            "entidades no lucrativas",
            "fundación",
            "asociación",
            "ong",
            "tercer sector",
            "economía social",
            "entidades sociales",
            "acción social",
            "voluntariado",
            "personas jurídicas que no desarrollan actividad económica",
            "personas físicas que no desarrollan actividad económica"
        ]

        confidence = 0.0
        # Use correct field names: descripcion (title), descripcionFinalidad (purpose)
        text_to_check = f"{detail.descripcion} {detail.descripcionFinalidad or ''}"

        # Add beneficiary types if available
        if detail.tiposBeneficiarios:
            beneficiary_text = " ".join([b.descripcion for b in detail.tiposBeneficiarios])
            text_to_check += " " + beneficiary_text

        text_lower = text_to_check.lower()

        # Contar keywords encontradas
        matches = sum(1 for keyword in nonprofit_keywords if keyword in text_lower)

        if matches > 0:
            confidence = min(0.5 + (matches * 0.15), 1.0)
            return True, confidence

        return False, 0.0
    
    def _should_update(self, existing: Grant, detail: BDNSConvocatoriaDetail) -> bool:
        """Determina si un grant existente debe actualizarse"""
        # Actualizar si el estado de apertura cambió
        if detail.abierto != existing.is_open:
            return True

        return False
    
    def _create_grant(self, detail: BDNSConvocatoriaDetail, confidence: float) -> Grant:
        """Crea un nuevo Grant desde una convocatoria BDNS"""
        import logging
        logger = logging.getLogger(__name__)

        # Helper function to parse dates in multiple formats
        def parse_bdns_date(date_str: str, field_name: str):
            if not date_str:
                return None

            # Try multiple date formats
            formats = [
                "%Y-%m-%d",     # YYYY-MM-DD (ISO format)
                "%d/%m/%Y",     # DD/MM/YYYY (Spanish format)
                "%Y-%m-%dT%H:%M:%S",  # ISO with time
                "%Y-%m-%d %H:%M:%S"   # SQL datetime format
            ]

            for fmt in formats:
                try:
                    result = datetime.strptime(date_str, fmt).date()
                    logger.debug(f"✅ Parsed {field_name}: {date_str} → {result} using format {fmt}")
                    return result
                except ValueError:
                    continue

            # If no format worked, log the error
            logger.warning(f"⚠️ Could not parse {field_name}: '{date_str}' - tried formats: {formats}")
            return None

        # Parse dates with debug logging
        logger.info(f"📅 Parsing dates for BDNS-{detail.codigoBDNS}")
        logger.debug(f"   Raw fechaRecepcion: {detail.fechaRecepcion}")
        logger.debug(f"   Raw fechaInicioSolicitud: {detail.fechaInicioSolicitud}")
        logger.debug(f"   Raw fechaFinSolicitud: {detail.fechaFinSolicitud}")

        publication_date = parse_bdns_date(detail.fechaRecepcion, "fechaRecepcion")
        application_start_date = parse_bdns_date(detail.fechaInicioSolicitud, "fechaInicioSolicitud")
        application_end_date = parse_bdns_date(detail.fechaFinSolicitud, "fechaFinSolicitud")

        # Extract organ information
        department = None
        if detail.organo:
            parts = []
            if detail.organo.nivel1:
                parts.append(detail.organo.nivel1)
            if detail.organo.nivel2:
                parts.append(detail.organo.nivel2)
            department = " - ".join(parts) if parts else None

        # Convert lists to JSON-serializable format
        beneficiary_types = [b.descripcion for b in detail.tiposBeneficiarios] if detail.tiposBeneficiarios else []
        sectors = [s.descripcion for s in detail.sectores] if detail.sectores else []
        regions = [r.descripcion for r in detail.regiones] if detail.regiones else []
        instruments = [i.descripcion for i in detail.instrumentos] if detail.instrumentos else []
        funds = [f.descripcion for f in detail.fondos] if detail.fondos else []

        # Extract BDNS documents (attached PDFs) - PRIORITY 1
        bdns_documents = []
        if detail.documentos and len(detail.documentos) > 0:
            for doc in detail.documentos:
                doc_info = {
                    'id': doc.id,
                    'nombre': doc.nombreFic,
                    'url': f"https://www.infosubvenciones.es/bdnstrans/api/documento/{doc.id}",
                    'descripcion': doc.descripcion if doc.descripcion else None,
                    'size': doc.long if hasattr(doc, 'long') else None
                }
                bdns_documents.append(doc_info)
            logger.debug(f"   BDNS Documents: {len(bdns_documents)} found")

        # Extract PDF URL - NEW PRIORITY LOGIC
        pdf_url = None
        html_url = None

        # PRIORITY 1: Use first BDNS document as main PDF
        if bdns_documents and len(bdns_documents) > 0:
            pdf_url = bdns_documents[0]['url']
            logger.debug(f"   PDF URL (from documentos): {pdf_url}")

        # PRIORITY 2: Fallback to BOE announcements if no documents
        if not pdf_url and detail.anuncios and len(detail.anuncios) > 0:
            first_announcement = detail.anuncios[0]
            if first_announcement.url:
                pdf_url = first_announcement.url
                # Also try to construct HTML version for BOE
                if 'boe.es' in first_announcement.url and 'pdf' in first_announcement.url.lower():
                    if first_announcement.cve:
                        html_url = f"https://boe.es/diario_boe/txt.php?id={first_announcement.cve}"
                logger.debug(f"   PDF URL (from anuncios): {pdf_url}")

        # PRIORITY 3: Fallback to regulatory base URL if still no PDF
        if not pdf_url and detail.urlBasesReguladoras:
            pdf_url = detail.urlBasesReguladoras
            logger.debug(f"   PDF URL (from urlBasesReguladoras): {pdf_url}")

        logger.debug(f"   Final PDF URL: {pdf_url}")
        logger.debug(f"   HTML URL: {html_url}")

        grant = Grant(
            id=f"BDNS-{detail.codigoBDNS}",
            source="BDNS",
            bdns_code=detail.codigoBDNS,
            bdns_id=detail.id,
            title=detail.descripcion,
            department=department,

            # Dates
            publication_date=publication_date,
            application_start_date=application_start_date,
            application_end_date=application_end_date,
            bdns_last_updated=None,  # No modification date in detail model

            # Budget & Status
            budget_amount=detail.presupuestoTotal,
            is_open=detail.abierto if detail.abierto is not None else False,

            # Nonprofit classification
            is_nonprofit=True,
            nonprofit_confidence=confidence,

            # Beneficiaries & Scope (stored as JSON)
            beneficiary_types=beneficiary_types,
            sectors=sectors,
            regions=regions,
            instruments=instruments,
            funds=funds,

            # Type & Purpose
            convocatoria_type=detail.tipoConvocatoria,
            purpose=detail.descripcionFinalidad,

            # URLs
            pdf_url=pdf_url,
            html_url=html_url,
            regulatory_base_url=detail.urlBasesReguladoras,
            electronic_office=detail.sedeElectronica,
            state_aid_number=detail.ayudaEstado,
            state_aid_url=detail.urlAyudaEstado,

            # BDNS Documents
            bdns_documents=bdns_documents if bdns_documents else None,

            # Metadata
            enriched=True,  # BDNS data is already enriched
            captured_at=datetime.now()
        )

        self.db.add(grant)
        return grant
    
    def _update_grant(self, grant: Grant, detail: BDNSConvocatoriaDetail, confidence: float):
        """Actualiza un Grant existente con datos nuevos de BDNS"""
        import logging
        logger = logging.getLogger(__name__)

        # Use the same date parsing logic as _create_grant
        def parse_bdns_date(date_str: str, field_name: str):
            if not date_str:
                return None

            formats = [
                "%Y-%m-%d",     # YYYY-MM-DD (ISO format)
                "%d/%m/%Y",     # DD/MM/YYYY (Spanish format)
                "%Y-%m-%dT%H:%M:%S",  # ISO with time
                "%Y-%m-%d %H:%M:%S"   # SQL datetime format
            ]

            for fmt in formats:
                try:
                    result = datetime.strptime(date_str, fmt).date()
                    logger.debug(f"✅ Parsed {field_name}: {date_str} → {result} using format {fmt}")
                    return result
                except ValueError:
                    continue

            logger.warning(f"⚠️ Could not parse {field_name}: '{date_str}'")
            return None

        # Parse dates
        application_start_date = parse_bdns_date(detail.fechaInicioSolicitud, "fechaInicioSolicitud")
        application_end_date = parse_bdns_date(detail.fechaFinSolicitud, "fechaFinSolicitud")

        # Extract organ information
        department = None
        if detail.organo:
            parts = []
            if detail.organo.nivel1:
                parts.append(detail.organo.nivel1)
            if detail.organo.nivel2:
                parts.append(detail.organo.nivel2)
            department = " - ".join(parts) if parts else None

        # Convert lists to JSON-serializable format
        beneficiary_types = [b.descripcion for b in detail.tiposBeneficiarios] if detail.tiposBeneficiarios else []
        sectors = [s.descripcion for s in detail.sectores] if detail.sectores else []
        regions = [r.descripcion for r in detail.regiones] if detail.regiones else []

        # Extract BDNS documents (attached PDFs) - PRIORITY 1
        bdns_documents = []
        if detail.documentos and len(detail.documentos) > 0:
            for doc in detail.documentos:
                doc_info = {
                    'id': doc.id,
                    'nombre': doc.nombreFic,
                    'url': f"https://www.infosubvenciones.es/bdnstrans/api/documento/{doc.id}",
                    'descripcion': doc.descripcion if doc.descripcion else None,
                    'size': doc.long if hasattr(doc, 'long') else None
                }
                bdns_documents.append(doc_info)
            logger.debug(f"   BDNS Documents: {len(bdns_documents)} found (update)")

        # Extract PDF URL - NEW PRIORITY LOGIC (same as _create_grant)
        pdf_url = None
        html_url = None

        # PRIORITY 1: Use first BDNS document as main PDF
        if bdns_documents and len(bdns_documents) > 0:
            pdf_url = bdns_documents[0]['url']
            logger.debug(f"   PDF URL (from documentos): {pdf_url}")

        # PRIORITY 2: Fallback to BOE announcements if no documents
        if not pdf_url and detail.anuncios and len(detail.anuncios) > 0:
            first_announcement = detail.anuncios[0]
            if first_announcement.url:
                pdf_url = first_announcement.url
                if 'boe.es' in first_announcement.url and 'pdf' in first_announcement.url.lower():
                    if first_announcement.cve:
                        html_url = f"https://boe.es/diario_boe/txt.php?id={first_announcement.cve}"
                logger.debug(f"   PDF URL (from anuncios): {pdf_url}")

        # PRIORITY 3: Fallback to regulatory base URL if still no PDF
        if not pdf_url and detail.urlBasesReguladoras:
            pdf_url = detail.urlBasesReguladoras
            logger.debug(f"   PDF URL (from urlBasesReguladoras): {pdf_url}")

        grant.title = detail.descripcion
        grant.department = department
        grant.budget_amount = detail.presupuestoTotal
        grant.is_open = detail.abierto if detail.abierto is not None else False
        grant.application_start_date = application_start_date
        grant.application_end_date = application_end_date
        grant.nonprofit_confidence = confidence
        grant.beneficiary_types = beneficiary_types
        grant.sectors = sectors
        grant.regions = regions
        grant.purpose = detail.descripcionFinalidad
        grant.pdf_url = pdf_url
        grant.html_url = html_url
        grant.regulatory_base_url = detail.urlBasesReguladoras
        grant.electronic_office = detail.sedeElectronica
        grant.bdns_documents = bdns_documents if bdns_documents else None
        grant.processed_at = datetime.now()
    
    def get_open_grants(self) -> List[Grant]:
        """Obtiene todas las convocatorias abiertas para nonprofits"""
        return self.db.query(Grant).filter(
            Grant.source == "BDNS",
            Grant.is_nonprofit == True,
            Grant.is_open == True
        ).order_by(Grant.application_end_date.asc()).all()
    
    def get_grants_by_deadline(self, days_ahead: int = 30) -> List[Grant]:
        """Obtiene grants que cierran en los próximos N días"""
        deadline = datetime.now() + timedelta(days=days_ahead)
        
        return self.db.query(Grant).filter(
            Grant.source == "BDNS",
            Grant.is_nonprofit == True,
            Grant.is_open == True,
            Grant.application_end_date <= deadline
        ).order_by(Grant.application_end_date.asc()).all()
