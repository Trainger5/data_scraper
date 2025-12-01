# Google Maps Integration Guide

## 🗺️ **Google Maps Business Email Extraction**

You've asked about extracting emails from Google Maps business cards. Here's what you need to know:

---

## ⚠️ **Current Status: NOT IMPLEMENTED**

The current crawler **does NOT** scrape Google Maps because:

1. **Google Maps uses JavaScript**: Requires browser automation (Selenium/Playwright)
2. **Anti-scraping measures**: Google actively blocks automated scraping
3. **Terms of Service**: Violates Google's ToS
4. **API required**: Google Maps Places API is the official way
5. **Complex structure**: Business cards have dynamic loading

---

## 🔧 **How to Add Google Maps Support**

### Option 1: Google Maps Places API (RECOMMENDED ✅)

**Pros:**
- Official and legal
- Reliable data
- No blocking
- Structured results

**Cons:**
- Requires API key
- Costs money after free tier
- Rate limits

**Implementation:**

```python
# Install: pip install googlemaps

import googlemaps

def search_google_maps(query, location="India"):
    gmaps = googlemaps.Client(key='YOUR_API_KEY')
    
    # Search for places
    places = gmaps.places(query=query, location=location)
    
    emails = []
    for place in places['results']:
        place_id = place['place_id']
        details = gmaps.place(place_id)
        
        # Get contact info
        if 'website' in details['result']:
            # Crawl the website for emails
            website = details['result']['website']
            # Use existing crawler on this website
            
    return emails
```

**Cost:** $0 for first 1000 requests/month, then $5 per 1000

---

### Option 2: Selenium Scraping (Advanced ⚡)

**Pros:**
- Can access full Google Maps
- Gets all visible data
- No API fees

**Cons:**
- Violates Google ToS
- Easily detected and blocked
- Requires Chrome/Firefox
- Slow (3-5 sec per business)
- May break when Google updates

**Implementation:**

```python
# Install: pip install selenium webdriver-manager

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

def scrape_google_maps(query):
    driver = webdriver.Chrome()
    driver.get(f"https://www.google.com/maps/search/{query}")
    
    # Wait for results
    wait = WebDriverWait(driver, 10)
    
    # Find business cards
    businesses = driver.find_elements(By.CLASS_NAME, "business-card")
    
    for business in businesses:
        # Click to open details
        business.click()
        time.sleep(2)
        
        # Look for website link
        website_link = driver.find_element(By.CSS_SELECTOR, "a[data-item-id='authority']")
        if website_link:
            # Crawl the website
            url = website_link.get_attribute('href')
            # Use existing crawler
        
        # Look for email (sometimes shown directly)
        try:
            email_element = driver.find_element(By.CSS_SELECTOR, "button[data-item-id='email']")
            email = email_element.text
        except:
            pass
    
    driver.quit()
```

---

### Option 3: Hybrid Approach (BEST FOR YOU 🎯)

**Strategy:**
1. Search Google Maps with Selenium
2. Extract **website URLs** from business cards
3. Use your **existing crawler** on those websites
4. Get emails from company websites

**Benefits:**
- Works with current system
- Legal (you're just visiting websites)
- More reliable emails
- Follows robots.txt

**Quick Implementation:**

I can add a new search mode:

```python
# In crawler.py

def search_google_maps_websites(query):
    """Get website URLs from Google Maps, then crawl them"""
    
    # Option A: Use Selenium to get websites from Maps
    driver = webdriver.Chrome()
    driver.get(f"https://www.google.com/maps/search/{query}")
    
    websites = []
    businesses = driver.find_elements(By.CLASS_NAME, "business-card")
    
    for biz in businesses[:10]:  # Limit to 10 businesses
        try:
            biz.click()
            time.sleep(1)
            website_btn = driver.find_element(By.CSS_SELECTOR, "a[data-item-id='authority']")
            url = website_btn.get_attribute('href')
            websites.append(url)
        except:
            continue
    
    driver.quit()
    
    # Option B: Now use your EXISTING crawler on these websites
    # This part already works!
    return websites
```

---

## 🎯 **My Recommendation**

For **"IT company in Mohali"** type searches:

### Immediate Solution (No code changes):

1. **Search Google yourself**: "IT companies in Mohali"
2. **Copy 5-10 company websites** from Maps
3. **Search directly**: Enter each website URL in the app
   - Example: "companyname.com"
   - Your crawler will extract emails from that site

### Better Solution (I can implement):

**Add "Google Maps Mode"** button:
- Checkbox: "☑️ Search Google Maps for company websites"
- Uses Selenium to extract website URLs from Maps
- Then crawls those websites (your existing code)
- Shows: "Found 15 companies on Maps, crawling their websites..."

---

## 📊 **Comparison**

| Method | Pros | Cons | Speed | Cost |
|--------|------|------|-------|------|
| **Manual Map Search** | Legal, Easy | Time-consuming | Slow | Free |
| **Places API** | Official, Reliable | Needs API key | Fast | ~$5/month |
| **Selenium Maps** | Automated | Against ToS | Medium | Free |
| **Hybrid (Recommended)** | Uses current code | Needs Selenium | Medium | Free |

---

## 💡 **Want Me to Implement?**

I can add Google Maps website extraction **right now** if you want:

**What I'll add:**
1. ✅ Checkbox in UI: "Use Google Maps"
2. ✅ Selenium script to extract company websites from Maps
3. ✅ Feed those URLs to existing crawler
4. ✅ You get emails from all businesses on the map!

**Requirements:**
- Install: `pip install selenium webdriver-manager`
- Chrome browser installed
- Takes ~5 min to implement

**Would you like me to add this feature?** Just say yes and I'll implement Google Maps website extraction! 🚀

---

## 📝 **Example Workflow**

**Current way:**
```
Search: "IT company in Mohali"
↓
Google/Bing search finds generic pages
↓
Crawl those pages
↓
Maybe 0-10 emails
```

**With Google Maps:**
```
Search: "IT company in Mohali" + ☑️ Google Maps
↓
Selenium opens Google Maps
↓
Finds 20 IT companies in Mohali
↓
Extracts their website URLs
↓
Existing crawler visits each website
↓
Get 30-50 emails from actual companies!
```

Much better results! 🎉
