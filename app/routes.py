from flask import Blueprint, request, jsonify, send_from_directory, make_response
import threading
import csv
import io
import os
from app.database import Database
from app.services.crawler import WebCrawler

main = Blueprint('main', __name__)

db = Database()
crawler = WebCrawler()

# Store active crawl threads
active_crawls = {}

def run_crawl(search_id, query, use_google_maps=False, search_type='web', platform=None, engine='duckduckgo', page_count=3, depth=2, max_pages=50, platform_type=None, target_website=None, scrape_emails=True, scrape_phones=True):
    """Run crawl in background thread"""
    def progress_callback(sid, message, percent):
        print(f"[{sid}] {percent}% - {message}")
    
    result = crawler.crawl(
        search_id, 
        query, 
        progress_callback, 
        use_google_maps=use_google_maps,
        search_type=search_type,
        platform=platform,
        engine=engine,
        page_count=page_count,
        depth=depth,
        max_pages=max_pages,
        platform_type=platform_type,
        target_website=target_website,
        scrape_emails=scrape_emails,
        scrape_phones=scrape_phones
    )
    
    # Remove from active crawls when done
    if search_id in active_crawls:
        del active_crawls[search_id]

@main.route('/')
def index():
    """Serve the main HTML page"""
    from flask import render_template
    return render_template('index.html')

@main.route('/settings')
def settings_page():
    """Serve the settings page"""
    from flask import render_template
    return render_template('settings.html')

@main.route('/docs')
def docs_page():
    """Serve the documentation page"""
    from flask import render_template
    return render_template('docs.html')

@main.route('/api/settings', methods=['GET', 'POST'])
def handle_settings():
    """Get or update settings"""
    from app.services.settings import SettingsManager
    
    if request.method == 'POST':
        data = request.get_json()
        for key, value in data.items():
            SettingsManager.update_setting(key, value)
        return jsonify({'status': 'success', 'settings': SettingsManager.get_all()})
    
    return jsonify(SettingsManager.get_all())

