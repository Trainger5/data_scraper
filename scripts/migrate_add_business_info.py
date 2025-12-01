import sys
import os

# Add parent directory to path to import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Database

def migrate():
    print("Starting database migration for business info...")
    try:
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Add columns to emails table
        print("Migrating emails table...")
        columns = [
            ("business_name", "VARCHAR(255)"),
            ("website", "TEXT"),
            ("address", "TEXT")
        ]
        
        for col_name, col_type in columns:
            try:
                cursor.execute(f"SHOW COLUMNS FROM emails LIKE '{col_name}'")
                if not cursor.fetchone():
                    cursor.execute(f"ALTER TABLE emails ADD COLUMN {col_name} {col_type}")
                    print(f"  ✓ Added {col_name} column to emails")
                else:
                    print(f"  - {col_name} column already exists in emails")
            except Exception as e:
                print(f"  ✗ Error checking/adding {col_name} to emails: {e}")

        # Add columns to phones table
        print("Migrating phones table...")
        for col_name, col_type in columns:
            try:
                cursor.execute(f"SHOW COLUMNS FROM phones LIKE '{col_name}'")
                if not cursor.fetchone():
                    cursor.execute(f"ALTER TABLE phones ADD COLUMN {col_name} {col_type}")
                    print(f"  ✓ Added {col_name} column to phones")
                else:
                    print(f"  - {col_name} column already exists in phones")
            except Exception as e:
                print(f"  ✗ Error checking/adding {col_name} to phones: {e}")
                
        conn.commit()
        conn.close()
        print("\nMigration completed successfully!")
        
    except Exception as e:
        print(f"\nMigration failed: {e}")

if __name__ == "__main__":
    migrate()
