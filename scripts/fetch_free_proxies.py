"""
Free Proxy Fetcher
Fetches and validates free proxies from public sources
"""

import requests
from bs4 import BeautifulSoup
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.services.proxy_manager import ProxyManager

def fetch_free_proxy_list():
    """Fetch proxies from free-proxy-list.net"""
    proxies = []
    try:
        print("Fetching proxies from free-proxy-list.net...")
        response = requests.get('https://free-proxy-list.net/', timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        table = soup.find('table', {'class': 'table'})
        if table:
            rows = table.find_all('tr')[1:]  # Skip header
            for row in rows[:50]:  # Get first 50
                cols = row.find_all('td')
                if len(cols) >= 7:
                    ip = cols[0].text.strip()
                    port = cols[1].text.strip()
                    https = cols[6].text.strip()
                    
                    if https == 'yes':  # Only HTTPS proxies
                        proxies.append(f"{ip}:{port}")
        
        print(f"[OK] Found {len(proxies)} HTTPS proxies")
    except Exception as e:
        print(f"[ERROR] Error fetching from free-proxy-list.net: {e}")
    
    return proxies

def fetch_proxy_scrape():
    """Fetch proxies from proxyscrape.com API"""
    proxies = []
    try:
        print("Fetching proxies from proxyscrape.com...")
        url = "https://api.proxyscrape.com/v2/?request=get&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            proxy_list = response.text.strip().split('\r\n')
            proxies = [p for p in proxy_list if p]
            print(f"[OK] Found {len(proxies)} proxies")
    except Exception as e:
        print(f"[ERROR] Error fetching from proxyscrape.com: {e}")
    
    return proxies

def validate_and_save(proxies, output_file='proxies.txt', max_validate=10):
    """Validate proxies and save working ones"""
    print(f"\nValidating proxies (testing first {max_validate})...")
    
    proxy_manager = ProxyManager()
    working_proxies = []
    
    for i, proxy_str in enumerate(proxies[:max_validate]):
        print(f"[{i+1}/{max_validate}] Testing {proxy_str}...", end=' ')
        proxy_dict = proxy_manager._parse_proxy(proxy_str)
        
        if proxy_dict and proxy_manager.validate_proxy(proxy_dict, timeout=5):
            working_proxies.append(proxy_str)
        else:
            print("[FAIL] Failed")
    
    # Save all proxies (not just validated ones, as validation can be slow)
    print(f"\nSaving {len(proxies)} proxies to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Free Proxies - Auto-fetched\n")
        f.write("# Format: ip:port\n")
        f.write("# Validated proxies are marked with [OK]\n\n")
        
        for proxy in proxies:
            marker = "[OK] " if proxy in working_proxies else "     "
            f.write(f"{marker}{proxy}\n")
    
    print(f"[OK] Saved {len(proxies)} proxies ({len(working_proxies)} validated)")
    print(f"\nTo use proxies, set USE_PROXIES=True in config.py")

if __name__ == '__main__':
    print("="*60)
    print("Free Proxy Fetcher")
    print("="*60)
    
    all_proxies = []
    
    # Fetch from multiple sources
    all_proxies.extend(fetch_free_proxy_list())
    all_proxies.extend(fetch_proxy_scrape())
    
    # Remove duplicates
    all_proxies = list(set(all_proxies))
    
    if all_proxies:
        validate_and_save(all_proxies, max_validate=5)
    else:
        print("\n[ERROR] No proxies found")
