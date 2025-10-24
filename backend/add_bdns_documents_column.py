"""
Quick script to add bdns_documents column to existing SQLite database
"""
import sqlite3

# Connect to the database
conn = sqlite3.connect('subvenciones.db')
cursor = conn.cursor()

try:
    # Add bdns_documents column as JSON/TEXT
    cursor.execute('ALTER TABLE grants ADD COLUMN bdns_documents TEXT')
    conn.commit()
    print("✅ Successfully added bdns_documents column")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e).lower():
        print("⚠️  Column bdns_documents already exists")
    else:
        print(f"❌ Error: {e}")
finally:
    conn.close()
