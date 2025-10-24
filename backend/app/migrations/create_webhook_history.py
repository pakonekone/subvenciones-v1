"""
Migration script to create webhook_history table
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
    """Create webhook_history table"""
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        # Check if table exists
        result = conn.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name='webhook_history'
        """))

        if result.fetchone() is None:
            print("Creating webhook_history table...")
            conn.execute(text("""
                CREATE TABLE webhook_history (
                    id SERIAL PRIMARY KEY,
                    grant_id VARCHAR NOT NULL,
                    attempt_number INTEGER DEFAULT 1,
                    max_retries INTEGER DEFAULT 3,
                    status VARCHAR NOT NULL,
                    http_status_code INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sent_at TIMESTAMP,
                    next_retry_at TIMESTAMP,
                    response_body JSONB,
                    error_message TEXT,
                    error_type VARCHAR,
                    webhook_url TEXT NOT NULL,
                    payload JSONB,
                    response_time_ms FLOAT
                )
            """))

            # Add indexes
            conn.execute(text("""
                CREATE INDEX idx_webhook_history_grant_id ON webhook_history(grant_id)
            """))

            conn.execute(text("""
                CREATE INDEX idx_webhook_history_created_at ON webhook_history(created_at)
            """))

            conn.execute(text("""
                CREATE INDEX idx_webhook_history_next_retry_at ON webhook_history(next_retry_at)
            """))

            conn.execute(text("""
                CREATE INDEX idx_webhook_history_status ON webhook_history(status)
            """))

            conn.commit()
            print("✅ Migration complete: webhook_history table created with indexes")
        else:
            print("⚠️  Table webhook_history already exists, skipping migration")

if __name__ == "__main__":
    run_migration()
