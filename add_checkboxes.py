"""
Script to add email/phone checkboxes to base.html
"""

import re

# Read the current base.html
with open('app/templates/base.html', 'r', encoding='utf-8') as f:
    content = f.read()

# The HTML to insert
checkbox_html = '''
            <!-- Data Type Selection -->
            <div class="sidebar-selector" style="border-top: 1px solid var(--border);padding:0px;">
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" id="scrapeEmails" checked>
                    <label class="form-check-label" for="scrapeEmails" style="font-size: 0.85rem;">
                        <i class="fas fa-envelope"></i> Emails
                    </label>
                </div>
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" id="scrapePhones" checked>
                    <label class="form-check-label" for="scrapePhones" style="font-size: 0.85rem;">
                        <i class="fas fa-phone"></i> Phone Numbers
                    </label>
                </div>
            </div>
'''

# JavaScript to add
checkbox_js = '''
    <script>
        // Email/Phone checkbox state management
        document.addEventListener('DOMContentLoaded', function() {
            const scrapeEmailsCheckbox = document.getElementById('scrapeEmails');
            const scrapePhonesCheckbox = document.getElementById('scrapePhones');
            
            if (scrapeEmailsCheckbox) {
                const emailsEnabled = localStorage.getItem('scrapeEmails') !== 'false';
                scrapeEmailsCheckbox.checked = emailsEnabled;
                
                scrapeEmailsCheckbox.addEventListener('change', function() {
                    localStorage.setItem('scrapeEmails', this.checked);
                });
            }
            
            if (scrapePhonesCheckbox) {
                const phonesEnabled = localStorage.getItem('scrapePhones') !== 'false';
                scrapePhonesCheckbox.checked = phonesEnabled;
                
                scrapePhonesCheckbox.addEventListener('change', function() {
                    localStorage.setItem('scrapePhones', this.checked);
                });
            }
        });
    </script>'''

# Check if checkboxes already exist
if 'scrapeEmails' in content:
    print("✓ Checkboxes already exist in base.html")
else:
    # Find the location to insert (after Infinite Scraping section, before <nav class="sidebar-nav">)
    # Look for the closing </div> before <nav class="sidebar-nav">
    
    pattern = r'(</div>\s*<nav class="sidebar-nav">)'
    
    if re.search(pattern, content):
        # Insert the checkbox HTML before <nav>
        content = re.sub(pattern, checkbox_html + r'\n\1', content, count=1)
        print("✓ Added email/phone checkboxes to base.html")
    else:
        print("❌ Could not find insertion point. Please add manually.")
        print("\nLooking for alternative pattern...")
        # Try alternative pattern
        if '<nav class="sidebar-nav">' in content:
            content = content.replace('<nav class="sidebar-nav">', checkbox_html + '\n            <nav class="sidebar-nav">')
            print("✓ Added checkboxes using alternative method")

# Add JavaScript if not already present
if 'scrapeEmails' not in content or 'localStorage.getItem' not in content:
    # Add before closing </body> tag
    content = content.replace('</body>', checkbox_js + '\n</body>')
    print("✓ Added JavaScript for checkbox state management")

# Write the updated content back
with open('app/templates/base.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("\n✅ Done! Restart your server to see the checkboxes in the sidebar.")
