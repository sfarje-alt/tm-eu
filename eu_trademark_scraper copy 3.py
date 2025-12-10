import os
import time
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import glob
import shutil

class EUTrademarkScraper:
    def __init__(self, download_dir=None, headless=True):
        """Initialize the scraper with Chrome WebDriver"""
        self.download_dir = download_dir or os.path.join(os.getcwd(), 'downloads')
        os.makedirs(self.download_dir, exist_ok=True)
        
        # Setup Chrome options
        self.chrome_options = Options()
        if headless:
            self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        
        # Configure download directory
        prefs = {
            'download.default_directory': self.download_dir,
            'download.prompt_for_download': False,
            'download.directory_upgrade': True,
            'safebrowsing.enabled': True
        }
        self.chrome_options.add_experimental_option('prefs', prefs)
        
    def get_date_range(self, date=None):
        """Format date range for URL (default: today)"""
        if date is None:
            date = datetime.now()
        date_str = date.strftime('%d/%m/%Y')
        # URL encode the date
        date_encoded = date_str.replace('/', '%2F')
        return f"{date_encoded}%20-%20{date_encoded}"
    
    def build_url(self, page_number, date_range):
        """Build the search URL with pagination and date filter"""
        base_url = "https://euipo.europa.eu/eSearch/#advanced/trademarks"
        return f"{base_url}/{page_number}/100/n1=PublicationDate&v1={date_range}&o1=AND&sf=ApplicationNumber&so=asc"
    
    def wait_for_download(self, timeout=30):
        """Wait for download to complete"""
        end_time = time.time() + timeout
        while time.time() < end_time:
            files = glob.glob(os.path.join(self.download_dir, '*.xlsx'))
            if files and not any(f.endswith('.crdownload') or f.endswith('.tmp') 
                                for f in glob.glob(os.path.join(self.download_dir, '*'))):
                time.sleep(1)  # Extra wait to ensure file is fully written
                return True
            time.sleep(0.5)
        return False
    
    def clear_downloads(self):
        """Clear the downloads directory"""
        for file in glob.glob(os.path.join(self.download_dir, '*')):
            try:
                os.remove(file)
            except:
                pass
    
    def scrape_page(self, driver, page_number, date_range):
        """Scrape a single page and download the Excel file"""
        url = self.build_url(page_number, date_range)
        print(f"Scraping page {page_number}: {url}")
        
        # Navigate to the page
        driver.get(url)
        print("Waiting for page to fully load...")
        time.sleep(10)  # Initial wait for page load
        
        try:
            # Wait for results to appear - wait for any element that indicates results are loaded
            wait = WebDriverWait(driver, 30)
            
            # Wait for the results section to be present
            print("Waiting for results to appear...")
            try:
                # Wait for either results or no-results message
                wait.until(lambda d: d.find_elements(By.CSS_SELECTOR, '.hit-list-item, .no-results, div[class*="result"]'))
                print("Results section loaded")
            except:
                print("Timeout waiting for results")
            
            # Check if there are no results
            try:
                no_results = driver.find_element(By.CLASS_NAME, "no-results")
                if no_results.is_displayed():
                    print(f"No results on page {page_number}")
                    return None
            except:
                print("Results found, proceeding...")
            
            # Extra wait for JavaScript to fully render
            time.sleep(5)
            
            # Try multiple methods to find and click the "Select All" checkbox
            clicked = False
            
            # List of selectors to try
            selectors = [
                ('XPATH', '/html/body/div[1]/div/div/div/section[2]/div/div/div/div[4]/div[1]/div[3]/label/span'),
                ('XPATH', '/html/body/div[1]/div/div/div/section[2]/div/div/div/div[4]/div[1]/div[3]/label'),
                ('ID', 'selectAll_view145_top'),
                ('CSS', 'input[name="selectAll"]'),
                ('CSS', 'label[for*="selectAll"]'),
                ('CSS', '.select-all-wrap label'),
                ('CSS', '.checkbox input[type="checkbox"]'),
            ]
            
            for selector_type, selector in selectors:
                if clicked:
                    break
                    
                try:
                    print(f"Trying {selector_type}: {selector[:50]}...")
                    
                    if selector_type == 'XPATH':
                        element = driver.find_element(By.XPATH, selector)
                    elif selector_type == 'ID':
                        element = driver.find_element(By.ID, selector)
                    else:  # CSS
                        element = driver.find_element(By.CSS_SELECTOR, selector)
                    
                    # Try JavaScript click
                    driver.execute_script("arguments[0].click();", element)
                    clicked = True
                    print(f"✅ Successfully clicked using {selector_type}")
                    
                except Exception as e:
                    # Try scrolling to element and clicking
                    try:
                        if selector_type == 'XPATH':
                            element = driver.find_element(By.XPATH, selector)
                        elif selector_type == 'ID':
                            element = driver.find_element(By.ID, selector)
                        else:
                            element = driver.find_element(By.CSS_SELECTOR, selector)
                        
                        driver.execute_script("arguments[0].scrollIntoView(true);", element)
                        time.sleep(1)
                        element.click()
                        clicked = True
                        print(f"✅ Successfully clicked after scrolling using {selector_type}")
                    except:
                        continue
            
            if not clicked:
                print("❌ Could not click select all checkbox")
                driver.save_screenshot('debug_no_select.png')
                print("Screenshot saved as debug_no_select.png")
                
                # Try to proceed anyway - maybe it's already selected
                print("Attempting to proceed without selecting all...")
            else:
                print("✅ Selected all items")
                time.sleep(3)  # Wait for export button to become enabled
            
            # Clear previous downloads
            self.clear_downloads()
            
            # Click Export .xlsx button
            try:
                print("Looking for export button...")
                
                # Try multiple selectors for export button
                export_selectors = [
                    'a.btn.exportXLSX',
                    'a[href*="resultsxls"]',
                    '.exportXLSX',
                    'a[data-url*="resultsxls"]'
                ]
                
                export_clicked = False
                for selector in export_selectors:
                    if export_clicked:
                        break
                    try:
                        export_button = driver.find_element(By.CSS_SELECTOR, selector)
                        driver.execute_script("arguments[0].click();", export_button)
                        export_clicked = True
                        print(f"✅ Clicked export button using selector: {selector}")
                    except:
                        continue
                
                if not export_clicked:
                    print("❌ Could not click export button")
                    driver.save_screenshot('debug_no_export.png')
                    return None
                    
            except Exception as e:
                print(f"❌ Export button error: {e}")
                driver.save_screenshot('debug_export_error.png')
                return None
            
            # Wait for download to complete
            if self.wait_for_download():
                # Get the downloaded file
                files = glob.glob(os.path.join(self.download_dir, '*.xlsx'))
                if files:
                    # Rename file to include page number
                    new_name = os.path.join(self.download_dir, f'page_{page_number}.xlsx')
                    shutil.move(files[0], new_name)
                    print(f"✅ Downloaded and saved: page_{page_number}.xlsx")
                    return new_name
            else:
                print(f"❌ Download timeout for page {page_number}")
                return None
                
        except Exception as e:
            print(f"Error on page {page_number}: {e}")
            driver.save_screenshot('debug_error.png')
            print("Screenshot saved as debug_error.png")
            return None
    
    def merge_excel_files(self, excel_files, output_file='merged_trademarks.xlsx'):
        """Merge multiple Excel files into one"""
        if not excel_files:
            print("No Excel files to merge")
            return None
        
        dfs = []
        for file in excel_files:
            try:
                df = pd.read_excel(file)
                dfs.append(df)
                print(f"Loaded {file}: {len(df)} rows")
            except Exception as e:
                print(f"Error reading {file}: {e}")
        
        if dfs:
            merged_df = pd.concat(dfs, ignore_index=True)
            
            # Remove duplicates if any (based on all columns)
            merged_df = merged_df.drop_duplicates()
            
            # Save to file
            output_path = os.path.join(self.download_dir, output_file)
            merged_df.to_excel(output_path, index=False)
            print(f"Merged {len(dfs)} files into {output_file}")
            print(f"Total rows: {len(merged_df)}")
            return output_path
        
        return None
    
    def scrape_all_pages(self, date=None, max_pages=100):
        """Main method to scrape all pages for a given date"""
        date_range = self.get_date_range(date)
        downloaded_files = []
        
        # Initialize driver
        driver = webdriver.Chrome(options=self.chrome_options)
        
        try:
            for page_num in range(1, max_pages + 1):
                file_path = self.scrape_page(driver, page_num, date_range)
                
                if file_path:
                    downloaded_files.append(file_path)
                else:
                    # No more results, stop scraping
                    print(f"Stopping at page {page_num} (no results or error)")
                    break
                
                # Close current tab and open new one for next page
                if page_num < max_pages:
                    driver.close()
                    driver.quit()
                    time.sleep(2)
                    driver = webdriver.Chrome(options=self.chrome_options)
            
            # Merge all Excel files
            if downloaded_files:
                date_str = date.strftime('%Y%m%d') if date else datetime.now().strftime('%Y%m%d')
                output_file = f'eu_trademarks_{date_str}.xlsx'
                merged_file = self.merge_excel_files(downloaded_files, output_file)
                
                # Also save as JSON for API access
                if merged_file:
                    df = pd.read_excel(merged_file)
                    json_path = merged_file.replace('.xlsx', '.json')
                    df.to_json(json_path, orient='records', date_format='iso')
                    print(f"Also saved as JSON: {json_path}")
                
                # Clean up individual files
                for file in downloaded_files:
                    try:
                        os.remove(file)
                    except:
                        pass
                
                return merged_file
            else:
                print("No files downloaded")
                return None
                
        finally:
            driver.quit()

def run_daily_scrape():
    """Function to run the daily scrape"""
    scraper = EUTrademarkScraper(headless=False)  # Keep False to see what's happening
    result = scraper.scrape_all_pages(date=datetime.now())
    
    if result:
        print(f"Successfully scraped data to: {result}")
        return result
    else:
        print("Scraping failed")
        return None

if __name__ == "__main__":
    # Run the scraper
    run_daily_scrape()