@main.route('/api/proxies', methods=['GET'])
def get_proxies():
    """Get list of available proxies with status"""
    import os
    from app.services.proxy_manager import ProxyManager
    
    proxy_file = 'proxies.txt'
    if not os.path.exists(proxy_file):
        return jsonify({'proxies': [], 'stats': {'total': 0, 'available': 0, 'failed': 0}})
    
    # Load proxies
    proxy_manager = ProxyManager(proxy_file=proxy_file)
    
    # Read file to get proxy strings with status markers
    proxies_info = []
    try:
        with open(proxy_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    validated = line.startswith('[OK]')
                    proxy_str = line[4:].strip() if validated else line.strip()
                    if ':' in proxy_str:
                        proxies_info.append({
                            'proxy': proxy_str,
                            'validated': validated
                        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    stats = proxy_manager.get_stats()
    
    return jsonify({
        'proxies': proxies_info,
        'stats': stats
    })

@main.route('/api/proxies/refresh', methods=['POST'])
def refresh_proxies():
    """Trigger proxy fetching script"""
    import subprocess
    import os
    
    try:
        script_path = os.path.join('scripts', 'fetch_free_proxies.py')
        
        # Run the script in background
        result = subprocess.run(
            ['python', script_path],
            capture_output=True,
            text=True,
            timeout=120  # 2 minutes timeout
        )
        
        if result.returncode == 0:
            return jsonify({
                'status': 'success',
                'message': 'Proxies refreshed successfully',
                'output': result.stdout
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to refresh proxies',
                'error': result.stderr
            }), 500
            
    except subprocess.TimeoutExpired:
        return jsonify({
            'status': 'error',
            'message': 'Proxy refresh timed out'
        }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@main.route('/api/search', methods=['POST'])
def start_search():
    """Start a new email extraction search"""
    data = request.get_json()
    query = data.get('query', '').strip()
    search_type = data.get('search_type', 'web')
    platform = data.get('platform')
    engine = data.get('engine', 'duckduckgo')
    page_count = data.get('page_count', 3)
    depth = data.get('depth', 2)
    max_pages = data.get('max_pages', 50)
    platform_type = data.get('platform_type')
    target_website = data.get('target_website')
    scrape_emails = data.get('scrape_emails', True)  # NEW: Default to True
    scrape_phones = data.get('scrape_phones', True)  # NEW: Default to True
    
    # Legacy support
    use_google_maps = data.get('use_google_maps', False)
    if use_google_maps:
        search_type = 'maps'
    
    if not query:
        return jsonify({'error': 'Query is required'}), 400
    
    # Debug logging
    print(f"\n{'='*60}")
    print(f"DEBUG - Start Search:")
    print(f"  search_type: {search_type}")
    print(f"  platform_type: {platform_type}")
    print(f"  target_website: {target_website}")
    print(f"  query: {query}")
    print(f"  scrape_emails: {scrape_emails}")
    print(f"  scrape_phones: {scrape_phones}")
    print(f"{'='*60}\n")
    
    # Create search record
    search_id = db.create_search(query, search_type, engine)
    
    # Start crawl in background thread
    thread = threading.Thread(
        target=run_crawl, 
        args=(search_id, query),
        kwargs={
            'use_google_maps': (search_type == 'maps'),
            'search_type': search_type,
            'platform': platform,
            'engine': engine,
            'page_count': page_count,
            'depth': depth,
            'max_pages': max_pages,
            'platform_type': platform_type,
            'target_website': target_website,
            'scrape_emails': scrape_emails,  # NEW
            'scrape_phones': scrape_phones   # NEW
        }
    )
    thread.daemon = True
    thread.start()
    
    active_crawls[search_id] = thread
    
    return jsonify({
        'search_id': search_id,
        'query': query,
        'status': 'started'
    })

@main.route('/history')
def history_page():
    """Serve the history page"""
    from flask import render_template
    searches = db.get_all_searches(limit=100)
    return render_template('history.html', searches=searches)

@main.route('/api/stop/<int:search_id>', methods=['POST'])
def stop_crawl(search_id):
    """Stop an active crawl and return current results"""
    try:
        # Mark search as stopped in database
        db.update_search_status(search_id, 'stopped', 0, 0)
        
        # Note: We can't actually kill the thread, but crawler will check status
        # and stop on next iteration
        
        return jsonify({
            'status': 'stopped',
            'message': 'Crawl stop requested. Results will be shown shortly.'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@main.route('/api/results/<int:search_id>', methods=['GET'])
def get_results(search_id):
    """Get results for a specific search"""
    search_info = db.get_search_status(search_id)
    if not search_info:
        return jsonify({'error': 'Search not found'}), 404
        
    results = db.get_search_results(search_id)
    
    # Add businesses to results
    businesses = db.get_businesses(search_id)
    results['businesses'] = businesses
    
    return jsonify({
        'search': search_info,
        'results': results
    })

@main.route('/api/history', methods=['GET'])
def get_history():
    """Get all past searches"""
    limit = request.args.get('limit', 50, type=int)
    searches = db.get_all_searches(limit)
    return jsonify({'searches': searches})

@main.route('/api/export/<int:search_id>', methods=['GET'])
def export_results(search_id):
    """Export results as CSV or JSON"""
    format_type = request.args.get('format', 'csv').lower()
    
    results = db.get_search_results(search_id)
    if not results:
        return jsonify({'error': 'Search not found'}), 404
        
    if format_type == 'json':
        return jsonify(results)
    
    elif format_type == 'csv':
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write Emails Section
        writer.writerow(['--- EMAILS ---'])
        writer.writerow(['Email', 'Domain', 'Source URL', 'Found At'])
        for row in results['emails']:
            writer.writerow([
                row.get('email', ''),
                row.get('domain', ''),
                row.get('source_url', ''),
                row.get('found_at', '')
            ])
            
        # Write Phones Section
        writer.writerow([])
        writer.writerow(['--- PHONES ---'])
        writer.writerow(['Phone', 'Source URL', 'Found At'])
        for row in results['phones']:
            writer.writerow([
                row.get('phone', ''),
                row.get('source_url', ''),
                row.get('found_at', '')
            ])
        
        csv_content = output.getvalue()
        output.close()
        
        response = make_response(csv_content)
        response.headers["Content-Disposition"] = f"attachment; filename=results_{search_id}.csv"
        response.headers["Content-type"] = "text/csv"
        return response
    
    else:
        return jsonify({'error': 'Invalid format. Use csv or json'}), 400

@main.route('/api/status/<int:search_id>', methods=['GET'])
def get_status(search_id):
    """Get current status of a search"""
    search = db.get_search_status(search_id)
    
    if not search:
        return jsonify({'error': 'Search not found'}), 404
    
    return jsonify({
        'search_id': search_id,
        'status': search['status'],
        'pages_crawled': search['pages_crawled'],
        'total_emails': search['total_emails'],
        'total_phones': db.get_phone_count(search_id),
        'current_url': search.get('current_url'),
        'is_active': search_id in active_crawls
    })

@main.route('/emails')
def emails_page():
    """Serve the emails page"""
    from flask import render_template
    return render_template('emails.html')

@main.route('/phones')
def phones_page():
    """Serve the phones page"""
    from flask import render_template
    return render_template('phones.html')

@main.route('/api/emails', methods=['GET'])
def get_all_emails():
    """Get all emails from the database"""
    emails = db.get_all_emails()
    return jsonify({'emails': emails})

@main.route('/api/phones', methods=['GET'])
def get_all_phones():
    """Get all phone numbers from the database"""
    phones = db.get_all_phones()
    return jsonify({'phones': phones})

@main.route('/api/delete/<int:search_id>', methods=['DELETE'])
def delete_search(search_id):
    """Delete a search and its results"""
    db.delete_search(search_id)
    return jsonify({'message': 'Search deleted successfully'})

@main.route('/api/stats', methods=['GET'])
def get_stats():
    """Get overall platform statistics"""
    searches = db.get_all_searches(1000)
    
    total_searches = len(searches)
    total_emails = sum(s['total_emails'] for s in searches)
    total_pages = sum(s['pages_crawled'] for s in searches)
    
    return jsonify({
        'total_searches': total_searches,
        'total_emails_found': total_emails,
        'total_pages_crawled': total_pages,
        'active_searches': len(active_crawls)
    })
