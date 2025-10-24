"""
Update existing BDNS grants with documents and PDF URLs
"""
import sys
sys.path.insert(0, '.')

from app.database import SessionLocal
from app.models import Grant
from shared.bdns_api import BDNSAPIClient
import json

db = SessionLocal()
client = BDNSAPIClient()

# Get all BDNS grants that don't have bdns_documents
grants = db.query(Grant).filter(
    Grant.source == 'BDNS',
    Grant.bdns_documents == None
).limit(10).all()  # Limit to 10 for testing

print(f"Found {len(grants)} BDNS grants to update\n")

updated = 0
errors = 0

for grant in grants:
    try:
        # Extract BDNS code from ID (BDNS-XXXXX)
        bdns_code = grant.bdns_code or grant.id.replace('BDNS-', '')

        print(f"Updating {grant.id}...")

        # Fetch detail from BDNS
        detail = client.get_convocatoria_detail(bdns_code)

        # Extract documents
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

        # Extract PDF URL with priority logic
        pdf_url = None
        if bdns_documents and len(bdns_documents) > 0:
            pdf_url = bdns_documents[0]['url']
            print(f"  ✅ Found {len(bdns_documents)} document(s), PDF: {pdf_url}")
        elif detail.anuncios and len(detail.anuncios) > 0 and detail.anuncios[0].url:
            pdf_url = detail.anuncios[0].url
            print(f"  ✅ Found PDF from anuncios: {pdf_url}")
        elif detail.urlBasesReguladoras:
            pdf_url = detail.urlBasesReguladoras
            print(f"  ✅ Using urlBasesReguladoras: {pdf_url}")

        # Update grant
        grant.bdns_documents = bdns_documents if bdns_documents else None
        grant.pdf_url = pdf_url

        updated += 1

    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        errors += 1

# Commit all updates
db.commit()
db.close()

print(f"\n{'='*60}")
print(f"✅ Updated: {updated}")
print(f"❌ Errors: {errors}")
print('='*60)
