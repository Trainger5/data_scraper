# Proxy Setup Guide

## Overview
The Email Extractor now supports proxy rotation to avoid IP-based blocking, making it production-ready like SerpApi and Goyral tools.

## Quick Start

### Option 1: Free Proxies (Recommended for Testing)

1. **Fetch Free Proxies**:
   ```bash
   python scripts/fetch_free_proxies.py
   ```
   This will download and validate free proxies, saving them to `proxies.txt`.

2. **Enable Proxies**:
   Edit `config.py`:
   ```python
   USE_PROXIES = True
   ```

3. **Run Application**:
   ```bash
   python run.py
   ```

### Option 2: Paid Proxies (Recommended for Production)

1. **Get Proxy Service**:
   - **Recommended Providers**:
     - [BrightData](https://brightdata.com) - $500/month, residential IPs
     - [Smartproxy](https://smartproxy.com) - $75/month, 5GB
     - [Oxylabs](https://oxylabs.io) - $300/month, datacenter
     - [ProxyMesh](https://proxymesh.com) - $10/month, basic

2. **Add Proxies to File**:
   Edit `proxies.txt`:
   ```
   # Simple proxy
   proxy1.example.com:8080
   proxy2.example.com:8080
   
   # Authenticated proxy
   proxy.example.com:8080:username:password
   ```

3. **Enable in Config**:
   ```python
   USE_PROXIES = True
   PROXY_ROTATION_STRATEGY = 'random'  # or 'round-robin'
   ```

## Configuration Options

### In `config.py`:

```python
# Proxy Settings
USE_PROXIES = False              # Enable/disable proxy rotation
PROXY_LIST_FILE = 'proxies.txt' # Path to proxy list
PROXY_TYPE = 'http'              # 'http' or 'socks5'
PROXY_ROTATION_STRATEGY = 'random'  # 'random' or 'round-robin'
MAX_PROXY_RETRIES = 3            # Retries before marking proxy as failed
PROXY_TIMEOUT = 10               # Seconds for proxy validation
```

## How It Works

1. **Proxy Manager**: Loads proxies from `proxies.txt`
2. **Rotation**: Each search uses a different proxy (random or round-robin)
3. **Health Checking**: Failed proxies are automatically marked and skipped
4. **Selenium Integration**: Proxies are configured in Chrome WebDriver

## Proxy File Format

```
# Comments start with #
ip:port
ip:port:username:password

# Examples:
8.8.8.8:8080
proxy.example.com:3128:myuser:mypass
```

## Free vs Paid Proxies

### Free Proxies
**Pros:**
- No cost
- Good for testing

**Cons:**
- Unreliable (often offline)
- Slow
- Limited locations
- May be blacklisted

### Paid Proxies
**Pros:**
- Reliable (99.9% uptime)
- Fast
- Multiple locations
- Residential IPs (harder to detect)

**Cons:**
- Monthly cost ($10-$500)

## Troubleshooting

### "No proxies available"
- Check `proxies.txt` exists and has valid proxies
- Run `python scripts/fetch_free_proxies.py` to get fresh proxies

### "All proxies failed"
- Free proxies often don't work - try fetching new ones
- Consider using paid proxies for reliability

### Slow scraping
- Free proxies are often slow
- Reduce `MAX_WORKERS` in config.py
- Use paid proxies for better speed

## Testing Proxy Setup

```bash
# 1. Fetch proxies
python scripts/fetch_free_proxies.py

# 2. Enable in config.py
# USE_PROXIES = True

# 3. Run a search and check console
python run.py

# Look for: "🔒 Using proxy: x.x.x.x:xxxx"
```

## Production Recommendations

For production use (like Goyral/SerpApi):
1. **Use Paid Proxies**: BrightData or Smartproxy
2. **Residential IPs**: Harder to detect than datacenter
3. **Rotate Frequently**: Use 'random' strategy
4. **Monitor Health**: Check proxy stats regularly
5. **Have Backup**: Maintain 50+ proxies in rotation
