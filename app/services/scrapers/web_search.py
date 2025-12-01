"""
Web Search Scraper
Extracts organic search results using Selenium to bypass bot detection
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import validators
import random
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config import PROXY_LIST_FILE
from app.services.settings import SettingsManager
from app.services.proxy_manager import ProxyManager

class WebSearchScraper:
    def __init__(self, headless=None, use_proxy=None):
        """Initialize Chrome browser with Selenium"""
        settings = SettingsManager.get_all()
        
        self.headless = headless if headless is not None else settings.get('headless_mode', True)
        self.use_proxy = use_proxy if use_proxy is not None else settings.get('use_proxies', True)
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
        
        # Anti-detection options
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # Randomize User-Agent to mimic different devices/browsers
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15'
        ]
        user_agent = random.choice(user_agents)
        chrome_options.add_argument(f'--user-agent={user_agent}')
        
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        
        # Configure proxy if enabled
        if self.use_proxy and self.proxy_manager:
            strategy = SettingsManager.get_setting('proxy_rotation_strategy', 'random')
            self.current_proxy = self.proxy_manager.get_proxy(strategy=strategy)
            if self.current_proxy:
                proxy_string = self.proxy_manager.get_selenium_proxy_config(self.current_proxy)
                chrome_options.add_argument(f'--proxy-server={proxy_string}')
                print(f"🔒 Using proxy: {proxy_string}")
        
        # Use Selenium's built-in manager (Selenium 4.6+)
        self.driver = webdriver.Chrome(options=chrome_options)
        
        print("✓ Chrome browser initialized for Web Search (incognito)")
    
    def search(self, query, max_results=20, engine='duckduckgo'):
        """Main search method - dispatches to specific engine"""
        engine = engine.lower()
        if engine == 'google':
            return self.search_google(query, max_results)
        elif engine == 'bing':
            return self.search_bing(query, max_results)
        elif engine == 'yahoo':
            return self.search_yahoo(query, max_results)
        elif engine == 'yandex':
            return self.search_yandex(query, max_results)
        elif engine == 'brave':
            return self.search_brave(query, max_results)
        elif engine == 'ecosia':
            return self.search_ecosia(query, max_results)
        else:
            return self.search_duckduckgo(query, max_results)

    def search_duckduckgo(self, query, max_results=20):
        """Search DuckDuckGo using Selenium (More reliable/lenient than Google)"""
        if not self.driver:
            self.setup_driver()
        
        links = []
        
        try:
            print(f"\n{'='*60}")
            print(f"🦆 Searching DuckDuckGo for: '{query}'")
            print(f"{'='*60}\n")
            
            # Navigate to DuckDuckGo
            self.driver.get(f"https://duckduckgo.com/?q={query.replace(' ', '+')}&t=h_&ia=web")
            
            # Wait for results to load (up to 15 seconds)
            print("⏳ Waiting for results to load...")
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.react-results--main, div#links, div.results"))
                )
                print("✓ Results container loaded")
            except Exception as e:
                print(f"⚠ Timeout waiting for results: {e}")
            
            # Scroll to load more results
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            for i in range(3):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2) # Allow time for dynamic content to load
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
            
            # Find results - Updated DuckDuckGo selectors (2024)
            selectors = [
                "a[data-testid='result-title-a']",   # Modern DDG
                "article h2 a",                       # Newer layout
                "div.result__body h2 a",              # Classic DDG
                "div.react-results--main li a[data-testid='result-title-a']", # Specific container
                "h2 a.result__a"                      # Older Classic
            ]
            
            results = []
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        print(f"Found {len(elements)} elements with selector: {selector}")
                        results.extend(elements)
                except Exception as e:
                    print(f"Selector {selector} failed: {e}")
            
            # Deduplicate elements based on href
            unique_results = []
            seen_hrefs = set()
            for el in results:
                try:
                    href = el.get_attribute('href')
                    if href and href not in seen_hrefs:
                        seen_hrefs.add(href)
                        unique_results.append(el)
                except:
                    pass
            
            print(f"Found {len(unique_results)} unique potential results...")
            
            for a in unique_results:
                try:
                    href = a.get_attribute('href')
                    
                    if not href:
                        continue
                        
                    # Filter out ads, internal links, and common aggregators
                    skip_domains = ['duckduckgo.com', 'yandex', 'facebook.com/l.php', 
                                   'google.com/url', 'bing.com/ck', 't.co', 'bit.ly', 'microsoft.com']
                    if any(domain in href for domain in skip_domains):
                        continue
                        
                    # Basic validation
                    if validators.url(href) and href.startswith('http'):
                        if href not in links:
                            links.append(href)
                            print(f"  [OK] Found: {href[:80]}")
                            
                    if len(links) >= max_results:
                        break
                        
                except Exception as e:
                    continue
            
            print(f"\n[OK] Extracted {len(links)} organic results from DuckDuckGo")
            
        except Exception as e:
            print(f"DuckDuckGo search error: {e}")
        
        finally:
            if self.driver:
                debug_mode = SettingsManager.get_setting('debug_mode', False)
                if not debug_mode:
                    self.driver.quit()
                    self.driver = None
                else:
                    print("Debug Mode: Browser left open. Close manually.")
                
        return links

    def search_google(self, query, max_results=20):
        """Search Google using Selenium"""
        if not self.driver:
            self.setup_driver()
        
        links = []
        
        try:
            print(f"\n{'='*60}")
            print(f"🔍 Searching Google for: '{query}'")
            print(f"{'='*60}\n")
            
            # Navigate to Google
            self.driver.get(f"https://www.google.com/search?q={query.replace(' ', '+')}&num={max_results+10}")
            
            # Wait for results
            print("⏳ Waiting for results to load...")
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div#search, div#rso"))
                )
                print("✓ Results container loaded")
            except Exception as e:
                print(f"⚠ Timeout waiting for results: {e}")
            
            # Handle cookie consent if present (basic attempt)
            try:
                consent_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Accept all') or contains(text(), 'I agree')]")
                if consent_buttons:
                    consent_buttons[0].click()
                    time.sleep(2)
            except:
                pass
            
            # Scroll a bit
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(1)
            
            # Find results - Google selectors
            # Google changes selectors often, so we try multiple common ones
            selectors = [
                "div.g div.yuRUbf a",  # Common desktop
                "div.g h3 a",          # Older desktop
                "div#search div.g a",  # Generic
                "a[jsname='UWckNb']",  # Mobile/Modern
                "div.g a[href^='http']" # Fallback
            ]
            
            results = []
            for selector in selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"Found {len(elements)} elements with selector: {selector}")
                    # Filter elements that have h3 child (usually the title) to avoid random links
                    valid_elements = []
                    for el in elements:
                        try:
                            if el.find_elements(By.TAG_NAME, 'h3') or el.find_elements(By.TAG_NAME, 'span'):
                                valid_elements.append(el)
                        except:
                            valid_elements.append(el)
                    
                    results.extend(valid_elements)
            
            print(f"Found {len(results)} potential results...")
            
            for a in results:
                try:
                    href = a.get_attribute('href')
                    
                    if not href:
                        continue
                        
                    # Filter out ads and internal links
                    if 'google.com' in href or 'googleadservices' in href:
                        continue
                        
                    # Basic validation
                    if validators.url(href) and href.startswith('http'):
                        if href not in links:
                            links.append(href)
                            print(f"  ✓ Found: {href}")
                            
                    if len(links) >= max_results:
                        break
                        
                except Exception as e:
                    continue
            
            print(f"\n✓ Extracted {len(links)} organic results from Google")
            
        except Exception as e:
            print(f"Google search error: {e}")
        
        finally:
            if self.driver:
                debug_mode = SettingsManager.get_setting('debug_mode', False)
                if not debug_mode:
                    self.driver.quit()
                    self.driver = None
                else:
                    print("Debug Mode: Browser left open. Close manually.")
                
        return links

    def search_bing(self, query, max_results=20):
        """Search Bing using Selenium"""
        if not self.driver:
            self.setup_driver()
        
        links = []
        
        try:
            print(f"\n{'='*60}")
            print(f"🅱️ Searching Bing for: '{query}'")
            print(f"{'='*60}\n")
            
            # Navigate to Bing
            self.driver.get(f"https://www.bing.com/search?q={query.replace(' ', '+')}")
            
            # Wait for results
            time.sleep(random.uniform(3, 5))
            
            # Scroll
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Find results - Bing selectors
            selectors = [
                "li.b_algo h2 a",
                "li.b_algo div.b_title a"
            ]
            
            results = []
            for selector in selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"Found {len(elements)} elements with selector: {selector}")
                    results.extend(elements)
                    if len(results) >= max_results:
                        break
            
            print(f"Found {len(results)} potential results...")
            
            for a in results:
                try:
                    href = a.get_attribute('href')
                    
                    if not href:
                        continue
                        
                    # Filter out ads and internal links
                    if 'bing.com' in href or 'microsoft.com' in href:
                        continue
                        
                    # Basic validation
                    if validators.url(href) and href.startswith('http'):
                        if href not in links:
                            links.append(href)
                            print(f"  ✓ Found: {href}")
                            
                    if len(links) >= max_results:
                        break
                        
                except Exception as e:
                    continue
            
            print(f"\n✓ Extracted {len(links)} organic results from Bing")
            
        except Exception as e:
            print(f"Bing search error: {e}")
        
        finally:
            if self.driver:
                debug_mode = SettingsManager.get_setting('debug_mode', False)
                if not debug_mode:
                    self.driver.quit()
                    self.driver = None
                else:
                    print("Debug Mode: Browser left open. Close manually.")
                
        return links

    def search_yahoo(self, query, max_results=20):
        """Search Yahoo using Selenium"""
        if not self.driver:
            self.setup_driver()
        
        links = []
        
        try:
            print(f"\n{'='*60}")
            print(f"🟣 Searching Yahoo for: '{query}'")
            print(f"{'='*60}\n")
            
            self.driver.get(f"https://search.yahoo.com/search?p={query.replace(' ', '+')}")
            time.sleep(random.uniform(3, 5))
            
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Yahoo uses different selectors
            results = self.driver.find_elements(By.CSS_SELECTOR, "div.dd.algo a")
            
            for result in results:
                try:
                    url = result.get_attribute('href')
                    if url and validators.url(url) and 'yahoo.com' not in url:
                        links.append(url)
                    if len(links) >= max_results:
                        break
                except:
                    continue
            
            print(f"\n✓ Extracted {len(links)} organic results from Yahoo")
            
        except Exception as e:
            print(f"Yahoo search error: {e}")
        
        finally:
            if self.driver:
                debug_mode = SettingsManager.get_setting('debug_mode', False)
                if not debug_mode:
                    self.driver.quit()
                    self.driver = None
                else:
                    print("🐞 Debug Mode: Browser left open for inspection")
                
        return links

    def search_yandex(self, query, max_results=20):
        """Search Yandex using Selenium"""
        if not self.driver:
            self.setup_driver()
        
        links = []
        
        try:
            print(f"\n{'='*60}")
            print(f"🟥 Searching Yandex for: '{query}'")
            print(f"{'='*60}\n")
            
            self.driver.get(f"https://yandex.com/search/?text={query.replace(' ', '+')}")
            time.sleep(random.uniform(3, 5))
            
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            results = self.driver.find_elements(By.CSS_SELECTOR, "li.serp-item a.OrganicTitle-Link")
            
            for result in results:
                try:
                    url = result.get_attribute('href')
                    if url and validators.url(url) and 'yandex' not in url:
                        links.append(url)
                    if len(links) >= max_results:
                        break
                except:
                    continue
            
            print(f"\n✓ Extracted {len(links)} organic results from Yandex")
            
        except Exception as e:
            print(f"Yandex search error: {e}")
        
        finally:
            if self.driver:
                debug_mode = SettingsManager.get_setting('debug_mode', False)
                if not debug_mode:
                    self.driver.quit()
                    self.driver = None
                else:
                    print("🐞 Debug Mode: Browser left open for inspection")
                
        return links

    def search_brave(self, query, max_results=20):
        """Search Brave Search using Selenium"""
        if not self.driver:
            self.setup_driver()
        
        links = []
        
        try:
            print(f"\n{'='*60}")
            print(f"🦁 Searching Brave for: '{query}'")
            print(f"{'='*60}\n")
            
            self.driver.get(f"https://search.brave.com/search?q={query.replace(' ', '+')}")
            time.sleep(random.uniform(3, 5))
            
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            results = self.driver.find_elements(By.CSS_SELECTOR, "div.snippet a")
            
            for result in results:
                try:
                    url = result.get_attribute('href')
                    if url and validators.url(url) and 'brave.com' not in url:
                        links.append(url)
                    if len(links) >= max_results:
                        break
                except:
                    continue
            
            print(f"\n✓ Extracted {len(links)} organic results from Brave")
            
        except Exception as e:
            print(f"Brave search error: {e}")
        
        finally:
            if self.driver:
                debug_mode = SettingsManager.get_setting('debug_mode', False)
                if not debug_mode:
                    self.driver.quit()
                    self.driver = None
                else:
                    print("🐞 Debug Mode: Browser left open for inspection")
                
        return links

    def search_ecosia(self, query, max_results=20):
        """Search Ecosia using Selenium"""
        if not self.driver:
            self.setup_driver()
        
        links = []
        
        try:
            print(f"\n{'='*60}")
            print(f"🌱 Searching Ecosia for: '{query}'")
            print(f"{'='*60}\n")
            
            self.driver.get(f"https://www.ecosia.org/search?q={query.replace(' ', '+')}")
            time.sleep(random.uniform(3, 5))
            
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            results = self.driver.find_elements(By.CSS_SELECTOR, "a.result__link")
            
            for result in results:
                try:
                    url = result.get_attribute('href')
                    if url and validators.url(url) and 'ecosia.org' not in url:
                        links.append(url)
                    if len(links) >= max_results:
                        break
                except:
                    continue
            
            print(f"\n✓ Extracted {len(links)} organic results from Ecosia")
            
        except Exception as e:
            print(f"Ecosia search error: {e}")
        
        finally:
            if self.driver:
                debug_mode = SettingsManager.get_setting('debug_mode', False)
                if not debug_mode:
                    self.driver.quit()
                    self.driver = None
                else:
                    print("🐞 Debug Mode: Browser left open for inspection")
                
        return links
