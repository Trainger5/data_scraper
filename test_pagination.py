import sys
import os
from app.services.scrapers.web_search import WebSearchScraper

def test_brave_pagination():
    print("Testing Brave Search Pagination...")
    scraper = WebSearchScraper(headless=True)
    
    # Search for a common term that yields many results
    # Request 30 results to force at least 2 pages (usually ~10-20 per page)
    results = scraper.search_brave("Interior designer in US", max_results=30)
    
    print(f"\nTotal results found: {len(results)}")
    
    if len(results) > 20:
        print("SUCCESS: Pagination worked (found > 20 results)")
    else:
        print("FAILURE: Pagination likely failed (found <= 20 results)")

if __name__ == "__main__":
    test_brave_pagination()
