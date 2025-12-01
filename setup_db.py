from database import Database

def setup():
    print("Initializing database...")
    try:
        db = Database()
        # The __init__ method calls init_database() which creates all tables
        # if they don't exist. Since tables were deleted, this will recreate them.
        print("Database tables created successfully.")
        
        # Verify tables
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]
        print(f"Tables found: {', '.join(tables)}")
        conn.close()
        
    except Exception as e:
        print(f"Setup failed: {e}")

if __name__ == "__main__":
    setup()
