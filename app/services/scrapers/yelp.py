"""
Yelp Scraper for Email Extractor Pro
Extracts structured business data from Yelp search results
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import re
import os
from urllib.parse import quote_plus


class YelpScraper:
    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None
        
    def _init_driver(self):
        """Initialize Chrome with incognito mode"""
        options = Options()
        
        # INCOGNITO MODE (Private browsing)
        options.add_argument('--incognito')
        
        # Anti-detection settings
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Privacy & stealth
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-notifications')
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--start-maximized')
        options.add_argument('--lang=en-US')
        
        # User agent
        from config import USER_AGENT
        options.add_argument(f'user-agent={USER_AGENT}')
        
        if self.headless:
            options.add_argument('--headless=new')
        
        print("🔓 Initializing Chrome in INCOGNITO mode...")
        
        # Use Selenium's built-in driver manager (Selenium 4.6+)
        try:
            self.driver = webdriver.Chrome(options=options)
            print("✅ Chrome initialized successfully (incognito)")
        except Exception as e:
            print(f"❌ Error: {e}")
            raise

        
    def search(self, query, max_results=20):
        """
        Search Yelp for businesses and extract structured data
        
        Args:
            query: Search query (e.g., "Plumbers in New York")
            max_results: Maximum number of results to extract
            
        Returns:
            List of dictionaries with business data
        """
        try:
            if not self.driver:
                self._init_driver()
            
            # Parse query to extract location if possible
            parts = query.split(' in ')
            if len(parts) == 2:
                business_type = parts[0].strip()
                location = parts[1].strip()
            else:
                business_type = query
                location = "United States"
            
            # Construct Yelp search URL
            encoded_query = quote_plus(business_type)
            encoded_location = quote_plus(location)
            url = f"https://www.yelp.com/search?find_desc={encoded_query}&find_loc={encoded_location}"
            
            print(f"🔍 Yelp URL: {url}")
            self.driver.get(url)
            
            # Random delay to appear human
            import random
            time.sleep(random.uniform(3, 6))
            
            # Scroll to load more results (with human-like pauses)
            for i in range(3):
                # Random scroll amount (not always to bottom)
                scroll_amount = random.randint(800, 1200)
                self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
                time.sleep(random.uniform(1.5, 3.5))
                print(f"   Scrolled {i+1}/3 times...")

            
            # Find all business links
            business_links = []
            try:
                # Find all business card links
                link_elements = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/biz/"]')
                seen_urls = set()
                
                for link in link_elements:
                    href = link.get_attribute('href')
                    if href and '/biz/' in href and '?' not in href:
                        # Clean URL - remove tracking parameters
                        clean_url = href.split('?')[0]
                        if clean_url not in seen_urls:
                            business_links.append(clean_url)
                            seen_urls.add(clean_url)
                            if len(business_links) >= max_results:
                                break
                
                print(f"✓ Found {len(business_links)} unique business links")
            except Exception as e:
                print(f"Error finding business links: {e}")
            
            # Visit each business page and extract data
            results = []
            for idx, business_url in enumerate(business_links[:max_results]):
                try:
                    print(f"\n[{idx+1}/{len(business_links)}] Visiting: {business_url}")
                    self.driver.get(business_url)
                    
                    # Human-like delay
                    time.sleep(random.uniform(2, 4))
                    
                    business_data = {
                        'name': None,
                        'phone': None,
                        'address': None,
                        'website': None
                    }
                    
                    # Extract Business Name
                    try:
                        name_elem = self.driver.find_element(By.CSS_SELECTOR, 'h1')
                        business_data['name'] = name_elem.text.strip()
                    except:
                        pass
                    
                    # Extract Phone
                    try:
                        phone_elem = self.driver.find_element(By.CSS_SELECTOR, '[href^="tel:"]')
                        phone_text = phone_elem.text or phone_elem.get_attribute('href').replace('tel:', '')
                        phone_match = re.search(r'\(?\d{3}\)?\s*-?\s*\d{3}\s*-?\s*\d{4}', phone_text)
                        if phone_match:
                            business_data['phone'] = phone_match.group()
                    except:
                        pass
                    
                    # Extract Address
                    try:
                        address_elem = self.driver.find_element(By.CSS_SELECTOR, '[itemprop="streetAddress"]')
                        business_data['address'] = address_elem.text.strip()
                    except:
                        try:
                            # Alternative selector
                            address_elems = self.driver.find_elements(By.XPATH, "//p[contains(text(), ',')]")
                            for elem in address_elems:
                                text = elem.text
                                if any(state in text for state in ['NY', 'CA', 'TX', 'FL']):
                                    business_data['address'] = text.strip()
                                    break
                        except:
                            pass
                    
                    # Extract Website
                    try:
                        website_elem = self.driver.find_element(By.CSS_SELECTOR, 'a[href*="biz_redir"]')
                        # Get the actual website from Yelp's redirect link
                        redirect_url = website_elem.get_attribute('href')
                        # Click to get real URL (or parse from redirect)
                        if 'url=' in redirect_url:
                            import urllib.parse
                            parsed = urllib.parse.parse_qs(urllib.parse.urlparse(redirect_url).query)
                            if 'url' in parsed:
                                business_data['website'] = parsed['url'][0]
                        else:
                            business_data['website'] = redirect_url
                    except:
                        pass
                    
                    results.append(business_data)
                    print(f"   ✓ {business_data['name']}")
                    print(f"     📞 {business_data['phone']}")
                    print(f"     📍 {business_data['address']}")
                    print(f"     🌐 {business_data['website']}")
                    
                except Exception as e:
                    print(f"   ✗ Error extracting business #{idx+1}: {e}")
                    continue
            
            return results
            
        except Exception as e:
            print(f"Yelp scraper error: {e}")
            import traceback
            traceback.print_exc()
            return []
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None

