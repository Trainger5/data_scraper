"""
Database management for Email Extractor Platform
Uses MySQL for scalability
"""

import mysql.connector
from mysql.connector import Error
import json
from datetime import datetime
from config import MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB


class Database:
    def __init__(self):
        self.init_database()
        self.migrate_database()
    
    def get_connection(self):
        """Create database connection"""
        try:
            conn = mysql.connector.connect(
                host=MYSQL_HOST,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DB
            )
            return conn
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            # Try to connect without DB to create it if it doesn't exist
            if "Unknown database" in str(e):
                self.create_database()
                return self.get_connection()
            return None

    def create_database(self):
        """Create the database if it doesn't exist"""
        try:
            conn = mysql.connector.connect(
                host=MYSQL_HOST,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD
            )
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DB}")
            print(f"Database '{MYSQL_DB}' created successfully")
            conn.close()
        except Error as e:
            print(f"Error creating database: {e}")

    def init_database(self):
        """Initialize database tables"""
        conn = self.get_connection()
        if not conn:
            return

        cursor = conn.cursor()
        
        # Searches table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS searches (
                id INT AUTO_INCREMENT PRIMARY KEY,
                query VARCHAR(255) NOT NULL,
                status VARCHAR(50) DEFAULT 'pending',
                total_emails INT DEFAULT 0,
                pages_crawled INT DEFAULT 0,
                current_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP NULL
            )
        ''')
        
        # Emails table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS emails (
                id INT AUTO_INCREMENT PRIMARY KEY,
                search_id INT NOT NULL,
                email VARCHAR(191) NOT NULL,
                source_url TEXT,
                domain VARCHAR(191),
                found_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (search_id) REFERENCES searches(id) ON DELETE CASCADE,
                UNIQUE KEY unique_email (search_id, email)
            )
        ''')
        
        # Phones table
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
        
        # Businesses table (for Yelp, Maps, etc.)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS businesses (
                id INT AUTO_INCREMENT PRIMARY KEY,
                search_id INT NOT NULL,
                name VARCHAR(255),
                phone VARCHAR(50),
                address TEXT,
                website TEXT,
                rating DECIMAL(3,2),
                review_count INT,
                source VARCHAR(50) DEFAULT 'Yelp',
                found_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (search_id) REFERENCES searches(id) ON DELETE CASCADE
            )
        ''')
        
        # Crawled URLs table (to avoid duplicate crawling)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crawled_urls (
                id INT AUTO_INCREMENT PRIMARY KEY,
                search_id INT NOT NULL,
                url TEXT NOT NULL,
                crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (search_id) REFERENCES searches(id) ON DELETE CASCADE
            )
        ''')
        
        conn.commit()
        conn.close()

    def migrate_database(self):
        """Add missing columns to tables"""
        conn = self.get_connection()
        if not conn: return
        cursor = conn.cursor()
        try:
            # Check if search_type exists
            cursor.execute("SHOW COLUMNS FROM searches LIKE 'search_type'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE searches ADD COLUMN search_type VARCHAR(50) DEFAULT 'web'")
                print("Added search_type column")
            
            # Check if engine exists
            cursor.execute("SHOW COLUMNS FROM searches LIKE 'engine'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE searches ADD COLUMN engine VARCHAR(50) DEFAULT 'duckduckgo'")
                print("Added engine column")
            
            # Add business columns to emails table
            cursor.execute("SHOW COLUMNS FROM emails LIKE 'business_name'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE emails ADD COLUMN business_name VARCHAR(255)")
                print("Added business_name to emails")
            
            cursor.execute("SHOW COLUMNS FROM emails LIKE 'website'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE emails ADD COLUMN website TEXT")
                print("Added website to emails")
            
            cursor.execute("SHOW COLUMNS FROM emails LIKE 'address'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE emails ADD COLUMN address TEXT")
                print("Added address to emails")
            
            # Add business columns to phones table
            cursor.execute("SHOW COLUMNS FROM phones LIKE 'business_name'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE phones ADD COLUMN business_name VARCHAR(255)")
                print("Added business_name to phones")
            
            cursor.execute("SHOW COLUMNS FROM phones LIKE 'website'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE phones ADD COLUMN website TEXT")
                print("Added website to phones")
            
            cursor.execute("SHOW COLUMNS FROM phones LIKE 'address'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE phones ADD COLUMN address TEXT")
                print("Added address to phones")
                
            conn.commit()
        except Error as e:
            print(f"Migration error: {e}")
        finally:
            conn.close()


    def create_search(self, query, search_type='web', engine='duckduckgo'):
        """Create new search record"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO searches (query, status, search_type, engine) VALUES (%s, %s, %s, %s)',
            (query, 'running', search_type, engine)
        )
        search_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return search_id
    
    def update_search_status(self, search_id, status, pages_crawled=None, total_emails=None, current_url=None):
        """Update search status"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        update_parts = ['status = %s']
        params = [status]
        
        if pages_crawled is not None:
            update_parts.append('pages_crawled = %s')
            params.append(pages_crawled)
        
        if total_emails is not None:
            update_parts.append('total_emails = %s')
            params.append(total_emails)
        
        if current_url is not None:
            update_parts.append('current_url = %s')
            params.append(current_url)
        
        if status == 'completed':
            update_parts.append('completed_at = %s')
            params.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            # Clear current_url when completed
            update_parts.append('current_url = %s')
            params.append(None)
        
        params.append(search_id)
        
        query = f"UPDATE searches SET {', '.join(update_parts)} WHERE id = %s"
        cursor.execute(query, tuple(params))
        conn.commit()
        conn.close()
    
    def add_email(self, search_id, email, source_url, domain, business_name=None, website=None, address=None):
        """Add extracted email to database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        inserted = False
        try:
            cursor.execute(
                'INSERT IGNORE INTO emails (search_id, email, source_url, domain, business_name, website, address) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                (search_id, email, source_url, domain, business_name, website, address)
            )
            conn.commit()
            inserted = cursor.rowcount > 0
        except Error as e:
            print(f"Error adding email: {e}")
        finally:
            conn.close()
        return inserted

    def add_phone(self, search_id, phone, source_url, business_name=None, website=None, address=None):
        """Add extracted phone to database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        inserted = False
        try:
            cursor.execute(
                'INSERT IGNORE INTO phones (search_id, phone, source_url, business_name, website, address) VALUES (%s, %s, %s, %s, %s, %s)',
                (search_id, phone, source_url, business_name, website, address)
            )
            conn.commit()
            inserted = cursor.rowcount > 0
        except Error as e:
            print(f"Error adding phone: {e}")
        finally:
            conn.close()
        return inserted
    
    def add_business(self, search_id, business_data, source='Yelp'):
        """Add business data to database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        inserted = False
        try:
            cursor.execute('''
                INSERT INTO businesses 
                (search_id, name, phone, address, website, rating, review_count, source) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                search_id,
                business_data.get('name'),
                business_data.get('phone'),
                business_data.get('address'),
                business_data.get('website'),
                business_data.get('rating'),
                business_data.get('review_count'),
                source
            ))
            conn.commit()
            inserted = cursor.rowcount > 0
        except Error as e:
            print(f"Error adding business: {e}")
        finally:
            conn.close()
        return inserted

    
    def add_crawled_url(self, search_id, url):
        """Mark URL as crawled"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # Check if exists first since we removed UNIQUE constraint on TEXT column
            cursor.execute(
                'SELECT id FROM crawled_urls WHERE search_id = %s AND url = %s', # This might be slow for TEXT, but ok for now
                (search_id, url)
            )
            if not cursor.fetchone():
                cursor.execute(
                    'INSERT INTO crawled_urls (search_id, url) VALUES (%s, %s)',
                    (search_id, url)
                )
                conn.commit()
        except Error as e:
            print(f"Error adding crawled URL: {e}")
        finally:
            conn.close()
    
    def is_url_crawled(self, search_id, url):
        """Check if URL was already crawled for this search"""
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            'SELECT COUNT(*) as count FROM crawled_urls WHERE search_id = %s AND url = %s',
            (search_id, url)
        )
        result = cursor.fetchone()
        conn.close()
        return result['count'] > 0
    
    def get_search_status(self, search_id):
        """Get status of a search"""
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM searches WHERE id = %s', (search_id,))
        search = cursor.fetchone()
        conn.close()
        return search

    def get_search_results(self, search_id):
        """Get all results for a search"""
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get emails
        cursor.execute(
            'SELECT email, source_url, domain, found_at, business_name, website, address FROM emails WHERE search_id = %s ORDER BY found_at DESC',
            (search_id,)
        )
        emails = cursor.fetchall()
        
        # Get phones
        cursor.execute(
            'SELECT phone, source_url, found_at, business_name, website, address FROM phones WHERE search_id = %s ORDER BY found_at DESC',
            (search_id,)
        )
        phones = cursor.fetchall()
        
        conn.close()
        
        return {
            'emails': emails,
            'phones': phones
        }
    
    def get_businesses(self, search_id):
        """Get all businesses for a search"""
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            'SELECT name, phone, address, website, rating, review_count, source, found_at FROM businesses WHERE search_id = %s ORDER BY found_at DESC',
            (search_id,)
        )
        businesses = cursor.fetchall()
        conn.close()
        return businesses

    
    def get_all_searches(self, limit=50):
        """Get all searches with email counts"""
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            'SELECT * FROM searches ORDER BY created_at DESC LIMIT %s',
            (limit,)
        )
        searches = cursor.fetchall()
        conn.close()
        return searches
    
    def get_all_emails(self):
        """Get all emails from database"""
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('''
            SELECT DISTINCT email, domain, source_url, found_at, business_name, website, address
            FROM emails
            ORDER BY found_at DESC
        ''')
        emails = cursor.fetchall()
        conn.close()
        return emails
    
    def get_all_phones(self):
        """Get all phone numbers from database"""
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('''
            SELECT DISTINCT phone, source_url, found_at, business_name, website, address
            FROM phones
            ORDER BY found_at DESC
        ''')
        phones = cursor.fetchall()
        conn.close()
        return phones
    
    def get_email_count(self, search_id):
        """Get total unique emails for a search"""
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            'SELECT COUNT(DISTINCT email) as count FROM emails WHERE search_id = %s',
            (search_id,)
        )
        result = cursor.fetchone()
        conn.close()
        return result['count']
    
    def delete_search(self, search_id):
        """Delete search and all associated data"""
        conn = self.get_connection()
        cursor = conn.cursor()
        # Cascading delete handles emails and crawled_urls if FK set up correctly, 
        # but explicit delete is safer if not.
        cursor.execute('DELETE FROM searches WHERE id = %s', (search_id,))
        conn.commit()
        conn.close()
