"""
Check why recent BDNS grants are not passing nonprofit filter
"""
import sys
sys.path.insert(0, '.')

from shared.bdns_api import BDNSAPIClient

client = BDNSAPIClient()

# Test with the codes from the logs
test_codes = ['864005', '864004', '864003']

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

for code in test_codes:
    print(f"\n{'='*70}")
    print(f"BDNS-{code}")
    print('='*70)

    detail = client.get_convocatoria_detail(code)

    print(f"\n📋 DESCRIPCIÓN:")
    print(f"  {detail.descripcion[:100]}...")

    print(f"\n🎯 FINALIDAD:")
    print(f"  {detail.descripcionFinalidad[:100] if detail.descripcionFinalidad else 'N/A'}...")

    print(f"\n👥 TIPOS DE BENEFICIARIOS: {len(detail.tiposBeneficiarios) if detail.tiposBeneficiarios else 0}")
    if detail.tiposBeneficiarios:
        for b in detail.tiposBeneficiarios:
            print(f"  - {b.descripcion}")

    # Check if nonprofit
    text_to_check = f"{detail.descripcion} {detail.descripcionFinalidad or ''}"
    if detail.tiposBeneficiarios:
        beneficiary_text = " ".join([b.descripcion for b in detail.tiposBeneficiarios])
        text_to_check += " " + beneficiary_text

    text_lower = text_to_check.lower()
    matches = []
    for keyword in nonprofit_keywords:
        if keyword in text_lower:
            matches.append(keyword)

    print(f"\n🔍 NONPROFIT FILTER:")
    if matches:
        confidence = min(0.5 + (len(matches) * 0.15), 1.0)
        print(f"  ✅ PASS - Confidence: {confidence:.2f}")
        print(f"  Keywords found: {', '.join(matches)}")
    else:
        print(f"  ❌ FAIL - No nonprofit keywords found")
        print(f"  Checked text: {text_to_check[:200]}...")

print(f"\n{'='*70}")
print("Analysis complete!")
print('='*70)
