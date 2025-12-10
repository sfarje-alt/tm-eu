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
        # Use Mac's default Downloads folder
        self.download_dir = download_dir or os.path.expanduser('~/Downloads')
        
        # Setup Chrome options
        self.chrome_options = Options()
        if headless:
            self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        
        # Configure download directory - force Chrome to use our directory
        prefs = {
            'download.default_directory': self.download_dir,
            'download.prompt_for_download': False,
            'download.directory_upgrade': True,
            'safebrowsing.enabled': True,
            'safebrowsing.disable_download_protection': True
        }
        self.chrome_options.add_experimental_option('prefs', prefs)
        
        # Add this to ensure downloads work properly
        self.chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
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
        print(f"Waiting for download in: {self.download_dir}")
        end_time = time.time() + timeout
        while time.time() < end_time:
            # Check for any .xlsx files
            files = glob.glob(os.path.join(self.download_dir, '*.xlsx'))
            # Also check for Excel temp files
            temp_files = glob.glob(os.path.join(self.download_dir, '*.xlsx.crdownload')) + \
                        glob.glob(os.path.join(self.download_dir, '*.tmp'))
            
            if files and not temp_files:
                # Found complete file and no temp files
                print(f"✅ Download completed: {files[0]}")
                time.sleep(2)  # Extra wait to ensure file is fully written
                return True
            
            # Show progress
            if temp_files:
                print("⏳ Download in progress...")
            
            time.sleep(1)
        
        # Check one more time
        files = glob.glob(os.path.join(self.download_dir, '*.xlsx'))
        if files:
            print(f"✅ Found downloaded file: {files[0]}")
            return True
            
        return False
    
    def clear_downloads(self):
        """Clear Excel files from the downloads directory"""
        # Only clear Excel files to avoid deleting other downloads
        for file in glob.glob(os.path.join(self.download_dir, '*.xlsx')):
            try:
                # Skip if it's our output file
                if 'eu_trademarks_' in file and 'page_' not in file:
                    continue
                os.remove(file)
                print(f"Cleared old file: {file}")
            except:
                pass
    
    def scrape_page(self, driver, page_number, date_range):
        """Scrape a single page and download the Excel file"""
        url = self.build_url(page_number, date_range)
        print(f"\n{'='*60}")
        print(f"Scraping page {page_number}")
        print(f"URL: {url}")
        print('='*60)
        
        # Navigate to the page
        driver.get(url)
        print("Waiting for page to fully load...")
        time.sleep(10)  # Initial wait for page load
        
        try:
            # Wait for results to appear
            wait = WebDriverWait(driver, 30)
            
            print("Waiting for results to appear...")
            try:
                wait.until(lambda d: d.find_elements(By.CSS_SELECTOR, '.hit-list-item, .no-results, div[class*="result"]'))
                print("Results section loaded")
            except:
                print("Timeout waiting for results")
            
            # Check if there are no results
            try:
                no_results = driver.find_element(By.CLASS_NAME, "no-results")
                if no_results.is_displayed():
                    print(f"❌ No results on page {page_number}")
                    return None
            except:
                print("✅ Results found, proceeding...")
            
            # Extra wait for JavaScript to fully render
            time.sleep(5)
            
            # Click Select All
            clicked = False
            
            selectors = [
                ('XPATH', '/html/body/div[1]/div/div/div/section[2]/div/div/div/div[4]/div[1]/div[3]/label/span'),
                ('XPATH', '/html/body/div[1]/div/div/div/section[2]/div/div/div/div[4]/div[1]/div[3]/label'),
                ('ID', 'selectAll_view145_top'),
                ('CSS', 'input[name="selectAll"]'),
            ]
            
            for selector_type, selector in selectors:
                if clicked:
                    break
                    
                try:
                    if selector_type == 'XPATH':
                        element = driver.find_element(By.XPATH, selector)
                    elif selector_type == 'ID':
                        element = driver.find_element(By.ID, selector)
                    else:
                        element = driver.find_element(By.CSS_SELECTOR, selector)
                    
                    driver.execute_script("arguments[0].click();", element)
                    clicked = True
                    print(f"✅ Selected all items using {selector_type}")
                    break
                except:
                    continue
            
            if not clicked:
                print("⚠️ Could not click select all - proceeding anyway")
            
            time.sleep(3)  # Wait for export button to become enabled
            
            # Clear previous downloads
            self.clear_downloads()
            
            # Click Export button
            try:
                export_button = driver.find_element(By.CSS_SELECTOR, 'a.btn.exportXLSX')
                driver.execute_script("arguments[0].click();", export_button)
                print("✅ Clicked export button")
            except Exception as e:
                print(f"❌ Could not click export button: {e}")
                return None
            
            # Wait for download
            if self.wait_for_download(timeout=60):  # Increased timeout
                # Find the downloaded file
                files = glob.glob(os.path.join(self.download_dir, '*.xlsx'))
                # Filter out our output files
                files = [f for f in files if 'eu_trademarks_' not in os.path.basename(f) or 'page_' in os.path.basename(f)]
                
                if files:
                    # Get the newest file
                    newest_file = max(files, key=os.path.getctime)
                    
                    # Create output directory if needed
                    output_dir = os.path.join(os.getcwd(), 'downloads')
                    os.makedirs(output_dir, exist_ok=True)
                    
                    # Move and rename file
                    new_name = os.path.join(output_dir, f'page_{page_number}.xlsx')
                    shutil.move(newest_file, new_name)
                    print(f"✅ Saved as: {new_name}")
                    return new_name
            else:
                print(f"❌ Download timeout for page {page_number}")
                # Check if file exists anyway
                files = glob.glob(os.path.join(self.download_dir, '*.xlsx'))
                if files:
                    print(f"Found file despite timeout: {files[0]}")
                    # Try to use it anyway
                    output_dir = os.path.join(os.getcwd(), 'downloads')
                    os.makedirs(output_dir, exist_ok=True)
                    new_name = os.path.join(output_dir, f'page_{page_number}.xlsx')
                    shutil.move(files[0], new_name)
                    return new_name
                return None
                
        except Exception as e:
            print(f"Error on page {page_number}: {e}")
            return None
    
    def merge_excel_files(self, excel_files, output_file='merged_trademarks.xlsx'):
        """Merge multiple Excel files into one"""
        if not excel_files:
            print("No Excel files to merge")
            return None
        
        print(f"\n{'='*60}")
        print("Merging Excel files...")
        print('='*60)
        
        dfs = []
        for file in excel_files:
            try:
                df = pd.read_excel(file)
                dfs.append(df)
                print(f"Loaded {os.path.basename(file)}: {len(df)} rows")
            except Exception as e:
                print(f"Error reading {file}: {e}")
        
        if dfs:
            merged_df = pd.concat(dfs, ignore_index=True)
            merged_df = merged_df.drop_duplicates()
            
            output_dir = os.path.join(os.getcwd(), 'downloads')
            output_path = os.path.join(output_dir, output_file)
            merged_df.to_excel(output_path, index=False)
            print(f"\n✅ Merged {len(dfs)} files into {output_file}")
            print(f"📊 Total rows: {len(merged_df)}")
            return output_path
        
        return None
    
    def scrape_all_pages(self, date=None, max_pages=100):
        """Main method to scrape all pages for a given date"""
        date_range = self.get_date_range(date)
        downloaded_files = []
        
        # Initialize driver once - don't recreate for each page
        driver = webdriver.Chrome(options=self.chrome_options)
        
        try:
            # Calculate total pages (1735 results / 100 per page = 18 pages)
            expected_pages = 18  # Based on the 1735 results you saw
            
            for page_num in range(1, min(expected_pages + 1, max_pages + 1)):
                file_path = self.scrape_page(driver, page_num, date_range)
                
                if file_path:
                    downloaded_files.append(file_path)
                    print(f"✅ Page {page_num} completed successfully")
                    
                    # Continue to next page
                    if page_num < expected_pages:
                        print(f"\n➡️ Moving to page {page_num + 1}...")
                        time.sleep(3)  # Brief pause between pages
                else:
                    # Only stop if we're sure there are no more results
                    print(f"⚠️ Page {page_num} failed - checking if there are more pages...")
                    
                    # Try to check if there's a next page
                    try:
                        # Check if we're on the last page
                        next_url = self.build_url(page_num + 1, date_range)
                        driver.get(next_url)
                        time.sleep(5)
                        
                        no_results = driver.find_elements(By.CLASS_NAME, "no-results")
                        if no_results and no_results[0].is_displayed():
                            print(f"✅ Reached end of results at page {page_num}")
                            break
                        else:
                            print(f"⚠️ More pages exist, continuing...")
                    except:
                        break
            
            # Merge all Excel files
            if downloaded_files:
                date_str = date.strftime('%Y%m%d') if date else datetime.now().strftime('%Y%m%d')
                output_file = f'eu_trademarks_{date_str}.xlsx'
                merged_file = self.merge_excel_files(downloaded_files, output_file)
                
                # Also save as JSON
                if merged_file:
                    df = pd.read_excel(merged_file)
                    json_path = merged_file.replace('.xlsx', '.json')
                    df.to_json(json_path, orient='records', date_format='iso')
                    print(f"📄 Also saved as JSON: {json_path}")
                
                # Clean up individual page files
                for file in downloaded_files:
                    try:
                        os.remove(file)
                    except:
                        pass
                
                return merged_file
            else:
                print("❌ No files downloaded")
                return None
                
        finally:
            driver.quit()

def run_daily_scrape():
    """Function to run the daily scrape"""
    scraper = EUTrademarkScraper(headless=False)
    result = scraper.scrape_all_pages(date=datetime.now())
    
    if result:
        print(f"\n{'='*60}")
        print(f"🎉 SUCCESS! Scraped data saved to:")
        print(f"📁 {result}")
        print('='*60)
        return result
    else:
        print("\n❌ Scraping failed")
        return None

if __name__ == "__main__":
    run_daily_scrape()