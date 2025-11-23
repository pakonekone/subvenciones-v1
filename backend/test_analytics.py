import sys
import os
import asyncio
from sqlalchemy.orm import Session

# Add current directory to path
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.api.v1.analytics import get_analytics_overview

async def test_full_analytics():
    db = SessionLocal()
    try:
        print("Testing get_analytics_overview...")
        result = await get_analytics_overview(days=30, db=db)
        print("Success!")
        print(result)
    except Exception as e:
        print(f"Error in get_analytics_overview: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_full_analytics())
