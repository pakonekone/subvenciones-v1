#!/usr/bin/env python3
"""
Initialize database with all tables
"""
from app.database import Base, engine
from app.models.grant import Grant

def init_database():
    """Create all database tables"""
    print("🔧 Initializing database...")
    print(f"📊 Database URL: {engine.url}")

    # Drop all tables (for clean start)
    # Base.metadata.drop_all(bind=engine)
    # print("🗑️  Dropped existing tables")

    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")

    # Verify tables were created
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"📋 Tables in database: {tables}")

    if "grants" in tables:
        print("✅ Grants table exists!")

        # Show table structure
        columns = inspector.get_columns("grants")
        print(f"📊 Grants table has {len(columns)} columns")
        for col in columns[:5]:  # Show first 5 columns
            print(f"   - {col['name']}: {col['type']}")
        print("   ...")
    else:
        print("❌ ERROR: Grants table was not created!")
        return False

    return True

if __name__ == "__main__":
    success = init_database()
    exit(0 if success else 1)
