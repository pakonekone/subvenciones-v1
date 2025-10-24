"""
Test script to verify BDNS PDF/documents capture
"""
import sys
sys.path.insert(0, '.')

from shared.bdns_api import BDNSAPIClient
import json

# Test with the BDNS codes we know have documents
test_codes = ['863219', '863218', '863217']

client = BDNSAPIClient()

for code in test_codes:
    print(f"\n{'='*60}")
    print(f"Testing BDNS-{code}")
    print('='*60)

    detail = client.get_convocatoria_detail(code)

    # Check documentos
    print(f"\n📄 DOCUMENTOS: {len(detail.documentos) if detail.documentos else 0}")
    if detail.documentos:
        for doc in detail.documentos:
            print(f"  - ID: {doc.id}")
            print(f"    Nombre: {doc.nombreFic}")
            print(f"    URL: https://www.infosubvenciones.es/bdnstrans/api/documento/{doc.id}")

    # Check anuncios
    print(f"\n📰 ANUNCIOS: {len(detail.anuncios) if detail.anuncios else 0}")
    if detail.anuncios:
        for anuncio in detail.anuncios:
            print(f"  - URL: {anuncio.url}")

    # Check urlBasesReguladoras
    print(f"\n🔗 URL BASES REGULADORAS: {detail.urlBasesReguladoras}")

    # Simulate our priority logic
    print(f"\n✅ RESULTADO CON NUEVA LÓGICA:")
    pdf_url = None

    if detail.documentos and len(detail.documentos) > 0:
        pdf_url = f"https://www.infosubvenciones.es/bdnstrans/api/documento/{detail.documentos[0].id}"
        print(f"  Priority 1 (documentos): {pdf_url}")
    elif detail.anuncios and len(detail.anuncios) > 0 and detail.anuncios[0].url:
        pdf_url = detail.anuncios[0].url
        print(f"  Priority 2 (anuncios): {pdf_url}")
    elif detail.urlBasesReguladoras:
        pdf_url = detail.urlBasesReguladoras
        print(f"  Priority 3 (urlBasesReguladoras): {pdf_url}")
    else:
        print(f"  ❌ NO PDF URL FOUND")

print(f"\n{'='*60}")
print("✅ Test completed!")
print('='*60)
