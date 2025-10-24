"""
Pydantic models for BOE API data structures

Type-safe models for Spanish Official State Gazette (BOE) API responses
"""

from pydantic import BaseModel, Field, HttpUrl, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date
from enum import Enum


class StatusModel(BaseModel):
    """API response status"""
    code: str
    text: str


class CodeTextPair(BaseModel):
    """Common structure for code-text pairs"""
    codigo: str = Field(alias="codigo")
    texto: str = Field(alias="texto")
    
    model_config = {"populate_by_name": True}


class Scope(CodeTextPair):
    """Legal scope (Estatal/Autonómico)"""
    pass


class Department(CodeTextPair):
    """Government department"""
    pass


class Rank(CodeTextPair):
    """Legal document rank (Ley, Real Decreto, etc.)"""
    pass


class ConsolidationState(CodeTextPair):
    """Consolidation state"""
    pass


class LegislationMetadata(BaseModel):
    """Metadata for a piece of legislation"""
    fecha_actualizacion: str = Field(description="Last update timestamp (ISO 8601)")
    identificador: str = Field(description="Unique document identifier")
    ambito: Scope = Field(description="Legal scope")
    departamento: Department = Field(description="Government department")
    rango: Rank = Field(description="Document rank")
    fecha_disposicion: Optional[str] = Field(None, description="Disposition date (YYYYMMDD)")
    numero_oficial: Optional[str] = Field(None, description="Official number")
    titulo: str = Field(description="Title")
    diario: str = Field(description="Official journal name")
    fecha_publicacion: str = Field(description="Publication date (YYYYMMDD)")
    diario_numero: str = Field(description="Journal number")
    fecha_vigencia: Optional[str] = Field(None, description="Effective date (YYYYMMDD)")
    estatus_derogacion: Optional[str] = Field(None, description="Repeal status (S/N)")
    fecha_derogacion: Optional[str] = Field(None, description="Repeal date (YYYYMMDD)")
    estatus_anulacion: Optional[str] = Field(None, description="Annulment status (S/N)")
    fecha_anulacion: Optional[str] = Field(None, description="Annulment date (YYYYMMDD)")
    vigencia_agotada: str = Field(description="Validity exhausted (S/N)")
    estado_consolidacion: ConsolidationState = Field(description="Consolidation state")
    url_eli: Optional[HttpUrl] = Field(None, description="ELI permalink")
    url_html_consolidada: HttpUrl = Field(description="HTML consolidated URL")
    
    @validator('fecha_actualizacion', 'fecha_disposicion', 'fecha_publicacion', 
              'fecha_vigencia', 'fecha_derogacion', 'fecha_anulacion', pre=True)
    def validate_dates(cls, v):
        """Validate date formats"""
        if v is None:
            return v
        if isinstance(v, str) and len(v) >= 8:
            return v
        return v


class Subject(BaseModel):
    """Legal subject matter"""
    codigo: str = Field(description="Subject code")
    texto: str = Field(description="Subject description")


class Note(BaseModel):
    """Legislation note"""
    texto: str = Field(description="Note text")


class LegalReference(BaseModel):
    """Reference to other legislation"""
    id_norma: str = Field(description="Referenced legislation ID")
    relacion: CodeTextPair = Field(description="Type of relation")
    texto: str = Field(description="Relation description text")


class LegislationAnalysis(BaseModel):
    """Analysis data for legislation"""
    materias: Optional[List[Subject]] = Field(None, description="Subject matters")
    notas: Optional[List[Note]] = Field(None, description="Notes")
    referencias: Optional[Dict[str, List[LegalReference]]] = Field(None, description="Legal references")


class TextVersion(BaseModel):
    """Version of legislation text"""
    fecha_publicacion: str = Field(description="Publication date (YYYYMMDD)")
    fecha_vigencia: Optional[str] = Field(None, description="Effective date (YYYYMMDD)")
    id_norma: str = Field(description="Modifying legislation ID")
    content: str = Field(description="HTML content")


class TextBlock(BaseModel):
    """Block of legislation text"""
    id: str = Field(description="Block ID")
    tipo: str = Field(description="Block type")
    titulo: str = Field(description="Block title")
    fecha_caducidad: Optional[str] = Field(None, description="Expiry date (YYYYMMDD)")
    versiones: List[TextVersion] = Field(description="Text versions")


class LegislationText(BaseModel):
    """Complete legislation text structure"""
    bloques: List[TextBlock] = Field(description="Text blocks")


class TextIndexItem(BaseModel):
    """Text index item"""
    id: str = Field(description="Block ID")
    titulo: str = Field(description="Block title") 
    fecha_actualizacion: str = Field(description="Last update date (YYYYMMDD)")
    url: HttpUrl = Field(description="Block URL")


class PDFInfo(BaseModel):
    """PDF file information"""
    szBytes: str = Field(description="Size in bytes")
    szKBytes: str = Field(description="Size in KB")
    pagina_inicial: Optional[str] = Field(None, description="Start page")
    pagina_final: Optional[str] = Field(None, description="End page")
    texto: HttpUrl = Field(description="PDF URL")


class BOEItem(BaseModel):
    """Individual BOE item"""
    identificador: str = Field(description="Item ID")
    control: str = Field(description="Control number")
    titulo: str = Field(description="Item title")
    url_pdf: PDFInfo = Field(description="PDF information")
    url_html: HttpUrl = Field(description="HTML URL")
    url_xml: HttpUrl = Field(description="XML URL")


class BOEEpigraph(BaseModel):
    """BOE epigraph/section"""
    nombre: str = Field(description="Epigraph name")
    item: Union[BOEItem, List[BOEItem]] = Field(description="Items in this epigraph")


