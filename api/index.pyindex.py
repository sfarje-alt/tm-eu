from flask import Flask, jsonify, request
import requests
from datetime import datetime
import json

app = Flask(__name__)

# IMPORTANT: Update this with your GitHub username and repository name
GITHUB_USER = "YOUR_GITHUB_USERNAME"  # <-- CHANGE THIS
GITHUB_REPO = "eu-trademark-scraper"
GITHUB_BRANCH = "main"

def get_github_file_url(filename):
    """Generate GitHub raw content URL"""
    return f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/data/{filename}"

@app.route('/')
def home():
    """API documentation"""
    return jsonify({
        'name': 'EU Trademark Scraper API',
        'version': '1.0.0',
        'endpoints': {
            'GET /api/status': 'Check API status',
            'GET /api/trademarks/today': 'Get today\'s trademark data',
            'GET /api/trademarks/<YYYYMMDD>': 'Get trademark data for specific date',
            'GET /api/trademarks/search': 'Search trademarks with filters',
            'GET /api/available-dates': 'Get list of available dates'
        },
        'github_repo': f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}"
    })

@app.route('/api/status')
def status():
    """Check API and data status"""
    today = datetime.now().strftime('%Y%m%d')
    
    # Check if today's data exists
    json_url = get_github_file_url(f"eu_trademarks_{today}.json")
    response = requests.head(json_url)
    
    return jsonify({
        'api_status': 'online',
        'today_data_available': response.status_code == 200,
        'date': today,
        'github_repo': f"{GITHUB_USER}/{GITHUB_REPO}"
    })

@app.route('/api/trademarks/today')
def get_today():
    """Get today's trademark data"""
    today = datetime.now().strftime('%Y%m%d')
    return get_trademarks_by_date(today)

@app.route('/api/trademarks/<date_str>')
def get_trademarks_by_date(date_str):
    """Get trademark data for a specific date"""
    # Try JSON first (faster)
    json_url = get_github_file_url(f"eu_trademarks_{date_str}.json")
    
    response = requests.get(json_url)
    
    if response.status_code == 200:
        try:
            data = response.json()
            return jsonify({
                'date': date_str,
                'total_records': len(data),
                'source': 'github',
                'data': data
            })
        except:
            return jsonify({'error': 'Invalid data format'}), 500
    else:
        return jsonify({'error': f'No data available for date {date_str}'}), 404

@app.route('/api/trademarks/search')
def search_trademarks():
    """Search trademarks with filters"""
    date = request.args.get('date', datetime.now().strftime('%Y%m%d'))
    trademark_name = request.args.get('name', '').lower()
    applicant = request.args.get('applicant', '').lower()
    status = request.args.get('status', '').lower()
    
    # Get data for the specified date
    json_url = get_github_file_url(f"eu_trademarks_{date}.json")
    response = requests.get(json_url)
    
    if response.status_code != 200:
        return jsonify({'error': f'No data available for date {date}'}), 404
    
    try:
        data = response.json()
        
        # Apply filters
        filtered_data = []
        for item in data:
            # Check trademark name
            if trademark_name and trademark_name not in str(item.get('TradeMark', '')).lower():
                continue
            
            # Check applicant
            if applicant and applicant not in str(item.get('Applicant', '')).lower():
                continue
            
            # Check status  
            if status and status not in str(item.get('Status', '')).lower():
                continue
            
            filtered_data.append(item)
        
        return jsonify({
            'date': date,
            'filters': {
                'name': trademark_name,
                'applicant': applicant,
                'status': status
            },
            'total_records': len(filtered_data),
            'data': filtered_data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/available-dates')
def get_available_dates():
    """Get list of dates with available data"""
    # This endpoint would need to query GitHub API to list files
    # For now, return a helpful message
    return jsonify({
        'message': 'Check the GitHub repository for available dates',
        'github_url': f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}/tree/{GITHUB_BRANCH}/data",
        'note': 'Look for files named eu_trademarks_YYYYMMDD.json'
    })

@app.route('/api/download/<date_str>')
def download_excel(date_str):
    """Provide download link for Excel file"""
    excel_url = get_github_file_url(f"eu_trademarks_{date_str}.xlsx")
    
    # Check if file exists
    response = requests.head(excel_url)
    if response.status_code == 200:
        return jsonify({
            'download_url': excel_url,
            'filename': f"eu_trademarks_{date_str}.xlsx",
            'message': 'Use the download_url to get the Excel file'
        })
    else:
        return jsonify({'error': f'No Excel file available for date {date_str}'}), 404

# Vercel serverless function handler
def handler(request, response):
    with app.test_request_context(
        path=request.path,
        method=request.method,
        headers=request.headers,
        data=request.body,
        query_string=request.query_string
    ):
        try:
            rv = app.dispatch_request()
            response_data = rv.get_json() if hasattr(rv, 'get_json') else rv
            response.status_code = 200
            response.headers['Content-Type'] = 'application/json'
            return json.dumps(response_data)
        except Exception as e:
            response.status_code = 500
            return json.dumps({'error': str(e)})

# For local testing
if __name__ == '__main__':
    app.run(debug=True)
