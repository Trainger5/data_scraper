import mysql.connector
from config import MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB

def verify():
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB
        )
        cursor = conn.cursor()
        
        print(f"Connected to database: {MYSQL_DB}")
        print("Checking 'emails' table schema:")
        cursor.execute("DESCRIBE emails")
        columns = cursor.fetchall()
        
        found_phone = False
        for col in columns:
            print(f" - {col[0]} ({col[1]})")
            if col[0] == 'phone':
                found_phone = True
                
        if found_phone:
            print("\nSUCCESS: 'phone' column exists.")
            
            # Try a dummy insert to be sure
            print("Attempting test insert...")
            try:
                # Create a dummy search first
                cursor.execute("INSERT INTO searches (query, status) VALUES ('test_verify', 'completed')")
                search_id = cursor.lastrowid
                
                cursor.execute(
                    "INSERT INTO emails (search_id, email, source_url, domain, phone) VALUES (%s, %s, %s, %s, %s)",
                    (search_id, 'test@example.com', 'http://test.com', 'test.com', '1234567890')
                )
                conn.commit()
                print("SUCCESS: Test insert worked!")
                
                # Cleanup
                cursor.execute("DELETE FROM searches WHERE id = %s", (search_id,))
                conn.commit()
                
            except Exception as insert_err:
                print(f"FAILURE: Test insert failed: {insert_err}")
                
        else:
            print("\nFAILURE: 'phone' column is MISSING.")
            
        conn.close()
    except Exception as e:
        print(f"Verification failed: {e}")

if __name__ == "__main__":
    verify()
