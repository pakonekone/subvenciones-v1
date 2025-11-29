import sys
import os
sys.path.append(os.getcwd())
from app.database import SessionLocal
from app.models import Grant

def show_captured_grants():
    db = SessionLocal()
    grants = db.query(Grant).filter(Grant.source == 'PLACSP').limit(5).all()
    
    print(f"Found {len(grants)} PLACSP grants in DB. Showing first 5:\n")
    for grant in grants:
        print(f"ID: {grant.id}")
        print(f"Title: {grant.title}")
        print(f"Amount: {grant.budget_amount} EUR")
        print(f"Department: {grant.department}")
        print(f"Folder ID: {grant.placsp_folder_id}")
        print(f"CPV: {grant.cpv_codes}")
        print(f"PDF: {grant.pdf_url}")
        print(f"Link: {grant.html_url}")
        print(f"Date: {grant.publication_date}")
        print(f"Purpose: {grant.purpose}")
        print("-" * 50)
    # Find grants with link
    grants_with_link = db.query(Grant).filter(Grant.source == 'PLACSP', Grant.html_url.isnot(None)).limit(5).all()
    
    if grants_with_link:
        print(f"\nFound {len(grants_with_link)} grants WITH link. Showing first 5:")
        for grant in grants_with_link:
            print(f"ID: {grant.id}")
            print(f"Title: {grant.title}")
            print(f"Link: {grant.html_url}")
            print("-" * 50)
    else:
        print("\nNo grants with link found.")

    db.close()

if __name__ == "__main__":
    show_captured_grants()
