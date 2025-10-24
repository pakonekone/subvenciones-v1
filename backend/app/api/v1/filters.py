"""
Filter management endpoints - Get and update capture filters
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

router = APIRouter()


class FilterKeywordsResponse(BaseModel):
    """Response model for filter keywords"""
    keywords: List[str]
    total: int
    description: str


class UpdateKeywordsRequest(BaseModel):
    """Request to update keywords"""
    keywords: List[str]


# Default BDNS nonprofit keywords (from bdns_service.py)
DEFAULT_BDNS_NONPROFIT_KEYWORDS = [
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
    "voluntariado"
]

# Default BOE grant keywords (from boe_service.py)
DEFAULT_BOE_GRANT_KEYWORDS = [
    'subvención', 'subvenciones', 'subvencion',
    'ayuda', 'ayudas', 'ayuda económica', 'ayuda financiera',
    'beca', 'becas',
    'premio', 'premios',
    'convocatoria', 'convocatorias', 'convoca',
    'bases reguladoras', 'bases de la convocatoria',
    'fondos next generation', 'next generation eu', 'ngeu',
    'plan de recuperación', 'prtr',
    'línea de ayuda', 'líneas de ayuda',
    'programa de apoyo', 'programa de ayuda',
    'incentivo', 'incentivos',
    'financiación', 'financiacion', 'cofinanciación',
    'startup', 'pyme', 'pymes', 'microempresa',
    'emprendedor', 'emprendedores', 'emprendimiento',
    'innovación', 'i+d+i', 'investigación', 'desarrollo',
    'transformación digital', 'digitalización',
    'sostenibilidad', 'medioambiente', 'economía circular',
    'transición energética', 'energías renovables'
]

# BOE relevant sections
BOE_RELEVANT_SECTIONS = [
    'I. Disposiciones generales',
    'III. Otras disposiciones',
    'V.A. Anuncios - Contratación del Sector Público',
    'V.B. Anuncios - Otros anuncios oficiales'
]


@router.get("/bdns", response_model=FilterKeywordsResponse)
async def get_bdns_filters():
    """
    Get BDNS nonprofit filter keywords

    Returns the list of keywords used to identify nonprofit grants in BDNS.
    These keywords are searched in the grant title, purpose, and beneficiary types.
    """
    return FilterKeywordsResponse(
        keywords=DEFAULT_BDNS_NONPROFIT_KEYWORDS,
        total=len(DEFAULT_BDNS_NONPROFIT_KEYWORDS),
        description="Keywords para identificar convocatorias sin ánimo de lucro en BDNS"
    )


@router.get("/boe", response_model=Dict[str, Any])
async def get_boe_filters():
    """
    Get BOE grant filter keywords and sections

    Returns:
    - Keywords used to identify grant-related documents
    - Relevant BOE sections that are scanned
    """
    return {
        "grant_keywords": {
            "keywords": DEFAULT_BOE_GRANT_KEYWORDS,
            "total": len(DEFAULT_BOE_GRANT_KEYWORDS),
            "description": "Keywords para identificar grants en BOE"
        },
        "sections": {
            "sections": BOE_RELEVANT_SECTIONS,
            "total": len(BOE_RELEVANT_SECTIONS),
            "description": "Secciones del BOE que se escanean"
        },
        "nonprofit_keywords": {
            "keywords": [
                'sin ánimo de lucro', 'sin animo de lucro',
                'ong', 'organizaciones no gubernamentales',
                'asociación', 'asociaciones',
                'fundación', 'fundaciones',
                'entidades sociales', 'tercer sector',
                'voluntariado', 'acción social'
            ],
            "total": 11,
            "description": "Keywords para identificar grants nonprofit en BOE"
        }
    }


@router.get("/summary")
async def get_filters_summary():
    """
    Get a summary of all active filters

    Useful for showing in the UI before capture
    """
    return {
        "bdns": {
            "total_keywords": len(DEFAULT_BDNS_NONPROFIT_KEYWORDS),
            "sample_keywords": DEFAULT_BDNS_NONPROFIT_KEYWORDS[:5],
            "filter_mode": "Only nonprofit (required match)"
        },
        "boe": {
            "total_grant_keywords": len(DEFAULT_BOE_GRANT_KEYWORDS),
            "sample_keywords": DEFAULT_BOE_GRANT_KEYWORDS[:5],
            "total_sections": len(BOE_RELEVANT_SECTIONS),
            "sections": BOE_RELEVANT_SECTIONS,
            "relevance_filtering": "Informational only (not excluding)"
        }
    }


# Note: POST endpoints for updating keywords would require:
# - Saving to a config file or database
# - Reloading the services with new keywords
# - For now, we return the defaults for viewing
# Future enhancement: Allow dynamic keyword management
