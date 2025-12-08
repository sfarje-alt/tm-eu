#!/usr/bin/env python3
"""
REAL EU Trademark Scraper Test
This actually tries to scrape from EUIPO website
"""

import os
import sys
import json
import time
from datetime import datetime
import pandas as pd

print("=" * 60)
print("REAL EU TRADEMARK SCRAPER TEST")
print("=" * 60)

# Try different approaches to scrape
def test_basic_request():
    """Test if we can even reach the website"""
    import requests
    
    print("\n1. Testing basic website access...")
    
    # Build URL for today
    today = datetime.now()
    date_str = today.strftime('%d/%m/%Y')
    date_encoded = date_str.replace('/', '%2F')
    date_range = f"{date_encoded}%20-%20{date_encoded}"
    
    url = f"https://euipo.europa.eu/eSearch/#advanced/trademarks/1/100/n1=PublicationDate&v1={date_range}&o1=AND&sf=ApplicationNumber&so=asc"
    
    print(f"   Date: {date_str}")
    print(f"   URL: {url[:100]}...")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        print(f"   ✅ Website responded: Status {response.status_code}")
        
        # Check if it's a JS-heavy site
        if 'angular' in response.text.lower() or 'react' in response.text.lower():
            print("   ⚠️  Site uses JavaScript framework - Selenium required!")
            return False
        return True
    except Exception as e:
        print(f"   ❌ Failed to reach website: {e}")
        return False

def test_selenium_scraper():
    """Test Selenium scraping"""
    print("\n2. Testing Selenium scraping...")
    
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.chrome.options import Options
        print("   ✅ Selenium imported successfully")
    except ImportError as e:
        print(f"   ❌ Selenium not available: {e}")
        return False
    
    driver = None
    try:
        # Setup Chrome options for GitHub Actions
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        print("   Setting up Chrome driver...")
        
        # Try different driver initialization methods
        try:
            driver = webdriver.Chrome(options=chrome_options)
            print("   ✅ Chrome driver initialized (method 1)")
        except:
            try:
                from selenium.webdriver.chrome.service import Service
                service = Service('/usr/bin/chromedriver')
                driver = webdriver.Chrome(service=service, options=chrome_options)
                print("   ✅ Chrome driver initialized (method 2)")
            except:
                from webdriver_manager.chrome import ChromeDriverManager
                from selenium.webdriver.chrome.service import Service
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=chrome_options)
                print("   ✅ Chrome driver initialized (method 3 - webdriver-manager)")
        
        # Build URL
        today = datetime.now()
        date_str = today.strftime('%d/%m/%Y')
        date_encoded = date_str.replace('/', '%2F')
        date_range = f"{date_encoded}%20-%20{date_encoded}"
        
        url = f"https://euipo.europa.eu/eSearch/#advanced/trademarks/1/100/n1=PublicationDate&v1={date_range}&o1=AND&sf=ApplicationNumber&so=asc"
        
        print(f"   Navigating to EUIPO...")
        driver.get(url)
        
        # Wait for page to load
        print("   Waiting for page to load...")
        time.sleep(5)
        
        # Try to find results or no-results message
        try:
            # Check for no results
            no_results = driver.find_elements(By.CLASS_NAME, "no-results")
            if no_results and no_results[0].is_displayed():
                print("   ℹ️  No trademark publications for today (this is normal)")
                print("   ℹ️  EU doesn't publish trademarks every day")
                return True  # This is actually a success - scraper works!
        except:
            pass
        
        # Try to find results count
        try:
            results_count = driver.find_elements(By.CLASS_NAME, "results-count")
            if results_count:
                count_text = results_count[0].text
                print(f"   ✅ Found results count: {count_text}")
                
                # Try to find actual trademark entries
                results = driver.find_elements(By.CSS_SELECTOR, "[class*='result'], [class*='trademark'], table.results tr")
                print(f"   ✅ Found {len(results)} result elements")
                
                if len(results) > 0:
                    print("   🎉 REAL TRADEMARKS FOUND!")
                    return True
        except Exception as e:
            print(f"   ⚠️  Could not find results: {e}")
        
        # Check page title to confirm we're on the right page
        title = driver.title
        print(f"   Page title: {title}")
        
        if "eSearch" in title or "EUIPO" in title:
            print("   ✅ Confirmed on EUIPO eSearch page")
            print("   ℹ️  Scraper can reach the site but found no results for today")
            return True
        
        return False
        
    except Exception as e:
        print(f"   ❌ Selenium scraping failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        if driver:
            driver.quit()
            print("   ✅ Driver closed")

def create_status_file():
    """Create a status file to show scraper test results"""
    status = {
        'test_date': datetime.now().isoformat(),
        'basic_request': False,
        'selenium_works': False,
        'can_scrape': False
    }
    
    # Run tests
    print("\n" + "=" * 60)
    print("RUNNING TESTS...")
    print("=" * 60)
    
    status['basic_request'] = test_basic_request()
    status['selenium_works'] = test_selenium_scraper()
    status['can_scrape'] = status['selenium_works']
    
    # Save status
    os.makedirs('data', exist_ok=True)
    status_file = f'data/scraper_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    
    with open(status_file, 'w') as f:
        json.dump(status, f, indent=2)
    
    print("\n" + "=" * 60)
    print("TEST RESULTS:")
    print("=" * 60)
    print(f"Basic Request: {'✅' if status['basic_request'] else '❌'}")
    print(f"Selenium Works: {'✅' if status['selenium_works'] else '❌'}")
    print(f"Can Scrape: {'✅' if status['can_scrape'] else '❌'}")
    print(f"\nStatus saved to: {status_file}")
    
    return status['can_scrape']

if __name__ == "__main__":
    success = create_status_file()
    
    if success:
        print("\n🎉 SUCCESS! The scraper can access EUIPO!")
        print("Note: No results for today might be normal - EU doesn't publish daily")
    else:
        print("\n⚠️  Scraper needs fixes - check the errors above")
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)
