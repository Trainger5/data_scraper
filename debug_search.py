"""
Debug script to test web search with visible browser
This will help you see what's happening during the search
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.scrapers.web_search import WebSearchScraper

print("="*60)
print("Web Search Debug Mode - Visible Browser")
print("="*60)

# Test query
query = "IT Company In Chandigarh"
engine = "google"  # Change to "duckduckgo" or "bing" as needed

print(f"\nQuery: {query}")
print(f"Engine: {engine}")
print(f"Headless: False (you will see the browser)\n")

try:
    # Create scraper with visible browser
    scraper = WebSearchScraper(headless=False)
    
    print("Starting search...")
    results = scraper.search(query, max_results=10, engine=engine)
    
    print(f"\n{'='*60}")
    print(f"RESULTS: Found {len(results)} URLs")
    print(f"{'='*60}\n")
    
    if results:
        for i, url in enumerate(results[:10], 1):
            print(f"{i}. {url}")
    else:
        print("No results found!")
        print("\nPossible reasons:")
        print("1. Search engine is blocking automation")
        print("2. Proxies are dead/blocked (disable in settings)")
        print("3. Page selectors need updating")
        print("4. Captcha or bot detection triggered")
    
    # Keep browser open to inspect
    input("\n\nPress Enter to close browser...")
    # Browser will close automatically when script ends
    
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()

print("\nDebug session complete!")
