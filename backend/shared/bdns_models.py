"""
BDNS Pydantic Models

Data models for BDNS (Base de Datos Nacional de Subvenciones) API
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from enum import Enum


class BDNSAdministrationType(str, Enum):
    """Types of administration"""
    STATE = "C"  # Administración del Estado
    AUTONOMOUS_COMMUNITY = "A"  # Comunidad Autónoma
    LOCAL_ENTITY = "L"  # Entidad Local
    OTHER = "O"  # Otros Órganos


class BDNSOrgan(BaseModel):
    """Organization/department information"""
    nivel1: Optional[str] = Field(None, description="Level 1 organization")
    nivel2: Optional[str] = Field(None, description="Level 2 organization")
    nivel3: Optional[str] = Field(None, description="Level 3 organization")

    class Config:
        extra = "allow"


class BDNSBeneficiaryType(BaseModel):
    """Type of beneficiary"""
    codigo: Optional[str] = Field(None, description="Beneficiary code")
    descripcion: str = Field(..., description="Beneficiary description")

    class Config:
        extra = "allow"


class BDNSSector(BaseModel):
    """Economic sector"""
    codigo: Optional[str] = Field(None, description="Sector code (CNAE)")
    descripcion: str = Field(..., description="Sector description")

    class Config:
        extra = "allow"


class BDNSRegion(BaseModel):
    """Geographic region"""
    descripcion: str = Field(..., description="Region description (e.g., ES41 - CASTILLA Y LEON)")

    class Config:
        extra = "allow"


class BDNSInstrument(BaseModel):
    """Funding instrument"""
    descripcion: str = Field(..., description="Instrument description")

    class Config:
        extra = "allow"


class BDNSFund(BaseModel):
    """European or other fund"""
    descripcion: str = Field(..., description="Fund description (e.g., FEDER)")

    class Config:
        extra = "allow"


class BDNSRegulation(BaseModel):
    """Legal regulation"""
    descripcion: str = Field(..., description="Regulation description")
    autorizacion: Optional[int] = Field(None, description="Authorization type")

    class Config:
        extra = "allow"


class BDNSObjective(BaseModel):
    """Policy objective"""
    descripcion: str = Field(..., description="Objective description")

    class Config:
        extra = "allow"


class BDNSDocument(BaseModel):
    """Attached document"""
    id: int = Field(..., description="Document ID")
    nombreFic: str = Field(..., description="Filename")
    descripcion: Optional[str] = Field(None, description="Description")
    long: int = Field(..., description="File size in bytes")
    datMod: Optional[str] = Field(None, description="Modification date")
    datPublicacion: Optional[str] = Field(None, description="Publication date")

    class Config:
        extra = "allow"


class BDNSAnnouncement(BaseModel):
    """Official announcement"""
    numAnuncio: int = Field(..., description="Announcement number")
    titulo: str = Field(..., description="Announcement title")
    tituloLeng: Optional[str] = Field(None, description="Title in co-official language")
    texto: Optional[str] = Field(None, description="Announcement text (HTML)")
    textoLeng: Optional[str] = Field(None, description="Text in co-official language")
    url: Optional[str] = Field(None, description="Official bulletin URL")
    cve: Optional[str] = Field(None, description="CVE code")
    desDiarioOficial: Optional[str] = Field(None, description="Official bulletin name")
    datPublicacion: Optional[str] = Field(None, description="Publication date")

    class Config:
        extra = "allow"


class BDNSConvocatoriaSummary(BaseModel):
    """Summary of a convocatoria (from search results)"""
    id: int = Field(..., description="Internal ID")
    numeroConvocatoria: str = Field(..., description="BDNS convocatoria number")
    descripcion: str = Field(..., description="Title/description")
    descripcionLeng: Optional[str] = Field(None, description="Description in co-official language")
    fechaRecepcion: str = Field(..., description="Reception date (YYYY-MM-DD)")
    nivel1: str = Field(..., description="Level 1 organization")
    nivel2: Optional[str] = Field(None, description="Level 2 organization")
    nivel3: Optional[str] = Field(None, description="Level 3 organization")
    mrr: bool = Field(False, description="EU Recovery Mechanism flag")
    codigoInvente: Optional[str] = Field(None, description="INVENTE code")

    class Config:
        extra = "allow"


class BDNSConvocatoriaDetail(BaseModel):
    """Detailed convocatoria information"""
    id: int = Field(..., description="Internal ID")
    codigoBDNS: str = Field(..., description="BDNS code")
    organo: Optional[BDNSOrgan] = Field(None, description="Publishing organization")
    sedeElectronica: Optional[str] = Field(None, description="Electronic headquarters URL")
    fechaRecepcion: str = Field(..., description="Reception date")
    descripcion: str = Field(..., description="Description/title")
    descripcionLeng: Optional[str] = Field(None, description="Description in co-official language")

    # Financial information
    presupuestoTotal: Optional[float] = Field(None, description="Total budget in EUR")
    instrumentos: Optional[List[BDNSInstrument]] = Field(None, description="Funding instruments")
    tipoConvocatoria: Optional[str] = Field(None, description="Convocatoria type")

    # Beneficiary information
    tiposBeneficiarios: Optional[List[BDNSBeneficiaryType]] = Field(None, description="Beneficiary types")
    sectores: Optional[List[BDNSSector]] = Field(None, description="Economic sectors")
    regiones: Optional[List[BDNSRegion]] = Field(None, description="Geographic regions")

    # Dates
    fechaInicioSolicitud: Optional[str] = Field(None, description="Application start date")
    fechaFinSolicitud: Optional[str] = Field(None, description="Application end date")
    abierto: Optional[bool] = Field(None, description="Is open for applications")

    # EU and regulatory information
    mrr: bool = Field(False, description="EU Recovery Mechanism (MRR) flag")
    ayudaEstado: Optional[str] = Field(None, description="State aid number")
    urlAyudaEstado: Optional[str] = Field(None, description="State aid URL")
    fondos: Optional[List[BDNSFund]] = Field(None, description="European funds")
    reglamento: Optional[BDNSRegulation] = Field(None, description="Regulation")
    objetivos: Optional[List[BDNSObjective]] = Field(None, description="Policy objectives")

    # Purpose and regulatory base
    descripcionFinalidad: Optional[str] = Field(None, description="Purpose description")
    descripcionBasesReguladoras: Optional[str] = Field(None, description="Regulatory base description")
    urlBasesReguladoras: Optional[str] = Field(None, description="Regulatory base URL")
    sePublicaDiarioOficial: Optional[bool] = Field(None, description="Published in official bulletin")

    # Documents and announcements
    documentos: Optional[List[BDNSDocument]] = Field(None, description="Attached documents")
    anuncios: Optional[List[BDNSAnnouncement]] = Field(None, description="Official announcements")

    # Products/sectors (less common)
    sectoresProductos: Optional[List[Any]] = Field(None, description="Product sectors")

    class Config:
        extra = "allow"


class BDNSSearchParams(BaseModel):
    """Search parameters for BDNS API"""
    page: int = Field(0, ge=0, description="Page number (0-indexed)")
    pageSize: int = Field(50, ge=1, le=100, description="Results per page (1-100)")
    order: Optional[str] = Field("fechaRecepcion", description="Order by field")
    direccion: Optional[str] = Field("desc", description="Sort direction (asc/desc)")
    vpd: str = Field("GE", description="Portal ID (GE = general)")

    # Search filters
    descripcion: Optional[str] = Field(None, description="Search in title/description")
    descripcionTipoBusqueda: Optional[int] = Field(1, description="Search type: 0=exact, 1=all words, 2=any word")
    numeroConvocatoria: Optional[str] = Field(None, description="BDNS convocatoria number")
    mrr: Optional[bool] = Field(None, description="Filter by MRR flag")

    # Date filters
    fechaDesde: Optional[str] = Field(None, description="Start date (dd/MM/yyyy)")
    fechaHasta: Optional[str] = Field(None, description="End date (dd/MM/yyyy)")

    # Organization filters
    tipoAdministracion: Optional[str] = Field(None, description="Administration type (C/A/L/O)")
    organos: Optional[List[str]] = Field(None, description="Organization IDs")

    # Other filters
    regiones: Optional[List[int]] = Field(None, description="Region IDs")
    tiposBeneficiario: Optional[List[int]] = Field(None, description="Beneficiary type IDs")
    instrumentos: Optional[List[int]] = Field(None, description="Instrument IDs")
    finalidad: Optional[int] = Field(None, description="Purpose/finalidad ID")
    ayudaEstado: Optional[str] = Field(None, description="State aid number")

    class Config:
        extra = "allow"

    def to_params_dict(self) -> Dict[str, Any]:
        """Convert to query parameters dictionary"""
        params = {}
        for field_name, field_value in self.dict(exclude_none=True).items():
            if isinstance(field_value, list):
                # Convert lists to comma-separated strings or handle as per API
                params[field_name] = field_value
            else:
                params[field_name] = field_value
        return params


class BDNSSearchResponse(BaseModel):
    """Search response from BDNS API"""
    content: List[BDNSConvocatoriaSummary] = Field(..., description="Search results")
    pageable: Dict[str, Any] = Field(..., description="Pagination info")
    last: bool = Field(..., description="Is last page")
    totalPages: int = Field(..., description="Total pages")
    totalElements: int = Field(..., description="Total elements")
    size: int = Field(..., description="Page size")
    number: int = Field(..., description="Current page number")
    first: bool = Field(..., description="Is first page")
    numberOfElements: int = Field(..., description="Number of elements in this page")
    empty: bool = Field(..., description="Is empty")
    advertencia: Optional[str] = Field(None, description="Legal notice")

    class Config:
        extra = "allow"


class BDNSNonprofitAnalysis(BaseModel):
    """Analysis result for nonprofit filter"""
    is_nonprofit: bool = Field(..., description="Is this for nonprofit organizations")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
    primary_keywords_found: List[str] = Field(default_factory=list, description="Primary nonprofit keywords found")
    entity_type_keywords_found: List[str] = Field(default_factory=list, description="Entity type keywords found")
    exclusion_keywords_found: List[str] = Field(default_factory=list, description="Exclusion keywords found")
    has_exclusions: bool = Field(False, description="Has for-profit exclusion keywords")
    matched_keywords: List[str] = Field(default_factory=list, description="All matched keywords")

    class Config:
        extra = "allow"


class BDNSEnrichedGrant(BaseModel):
    """Enriched grant combining BOE and BDNS data"""
    # Original BOE fields
    boe_id: Optional[str] = Field(None, description="BOE document ID")
    title: str = Field(..., description="Grant title")
    publication_date: Optional[str] = Field(None, description="BOE publication date")

    # BDNS fields
    bdns_code: Optional[str] = Field(None, description="BDNS convocatoria number")
    bdns_id: Optional[int] = Field(None, description="BDNS internal ID")
    budget_amount: Optional[float] = Field(None, description="Total budget in EUR")
    application_start_date: Optional[str] = Field(None, description="Application period start")
    application_end_date: Optional[str] = Field(None, description="Application period end")
    is_open: Optional[bool] = Field(None, description="Is open for applications")
    is_mrr: bool = Field(False, description="EU Recovery Mechanism flag")

    # Nonprofit analysis
    is_nonprofit: bool = Field(False, description="Is for nonprofit organizations")
    nonprofit_confidence: Optional[float] = Field(None, description="Nonprofit filter confidence")
    nonprofit_keywords: List[str] = Field(default_factory=list, description="Nonprofit keywords matched")

    # Structured metadata
    beneficiary_types: List[str] = Field(default_factory=list, description="Target beneficiaries")
    sectors: List[str] = Field(default_factory=list, description="Economic sectors")
    regions: List[str] = Field(default_factory=list, description="Geographic regions")
    instruments: List[str] = Field(default_factory=list, description="Funding instruments")

    # Organization
    department: Optional[str] = Field(None, description="Department/organization")
    organ_level1: Optional[str] = Field(None, description="Organization level 1")
    organ_level2: Optional[str] = Field(None, description="Organization level 2")

    # URLs and documents
    pdf_url: Optional[str] = Field(None, description="PDF document URL")
    regulatory_base_url: Optional[str] = Field(None, description="Regulatory base URL")

    # Metadata
    source: str = Field("BDNS", description="Data source (BOE, BDNS, or BOE+BDNS)")
    enriched: bool = Field(False, description="Has been enriched with BDNS data")
    enrichment_date: Optional[str] = Field(None, description="When enrichment occurred")
    relevance_score: Optional[float] = Field(None, description="Overall relevance score")

    class Config:
        extra = "allow"
