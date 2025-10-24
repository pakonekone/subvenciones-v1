"""
Migration script to add boe_id column to grants table
"""
from sqlalchemy import create_engine, text
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.config import settings

DATABASE_URL = settings.database_url

def run_migration():
    """Add boe_id column to grants table"""
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        # Check if column exists
        result = conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='grants' AND column_name='boe_id'
        """))

        if result.fetchone() is None:
            print("Adding boe_id column...")
            conn.execute(text("""
                ALTER TABLE grants
                ADD COLUMN boe_id VARCHAR
            """))

            # Add index
            conn.execute(text("""
                CREATE INDEX idx_grants_boe_id ON grants(boe_id)
            """))

            conn.commit()
            print("✅ Migration complete: boe_id column added with index")
        else:
            print("⚠️  Column boe_id already exists, skipping migration")

if __name__ == "__main__":
    run_migration()
