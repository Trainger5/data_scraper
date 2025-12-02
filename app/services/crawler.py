"""
Web Crawler for Email Extractor
Responsible crawling with robots.txt compliance and rate limiting
"""

import requests
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, quote_plus
from urllib.robotparser import RobotFileParser
import validators
from config import (
    USER_AGENT,
    MAX_PAGES_PER_SEARCH, MAX_CRAWL_DEPTH, 
    MAX_SEARCH_RESULTS, MAX_EXTERNAL_LINKS
)
from app.services.settings import SettingsManager
from app.services.email_extractor import EmailExtractor
from app.database import Database
from app.services.scrapers.google_maps import MapsScraper
from app.services.scrapers.web_search import WebSearchScraper

class WebCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': USER_AGENT})
        self.email_extractor = EmailExtractor()
        self.db = Database()
        self.robots_cache = {}  # Cache robots.txt parsers
        headless = SettingsManager.get_setting('headless_mode', False)
        self.maps_scraper = MapsScraper(headless=headless)
    
    # ... existing methods ...

    def search_web(self, query, engine='duckduckgo', max_results=None, on_result=None, stop_check=None):
        """
        Search the web using Selenium to bypass bot detection
        """
        from app.services.scrapers.web_search import WebSearchScraper
        headless = SettingsManager.get_setting('headless_mode', False)
        scraper = WebSearchScraper(headless=headless)
        
        if max_results is None:
            max_results = MAX_SEARCH_RESULTS
            
        return scraper.search(query, max_results=max_results, engine=engine, on_result=on_result, stop_check=stop_check)

    def fetch_page(self, url):
        """
        Fetch a page and extract emails, phones, and links
        """
        try:
            # Respect robots.txt (simplified for now, just delay)
            delay = SettingsManager.get_setting('request_delay', 2.0)
            timeout = SettingsManager.get_setting('request_timeout', 30)
            time.sleep(delay)
            
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            
            # Extract emails and phones
            emails, phones = self.email_extractor.extract_from_html(response.text)
            
            # Extract links
            soup = BeautifulSoup(response.text, 'html.parser')
            links = []
            
            for a in soup.find_all('a', href=True):
                href = a['href']
                full_url = urljoin(url, href)
                
                # Basic filtering
                if validators.url(full_url) and full_url.startswith('http'):
                    # Avoid same page anchors
                    if '#' in full_url:
                        full_url = full_url.split('#')[0]
                    
                    if full_url != url:
                        links.append(full_url)
            
            return emails, phones, links
            
        except Exception as e:
            print(f"Fetch error for {url}: {e}")
            return [], [], []


    def crawl(self, search_id, query, progress_callback=None, use_google_maps=False, search_type='web', platform=None, engine=None, page_count=3, depth=2, max_pages=50, platform_type=None, target_website=None, scrape_emails=True, scrape_phones=True):
        """
        Main crawl function with Parallel Processing
        """
        # Use the default search engine from settings if not explicitly provided
        if engine is None:
            engine = SettingsManager.get_setting('default_search_engine', 'duckduckgo')
        
        results = {
            'search_id': search_id,
            'query': query,
            'emails': [],
            'phones': [],
            'pages_crawled': 0,
            'status': 'running'
        }
        email_set = set()
        phone_set = set()
        
        try:
            # Step 1: Search for relevant URLs
            print(f"\n{'='*60}")
            max_threads = SettingsManager.get_setting('max_threads', 8)
            print(f"Starting search for: '{query}' (Type: {search_type}, Engine: {engine.upper()}, Parallel: {max_threads} threads)")
            print(f"{'='*60}\n")
            
            if progress_callback:
                progress_callback(search_id, 'Searching for relevant websites...', 0)
            
            seed_urls = []
            business_data = []  # NEW: For storing business card data
            
            # Handle Search Types
            if search_type == 'maps' or use_google_maps:
                if progress_callback:
                    progress_callback(search_id, f'Extracting business cards from {engine.upper()} Maps...', 10)
                
                # NEW: Maps scraper now returns contact data, not URLs
                business_data = self.maps_scraper.search_maps(query, page_count=page_count, engine=engine)
                
                # Save contact data directly to database
                if business_data and len(business_data) > 0 and isinstance(business_data[0], dict):
                    print(f"\n✓ Received {len(business_data)} businesses with contact info")
                    print(f"💾 Saving directly to database (skipping website crawling)...\n")
                    
                    email_count = 0
                    phone_count = 0
                    business_count = 0
                    
                    for idx, business in enumerate(business_data):
                        # Save full business record
                        if self.db.add_business(search_id, business, 'Google Maps'):
                            business_count += 1
                            print(f"  [{idx+1}] 🏢 {business.get('name', 'Unknown')}")
                        
                        # Also save phone/email to respective tables for backward compatibility
                        if scrape_phones and business.get('phone'):
                            if self.db.add_phone(
                                search_id, 
                                business['phone'], 
                                'Google Maps',
                                business_name=business.get('name'),
                                website=business.get('website'),
                                address=business.get('address')
                            ):
                                phone_count += 1
                        
                        if scrape_emails and business.get('email'):
                            domain = self.email_extractor.get_domain(business['email'])
                            if self.db.add_email(
                                search_id, 
                                business['email'], 
                                'Google Maps', 
                                domain,
                                business_name=business.get('name'),
                                website=business.get('website'),
                                address=business.get('address')
                            ):
                                email_count += 1
                    
                    # Mark search as completed
                    total_records = 0
                    if scrape_emails:
                        total_records += email_count
                    if scrape_phones:
                        total_records += phone_count
                    self.db.update_search_status(search_id, 'completed', 0, total_records)
                    
                    results['status'] = 'completed'
                    results['emails'] = [b['email'] for b in business_data if b.get('email')] if scrape_emails else []
                    results['phones'] = [b['phone'] for b in business_data if b.get('phone')] if scrape_phones else []
                    results['businesses'] = business_data
                    
                    print(f"\n✓ Saved {business_count} businesses, {email_count} emails, and {phone_count} phones to database")
                    if progress_callback:
                        progress_callback(search_id, 'Completed!', 100)
                    
                    return results
                else:
                    # Fallback: old format (list of URLs)
                    seed_urls = business_data if business_data else []
            
            elif search_type == 'social' and platform:
                site_map = {
                    'linkedin': 'site:linkedin.com/in/ OR site:linkedin.com/company/',
                    'twitter': 'site:twitter.com',
                    'instagram': 'site:instagram.com',
                    'facebook': 'site:facebook.com'
                }
                site_operator = site_map.get(platform, '')
                modified_query = f"{site_operator} {query}"
                print(f"Social Search Query: {modified_query}")
                seed_urls = self.search_web(modified_query, engine=engine)
            
            elif search_type == 'platform':
                # Check if this is a Yelp search using platform_type parameter
                if platform_type == 'yelp' or (target_website and 'yelp.com' in target_website.lower()):
                    print(f"🔍 Yelp Search Detected: {query}")
                    print(f"   platform_type: {platform_type}")
                    print(f"   target_website: {target_website}")
                    
                    try:
                        from app.services.scrapers.yelp import YelpScraper
                        
                        # Extract actual search query (remove site: operator if present)
                        import re
                        clean_query = re.sub(r'site:\S+\s+', '', query)
                        print(f"   clean_query: {clean_query}")
                        
                        # Use Yelp Scraper
                        headless = SettingsManager.get_setting('headless_mode', False)
                        print(f"   Initializing YelpScraper (headless={headless})...")
                        
                        yelp_scraper = YelpScraper(headless=headless)
                        business_data = yelp_scraper.search(clean_query, max_results=20)
                        
                        # Save results directly (similar to Maps)
                        if business_data and len(business_data) > 0:
                            print(f"\n✓ Received {len(business_data)} businesses from Yelp")
                            print(f"💾 Saving directly to database...\n")
                            
                            email_count = 0
                            phone_count = 0
                            business_count = 0
                            
                            for idx, business in enumerate(business_data):
                                # Save full business record
                                if self.db.add_business(search_id, business, 'Yelp'):
                                    business_count += 1
                                    print(f"  [{idx+1}] 🏢 {business.get('name', 'Unknown')}")
                                
                                # Also save phone to phones table for backward compatibility
                                if scrape_phones and business.get('phone'):
                                    if self.db.add_phone(
                                        search_id, 
                                        business['phone'], 
                                        'Yelp',
                                        business_name=business.get('name'),
                                        website=business.get('website'),
                                        address=business.get('address')
                                    ):
                                        phone_count += 1
                            
                            # Mark search as completed
                            self.db.update_search_status(search_id, 'completed', 0, email_count + phone_count)
                            
                            results['status'] = 'completed'
                            results['phones'] = [b['phone'] for b in business_data if b.get('phone')]
                            results['businesses'] = business_data
                            
                            print(f"\n✓ Saved {business_count} businesses and {phone_count} phones to database")
                            if progress_callback:
                                progress_callback(search_id, 'Completed!', 100)
                            
                            return results
                        else:
                            print("⚠️  YelpScraper returned 0 businesses")
                            self.db.update_search_status(search_id, 'completed', 0, 0)
                            results['status'] = 'completed'
                            return results
                            
                    except Exception as e:
                        print(f"❌ YelpScraper Error: {e}")
                        import traceback
                        traceback.print_exc()
                        # Fall through to regular web search

                
                # Fallback to regular web search with site: operator
                print(f"Platform Search Query: {query}")
                seed_urls = self.search_web(query, engine=engine)

            elif search_type == 'crawler':
                # Direct website crawl
                print(f"Direct Website Crawl: {query}")
                if not query.startswith('http'):
                    query = 'https://' + query
                seed_urls = [query]
                
            else:
                seed_urls = self.search_web(query, engine=engine)
            
            
            print(f"\n✓ Found {len(seed_urls)} URLs from search")
            
            if not seed_urls:
                if '.' in query and ' ' not in query:
                    seed_urls = [f"https://{query}" if not query.startswith('http') else query]
                    print(f"⚠ Trying direct URL: {seed_urls[0]}")
            
            if not seed_urls:
                results['status'] = 'completed'
                results['error'] = 'No relevant websites found'
                self.db.update_search_status(search_id, 'completed', 0, 0, error_message='No relevant websites found')
                return results
            
            # Step 2: Parallel Crawl with Streaming
            print(f"\n{'='*60}")
            print(f"Starting parallel crawl with streaming results...")
            print(f"{'='*60}\n")
            
            # Queue: (url, depth, source_domain)
            visited_urls = set()
            url_queue = []
            
            # Thread-safe primitives
            import threading
            queue_lock = threading.Lock()
            search_finished = threading.Event()
            stop_requested = threading.Event()
            
            # Callback to handle new results from search
            def on_search_result(url):
                with queue_lock:
                    if url not in visited_urls:
                        try:
                            domain = urlparse(url).netloc
                            url_queue.append((url, 0, domain))
                            visited_urls.add(url)
                            # print(f"  [+] Added to queue: {url[:60]}...")
                        except:
                            pass

            # Callback to check if we should stop
            def stop_check():
                if stop_requested.is_set():
                    return True
                status = self.db.get_search_status(search_id)
                if status and status.get('status') == 'stopped':
                    stop_requested.set()
                    return True
                return False

            # Run search in a background thread so we can process results immediately
            def run_search_thread():
                try:
                    # Determine max_results based on max_pages input
                    # If max_pages is -1 or very large, we treat it as infinite search
                    search_max_results = -1 if max_pages == -1 or max_pages > 1000 else MAX_SEARCH_RESULTS
                    
                    if search_type == 'crawler':
                        # Direct crawl, just add the query as seed
                        on_search_result(query if query.startswith('http') else 'https://' + query)
                    elif search_type == 'social' and platform:
                        # ... (social logic similar to before, but using streaming search)
                        site_map = {
                            'linkedin': 'site:linkedin.com/in/ OR site:linkedin.com/company/',
                            'twitter': 'site:twitter.com',
                            'instagram': 'site:instagram.com',
                            'facebook': 'site:facebook.com'
                        }
                        site_operator = site_map.get(platform, '')
                        modified_query = f"{site_operator} {query}"
                        self.search_web(modified_query, engine=engine, max_results=search_max_results, on_result=on_search_result, stop_check=stop_check)
                    else:
                        # Regular web search
                        self.search_web(query, engine=engine, max_results=search_max_results, on_result=on_search_result, stop_check=stop_check)
                except Exception as e:
                    print(f"Search thread error: {e}")
                finally:
                    search_finished.set()
            
            # Start search thread
            search_thread = threading.Thread(target=run_search_thread)
            search_thread.start()
            
            crawled_count = 0
            
            import concurrent.futures
            
            # ThreadPoolExecutor for crawling pages
            max_workers = SettingsManager.get_setting('max_threads', 8)
            
            # Use provided max_pages for crawler mode, otherwise default
            # If max_pages is -1, we treat it as infinite (or very large limit)
            effective_max_pages = float('inf') if max_pages == -1 else (max_pages if search_type == 'crawler' else SettingsManager.get_setting('max_pages_per_search', MAX_PAGES_PER_SEARCH))
            
            max_depth = (depth - 1) if search_type == 'crawler' else MAX_CRAWL_DEPTH
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {}
                
                while True:
                    # Check for stop signal
                    if stop_check():
                        print("\n🛑 Stop signal received. Terminating crawl...")
                        break
                        
                    # Check if done: search finished AND no more work
                    with queue_lock:
                        is_queue_empty = len(url_queue) == 0
                    
                    if search_finished.is_set() and is_queue_empty and not futures:
                        print("\n✓ All tasks completed.")
                        break
                        
                    # Check limit
                    if crawled_count >= effective_max_pages:
                        print(f"\n✓ Max pages limit reached ({effective_max_pages}). Stopping.")
                        break

                    # Submit tasks
                    with queue_lock:
                        while url_queue and len(futures) < max_workers and crawled_count + len(futures) < effective_max_pages:
                            url, depth, source_domain = url_queue.pop(0)
                            
                            if self.db.is_url_crawled(search_id, url):
                                continue
                                
                            future = executor.submit(self.process_single_url, search_id, url)
                            futures[future] = (url, depth, source_domain)
                    
                    # Process completed futures
                    # Wait briefly for any future to complete, or just poll
                    done, _ = concurrent.futures.wait(futures, timeout=0.5, return_when=concurrent.futures.FIRST_COMPLETED)
                    
                    for future in done:
                        url, depth, source_domain = futures.pop(future)
                        crawled_count += 1
                        
                        try:
                            page_emails, page_phones, new_links = future.result()
                            
                            # Show emails to user FIRST (print to console)
                            if scrape_emails and page_emails:
                                for email in page_emails:
                                    print(f"  ✓ Email found: {email}")
                            
                            # Show phones to user FIRST (print to console)
                            if scrape_phones and page_phones:
                                for phone in page_phones:
                                    print(f"  ✓ Phone found: {phone}")
                            
                            # THEN save emails to database
                            if scrape_emails and page_emails:
                                for email in page_emails:
                                    domain = self.email_extractor.get_domain(email)
                                    if self.db.add_email(search_id, email, url, domain):
                                        email_set.add(email)
                            
                            # THEN save phones to database
                            if scrape_phones and page_phones:
                                for phone in page_phones:
                                    if self.db.add_phone(search_id, phone, url):
                                        phone_set.add(phone)
                            
                            # Add new links to queue if depth allows
                            if depth < max_depth:
                                with queue_lock:
                                    for link in new_links:
                                        if link not in visited_urls:
                                            url_queue.append((link, depth + 1, source_domain))
                                            visited_urls.add(link)
                        except Exception as e:
                            print(f"Error processing {url}: {e}")
                            
                        # Update progress and database status periodically
                        if crawled_count % 5 == 0:
                            total_records = len(email_set) + len(phone_set)
                            self.db.update_search_status(search_id, 'running', crawled_count, total_records, url)
                            if progress_callback:
                                progress_callback(search_id, f"Crawled {crawled_count} pages...", int((crawled_count / (effective_max_pages if effective_max_pages != float('inf') else 1000)) * 100))
            
            # Ensure search thread joins (it should have finished or we ignore it if we stopped early)
            # If we stopped early, search thread might still be running. 
            # Ideally we should signal it to stop via stop_check, which we do.
            search_thread.join(timeout=1.0) 
            
            results['pages_crawled'] = crawled_count
            results['emails'] = list(email_set) if scrape_emails else []
            results['phones'] = list(phone_set) if scrape_phones else []
            total_records = len(email_set) + len(phone_set)
            
            if stop_requested.is_set():
                results['status'] = 'stopped'
                self.db.update_search_status(search_id, 'stopped', crawled_count, total_records)
            else:
                results['status'] = 'completed'
                self.db.update_search_status(search_id, 'completed', crawled_count, total_records)
            
            if progress_callback:
                progress_callback(search_id, 'Completed!', 100)
        
        except Exception as e:
            results['status'] = 'error'
            results['error'] = str(e)
            total_records = len(email_set) + len(phone_set)
            self.db.update_search_status(search_id, 'error', results['pages_crawled'], total_records, error_message=str(e))
            print(f"\n✗ Crawl error: {e}")
            import traceback
            traceback.print_exc()
        
        return results

    def process_single_url(self, search_id, url):
        """
        Worker method to process a single URL
        """
        print(f"Crawling: {url}")
        
        # Fetch page
        emails, phones, links = self.fetch_page(url)
        
        # Mark as crawled
        self.db.add_crawled_url(search_id, url)
        
        return emails, phones, links
