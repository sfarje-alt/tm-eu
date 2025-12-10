from http.server import BaseHTTPRequestHandler
import json
from datetime import datetime
import urllib.request
from urllib.parse import urlparse, parse_qs

# IMPORTANT: Update this with your GitHub username
GITHUB_USER = "sfarje-alt"
GITHUB_REPO = "tm-eu"
GITHUB_BRANCH = "main"
GITHUB_RAW_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}"

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Parse the URL path
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query_params = parse_qs(parsed_path.query)
        
        # Route to appropriate handler
        if path == '/' or path == '/api':
            self.send_home()
        elif path == '/api/status':
            self.send_status()
        elif path == '/api/trademarks/today/pages':
            self.send_today_pages()
        elif path.startswith('/api/trademarks/today/page/'):
            page_num = path.split('/')[-1]
            self.send_page_url(datetime.now().strftime('%Y%m%d'), page_num)
        elif path.endswith('/pages'):
            # Format: /api/trademarks/YYYYMMDD/pages
            parts = path.split('/')
            if len(parts) >= 4:
                date_str = parts[-2]
                self.send_date_pages(date_str)
        elif '/page/' in path:
            # Format: /api/trademarks/YYYYMMDD/page/N
            parts = path.split('/')
            if len(parts) >= 5:
                date_str = parts[-3]
                page_num = parts[-1]
                self.send_page_url(date_str, page_num)
        elif path == '/api/trademarks/today':
            # Legacy endpoint - return pages list
            self.send_today_pages()
        elif path.startswith('/api/trademarks/'):
            date_str = path.split('/')[-1]
            self.send_date_pages(date_str)
        else:
            self.send_error_response(404, "Endpoint not found")
    
    def send_json_response(self, data, status_code=200):
        """Send JSON response"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def send_error_response(self, status_code, message):
        """Send error response"""
        self.send_json_response({'error': message}, status_code)
    
    def send_home(self):
        """API documentation"""
        self.send_json_response({
            'name': 'EU Trademark Scraper API',
            'version': '2.0.0',
            'description': 'Serves individual Excel files with embedded trademark images',
            'endpoints': {
                'GET /api/status': 'Check API status and data availability',
                'GET /api/trademarks/today/pages': 'List all page files from today\'s scrape',
                'GET /api/trademarks/today/page/{N}': 'Get download URL for specific page from today',
                'GET /api/trademarks/{YYYYMMDD}/pages': 'List all page files for specific date',
                'GET /api/trademarks/{YYYYMMDD}/page/{N}': 'Get download URL for specific page and date'
            },
            'github_repo': f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}",
            'note': 'Excel files contain embedded images in Graphic representation column'
        })
    
    def send_status(self):
        """Check API and data status"""
        today = datetime.now().strftime('%Y%m%d')
        
        # Check if today's manifest exists
        manifest_url = f"{GITHUB_RAW_URL}/data/{today}/manifest.json"
        
        try:
            with urllib.request.urlopen(manifest_url) as response:
                manifest = json.loads(response.read().decode())
                data_available = True
                total_pages = manifest.get('total_pages', 0)
        except:
            data_available = False
            total_pages = 0
        
        self.send_json_response({
            'api_status': 'online',
            'today_data_available': data_available,
            'date': today,
            'total_pages': total_pages,
            'github_repo': f"{GITHUB_USER}/{GITHUB_REPO}"
        })
    
    def send_today_pages(self):
        """Get list of all page files from today's scrape"""
        today = datetime.now().strftime('%Y%m%d')
        self.send_date_pages(today)
    
    def send_date_pages(self, date_str):
        """Get list of all page files for specific date"""
        manifest_url = f"{GITHUB_RAW_URL}/data/{date_str}/manifest.json"
        
        try:
            with urllib.request.urlopen(manifest_url) as response:
                manifest = json.loads(response.read().decode())
                
                # Build response with download URLs for each page
                pages = []
                for filename in manifest.get('files', []):
                    # Extract page number from filename
                    try:
                        page_num = int(filename.split('_page_')[1].split('.')[0])
                    except:
                        page_num = 0
                    
                    pages.append({
                        'page_number': page_num,
                        'filename': filename,
                        'download_url': f"{GITHUB_RAW_URL}/data/{date_str}/{filename}",
                        'has_images': True  # Excel files contain embedded images
                    })
                
                # Sort by page number
                pages.sort(key=lambda x: x['page_number'])
                
                self.send_json_response({
                    'success': True,
                    'date': date_str,
                    'total_pages': manifest.get('total_pages', len(pages)),
                    'scraped_at': manifest.get('scraped_at', ''),
                    'pages': pages,
                    'note': 'Download Excel files directly to preserve embedded images'
                })
                
        except urllib.error.HTTPError as e:
            if e.code == 404:
                self.send_error_response(404, f'No data available for date {date_str}')
            else:
                self.send_error_response(500, f'Error fetching data: {str(e)}')
        except Exception as e:
            self.send_error_response(500, f'Server error: {str(e)}')
    
    def send_page_url(self, date_str, page_num):
        """Get direct download URL for a specific page"""
        try:
            page_num = int(page_num)
        except:
            self.send_error_response(400, 'Invalid page number')
            return
        
        # Build expected filename
        filename = f"eu_trademarks_{date_str}_page_{page_num:03d}.xlsx"
        file_url = f"{GITHUB_RAW_URL}/data/{date_str}/{filename}"
        
        # Check if file exists by trying to fetch manifest
        manifest_url = f"{GITHUB_RAW_URL}/data/{date_str}/manifest.json"
        
        try:
            with urllib.request.urlopen(manifest_url) as response:
                manifest = json.loads(response.read().decode())
                
                # Check if this page exists in manifest
                if filename in manifest.get('files', []):
                    self.send_json_response({
                        'success': True,
                        'page_number': page_num,
                        'filename': filename,
                        'download_url': file_url,
                        'date': date_str,
                        'has_images': True
                    })
                else:
                    self.send_error_response(404, f'Page {page_num} not found for date {date_str}')
                    
        except urllib.error.HTTPError:
            self.send_error_response(404, f'No data available for date {date_str}')
        except Exception as e:
            self.send_error_response(500, f'Server error: {str(e)}')