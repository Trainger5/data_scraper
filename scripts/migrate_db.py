import sys
import os

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Database

def migrate():
    print("Starting database migration...")
    try:
        db = Database()
        # init_database is called in __init__, so just instantiating it triggers table creation
        print("Database initialized and tables created/verified.")
        
        # Verify businesses table exists
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES LIKE 'businesses'")
        if cursor.fetchone():
            print("✅ 'businesses' table exists.")
        else:
            print("❌ 'businesses' table was NOT created.")
            
        conn.close()
        
    except Exception as e:
        print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate()
