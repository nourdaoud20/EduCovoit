# migrations.py
"""Database migration utilities for handling schema updates"""

import sqlite3
from pathlib import Path

def migrate_messages_table(db_path):
    """
    Migrate messages table to add destinataire_id column if it doesn't exist.
    This supports direct messaging between users.
    
    Note: SQLite does not support adding foreign key constraints via ALTER TABLE,
    so destinataire_id is added as an INTEGER column referencing utilisateurs.id.
    The foreign key constraint is defined in the SQLAlchemy model (models.py)
    for ORM-level enforcement.
    
    Returns:
        bool: True if migration succeeded or wasn't needed, False on error
    """
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Check if destinataire_id column exists
            cursor.execute("PRAGMA table_info(messages)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            if 'destinataire_id' not in column_names:
                print("🔧 Migrating messages table: adding destinataire_id column...")
                
                # Add the missing column for direct messages (references utilisateurs.id)
                cursor.execute("""
                    ALTER TABLE messages 
                    ADD COLUMN destinataire_id INTEGER
                """)
                
                print("✅ Added destinataire_id column to messages table")
            else:
                print("✅ destinataire_id column already exists")
        
        return True
        
    except sqlite3.OperationalError as e:
        print(f"❌ Migration error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during migration: {e}")
        return False


def run_all_migrations(db_path):
    """
    Run all pending migrations on the database.
    
    Args:
        db_path (str): Path to the SQLite database file
        
    Returns:
        bool: True if all migrations succeeded, False if any failed
    """
    print("🔄 Running database migrations...")
    
    # Ensure database file exists
    if not Path(db_path).exists():
        print("✅ New database will be created by SQLAlchemy")
        return True
    
    # Run migrations
    if not migrate_messages_table(db_path):
        print("⚠️  Migration failed - some features may not work correctly")
        return False
    
    print("✅ Migrations completed successfully")
    return True
