"""
Create all database tables using SQLAlchemy models
Run this before Alembic migrations on fresh databases
"""
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(__file__))

from app.database import Base, engine
from app.models.grant import Grant
from app.models.webhook_history import WebhookHistory

def create_tables():
    """Create all tables defined in SQLAlchemy models"""
    print("Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created successfully!")
        return 0
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(create_tables())
