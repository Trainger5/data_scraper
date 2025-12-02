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

    def _click_next_page(self, engine):
        """
        Generic method to find and click the 'Next' button for various engines.
        Returns True if successful, False otherwise.
        """
        if not self.driver:
            return False
            
        selectors = {
            'google': [
                "a#pnnext",                 # Standard Desktop
                "a[aria-label='Next page']", # Modern/Mobile
                "a[aria-label='Next']",
                "table#nav td.b:last-child a" # Old school
            ],
            'bing': [
                "a.sb_pagN",
                "a[title='Next page']",
                "li.b_pag a.sb_pagN"
            ],
            'yahoo': [
                "a.next",
                "a[title='Next']"
            ],
            'brave': [
                "button.show-more-btn",      # New Brave "Show more" button
                "a.pagination-next-btn",     # Standard pagination
                "button.footer__more-btn",   # Older "Load more"
                "div.pagination a.next",
                "button[type='button'].btn"  # Generic button at bottom
            ],
            'duckduckgo': [
                "a.result--more__btn",
                "button#more-results",
                "a.result--more__btn"
            ],
            'ecosia': [
                "a.pagination-next",
                "a[aria-label='Next page']"
            ]
        }
        
        engine_selectors = selectors.get(engine, [])
        
        # 1. Try specific CSS selectors
        for selector in engine_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        # Verify it's likely a next button (not some other button)
                        text = element.text.lower()
                        if 'more' in text or 'next' in text or 'load' in text or not text:
                            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
                            time.sleep(1)
                            try:
                                self.driver.execute_script("arguments[0].click();", element)
                            except:
                                element.click()
                            print(f"  ➡ Clicking 'Next' page for {engine} (Selector: {selector})...")
                            time.sleep(random.uniform(2, 4))
                            return True
            except Exception as e:
                continue

        # 2. Fallback: Try finding by text "Next" or "More results"
        try:
            xpath_selectors = [
                "//button[contains(text(), 'Show more')]",
                "//button[contains(text(), 'More results')]",
                "//a[contains(text(), 'Next')]",
                "//span[contains(text(), 'Next')]/.."
            ]
            for xpath in xpath_selectors:
                elements = self.driver.find_elements(By.XPATH, xpath)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
                        time.sleep(1)
                        try:
                            self.driver.execute_script("arguments[0].click();", element)
                        except:
                            element.click()
                        print(f"  ➡ Clicking 'Next' page for {engine} (XPath: {xpath})...")
                        time.sleep(random.uniform(2, 4))
                        return True
        except Exception as e:
            print(f"  (Debug) Fallback click failed: {e}")

        print(f"  ⚠ Could not find 'Next' button for {engine}. Stopping pagination.")
        return False
    
    def search(self, query, max_results=20, engine='duckduckgo', on_result=None, stop_check=None):
        """Main search method - dispatches to specific engine"""
        engine = engine.lower()
        
        # Dispatch to appropriate method
        if engine == 'google':
            return self.search_google(query, max_results, on_result, stop_check)
        elif engine == 'bing':
            return self.search_bing(query, max_results, on_result, stop_check)
        elif engine == 'yahoo':
            return self.search_yahoo(query, max_results, on_result, stop_check)
        elif engine == 'brave':
            return self.search_brave(query, max_results, on_result, stop_check)
        else:
            return self.search_duckduckgo(query, max_results, on_result, stop_check)

    def search_duckduckgo(self, query, max_results=20, on_result=None, stop_check=None):
        """Search DuckDuckGo using Selenium with Pagination/Infinite Scroll"""
        if not self.driver:
            self.setup_driver()
        
        links = []
        
        try:
            print(f"\n{'='*60}")
            print(f"🦆 Searching DuckDuckGo for: '{query}'")
            print(f"{'='*60}\n")
            
            self.driver.get(f"https://duckduckgo.com/?q={query.replace(' ', '+')}&t=h_&ia=web")
            
            # Wait for results
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.react-results--main, div#links, div.results"))
                )
            except:
                pass
            
            while len(links) < max_results:
                # Scroll to bottom
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                # Try clicking "More Results" if available
                self._click_next_page('duckduckgo')
                
                # Scrape
                selectors = ["a[data-testid='result-title-a']", "article h2 a", "div.result__body h2 a"]
                current_count = len(links)
                
                for selector in selectors:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for el in elements:
                        try:
                            href = el.get_attribute('href')
                            if href and validators.url(href) and 'duckduckgo' not in href:
                                if href not in links:
                                    links.append(href)
                        except:
                            continue
                
                if len(links) >= max_results:
                    break
                    
                # If no new links found after scroll and click attempt, stop
                if len(links) == current_count:
                    print("  ⚠ No new results found, stopping.")
                    break
                    
                print(f"  ✓ Found {len(links)} links so far...")
            
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
        """Search Google using Selenium with Pagination"""
        if not self.driver:
            self.setup_driver()
        
        links = []
        page = 1
        
        try:
            print(f"\n{'='*60}")
            print(f"🔍 Searching Google for: '{query}'")
            print(f"{'='*60}\n")
            
            # Navigate to Google
            self.driver.get(f"https://www.google.com/search?q={query.replace(' ', '+')}&num=100") # Try to get 100 results first
            
            # Wait for results
            print("⏳ Waiting for results to load...")
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div#search, div#rso"))
                )
                print("✓ Results container loaded")
            except Exception as e:
                print(f"⚠ Timeout waiting for results: {e}")
            
            # Handle cookie consent
            try:
                consent_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Accept all') or contains(text(), 'I agree')]")
                if consent_buttons:
                    consent_buttons[0].click()
                    time.sleep(2)
            except:
                pass
            
            while len(links) < max_results:
                # Scroll to bottom to ensure all lazy-loaded elements are visible
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                
                # Find results
                selectors = [
                    "div.g div.yuRUbf a",
                    "div.g h3 a",
                    "div#search div.g a",
                    "a[jsname='UWckNb']"
                ]
                
                current_page_links = []
                for selector in selectors:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for el in elements:
                        try:
                            href = el.get_attribute('href')
                            if href and validators.url(href) and href.startswith('http'):
                                if 'google.com' not in href and 'googleadservices' not in href:
                                    if href not in links and href not in current_page_links:
                                        current_page_links.append(href)
                        except:
                            continue
                
                # Add new links
                for link in current_page_links:
                    if len(links) >= max_results:
                        break
                    links.append(link)
                    print(f"  ✓ Found: {link[:60]}...")
                
                print(f"  -- Page {page}: Found {len(current_page_links)} new links (Total: {len(links)})")
                
                if len(links) >= max_results:
                    break
                    
                # Try to go to next page
                if not self._click_next_page('google'):
                    print("  ⚠ No more pages or 'Next' button not found.")
                    break
                
                page += 1
            
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
        """Search Bing using Selenium with Pagination"""
        if not self.driver:
            self.setup_driver()
        
        links = []
        page = 1
        
        try:
            print(f"\n{'='*60}")
            print(f"🅱️ Searching Bing for: '{query}'")
            print(f"{'='*60}\n")
            
            self.driver.get(f"https://www.bing.com/search?q={query.replace(' ', '+')}")
            time.sleep(3)
            
            while len(links) < max_results:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                
                selectors = ["li.b_algo h2 a", "li.b_algo div.b_title a"]
                current_page_links = []
                
                for selector in selectors:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for el in elements:
                        try:
                            href = el.get_attribute('href')
                            if href and validators.url(href) and 'bing.com' not in href:
                                if href not in links and href not in current_page_links:
                                    current_page_links.append(href)
                        except:
                            continue
                
                for link in current_page_links:
                    if len(links) >= max_results: break
                    links.append(link)
                    print(f"  ✓ Found: {link[:60]}...")
                
                if len(links) >= max_results: break
                
                if not self._click_next_page('bing'):
                    print("  ⚠ No more pages.")
                    break
                page += 1
            
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
        """Search Yahoo using Selenium with Pagination"""
        if not self.driver:
            self.setup_driver()
        
        links = []
        page = 1
        
        try:
            print(f"\n{'='*60}")
            print(f"🟣 Searching Yahoo for: '{query}'")
            print(f"{'='*60}\n")
            
            self.driver.get(f"https://search.yahoo.com/search?p={query.replace(' ', '+')}")
            time.sleep(3)
            
            while len(links) < max_results:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                
                results = self.driver.find_elements(By.CSS_SELECTOR, "div.dd.algo a")
                current_page_links = []
                
                for result in results:
                    try:
                        url = result.get_attribute('href')
                        if url and validators.url(url) and 'yahoo.com' not in url:
                            if url not in links and url not in current_page_links:
                                current_page_links.append(url)
                    except:
                        continue
                
                for link in current_page_links:
                    if len(links) >= max_results: break
                    links.append(link)
                    print(f"  ✓ Found: {link[:60]}...")
                
                if len(links) >= max_results: break
                
                if not self._click_next_page('yahoo'):
                    print("  ⚠ No more pages.")
                    break
                page += 1
            
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

    def search_brave(self, query, max_results=20, on_result=None, stop_check=None):
        """Search Brave Search using Selenium with Pagination"""
        if not self.driver:
            self.setup_driver()
        
        links = []
        page = 1
        is_infinite = (max_results == -1)
        target_count = float('inf') if is_infinite else max_results
        
        try:
            print(f"\n{'='*60}")
            print(f"🦁 Searching Brave for: '{query}' (Target: {'Infinite' if is_infinite else max_results})")
            print(f"{'='*60}\n")
            
            self.driver.get(f"https://search.brave.com/search?q={query.replace(' ', '+')}")
            time.sleep(3)
            
            while len(links) < target_count:
                # Check stop signal
                if stop_check and stop_check():
                    print("  🛑 Stop signal received. Halting search.")
                    break

                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                
                results = self.driver.find_elements(By.CSS_SELECTOR, "div.snippet a")
                current_page_links = []
                
                for result in results:
                    try:
                        url = result.get_attribute('href')
                        if url and validators.url(url) and 'brave.com' not in url:
                            if url not in links and url not in current_page_links:
                                current_page_links.append(url)
                                # Stream result immediately
                                if on_result:
                                    on_result(url)
                    except:
                        continue
                
                for link in current_page_links:
                    if len(links) >= target_count: break
                    links.append(link)
                    print(f"  ✓ Found: {link[:60]}...")
                
                print(f"  -- Page {page}: Found {len(current_page_links)} new links. Total: {len(links)}/{'∞' if is_infinite else max_results}")
                
                if len(links) >= target_count: 
                    print("  ✓ Target result count reached. Stopping.")
                    break
                
                if not self._click_next_page('brave'):
                    print("  ⚠ No more pages.")
                    break
                page += 1
            
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
