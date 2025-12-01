import mysql.connector
from config import MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB

def migrate_phones():
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB
        )
        cursor = conn.cursor()
        
        print("Creating 'phones' table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS phones (
                id INT AUTO_INCREMENT PRIMARY KEY,
                search_id INT NOT NULL,
                phone VARCHAR(50) NOT NULL,
                source_url TEXT,
                found_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (search_id) REFERENCES searches(id) ON DELETE CASCADE,
                UNIQUE KEY unique_phone (search_id, phone)
            )
        ''')
        conn.commit()
        print("Migration successful: 'phones' table created.")
            
        conn.close()
    except Exception as e:
        print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate_phones()
