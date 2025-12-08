from http.server import BaseHTTPRequestHandler
import json
from datetime import datetime
import urllib.request
from urllib.parse import urlparse, parse_qs

# IMPORTANT: Update this with your GitHub username
GITHUB_USER = "sfarje-alt"
GITHUB_REPO = "tm-eu"
GITHUB_BRANCH = "main"

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
        elif path == '/api/trademarks/today':
            self.send_today_data()
        elif path.startswith('/api/trademarks/'):
            date_str = path.split('/')[-1]
            self.send_date_data(date_str)
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
            'version': '1.0.0',
            'endpoints': {
                'GET /api/status': 'Check API status',
                'GET /api/trademarks/today': 'Get today\'s trademark data',
                'GET /api/trademarks/YYYYMMDD': 'Get trademark data for specific date'
            },
            'github_repo': f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}"
        })
    
    def send_status(self):
        """Check API and data status"""
        today = datetime.now().strftime('%Y%m%d')
        
        # Check if today's data exists
        json_url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/data/eu_trademarks_{today}.json"
        
        try:
            with urllib.request.urlopen(json_url) as response:
                data_available = response.status == 200
        except:
            data_available = False
        
        self.send_json_response({
            'api_status': 'online',
            'today_data_available': data_available,
            'date': today,
            'github_repo': f"{GITHUB_USER}/{GITHUB_REPO}"
        })
    
    def send_today_data(self):
        """Get today's trademark data"""
        today = datetime.now().strftime('%Y%m%d')
        self.send_date_data(today)
    
    def send_date_data(self, date_str):
        """Get trademark data for a specific date"""
        json_url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/data/eu_trademarks_{date_str}.json"
        
        try:
            with urllib.request.urlopen(json_url) as response:
                data = json.loads(response.read().decode())
                self.send_json_response({
                    'date': date_str,
                    'total_records': len(data),
                    'source': 'github',
                    'data': data
                })
        except urllib.error.HTTPError as e:
            if e.code == 404:
                self.send_error_response(404, f'No data available for date {date_str}')
            else:
                self.send_error_response(500, f'Error fetching data: {str(e)}')
        except Exception as e:
            self.send_error_response(500, f'Server error: {str(e)}')
