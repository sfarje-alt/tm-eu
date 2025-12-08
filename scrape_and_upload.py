#!/usr/bin/env python3
"""
Simplified scraper for GitHub Actions
Runs the scraper and saves data to the repository
"""

import os
from datetime import datetime
from eu_trademark_scraper import EUTrademarkScraper
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def main():
    print(f"Starting EU Trademark scrape at {datetime.now()}")
    
    # Create data directory
    data_dir = os.path.join(os.getcwd(), 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    # Initialize scraper with headless Chrome
    scraper = EUTrademarkScraper(download_dir=data_dir, headless=True)
    
    # Override the Chrome driver initialization to use webdriver-manager
    original_init = webdriver.Chrome.__init__
    
    def new_init(self, options=None, *args, **kwargs):
        if options:
            service = Service(ChromeDriverManager().install())
            original_init(self, service=service, options=options)
        else:
            original_init(self, *args, **kwargs)
    
    webdriver.Chrome.__init__ = new_init
    
    # Run the scraper
    result = scraper.scrape_all_pages(date=datetime.now())
    
    if result:
        print(f"Successfully scraped data to: {result}")
        # Read the file to show statistics
        import pandas as pd
        df = pd.read_excel(result)
        print(f"Total records scraped: {len(df)}")
        print(f"Columns: {', '.join(df.columns.tolist())}")
    else:
        print("Scraping failed - no data retrieved")
        exit(1)

if __name__ == "__main__":
    main()