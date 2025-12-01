# Email Extractor Pro 🚀

A powerful web-based email extraction platform that crawls websites and finds publicly available email addresses based on your search queries.

![Platform Status](https://img.shields.io/badge/status-active-success)
![Python](https://img.shields.io/badge/python-3.8+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## ⚠️ Legal Disclaimer

**IMPORTANT:** This tool is designed for **legitimate business research purposes only**. Users must:

- Comply with GDPR, CAN-SPAM Act, CASL, and all applicable privacy laws
- Only use extracted emails for lawful purposes
- Respect website terms of service and robots.txt files
- Obtain proper consent before using emails for marketing

**You are solely responsible for ensuring legal compliance in your jurisdiction.**

## ✨ Features

- 🔍 **Smart Web Crawling** - Automatically finds relevant websites based on your search query
- 📧 **Email Extraction** - Advanced pattern matching to identify valid email addresses
- 🤖 **Robots.txt Compliance** - Respects website crawling policies
- ⚡ **Real-time Progress** - Live updates as emails are discovered
- 💾 **Export Options** - Download results as CSV or JSON
- 📊 **Search History** - View and re-access previous searches
- 🎨 **Premium UI** - Beautiful dark mode interface with glassmorphism
- 🚦 **Rate Limiting** - Respectful crawling with delays between requests

## 🛠️ Technology Stack

**Backend:**
- Python 3.8+
- Flask (Web Framework)
- BeautifulSoup4 (HTML Parsing)
- SQLite (Database)
- Validators (Email Validation)

**Frontend:**
- HTML5
- CSS3 (Glassmorphism design)
- Vanilla JavaScript
- Google Fonts (Inter)

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Modern web browser (Chrome, Firefox, Edge, Safari)

## 🚀 Installation

### 1. Clone or Download

If you haven't already, navigate to the project directory:

```bash
cd c:\Users\hp\Documents\Codezone\email_extractor
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Application

```bash
python app.py
```

You should see:

```
╔══════════════════════════════════════════╗
║   Email Extractor Platform Started!     ║
╠══════════════════════════════════════════╣
║  Open: http://127.0.0.1:5000            ║
╚══════════════════════════════════════════╝
```

### 4. Open in Browser

Navigate to: **http://127.0.0.1:5000**

## 📖 Usage Guide

### Starting a Search

1. Enter your search query in the search box
   - Examples:
     - "AI startups in San Francisco"
     - "digital marketing agencies in New York"
     - "e-commerce companies in Austin"

2. Click **"Start Extraction"**

3. Watch real-time progress as the crawler:
   - Searches for relevant websites
   - Crawls pages (respecting robots.txt)
   - Extracts email addresses
   - Validates and stores results

### Viewing Results

- **Filter**: Use the filter box to search for specific emails or domains
- **Export CSV**: Download all emails as a spreadsheet
- **Export JSON**: Get structured JSON data
- **New Search**: Start another extraction

### Search History

- Click on any previous search to view its results
- History shows:
  - Search query
  - Status (completed, running, error)
  - Number of emails found
  - Number of pages crawled
  - Time elapsed

## ⚙️ Configuration

Edit `config.py` to customize:

```python
MAX_PAGES_PER_SEARCH = 20    # Maximum pages to crawl
MAX_CRAWL_DEPTH = 2          # Link following depth
REQUEST_DELAY = 2            # Seconds between requests
MAX_SEARCH_RESULTS = 10      # Initial search results
```

## 📁 Project Structure

```
email_extractor/
├── app.py                 # Flask API server
├── crawler.py             # Web crawling engine
├── email_extractor.py     # Email extraction & validation
├── database.py            # SQLite database management
├── config.py              # Application configuration
├── requirements.txt       # Python dependencies
├── index.html             # Frontend interface
├── style.css              # Premium styling
├── app.js                 # Frontend logic
├── README.md              # Documentation
└── email_extractor.db     # SQLite database (auto-created)
```

## 🔧 API Endpoints

### POST /api/search
Start a new email extraction search
```json
Request: { "query": "search term" }
Response: { "search_id": 1, "query": "search term", "status": "started" }
```

### GET /api/results/{search_id}
Get results for a specific search
```json
Response: {
  "search": {...},
  "emails": [
    {
      "email": "example@domain.com",
      "domain": "domain.com",
      "source_url": "https://...",
      "found_at": "2025-11-27T10:00:00"
    }
  ]
}
```

### GET /api/history
Get all past searches

### GET /api/status/{search_id}
Check search progress

### GET /api/export/{search_id}?format=csv|json
Export results

### DELETE /api/delete/{search_id}
Delete a search

### GET /api/stats
Get platform statistics

## 🐛 Troubleshooting

### Search Returns No Results

- Try a more specific query
- Ensure you have internet connection
- Check if target websites block crawlers
- Some websites may have strong anti-bot measures

### Installation Issues

```bash
# If pip install fails, try:
python -m pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```

### Port Already in Use

Edit `config.py` and change:
```python
PORT = 5001  # or any available port
```

## 🎯 Best Practices

1. **Be Specific** - Use detailed search queries for better results
2. **Respect Limits** - Don't modify delays to be too aggressive
3. **Verify Emails** - Always validate emails before using them
4. **Legal Compliance** - Ensure your use case is legitimate
5. **Rate Limiting** - The platform respects websites automatically

## 🔒 Privacy & Security

- All data is stored locally in SQLite database
- No data is shared with external services
- Crawler identifies itself with proper User-Agent
- Respects robots.txt directives
- Implements request delays to avoid server overload

## 📝 Database Schema

**searches** - Search records
- id, query, status, total_emails, pages_crawled, created_at, completed_at

**emails** - Extracted emails
- id, search_id, email, source_url, domain, found_at

**crawled_urls** - Crawl history (prevents duplicates)
- id, search_id, url, crawled_at

## 🤝 Contributing

This is a professional demonstration project. For production use, consider:

- Adding user authentication
- Implementing Redis for task queuing
- Adding CAPTCHA solving capabilities
- Email verification via SMTP
- Proxy rotation for larger crawls
- Advanced anti-bot detection bypass

## 📄 License

MIT License - Use responsibly and legally.

## 🙏 Acknowledgments

- Built with Flask, BeautifulSoup, and modern web technologies
- Design inspired by contemporary web aesthetics
- Created for legitimate business research purposes

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review configuration settings
3. Check browser console for errors
4. Ensure all dependencies are installed

---

**Remember:** With great power comes great responsibility. Use this tool ethically and legally. 🌟