class BOEDepartment(BaseModel):
    """BOE department section"""
    codigo: str = Field(description="Department code")
    nombre: str = Field(description="Department name")
    epigrafe: List[BOEEpigraph] = Field(description="Epigraphs")


class BOESection(BaseModel):
    """BOE section"""
    codigo: str = Field(description="Section code")
    nombre: str = Field(description="Section name")
    departamento: List[BOEDepartment] = Field(description="Departments")


class BOEDiary(BaseModel):
    """BOE diary information"""
    numero: str = Field(description="Diary number")
    sumario_diario: Dict[str, Any] = Field(description="Daily summary info")
    seccion: List[BOESection] = Field(description="Sections")


class BOESummaryMetadata(BaseModel):
    """BOE summary metadata"""
    publicacion: str = Field(description="Publication name")
    fecha_publicacion: str = Field(description="Publication date (YYYYMMDD)")


class BOESummary(BaseModel):
    """BOE daily summary"""
    metadatos: BOESummaryMetadata = Field(description="Metadata")
    diario: List[BOEDiary] = Field(description="Diary entries")


class BOEResponse(BaseModel):
    """Generic BOE API response"""
    status: StatusModel = Field(description="Response status")
    data: Any = Field(description="Response data")


class LegislationListResponse(BOEResponse):
    """Response for legislation list"""
    data: List[LegislationMetadata]


class LegislationDetailResponse(BOEResponse):
    """Response for single legislation detail"""
    data: List[LegislationMetadata]  # API returns single item in array


class LegislationAnalysisResponse(BOEResponse):
    """Response for legislation analysis"""
    data: LegislationAnalysis


class TextIndexResponse(BOEResponse):
    """Response for text index"""
    data: List[TextIndexItem]


class BOESummaryResponse(BOEResponse):
    """Response for BOE summary"""
    data: Dict[str, BOESummary]


class AuxiliaryDataResponse(BOEResponse):
    """Response for auxiliary data"""
    data: Dict[str, str]  # Code -> Description mapping


class SearchQuery(BaseModel):
    """Query builder for legislation search"""
    query: Optional[Dict[str, Any]] = None
    sort: Optional[List[Dict[str, str]]] = None
    
    def add_title_search(self, text: str):
        """Add title search condition"""
        if not self.query:
            self.query = {"query_string": {"query": ""}}
        elif "query_string" not in self.query:
            self.query["query_string"] = {"query": ""}
            
        current = self.query["query_string"]["query"]
        condition = f"titulo:{text}"
        
        if current:
            self.query["query_string"]["query"] = f"{current} and {condition}"
        else:
            self.query["query_string"]["query"] = condition
    
    def add_subject_codes(self, codes: List[int]):
        """Add subject code search"""
        if not codes:
            return
            
        if not self.query:
            self.query = {"query_string": {"query": ""}}
        elif "query_string" not in self.query:
            self.query["query_string"] = {"query": ""}
            
        current = self.query["query_string"]["query"]
        subject_conditions = " or ".join([f"materia@codigo:{code}" for code in codes])
        condition = f"({subject_conditions})"
        
        if current:
            self.query["query_string"]["query"] = f"{current} and {condition}"
        else:
            self.query["query_string"]["query"] = condition
    
    def add_date_range(self, from_date: Union[str, date], to_date: Union[str, date]):
        """Add publication date range"""
        if isinstance(from_date, date):
            from_date = from_date.strftime("%Y%m%d")
        if isinstance(to_date, date):
            to_date = to_date.strftime("%Y%m%d")
            
        if not self.query:
            self.query = {}
            
        self.query["range"] = {
            "fecha_publicacion": {
                "gte": from_date,
                "lte": to_date
            }
        }
    
    def add_sort(self, field: str, descending: bool = False):
        """Add sort criteria"""
        if not self.sort:
            self.sort = []
            
        order = "desc" if descending else "asc"
        self.sort.append({field: order})
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API request"""
        result = {}
        if self.query:
            result["query"] = self.query
        if self.sort:
            result["sort"] = self.sort
        return result


# Document type enums for better type safety
class DocumentScope(str, Enum):
    """Document scope enumeration"""
    NATIONAL = "1"
    REGIONAL = "2"


class DocumentRank(str, Enum):
    """Common document ranks"""
    LAW = "1300"
    ROYAL_DECREE = "1340"
    ORDER = "1380"
    RESOLUTION = "1440"


class ConsolidationStatus(str, Enum):
    """Consolidation status"""
    IN_PROGRESS = "4"
    FINISHED = "3"


class ValidityStatus(str, Enum):
    """Validity status"""
    VALID = "N"
    EXPIRED = "S"


# Helper functions for model validation and conversion
def parse_boe_date(date_str: Optional[str]) -> Optional[date]:
    """Parse BOE date format (YYYYMMDD) to Python date"""
    if not date_str or len(date_str) != 8:
        return None
    try:
        return datetime.strptime(date_str, "%Y%m%d").date()
    except ValueError:
        return None


def format_boe_date(date_obj: Union[date, datetime]) -> str:
    """Format Python date to BOE format (YYYYMMDD)"""
    if isinstance(date_obj, datetime):
        date_obj = date_obj.date()
    return date_obj.strftime("%Y%m%d")


def parse_boe_datetime(datetime_str: str) -> Optional[datetime]:
    """Parse BOE datetime format (YYYYMMDDTHHMMSSZ) to Python datetime"""
    if not datetime_str or len(datetime_str) < 15:
        return None
    try:
        return datetime.strptime(datetime_str, "%Y%m%dT%H%M%SZ")
    except ValueError:
        return None