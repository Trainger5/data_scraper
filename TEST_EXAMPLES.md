# 🧪 Email Extractor - Test Queries & Examples

## ✅ **Google Maps - NO**
The crawler does **NOT** scrape Google Maps. It only crawls regular websites (HTML pages) to extract emails from:
- Contact pages
- About pages
- Team pages
- Footer sections
- Body content

---

## 🎯 **Recommended Test Queries**

### Option 1: Company Websites (Most Reliable)
Try searching for **specific well-known companies**:

```
examples:
- "Infosys contact"
- "TCS careers"
- "Wipro contact us"
- "Microsoft contact"
```

**Why this works:** Well-established companies have clear contact pages with emails.

---

### Option 2: Technology Industry Directories

```
examples:
- "software companies in Chandigarh"
- "web development agencies in Mumbai"
- "IT services in Bangalore"
```

**Why this works:** Industry directories often list multiple companies with contact info.

---

### Option 3: Educational Institutions

```
examples:
- "engineering colleges in Punjab"
- "universities in Delhi contact"
- "technical institutes in India"
```

**Why this works:** Educational sites typically have faculty emails, department contacts.

---

### Option 4: Direct Website Crawling

If you know a company website, just enter the domain:

```
examples:
- "infosys.com"
- "tcs.com"
- "microsoft.com"
- "google.com"
```

**Why this works:** Directly crawls the website without searching.

---

## 🚀 **Best Practices for Results**

### ✅ **DO:**
1. **Be specific**: "digital marketing agencies in Mohali" instead of "companies"
2. **Use industry terms**: "software development", "web design", "consulting"
3. **Include location**: "in Mohali", "in Chandigarh", "in India"
4. **Check server logs**: Watch the terminal to see which sites are being crawled
5. **Wait for completion**: Some searches take 30-60 seconds

### ❌ **DON'T:**
1. Use very generic terms like "companies" or "business"
2. Search for social media profiles (Facebook, LinkedIn block scrapers)
3. Expect instant results (crawling takes time)
4. Search for individual people (works best for companies)

---

## 📊 **Expected Results**

| Query Type | Expected Emails | Time Taken | Success Rate |
|------------|----------------|------------|--------------|
| Specific company | 5-15 emails | 20-30 sec | High ✅ |
| Industry + location | 10-30 emails | 40-60 sec | Medium 🟡 |
| Generic search | 0-10 emails | 30-45 sec | Low ⚠️ |
| Direct website | 3-20 emails | 15-25 sec | High ✅ |

---

## 🔍 **What to Watch in Terminal**

When you start a search, you'll see detailed logs like:

```
============================================================
Starting search for: 'IT company in Mohali'
============================================================

✓ Found 10 URLs from search:
  1. https://example1.com
  2. https://example2.com
  ...

============================================================
Starting crawl of 10 URLs...
============================================================

[1/20] Crawling: https://example1.com
  ✓ Found 3 emails:
    • contact@example1.com
    • info@example1.com
    • support@example1.com
  → Added 2 new links to crawl

[2/20] Crawling: https://example2.com
  ✗ No emails found on this page
  
...

============================================================
Crawl completed!
============================================================
✓ Pages crawled: 15
✓ Total emails found: 23

All emails found:
  • email1@domain.com
  • email2@domain.com
  ...
```

This way you can **verify in real-time** which websites are being crawled!

---

## 💡 **Quick Test Right Now**

Try this query to test immediately:

### Test 1: Wikipedia (should find admin emails)
```
wikipedia.org
```

### Test 2: Open Source Projects
```
github.com
```

### Test 3: Well-known company
```
infosys.com
```

**Important:** Make sure to watch your terminal/console window where `python app.py` is running - you'll see everything happening in real-time!

---

## 🐛 **Troubleshooting**

### "No emails found"
- Check terminal logs - are websites being crawled?
- Try a more specific query
- Some sites block web scrapers
- Try a well-known company website directly

### "Search taking too long"
- Crawling 20 pages can take 40-60 seconds (2 sec delay per page)
- Watch terminal to confirm it's working
- Don't refresh the page

### "Wrong/fake emails"
- The system filters common fakes (noreply@, test@, example.com)
- Some websites display example emails on their pages
- Export and manually verify important emails

---

## 📝 **Notes**

1. **Google Maps**: NOT supported (only HTML websites)
2. **Social Media**: Usually blocked (LinkedIn, Facebook, Twitter)
3. **JavaScript sites**: May not work fully (we use basic HTML parser)
4. **Rate limiting**: 2-second delay between requests (respectful crawling)
5. **Robots.txt**: We respect website crawling policies

---

## 🎉 **Try It Now!**

1. Open http://127.0.0.1:5000
2. Try query: **"infosys.com"**
3. Watch your terminal for live crawling logs
4. Wait 30-60 seconds
5. See results!

The **progress bar will now show which website is being crawled** in real-time! 🚀
