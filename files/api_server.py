from flask import Flask, jsonify, send_file, request
from flask_cors import CORS
import os
import glob
import pandas as pd
from datetime import datetime, timedelta
import threading
import schedule
import time
from eu_trademark_scraper import EUTrademarkScraper
import json

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
DATA_DIR = os.path.join(os.getcwd(), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

# Global variable to track scraping status
scraping_status = {
    'is_running': False,
    'last_run': None,
    'last_success': None,
    'last_error': None,
    'total_records': 0
}

def get_latest_file():
    """Get the most recent trademark data file"""
    files = glob.glob(os.path.join(DATA_DIR, 'eu_trademarks_*.xlsx'))
    if files:
        return max(files, key=os.path.getctime)
    return None

def scrape_job():
    """Job to run the scraper"""
    global scraping_status
    
    if scraping_status['is_running']:
        print("Scraping already in progress, skipping...")
        return
    
    print(f"Starting daily scrape at {datetime.now()}")
    scraping_status['is_running'] = True
    scraping_status['last_run'] = datetime.now().isoformat()
    
    try:
        scraper = EUTrademarkScraper(download_dir=DATA_DIR, headless=True)
        result_file = scraper.scrape_all_pages(date=datetime.now())
        
        if result_file:
            # Count records in the file
            df = pd.read_excel(result_file)
            scraping_status['total_records'] = len(df)
            scraping_status['last_success'] = datetime.now().isoformat()
            scraping_status['last_error'] = None
            print(f"Scraping completed successfully: {scraping_status['total_records']} records")
        else:
            scraping_status['last_error'] = "No data retrieved"
            
    except Exception as e:
        scraping_status['last_error'] = str(e)
        print(f"Scraping failed: {e}")
    finally:
        scraping_status['is_running'] = False

def run_scheduler():
    """Background thread to run scheduled jobs"""
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

# API Routes

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get the current scraping status"""
    return jsonify(scraping_status)

@app.route('/api/scrape', methods=['POST'])
def trigger_scrape():
    """Manually trigger a scrape"""
    if scraping_status['is_running']:
        return jsonify({'error': 'Scraping already in progress'}), 400
    
    # Run scrape in background thread
    thread = threading.Thread(target=scrape_job)
    thread.daemon = True
    thread.start()
    
    return jsonify({'message': 'Scraping started', 'status': scraping_status})

@app.route('/api/trademarks/today', methods=['GET'])
def get_todays_trademarks():
    """Get today's trademark data as JSON"""
    today = datetime.now().strftime('%Y%m%d')
    file_path = os.path.join(DATA_DIR, f'eu_trademarks_{today}.xlsx')
    
    if not os.path.exists(file_path):
        # Try to find the latest file
        import glob
        files = glob.glob(os.path.join(DATA_DIR, 'eu_trademarks_*.xlsx'))
        if files:
            file_path = max(files, key=os.path.getctime)
        else:
            return jsonify({'error': 'No data available. Please run /api/scrape first'}), 404
    
    try:
        df = pd.read_excel(file_path)
        # Convert to JSON
        data = df.to_dict(orient='records')
        
        return jsonify({
            'date': today,
            'total_records': len(data),
            'data': data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/trademarks/date/<date_str>', methods=['GET'])
def get_trademarks_by_date(date_str):
    """Get trademark data for a specific date (format: YYYYMMDD)"""
    file_path = os.path.join(DATA_DIR, f'eu_trademarks_{date_str}.xlsx')
    
    if not os.path.exists(file_path):
        return jsonify({'error': f'No data available for date {date_str}'}), 404
    
    try:
        df = pd.read_excel(file_path)
        data = df.to_dict(orient='records')
        
        return jsonify({
            'date': date_str,
            'total_records': len(data),
            'data': data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/trademarks/download/<date_str>', methods=['GET'])
def download_trademarks(date_str):
    """Download the Excel file for a specific date"""
    file_path = os.path.join(DATA_DIR, f'eu_trademarks_{date_str}.xlsx')
    
    if not os.path.exists(file_path):
        return jsonify({'error': f'No file available for date {date_str}'}), 404
    
    return send_file(file_path, as_attachment=True, download_name=f'eu_trademarks_{date_str}.xlsx')

@app.route('/api/trademarks/search', methods=['GET'])
def search_trademarks():
    """Search trademarks with filters"""
    date = request.args.get('date', datetime.now().strftime('%Y%m%d'))
    trademark_name = request.args.get('name', '').lower()
    applicant = request.args.get('applicant', '').lower()
    status = request.args.get('status', '').lower()
    
    file_path = os.path.join(DATA_DIR, f'eu_trademarks_{date}.xlsx')
    
    if not os.path.exists(file_path):
        return jsonify({'error': f'No data available for date {date}'}), 404
    
    try:
        df = pd.read_excel(file_path)
        
        # Apply filters
        if trademark_name:
            df = df[df['TradeMark'].str.lower().str.contains(trademark_name, na=False)]
        if applicant:
            df = df[df['Applicant'].str.lower().str.contains(applicant, na=False)]
        if status:
            df = df[df['Status'].str.lower().str.contains(status, na=False)]
        
        data = df.to_dict(orient='records')
        
        return jsonify({
            'date': date,
            'filters': {
                'name': trademark_name,
                'applicant': applicant,
                'status': status
            },
            'total_records': len(data),
            'data': data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/trademarks/available-dates', methods=['GET'])
def get_available_dates():
    """Get list of dates for which data is available"""
    import glob
    import re
    
    files = glob.glob(os.path.join(DATA_DIR, 'eu_trademarks_*.xlsx'))
    dates = []
    
    for file in files:
        match = re.search(r'eu_trademarks_(\d{8})\.xlsx', os.path.basename(file))
        if match:
            dates.append(match.group(1))
    
    return jsonify({
        'dates': sorted(dates, reverse=True),
        'count': len(dates)
    })

@app.route('/', methods=['GET'])
def home():
    """API documentation"""
    return jsonify({
        'name': 'EU Trademark Scraper API',
        'version': '1.0.0',
        'endpoints': {
            'GET /api/status': 'Get scraping status',
            'POST /api/scrape': 'Trigger manual scrape',
            'GET /api/trademarks/today': 'Get today\'s trademark data',
            'GET /api/trademarks/date/<YYYYMMDD>': 'Get trademark data for specific date',
            'GET /api/trademarks/download/<YYYYMMDD>': 'Download Excel file for specific date',
            'GET /api/trademarks/search': 'Search trademarks with filters',
            'GET /api/trademarks/available-dates': 'Get list of available dates'
        },
        'search_parameters': {
            'date': 'Date in YYYYMMDD format',
            'name': 'Trademark name (partial match)',
            'applicant': 'Applicant name (partial match)',
            'status': 'Status (partial match)'
        }
    })

if __name__ == '__main__':
    # Schedule daily scraping at 2 AM
    schedule.every().day.at("02:00").do(scrape_job)
    
    # Start scheduler in background thread
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    
    # Run initial scrape if no data exists
    import glob
    if not glob.glob(os.path.join(DATA_DIR, 'eu_trademarks_*.xlsx')):
        print("No existing data found. Running initial scrape...")
        thread = threading.Thread(target=scrape_job)
        thread.daemon = True
        thread.start()
    
    # Start Flask app
    app.run(host='0.0.0.0', port=5000, debug=False)
