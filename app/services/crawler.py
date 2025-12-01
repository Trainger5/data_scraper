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

    def search_web(self, query, engine='duckduckgo'):
        """
        Search the web using Selenium to bypass bot detection
        """
        from app.services.scrapers.web_search import WebSearchScraper
        headless = SettingsManager.get_setting('headless_mode', False)
        scraper = WebSearchScraper(headless=headless)
        return scraper.search(query, max_results=MAX_SEARCH_RESULTS, engine=engine)

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


    def crawl(self, search_id, query, progress_callback=None, use_google_maps=False, search_type='web', platform=None, engine=None, page_count=3, depth=2, max_pages=50, platform_type=None, target_website=None):
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
            'pages_crawled': 0,
            'status': 'running'
        }
        
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
                        if business.get('phone'):
                            if self.db.add_phone(
                                search_id, 
                                business['phone'], 
                                'Google Maps',
                                business_name=business.get('name'),
                                website=business.get('website'),
                                address=business.get('address')
                            ):
                                phone_count += 1
                        
                        if business.get('email'):
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
                    self.db.update_search_status(search_id, 'completed', 0, email_count + phone_count)
                    
                    results['status'] = 'completed'
                    results['emails'] = [b['email'] for b in business_data if b.get('email')]
                    results['phones'] = [b['phone'] for b in business_data if b.get('phone')]
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
                                if business.get('phone'):
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
                self.db.update_search_status(search_id, 'completed', 0, 0)
                return results
            
            # Step 2: Parallel Crawl
            print(f"\n{'='*60}")
            print(f"Starting parallel crawl...")
            print(f"{'='*60}\n")
            
            # Queue: (url, depth, source_domain)
            # We use a set for visited URLs to avoid duplicates
            visited_urls = set()
            url_queue = []
            
            # Initialize queue with seeds
            for url in seed_urls:
                if url not in visited_urls:
                    # Depth 0 for seeds
                    try:
                        domain = urlparse(url).netloc
                        url_queue.append((url, 0, domain))
                        visited_urls.add(url)
                    except:
                        pass

            crawled_count = 0
            email_set = set()
            
            import concurrent.futures
            
            # We'll use a ThreadPoolExecutor
            # We'll use a ThreadPoolExecutor
            max_workers = SettingsManager.get_setting('max_threads', 8)
            # Use provided max_pages for crawler mode, otherwise default
            if search_type != 'crawler':
                max_pages = SettingsManager.get_setting('max_pages_per_search', MAX_PAGES_PER_SEARCH)
            
            # Use provided depth for crawler mode, otherwise default
            # Subtract 1 because UI labels (1, 2, 3) correspond to depths (0, 1, 2)
            max_depth = (depth - 1) if search_type == 'crawler' else MAX_CRAWL_DEPTH
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Keep track of futures: {future: url}
                futures = {}
                
                while (url_queue or futures) and crawled_count < max_pages:
                    # Submit tasks up to max_workers
                    while url_queue and len(futures) < max_workers and crawled_count + len(futures) < max_pages:
                        url, depth, source_domain = url_queue.pop(0)
                        
                        # Check if already crawled in DB (global check)
                        if self.db.is_url_crawled(search_id, url):
                            continue
                            
                        future = executor.submit(self.process_single_url, search_id, url)
                        futures[future] = (url, depth, source_domain)
                    
                    if not futures:
                        break
                    
                    # Wait for at least one future to complete
                    done, _ = concurrent.futures.wait(
                        futures.keys(), 
                        return_when=concurrent.futures.FIRST_COMPLETED
                    )
                    
                    for future in done:
                        url, depth, source_domain = futures.pop(future)
                        crawled_count += 1
                        
                        try:
                            emails, phones, links = future.result()
                            
                            # Update progress
                            if emails:
                                for email in emails:
                                    domain = self.email_extractor.get_domain(email)
                                    if self.db.add_email(search_id, email, url, domain):
                                        email_set.add(email)
                                        print(f"  ✓ Email: {email}")
                            
                            if phones:
                                for phone in phones:
                                    if self.db.add_phone(search_id, phone, url):
                                        print(f"  ✓ Phone: {phone}")
                            
                            # Process new links
                            if depth < max_depth:
                                internal_links = []
                                external_links = []
                                
                                for link in links:
                                    if link in visited_urls:
                                        continue
                                        
                                    try:
                                        link_domain = urlparse(link).netloc
                                        
                                        if link_domain == source_domain:
                                            internal_links.append(link)
                                        else:
                                            external_links.append(link)
                                    except:
                                        pass
                                
                                # Add internal links (prioritize)
                                for link in internal_links:
                                    if link not in visited_urls:
                                        visited_urls.add(link)
                                        url_queue.append((link, depth + 1, source_domain))
                                
                                # Add external links (limit per page)
                                for i, link in enumerate(external_links):
                                    if i >= MAX_EXTERNAL_LINKS: break
                                    if link not in visited_urls:
                                        visited_urls.add(link)
                                        # External links start fresh depth? Or continue?
                                        # Let's treat them as depth+1 but update source_domain
                                        new_domain = urlparse(link).netloc
                                        url_queue.append((link, depth + 1, new_domain))
                                        
                        except Exception as e:
                            print(f"Error processing {url}: {e}")
                        
                        # Update DB status periodically
                        if crawled_count % 5 == 0:
                            self.db.update_search_status(
                                search_id, 'running', crawled_count, len(email_set), url
                            )
                            if progress_callback:
                                progress = min(int((crawled_count / MAX_PAGES_PER_SEARCH) * 100), 95)
                                progress_callback(search_id, f"Crawled {crawled_count} pages...", progress)

            # Step 3: Complete
            print(f"\n{'='*60}")
            print(f"Crawl completed! Pages: {crawled_count}, Emails: {len(email_set)}")
            print(f"{'='*60}\n")
            
            results['emails'] = list(email_set)
            results['pages_crawled'] = crawled_count
            results['status'] = 'completed'
            
            self.db.update_search_status(search_id, 'completed', crawled_count, len(email_set))
            
            if progress_callback:
                progress_callback(search_id, 'Completed!', 100)
        
        except Exception as e:
            results['status'] = 'error'
            results['error'] = str(e)
            self.db.update_search_status(search_id, 'error', results['pages_crawled'], len(results['emails']))
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
