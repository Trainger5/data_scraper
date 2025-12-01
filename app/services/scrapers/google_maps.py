"""
Maps Scraper (Multi-Engine Support)
Extracts company website URLs from various search engines
Uses Selenium browser automation - NO API KEY REQUIRED
Supports: Google Maps, Bing Maps, and fallback web search for other engines
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import validators
from config import USE_PROXIES, PROXY_LIST_FILE, PROXY_ROTATION_STRATEGY, HEADLESS_MODE
from app.services.proxy_manager import ProxyManager

class MapsScraper:
    def __init__(self, headless=None, use_proxy=None):
        """Initialize Chrome browser with Selenium"""
        self.headless = headless if headless is not None else HEADLESS_MODE
        self.use_proxy = use_proxy if use_proxy is not None else USE_PROXIES
        self.driver = None
        self.proxy_manager = None
        self.current_proxy = None
        
        # Initialize proxy manager if enabled
        if self.use_proxy:
            self.proxy_manager = ProxyManager(proxy_file=PROXY_LIST_FILE)
            if self.proxy_manager.get_stats()['available'] == 0:
                print("⚠ No proxies available, disabling proxy support")
                self.use_proxy = False
    
    def setup_driver(self):
        """Setup Chrome driver with incognito mode"""
        chrome_options = Options()
        
        # INCOGNITO MODE (Private browsing)
        chrome_options.add_argument('--incognito')
        
        if self.headless:
            chrome_options.add_argument('--headless')
        
        # Additional options for stability
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        # Configure proxy if enabled
        if self.use_proxy and self.proxy_manager:
            self.current_proxy = self.proxy_manager.get_proxy(strategy=PROXY_ROTATION_STRATEGY)
            if self.current_proxy:
                proxy_string = self.proxy_manager.get_selenium_proxy_config(self.current_proxy)
                chrome_options.add_argument(f'--proxy-server={proxy_string}')
                print(f"🔒 Using proxy: {proxy_string}")
        
        # Use Selenium's built-in manager (Selenium 4.6+)
        self.driver = webdriver.Chrome(options=chrome_options)
        
        print("✓ Chrome browser initialized (incognito)")
    
    def search_maps(self, query, page_count=3, engine='google'):
        """Search maps using the specified engine and extract contact data from business cards"""
        print(f"\n🗺️  Maps Search Engine: {engine.upper()}")
        
        # Route to appropriate search method based on engine
        if engine.lower() == 'google':
            return self._search_google_maps(query, page_count)
        elif engine.lower() == 'bing':
            return self._search_bing_maps(query, page_count)
        else:
            # For other engines (DuckDuckGo, Yahoo, etc.), use web search with location
            return self._search_web_fallback(query, page_count * 20, engine)  # Convert pages to approximate results
    
    def _search_google_maps(self, query, page_count=3):
        """Extract contact info directly from Google Maps business cards"""
        if not self.driver:
            self.setup_driver()
        
        results = []  # List of {name, phone, email, source}
        
        try:
            print(f"\n{'='*60}")
            print(f"🗺️  Scraping Google Maps business cards: '{query}'")
            print(f"📄 Pages to load: {page_count} (~{page_count * 20} businesses)")
            print(f"{'='*60}\n")
            
            # Navigate to Google Maps search (with proper URL encoding)
            from urllib.parse import quote_plus
            encoded_query = quote_plus(query)
            maps_url = f"https://www.google.com/maps/search/{encoded_query}"
            print(f"🔗 URL: {maps_url}\n")
            self.driver.get(maps_url)
            
            # Wait for results to load
            print("⏳ Waiting for results to load...")
            time.sleep(5)
            
            # Find the scrollable results panel
            try:
                scrollable_div = self.driver.find_element(By.CSS_SELECTOR, "div[role='feed']")
            except:
                print("✗ Could not find results panel")
                return results
            
            # Scroll to load more businesses based on page_count
            print(f"\n📜 Scrolling to load {page_count} pages of results...")
            scrolls_per_page = 3
            total_scrolls = page_count * scrolls_per_page
            
            for i in range(total_scrolls):
                self.driver.execute_script(
                    'arguments[0].scrollTop = arguments[0].scrollHeight', 
                    scrollable_div
                )
                time.sleep(2)  # Wait for new results to load
                if (i + 1) % scrolls_per_page == 0:
                    print(f"  ✓ Loaded page {(i + 1) // scrolls_per_page}/{page_count}")
            
            # Find all business cards
            print(f"\n🔍 Finding business cards...")
            business_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/maps/place/']")
            print(f"✓ Found {len(business_links)} business cards\n")
            
            # Extract contact info from each business card
            processed = 0
            for idx, link in enumerate(business_links):
                try:
                    # Extract business name from the link first (more reliable)
                    business_name = None
                    try:
                        # Try to get name from aria-label or nearby text
                        business_name = link.get_attribute('aria-label')
                        if not business_name:
                            # Try parent div with class containing 'fontBodyMedium'
                            parent = link.find_element(By.XPATH, './ancestor::div[@class and contains(@class, "Nv2PK")]')
                            name_div = parent.find_element(By.CSS_SELECTOR, 'div.fontBodyMedium')
                            business_name = name_div.text.strip()
                    except:
                        pass
                    
                    # Click the business card to open details panel
                    self.driver.execute_script("arguments[0].click();", link)
                    time.sleep(2)  # Wait for details to load
                    
                    # If we didn't get name from card, try the details panel
                    if not business_name:
                        try:
                            name_element = self.driver.find_element(By.CSS_SELECTOR, "h1.fontHeadlineLarge, h1.DUwDvf")
                            business_name = name_element.text.strip()
                        except:
                            pass
                    
                    # Fallback
                    if not business_name or len(business_name) < 2:
                        business_name = f"Business {idx + 1}"
                    
                    # Extract ADDRESS
                    address = None
                    try:
                        address_selectors = [
                            "button[data-item-id*='address']",
                            "button[aria-label*='Address']",
                            "[data-tooltip*='address']",
                            "div[class*='address']"
                        ]
                        for selector in address_selectors:
                            try:
                                address_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                                address = address_element.get_attribute('aria-label') or address_element.text
                                if address and len(address) > 10:
                                    break
                            except:
                                continue
                    except:
                        pass
                    
                    # Extract phone number
                    phone = None
                    try:
                        # Try multiple selectors for phone
                        phone_selectors = [
                            "button[data-item-id*='phone']",
                            "button[aria-label*='Phone']",
                            "a[href^='tel:']",
                            "[data-tooltip*='phone']"
                        ]
                        
                        for selector in phone_selectors:
                            try:
                                phone_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                                phone_text = phone_element.get_attribute('aria-label') or phone_element.text
                                
                                # Extract phone using EmailExtractor
                                from app.services.email_extractor import EmailExtractor
                                extractor = EmailExtractor()
                                phones = extractor.extract_phones(phone_text)
                                if phones:
                                    phone = phones[0]
                                    break
                            except:
                                continue
                    except:
                        pass
                    
                    # Extract WEBSITE
                    website = None
                    try:
                        website_selectors = [
                            "a[data-item-id*='authority']",
                            "a[aria-label*='Website']",
                            "button[data-item-id*='authority']",
                            "a[href*='http']:not([href*='google.com']):not([href*='maps'])"
                        ]
                        for selector in website_selectors:
                            try:
                                website_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                                website = website_element.get_attribute('href')
                                if website and 'http' in website and 'google.com' not in website:
                                    break
                            except:
                                continue
                    except:
                        pass
                    
                    # Extract email if visible
                    email = None
                    try:
                        # Check website/description for email
                        description_element = self.driver.find_element(By.CSS_SELECTOR, "[class*='description']")
                        desc_text = description_element.text
                        
                        from app.services.email_extractor import EmailExtractor
                        extractor = EmailExtractor()
                        emails = extractor.extract_from_text(desc_text)
                        if emails:
                            email = emails[0]
                    except:
                        pass
                    
                    # Add business data (even if no contact info - we have name/address/website)
                    if business_name != f"Business {idx + 1}":  # Only if we got a real name
                        results.append({
                            'name': business_name,
                            'phone': phone,
                            'email': email,
                            'address': address,
                            'website': website,
                            'source': 'Google Maps'
                        })
                        processed += 1
                        
                        status = []
                        if phone:
                            status.append(f"📞 {phone}")
                        if email:
                            status.append(f"📧 {email}")
                        if website:
                            status.append(f"🌐 Website")
                        if address:
                            status.append(f"📍 Address")
                        
                        print(f"  [{processed}] ✓ {business_name[:40]}")
                        if status:
                            print(f"      {' | '.join(status)}")
                    else:
                        print(f"  [{idx+1}] ⚠ Skipped - couldn't identify business")

                
                except Exception as e:
                    print(f"  [{idx+1}] ✗ Error: {str(e)[:50]}")
                    continue
            
            print(f"\n{'='*60}")
            print(f"✓ Extracted {len(results)} businesses with contact info")
            print(f"📞 Phones: {sum(1 for r in results if r['phone'])}")
            print(f"📧 Emails: {sum(1 for r in results if r['email'])}")
            print(f"{'='*60}\n")
        
        except Exception as e:
            print(f"\n✗ Google Maps scraping error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            from app.services.settings import SettingsManager
            debug_mode = SettingsManager.get_setting('debug_mode', False)
            
            if self.driver and not debug_mode:
                self.driver.quit()
                self.driver = None
                print("✓ Browser closed\n")
        
        return results
    
    
    def _search_bing_maps(self, query, page_count=3):
        """Search Bing Maps and extract company website URLs"""
        if not self.driver:
            self.setup_driver()
        
        websites = []
        
        try:
            print(f"\n{'='*60}")
            print(f"🗺️  Searching Bing Maps for: '{query}'")
            print(f"{'='*60}\n")
            
            # Navigate to Bing Maps search
            bing_url = f"https://www.bing.com/maps?q={query.replace(' ', '+')}"
            self.driver.get(bing_url)
            
            print("⏳ Waiting for results to load...")
            time.sleep(5)
            
            # Find business listings
            print("\n🔍 Looking for businesses...")
            
            # Bing Maps uses different selectors
            business_cards = self.driver.find_elements(By.CSS_SELECTOR, ".taskCard, .businessCard")
            print(f"✓ Found {len(business_cards)} businesses\n")
            
            processed = 0
            for idx, card in enumerate(business_cards[:max_results]):
                if processed >= max_results:
                    break
                
                try:
                    # Click business card
                    self.driver.execute_script("arguments[0].click();", card)
                    time.sleep(2)
                    
                    # Look for website link
                    try:
                        website_link = self.driver.find_element(By.CSS_SELECTOR, "a[href^='http']:not([href*='bing.com'])")
                        website_url = website_link.get_attribute('href')
                        
                        if website_url and validators.url(website_url):
                            if website_url not in websites:
                                websites.append(website_url)
                                processed += 1
                                
                                from urllib.parse import urlparse
                                domain = urlparse(website_url).netloc.replace('www.', '')
                                print(f"  [{processed}/{max_results}] ✓ {domain}")
                    except:
                        print(f"  [{idx+1}] ✗ No website found")
                    
                except Exception as e:
                    print(f"  [{idx+1}] ✗ Error: {str(e)[:50]}")
                    continue
            
            print(f"\n{'='*60}")
            print(f"✓ Extracted {len(websites)} websites from Bing Maps")
            print(f"{'='*60}\n")
            
        except Exception as e:
            print(f"\n✗ Bing Maps scraping error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            from app.services.settings import SettingsManager
            debug_mode = SettingsManager.get_setting('debug_mode', False)
            
            if self.driver and not debug_mode:
                self.driver.quit()
                self.driver = None
                print("✓ Browser closed\n")
        
        return websites
    
    def _search_web_fallback(self, query, max_results=15, engine='duckduckgo'):
        """Fallback to web search for engines without dedicated maps interface"""
        print(f"\n{'='*60}")
        print(f"ℹ️  {engine.upper()} doesn't have dedicated maps scraping")
        print(f"Using web search with location-based query instead")
        print(f"{'='*60}\n")
        
        # Use the existing WebSearchScraper
        try:
            from app.services.scrapers.web_search import WebSearchScraper
            web_scraper = WebSearchScraper(headless=self.headless, use_proxy=self.use_proxy)
            
            # Perform web search with the query (already contains location)
            urls = web_scraper.search(query, max_results, engine)
            
            print(f"\n✓ Found {len(urls)} URLs from {engine.upper()} web search\n")
            return urls
            
        except Exception as e:
            print(f"✗ Web fallback error: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def __del__(self):
        """Cleanup driver on deletion"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
