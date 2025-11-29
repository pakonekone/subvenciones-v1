"""
Grant SQLAlchemy model - Complete fields for BOE and BDNS
"""
from datetime import datetime
from sqlalchemy import Column, String, Float, Boolean, DateTime, Integer, Text, JSON
from sqlalchemy.sql import func

from app.database import Base


class Grant(Base):
    """Grant model with complete BOE and BDNS fields"""
    __tablename__ = "grants"

    # Primary key
    id = Column(String, primary_key=True, index=True)  # BOE-A-XXXX or BDNS-XXXX
    
    # Basic fields (common to BOE and BDNS)
    source = Column(String, nullable=False, index=True)  # "BOE" or "BDNS"
    title = Column(Text, nullable=False)
    department = Column(Text)  # Organismo convocante
    section = Column(String)
    
    # Dates
    publication_date = Column(DateTime)
    captured_at = Column(DateTime, default=func.now())
    processed_at = Column(DateTime, default=func.now())
    
    # Relevance & Status
    relevance_score = Column(Float, default=0.0)
    sent_to_n8n = Column(Boolean, default=False)
    sent_to_n8n_at = Column(DateTime, nullable=True)
    
    # BOE specific fields
    pdf_url = Column(Text)
    html_url = Column(Text)
    xml_url = Column(Text)
    pdf_processed = Column(Boolean, default=False)
    pdf_content_text = Column(Text)  # Extracted PDF text
    pdf_content_markdown = Column(Text)  # PDF as markdown
    
    # BDNS specific fields (24 campos adicionales) ⭐
    bdns_code = Column(String, index=True)  # Código convocatoria BDNS
    bdns_id = Column(Integer)  # ID interno BDNS

    # BOE specific field
    boe_id = Column(String, index=True)  # Identificador BOE (BOE-A-XXXX)

    # PLACSP specific fields
    placsp_folder_id = Column(String, index=True)  # ContractFolderID (EXP-...)
    contract_type = Column(String)  # Tipo de contrato (Obras, Servicios...)
    cpv_codes = Column(JSON)  # Códigos CPV
    tender_value_estimated = Column(Float)  # Valor estimado del contrato

    # Budget & Amounts
    budget_amount = Column(Float, index=True)  # Montante económico
    
    # Application dates
    application_start_date = Column(DateTime)
    application_end_date = Column(DateTime, index=True)  # Fecha límite presentación
    
    # Status
    is_open = Column(Boolean, default=False)  # Si está abierta
    
    # Nonprofit classification
    is_nonprofit = Column(Boolean, default=False, index=True)  # Sin ánimo de lucro
    nonprofit_confidence = Column(Float)  # Confianza del filtro (0.0-1.0)
    
    # Beneficiaries & Scope (stored as JSON)
    beneficiary_types = Column(JSON)  # ["Fundaciones", "Asociaciones", ...]
    sectors = Column(JSON)  # ["Acción Social", "Cultura", ...]
    regions = Column(JSON)  # ["ES41 - CASTILLA Y LEÓN", ...]
    instruments = Column(JSON)  # Instrumentos de financiación
    funds = Column(JSON)  # Fondos (MRR, etc.)
    
    # Grant type & purpose
    convocatoria_type = Column(String)  # Tipo de convocatoria
    purpose = Column(Text)  # Finalidad/objeto
    
    # URLs & Links (BDNS)
    regulatory_base_url = Column(Text)  # Bases reguladoras (PDF)
    electronic_office = Column(Text)  # Sede electrónica tramitación
    state_aid_number = Column(String)  # Número ayuda de estado
    state_aid_url = Column(Text)  # URL transparencia ayuda estado

    # BDNS Documents (JSON array of attached documents)
    bdns_documents = Column(JSON)  # Array of {id, nombre, url, descripcion}

    # Metadata
    bdns_last_updated = Column(DateTime)  # Última actualización BDNS
    enriched = Column(Boolean, default=False)  # Si tiene datos completos BDNS
    
    # N8n Analysis results (optional)
    priority = Column(String)  # HIGH/MEDIUM/LOW
    priority_score = Column(Float)
    strategic_value = Column(Float)
    notification_sent = Column(Boolean, default=False)
    analysis_timestamp = Column(DateTime)

    # Google Sheets integration
    google_sheets_exported = Column(Boolean, default=False, index=True)
    google_sheets_exported_at = Column(DateTime, nullable=True)
    google_sheets_row_id = Column(String, nullable=True)  # ID de fila en Sheets
    google_sheets_url = Column(Text, nullable=True)  # URL directa a la fila
    
    def __repr__(self):
        return f"<Grant {self.id}: {self.title[:50]}>"
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "source": self.source,
            "title": self.title,
            "department": self.department,
            "publication_date": self.publication_date.isoformat() if self.publication_date else None,
            "application_end_date": self.application_end_date.isoformat() if self.application_end_date else None,
            "budget_amount": self.budget_amount,
            "is_nonprofit": self.is_nonprofit,
            "is_open": self.is_open,
            "bdns_code": self.bdns_code,
            "bdns_documents": self.bdns_documents,
            "regulatory_base_url": self.regulatory_base_url,
            "electronic_office": self.electronic_office,
            "sent_to_n8n": self.sent_to_n8n,
            "google_sheets_exported": self.google_sheets_exported,
            "google_sheets_exported_at": self.google_sheets_exported_at.isoformat() if self.google_sheets_exported_at else None,
            "google_sheets_url": self.google_sheets_url,
            "html_url": self.html_url,
            # PLACSP fields
            "placsp_folder_id": self.placsp_folder_id,
            "contract_type": self.contract_type,
            "cpv_codes": self.cpv_codes,
            "pdf_url": self.pdf_url,
        }
    
    def to_n8n_payload(self):
        """
        Complete payload for N8n matching BOE project structure
        Includes rich content with pdf_content_text, metadata, and processing_info
        """
        # Detect if BDNS or BOE
        is_bdns = self.source == 'BDNS' or (self.bdns_code is not None)

        # Build rich content text
        if is_bdns:
            # For BDNS, create structured informative text
            budget_text = f"{self.budget_amount} EUR" if self.budget_amount else "No especificado"
            open_status = "ABIERTA" if self.is_open else "CERRADA"
            confidence_text = f"{self.nonprofit_confidence * 100:.0f}%" if self.nonprofit_confidence else "No disponible"
            relevance_text = f"{self.relevance_score:.2f}" if self.relevance_score is not None else "0.00"

            pdf_content_text = f"""CONVOCATORIA BDNS - {self.title or 'Sin título'}
=====================================

INFORMACIÓN GENERAL
-------------------
Código BDNS: {self.bdns_code or 'No disponible'}
ID BDNS: {self.bdns_id or 'No disponible'}
Organismo: {self.department or 'No especificado'}
Tipo: {self.convocatoria_type or 'No especificado'}

PRESUPUESTO Y FINANCIACIÓN
--------------------------
Presupuesto Total: {budget_text}
Instrumentos: {self.instruments or 'No especificado'}
Fondos: {self.funds or 'No especificado'}

PLAZOS Y ESTADO
---------------
Inicio Solicitudes: {self.application_start_date.isoformat() if self.application_start_date else 'No especificado'}
Fin Solicitudes: {self.application_end_date.isoformat() if self.application_end_date else 'No especificado'}
Estado: {open_status}

BENEFICIARIOS Y ALCANCE
-----------------------
Tipos de Beneficiarios: {self.beneficiary_types or 'No especificado'}
Sectores: {self.sectors or 'No especificado'}
Regiones: {self.regions or 'No especificado'}

ORGANIZACIÓN SIN ÁNIMO DE LUCRO
-------------------------------
Dirigida a entidades sin ánimo de lucro: {"Sí" if self.is_nonprofit else "No"}
Confianza del filtro: {confidence_text}

FINALIDAD
---------
{self.purpose or 'No especificada'}

INFORMACIÓN NORMATIVA
--------------------
Bases Reguladoras: {self.regulatory_base_url or 'No disponible'}
Sede Electrónica: {self.electronic_office or 'No disponible'}
Ayuda de Estado: {self.state_aid_number or 'No disponible'}
URL Transparencia: {self.state_aid_url or 'No disponible'}

DATOS TÉCNICOS
--------------
Fecha de Publicación: {self.publication_date.isoformat() if self.publication_date else 'No disponible'}
Capturada: {self.captured_at.isoformat() if self.captured_at else 'No disponible'}
Relevancia Estimada: {relevance_text}

FUENTE DE DATOS
---------------
Esta convocatoria proviene de la Base de Datos Nacional de Subvenciones (BDNS).
Los datos son estructurados y se actualizan automáticamente desde el sistema oficial.

Para más información:
https://www.infosubvenciones.es/bdnstrans/GE/es/convocatoria/{self.bdns_code or ''}
"""
        else:
            # For BOE, use existing pdf_content_text or create fallback
            if self.pdf_content_text and len(self.pdf_content_text.strip()) > 50:
                pdf_content_text = self.pdf_content_text
            else:
                relevance_text = f"{self.relevance_score:.2f}" if self.relevance_score is not None else "0.00"
                pdf_content_text = f"""INFORMACIÓN DE SUBVENCIÓN DEL BOE
=====================================

TÍTULO: {self.title or 'Sin título'}

ORGANISMO CONVOCANTE: {self.department or 'No especificado'}

SECCIÓN BOE: {self.section or ''}

FECHA DE PUBLICACIÓN: {self.publication_date.isoformat() if self.publication_date else ''}

IDENTIFICADOR: {self.id or ''}

ENLACES:
- PDF Original: {self.pdf_url or 'No disponible'}
- HTML: {self.html_url or 'No disponible'}
- XML: {self.xml_url or 'No disponible'}

INFORMACIÓN ADICIONAL:
- Relevancia Estimada: {relevance_text}
- Sección: {self.section or 'No especificada'}

NOTA IMPORTANTE:
El contenido completo del PDF no pudo ser procesado automáticamente.
Para obtener información detallada sobre requisitos, plazos, cuantías y procedimientos,
consulte directamente el documento oficial en el BOE mediante el enlace PDF proporcionado.
"""

        # Build metadata dict
        metadata = {}
        if is_bdns:
            metadata = {
                'bdns_code': self.bdns_code,
                'bdns_id': self.bdns_id,
                'bdns_documents': self.bdns_documents,
                'budget_amount': self.budget_amount,
                'application_start_date': self.application_start_date.isoformat() if self.application_start_date else None,
                'application_end_date': self.application_end_date.isoformat() if self.application_end_date else None,
                'is_open': self.is_open,
                'is_nonprofit': self.is_nonprofit,
                'nonprofit_confidence': self.nonprofit_confidence,
                'beneficiary_types': self.beneficiary_types,
                'sectors': self.sectors,
                'regions': self.regions,
                'instruments': self.instruments,
                'funds': self.funds,
                'convocatoria_type': self.convocatoria_type,
                'purpose': self.purpose,
                'regulatory_base_url': self.regulatory_base_url,
                'electronic_office': self.electronic_office,
                'state_aid_number': self.state_aid_number,
                'state_aid_url': self.state_aid_url
            }
        else:
            # For BOE, basic metadata
            metadata = {
                'publication_date': self.publication_date.isoformat() if self.publication_date else None,
                'department': self.department,
                'section': self.section,
                'relevance_score': self.relevance_score
            }

        # Build processing_info
        processing_info = {
            'captured_at': self.captured_at.isoformat() if self.captured_at else None,
            'estimated_relevance': self.relevance_score or 0,
            'pdf_processed': bool(self.pdf_processed),
            'extraction_method': 'bdns_api' if is_bdns else ('pdf_processed' if self.pdf_processed else 'metadata_only'),
            'data_type': 'structured' if is_bdns else 'pdf',
            'enriched': self.enriched
        }

        # Return complete payload matching BOE project structure
        return {
            # Core identification
            "id": self.id,
            "source": "BDNS" if is_bdns else "BOE",
            "type": "grant",
            "timestamp": self.captured_at.isoformat() if self.captured_at else None,

            # Basic info
            "title": self.title,
            "description": f"Convocatoria publicada por {self.department}" if self.department else "",
            "department": self.department,
            "section": self.section,

            # URLs
            "pdf_url": self.pdf_url or (f"https://www.infosubvenciones.es/bdnstrans/GE/es/convocatoria/{self.bdns_code}" if self.bdns_code else None),
            "html_url": self.html_url,
            "xml_url": self.xml_url,

            # Rich content - CRITICAL FOR N8N ANALYSIS
            "pdf_content_text": pdf_content_text,
            "pdf_content_markdown": self.pdf_content_markdown or "",

            # Structured metadata - CRITICAL FOR N8N EXTRACTION
            "metadata": metadata,

            # Processing info
            "processing_info": processing_info,

            # Legacy fields for backwards compatibility
            "bdns_code": self.bdns_code,
            "bdns_id": self.bdns_id,
            "publication_date": self.publication_date.isoformat() if self.publication_date else None,
            "application_start_date": self.application_start_date.isoformat() if self.application_start_date else None,
            "application_end_date": self.application_end_date.isoformat() if self.application_end_date else None,
            "budget_amount": self.budget_amount,
            "is_open": self.is_open,
            "is_nonprofit": self.is_nonprofit,
            "nonprofit_confidence": self.nonprofit_confidence,
            "beneficiary_types": self.beneficiary_types,
            "sectors": self.sectors,
            "regions": self.regions,
            "instruments": self.instruments,
            "funds": self.funds,
            "convocatoria_type": self.convocatoria_type,
            "purpose": self.purpose,
            "regulatory_base_url": self.regulatory_base_url,
            "electronic_office": self.electronic_office,
            "state_aid_url": self.state_aid_url,
            "relevance_score": self.relevance_score,
            "enriched": self.enriched,
        }
