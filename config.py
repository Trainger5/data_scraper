"""
Configuration settings for Email Extractor Platform
"""

import os

# Application Settings
DEBUG = True
HOST = '127.0.0.1'
PORT = 5000

# Database Settings
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# SQLite path (kept for reference/fallback)
SQLITE_DB_PATH = os.path.join(BASE_DIR, 'email_extractor.db')

# MySQL Settings
MYSQL_HOST = 'localhost'
MYSQL_USER = 'root'
MYSQL_PASSWORD = ''  # Default for local dev, change if needed
MYSQL_DB = 'email_extractor'

# Crawler Settings
MAX_PAGES_PER_SEARCH = 100  # Increased for broader crawling
MAX_WORKERS = 8  # Number of parallel threads
MAX_CRAWL_DEPTH = 2  # How deep to follow links
REQUEST_DELAY = 1  # Reduced delay since we are parallel (per thread)
REQUEST_TIMEOUT = 15  # Seconds to wait for response
MAX_SEARCH_RESULTS = 20  # Number of initial URLs from search
MAX_EXTERNAL_LINKS = 5  # Max external links to follow per page

# User Agent (identify yourself)
USER_AGENT = 'EmailExtractorBot/1.0 (Educational/Research Purpose)'

# Email Validation
MIN_EMAIL_LENGTH = 6
MAX_EMAIL_LENGTH = 100

# Excluded email patterns (common placeholders/fake emails)
EXCLUDED_PATTERNS = [
    'example.com',
    'test.com',
    'sample.com',
    'domain.com',
    'email.com',
    'your-email.com',
    'noreply@',
    'no-reply@',
    'donotreply@'
]

# Search Settings
SEARCH_ENGINES = {
    'duckduckgo': 'https://html.duckduckgo.com/html/?q={query}',
    'bing': 'https://www.bing.com/search?q={query}',
    'google': 'https://www.google.com/search?q={query}&num=20'
}
DEFAULT_SEARCH_ENGINE = 'duckduckgo'

# Rate Limiting
MAX_CONCURRENT_SEARCHES = 3
SEARCH_COOLDOWN = 5  # Seconds between searches from same IP

# Proxy Settings
USE_PROXIES = False  # Enable/disable proxy rotation
# USE_PROXIES = True  # Enable/disable proxy rotation
PROXY_LIST_FILE = os.path.join(BASE_DIR, 'proxies.txt')  # Path to proxy list file
PROXY_TYPE = 'http'  # 'http' or 'socks5'
PROXY_ROTATION_STRATEGY = 'random'  # 'random' or 'round-robin'
MAX_PROXY_RETRIES = 3  # Number of retries before marking proxy as failed
PROXY_TIMEOUT = 10  # Seconds to wait for proxy validation

# Selenium/Chrome Settings
HEADLESS_MODE = False  # Run browser in headless mode (set to False to see browser window)
CHROME_DRIVER_PATH = None  # None = use Selenium's built-in manager

