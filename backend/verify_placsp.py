import sys
import os
sys.path.append(os.getcwd())
import logging
from app.database import SessionLocal, engine, Base
from app.services.placsp_service import PLACSPService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_placsp():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    
    print("Initializing DB session...")
    db = SessionLocal()
    
    try:
        service = PLACSPService(db)
        print("Service initialized. Fetching grants...")
        
        # Capture recent grants
        stats = service.capture_recent_grants(days_back=1)
        print("\nCapture finished.")
        print(f"Stats: {stats}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    verify_placsp()
