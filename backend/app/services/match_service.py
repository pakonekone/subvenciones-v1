"""
Match Score Service - Calculate compatibility between organization and grant
"""
from typing import Dict, Optional, Any


def calculate_match_score(organization: Any, grant: Any) -> Dict:
    """
    Calcula score de compatibilidad organización vs convocatoria.

    Ponderación:
    - Tipo de beneficiario (25%): ¿El tipo de organización está en beneficiary_types?
    - Sectores (30%): ¿Cuántos sectores coinciden?
    - Regiones (25%): ¿La org opera en las regiones de la convocatoria?
    - Presupuesto (20%): ¿El budget de la org es apropiado?

    Returns:
        {
            "total_score": 0-100,
            "breakdown": { ... },
            "recommendation": "APLICAR" | "REVISAR" | "NO RECOMENDADO"
        }
    """
    scores = {}

    # Get organization data
    org_type = getattr(organization, 'organization_type', None) or ''
    org_sectors = set(getattr(organization, 'sectors', None) or [])
    org_regions = set(getattr(organization, 'regions', None) or [])
    org_budget = getattr(organization, 'annual_budget', None)

    # Get grant data
    grant_beneficiaries = getattr(grant, 'beneficiary_types', None) or []
    grant_sectors = set(getattr(grant, 'sectors', None) or [])
    grant_regions = set(getattr(grant, 'regions', None) or [])
    grant_budget = getattr(grant, 'budget_amount', None)

    # 1. Tipo de beneficiario (25%)
    org_type_keywords = {
        "fundacion": ["fundación", "fundaciones", "entidades sin ánimo de lucro", "entidades sin animo de lucro", "personas jurídicas sin ánimo de lucro"],
        "asociacion": ["asociación", "asociaciones", "entidades sin ánimo de lucro", "entidades sin animo de lucro", "personas jurídicas sin ánimo de lucro"],
        "ong": ["ong", "organizaciones no gubernamentales", "entidades sin ánimo de lucro", "entidades sin animo de lucro", "tercer sector"],
        "cooperativa": ["cooperativa", "cooperativas", "economía social"],
        "empresa": ["empresa", "empresas", "pyme", "pymes", "autónomos", "personas jurídicas"],
    }

    type_keywords = org_type_keywords.get(org_type.lower(), []) if org_type else []
    beneficiary_text = " ".join(grant_beneficiaries).lower()

    if not beneficiary_text:
        # No hay info de beneficiarios, asumimos neutral
        scores["beneficiary_type"] = 0.5
    elif any(keyword in beneficiary_text for keyword in type_keywords):
        scores["beneficiary_type"] = 1.0
    else:
        # Verificar si hay "cualquier persona jurídica" o similar
        if any(term in beneficiary_text for term in ["cualquier", "todas", "persona jurídica", "entidad"]):
            scores["beneficiary_type"] = 0.7
        else:
            scores["beneficiary_type"] = 0.0

    # 2. Sectores (30%)
    if grant_sectors:
        if org_sectors:
            # Intersección de sectores
            matching_sectors = org_sectors & grant_sectors
            scores["sectors"] = len(matching_sectors) / len(grant_sectors)
        else:
            # Org no tiene sectores definidos
            scores["sectors"] = 0.3
    else:
        # Grant no tiene sectores definidos, asumimos neutral
        scores["sectors"] = 0.5

    # 3. Regiones (25%)
    if grant_regions:
        # Normalizar regiones (quitar prefijos como "ES41 - ")
        normalized_grant_regions = set()
        for r in grant_regions:
            if " - " in r:
                code = r.split(" - ")[0]
                normalized_grant_regions.add(code)
            else:
                normalized_grant_regions.add(r)

        normalized_org_regions = set()
        for r in org_regions:
            if " - " in r:
                code = r.split(" - ")[0]
                normalized_org_regions.add(code)
            else:
                normalized_org_regions.add(r)

        if not normalized_org_regions:
            # Org no tiene regiones definidas, asumimos neutral
            scores["regions"] = 0.5
        elif "ES" in normalized_org_regions or "nacional" in [r.lower() for r in org_regions]:
            # Organización opera a nivel nacional
            scores["regions"] = 1.0
        elif normalized_org_regions & normalized_grant_regions:
            # Hay coincidencia de regiones
            scores["regions"] = 1.0
        else:
            scores["regions"] = 0.0
    else:
        # Sin restricción regional
        scores["regions"] = 1.0

    # 4. Budget match (20%)
    if grant_budget and org_budget:
        # Si el presupuesto de la org es >= 10% del presupuesto de la convocatoria,
        # consideramos que tiene capacidad
        if grant_budget > 0:
            ratio = org_budget / grant_budget
            if ratio >= 0.5:
                scores["budget"] = 1.0
            elif ratio >= 0.2:
                scores["budget"] = 0.7
            elif ratio >= 0.1:
                scores["budget"] = 0.5
            else:
                scores["budget"] = 0.3
        else:
            scores["budget"] = 0.5
    else:
        # Sin info de presupuesto
        scores["budget"] = 0.5

    # Score total ponderado
    total = (
        scores["beneficiary_type"] * 0.25 +
        scores["sectors"] * 0.30 +
        scores["regions"] * 0.25 +
        scores["budget"] * 0.20
    )

    # Determinar recomendación
    if total >= 0.7:
        recommendation = "APLICAR"
    elif total >= 0.4:
        recommendation = "REVISAR"
    else:
        recommendation = "NO RECOMENDADO"

    return {
        "total_score": round(total * 100),  # 0-100
        "breakdown": {
            "beneficiary_type": round(scores["beneficiary_type"] * 100),
            "sectors": round(scores["sectors"] * 100),
            "regions": round(scores["regions"] * 100),
            "budget": round(scores["budget"] * 100),
        },
        "recommendation": recommendation
    }
