"""
Email and Phone Extraction Engine
Extracts and validates email addresses and phone numbers from text content
"""

import re
import validators
from config import MIN_EMAIL_LENGTH, MAX_EMAIL_LENGTH, EXCLUDED_PATTERNS


class EmailExtractor:
    def __init__(self):
        # Comprehensive email regex pattern
        self.email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )
        
        # Phone number patterns (International & US/UK formats)
        # Matches: +1-555-555-5555, (555) 555-5555, 555 555 5555, etc.
        self.phone_pattern = re.compile(
            r'''(?:(?:\+|00)([1-9]\d{0,2}))?[-. (]*(\d{3})[-. )]*(\d{3})[-. ]*(\d{4})(?: *x(\d+))?'''
        )
    
    def extract_from_text(self, text):
        """Extract all email addresses from text"""
        if not text:
            return []
        
        # Find all matches
        emails = self.email_pattern.findall(text)
        
        # Validate and filter
        valid_emails = []
        for email in emails:
            if self.is_valid_email(email):
                valid_emails.append(email.lower())
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(valid_emails))
    
    def extract_phones(self, text):
        """Extract phone numbers from text"""
        if not text:
            return []
            
        matches = self.phone_pattern.findall(text)
        phones = []
        
        for match in matches:
            # Reconstruct phone number from groups
            # Groups: 1=CountryCode, 2=AreaCode, 3=Prefix, 4=Line, 5=Extension
            parts = [p for p in match if p]
            if len(parts) >= 3: # At least Area, Prefix, Line
                phone = "-".join(parts)
                # Basic length check to avoid false positives like dates
                if len(re.sub(r'\D', '', phone)) >= 10:
                    phones.append(phone)
        
        return list(dict.fromkeys(phones))
    
    def is_valid_email(self, email):
        """Validate email address"""
        # Length check
        if len(email) < MIN_EMAIL_LENGTH or len(email) > MAX_EMAIL_LENGTH:
            return False
        
        # Check for excluded patterns
        for pattern in EXCLUDED_PATTERNS:
            if pattern in email.lower():
                return False
        
        # Use validators library for robust validation
        if not validators.email(email):
            return False
        
        # Additional checks
        if email.count('@') != 1:
            return False
        
        # Check for suspicious patterns
        if '..' in email or email.startswith('.') or email.endswith('.'):
            return False
        
        # NEW: Reject emails with file extensions in the local part (before @)
        # This prevents matching things like "image.jpg@domain.com"
        local_part = email.split('@')[0].lower()
        domain_part = email.split('@')[1].lower()
        
        file_extensions = [
            '.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp', '.ico',
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.zip', '.rar', '.tar', '.gz', '.mp4', '.avi', '.mov', '.mp3',
            '.wav', '.css', '.js', '.html', '.xml', '.json', '.txt',
            '.woff', '.woff2', '.ttf', '.eot'
        ]
        
        # Check local part
        for ext in file_extensions:
            if local_part.endswith(ext):
                return False
                
        # Check domain part (e.g. user@image.png)
        for ext in file_extensions:
            if domain_part.endswith(ext):
                return False
        
        return True
    
    def get_domain(self, email):
        """Extract domain from email address"""
        try:
            return email.split('@')[1].lower()
        except:
            return None
    
    def extract_from_html(self, html_content):
        """Extract emails and phones from HTML content"""
        # Remove script and style tags
        cleaned_text = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        cleaned_text = re.sub(r'<style[^>]*>.*?</style>', '', cleaned_text, flags=re.DOTALL | re.IGNORECASE)
        
        # Extract from mailto links
        mailto_pattern = re.compile(r'mailto:([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})', re.IGNORECASE)
        mailto_emails = mailto_pattern.findall(html_content)
        
        # Extract from plain text
        text_emails = self.extract_from_text(cleaned_text)
        
        # Extract phones
        phones = self.extract_phones(cleaned_text)
        
        # Combine and deduplicate
        all_emails = mailto_emails + text_emails
        valid_emails = []
        
        for email in all_emails:
            if self.is_valid_email(email):
                valid_emails.append(email.lower())
        
        return list(dict.fromkeys(valid_emails)), phones
    
    def filter_emails(self, emails, domain_filter=None):
        """Filter emails by domain"""
        if not domain_filter:
            return emails
        
        filtered = []
        for email in emails:
            domain = self.get_domain(email)
            if domain and domain_filter.lower() in domain.lower():
                filtered.append(email)
        
        return filtered
    
    def get_stats(self, emails):
        """Get statistics about extracted emails"""
        if not emails:
            return {
                'total': 0,
                'unique_domains': 0,
                'domains': {}
            }
        
        domains = {}
        for email in emails:
            domain = self.get_domain(email)
            if domain:
                domains[domain] = domains.get(domain, 0) + 1
        
        return {
            'total': len(emails),
            'unique_domains': len(domains),
            'domains': domains
        }
