"""
FastAPI dependencies
"""
from typing import Generator

def get_db() -> Generator:
    """
    Database session dependency
    TODO: Implement actual DB session
    """
    try:
        # db = SessionLocal()
        # yield db
        yield None
    finally:
        # db.close()
        pass
