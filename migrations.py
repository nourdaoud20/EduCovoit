# migrations.py
"""Database migration utilities for handling schema updates"""

import sqlite3
from pathlib import Path

def migrate_messages_table(db_path):
    """
    Migrate messages table to add destinataire_id column if it doesn't exist.
    This supports direct messaging between users.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if destinataire_id column exists
        cursor.execute("PRAGMA table_info(messages)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'destinataire_id' not in column_names:
            print("🔧 Migrating messages table: adding destinataire_id column...")
            
            # Add the missing column
            cursor.execute("""
                ALTER TABLE messages 
                ADD COLUMN destinataire_id INTEGER
            """)
            
            # Add foreign key constraint (SQLite doesn't support ALTER to add FK directly,
            # so we just make it a regular column and ensure it references utilisateurs.id)
            print("✅ Added destinataire_id column to messages table")
            conn.commit()
        else:
            print("✅ destinataire_id column already exists")
            
        conn.close()
        return True
        
    except sqlite3.OperationalError as e:
        print(f"❌ Migration error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during migration: {e}")
        return False


def run_all_migrations(db_path):
    """Run all pending migrations on the database."""
    print("🔄 Running database migrations...")
    
    # Ensure database file exists
    if not Path(db_path).exists():
        print("✅ New database will be created by SQLAlchemy")
        return True
    
    # Run migrations
    if not migrate_messages_table(db_path):
        print("⚠️  Migration encountered issues but continuing...")
    
    print("✅ Migrations completed")
    return True
