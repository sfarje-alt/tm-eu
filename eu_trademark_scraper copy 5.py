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
        # Use Mac's default Downloads folder for Chrome downloads
        self.temp_download_dir = os.path.expanduser('~/Downloads')
        
        # Project downloads folder for final files
        self.project_dir = os.getcwd()
        self.download_dir = download_dir or os.path.join(self.project_dir, 'downloads')
        os.makedirs(self.download_dir, exist_ok=True)
        
        # Setup Chrome options
        self.chrome_options = Options()
        if headless:
            self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        
        # Configure download directory
        prefs = {
            'download.default_directory': self.temp_download_dir,
            'download.prompt_for_download': False,
            'download.directory_upgrade': True,
            'safebrowsing.enabled': True,
            'safebrowsing.disable_download_protection': True
        }
        self.chrome_options.add_experimental_option('prefs', prefs)
        self.chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
    def get_date_range(self, date=None):
        """Format date range for URL (default: today)"""
        if date is None:
            date = datetime.now()
        self.current_date = date
        date_str = date.strftime('%d/%m/%Y')
        date_encoded = date_str.replace('/', '%2F')
        return f"{date_encoded}%20-%20{date_encoded}"
    
    def build_url(self, page_number, date_range):
        """Build the search URL with pagination and date filter"""
        base_url = "https://euipo.europa.eu/eSearch/#advanced/trademarks"
        return f"{base_url}/{page_number}/100/n1=PublicationDate&v1={date_range}&o1=AND&sf=ApplicationNumber&so=asc"
    
    def wait_for_download(self, timeout=30):
        """Wait for download to complete - handles both .xls and .xlsx"""
        print(f"Checking for download in: {self.temp_download_dir}")
        
        # Give it a moment to start downloading
        time.sleep(2)
        
        # Look for Excel files (BOTH .xls and .xlsx)
        end_time = time.time() + timeout
        while time.time() < end_time:
            # Get all Excel files - BOTH FORMATS
            xls_files = glob.glob(os.path.join(self.temp_download_dir, '*.xls'))
            xlsx_files = glob.glob(os.path.join(self.temp_download_dir, '*.xlsx'))
            excel_files = xls_files + xlsx_files
            
            if excel_files:
                # Get the newest file (just downloaded)
                newest_file = max(excel_files, key=os.path.getmtime)
                
                # Check if it was modified recently (within last minute)
                if time.time() - os.path.getmtime(newest_file) < 60:
                    print(f"✅ Found download: {os.path.basename(newest_file)}")
                    time.sleep(1)  # Ensure it's fully written
                    return newest_file
            
            print("⏳ Waiting for download...")
            time.sleep(1)
        
        # Final check
        xls_files = glob.glob(os.path.join(self.temp_download_dir, '*.xls'))
        xlsx_files = glob.glob(os.path.join(self.temp_download_dir, '*.xlsx'))
        excel_files = xls_files + xlsx_files
        
        if excel_files:
            newest_file = max(excel_files, key=os.path.getmtime)
            if time.time() - os.path.getmtime(newest_file) < 60:
                print(f"✅ Found download: {os.path.basename(newest_file)}")
                return newest_file
        
        print("❌ No Excel file found (.xls or .xlsx)")
        return None
    
    def clear_old_downloads(self):
        """Clear old Excel files from Downloads folder"""
        # Clear both .xls and .xlsx files
        patterns = ['resultsxls*.xls', 'resultsxls*.xlsx', 'Report*.xls', 'Report*.xlsx']
        
        for pattern in patterns:
            for file in glob.glob(os.path.join(self.temp_download_dir, pattern)):
                try:
                    if time.time() - os.path.getmtime(file) > 60:  # Older than 1 minute
                        os.remove(file)
                        print(f"Cleared old download: {os.path.basename(file)}")
                except:
                    pass
    
    def scrape_page(self, driver, page_number, date_range):
        """Scrape a single page and download the Excel file"""
        url = self.build_url(page_number, date_range)
        print(f"\n{'='*60}")
        print(f"📄 SCRAPING PAGE {page_number}")
        print(f"🔗 {url[:80]}...")
        print('='*60)
        
        # CRITICAL: Close and reopen tab for each page after page 1
        if page_number > 1:
            print("Opening new tab for fresh page load...")
            driver.execute_script("window.open('');")  # Open new tab
            old_window = driver.current_window_handle
            driver.switch_to.window(driver.window_handles[-1])  # Switch to new tab
            driver.switch_to.window(old_window)  # Go back to old tab
            driver.close()  # Close old tab
            driver.switch_to.window(driver.window_handles[-1])  # Switch to new tab
            time.sleep(2)
        
        # Navigate to the page
        driver.get(url)
        print("⏳ Waiting for page to load...")
        time.sleep(10)
        
        try:
            wait = WebDriverWait(driver, 30)
            
            # Wait for results
            print("🔍 Looking for results...")
            try:
                wait.until(lambda d: d.find_elements(By.CSS_SELECTOR, '.hit-list-item, .no-results, div[class*="result"]'))
                print("✅ Page loaded")
            except:
                print("⚠️ Timeout waiting for results")
            
            # Check for no results
            try:
                no_results = driver.find_element(By.CLASS_NAME, "no-results")
                if no_results.is_displayed():
                    print(f"❌ No results on page {page_number}")
                    return None
            except:
                print("✅ Results found")
            
            time.sleep(5)  # Let JavaScript render
            
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
                    print(f"✅ Selected all items")
                    break
                except:
                    continue
            
            if not clicked:
                print("⚠️ Could not select all - trying export anyway")
            
            time.sleep(3)
            
            # Clear old downloads
            self.clear_old_downloads()
            
            # Click Export
            try:
                export_button = driver.find_element(By.CSS_SELECTOR, 'a.btn.exportXLSX')
                driver.execute_script("arguments[0].click();", export_button)
                print("✅ Export clicked")
            except Exception as e:
                print(f"❌ Could not click export: {e}")
                return None
            
            # Wait for download
            downloaded_file = self.wait_for_download(timeout=60)
            
            if downloaded_file:
                # Create unique filename with date and page
                date_str = self.current_date.strftime('%Y%m%d')
                unique_filename = f'eu_trademarks_{date_str}_page_{page_number:03d}.xlsx'
                final_path = os.path.join(self.download_dir, unique_filename)
                
                # Move file to project downloads folder
                shutil.move(downloaded_file, final_path)
                print(f"💾 Saved as: {unique_filename}")
                return final_path
            else:
                print(f"❌ Download failed for page {page_number}")
                return None
                
        except Exception as e:
            print(f"❌ Error on page {page_number}: {e}")
            driver.save_screenshot(f'error_page_{page_number}.png')
            return None
    
    def merge_excel_files(self, excel_files, output_file='merged_trademarks.xlsx'):
        """Merge multiple Excel files into one"""
        if not excel_files:
            print("No Excel files to merge")
            return None
        
        print(f"\n{'='*60}")
        print("📊 MERGING FILES...")
        print('='*60)
        
        dfs = []
        for file in excel_files:
            try:
                df = pd.read_excel(file)
                dfs.append(df)
                print(f"✅ Loaded {os.path.basename(file)}: {len(df)} rows")
            except Exception as e:
                print(f"❌ Error reading {file}: {e}")
        
        if dfs:
            merged_df = pd.concat(dfs, ignore_index=True)
            merged_df = merged_df.drop_duplicates()
            
            # Save with date in filename
            date_str = self.current_date.strftime('%Y%m%d')
            output_file = f'eu_trademarks_{date_str}_COMPLETE.xlsx'
            output_path = os.path.join(self.download_dir, output_file)
            
            merged_df.to_excel(output_path, index=False)
            print(f"\n🎉 Merged {len(dfs)} files → {output_file}")
            print(f"📊 Total records: {len(merged_df)}")
            return output_path
        
        return None
    
    def scrape_all_pages(self, date=None, max_pages=100):
        """Main method to scrape all pages for a given date"""
        date_range = self.get_date_range(date)
        downloaded_files = []
        
        print(f"\n{'='*60}")
        print(f"🚀 STARTING EU TRADEMARK SCRAPER")
        print(f"📅 Date: {self.current_date.strftime('%Y-%m-%d')}")
        print(f"📁 Output folder: {self.download_dir}")
        print('='*60)
        
        # Initialize driver
        driver = webdriver.Chrome(options=self.chrome_options)
        
        try:
            # We expect ~18 pages for 1735 results
            for page_num in range(1, max_pages + 1):
                file_path = self.scrape_page(driver, page_num, date_range)
                
                if file_path:
                    downloaded_files.append(file_path)
                    print(f"✅ Page {page_num} complete")
                    
                    # Small delay between pages
                    if page_num < max_pages:
                        time.sleep(2)
                else:
                    # Check if we've reached the end
                    if page_num > 1:
                        print(f"📍 Reached end at page {page_num - 1}")
                        break
                    else:
                        print("❌ First page failed - stopping")
                        break
            
            # Merge all files
            if downloaded_files:
                print(f"\n{'='*60}")
                print(f"✅ Downloaded {len(downloaded_files)} pages successfully")
                print('='*60)
                
                merged_file = self.merge_excel_files(downloaded_files)
                
                if merged_file:
                    # Also save as JSON
                    df = pd.read_excel(merged_file)
                    json_path = merged_file.replace('.xlsx', '.json')
                    df.to_json(json_path, orient='records', date_format='iso')
                    print(f"📄 JSON saved: {os.path.basename(json_path)}")
                
                # Keep individual page files for reference
                print(f"\n📁 Individual page files kept in: {self.download_dir}")
                
                return merged_file
            else:
                print("❌ No files downloaded")
                return None
                
        finally:
            driver.quit()
            print("\n✅ Browser closed")

def run_daily_scrape():
    """Function to run the daily scrape"""
    print("\n" + "="*60)
    print("🚀 EU TRADEMARK SCRAPER")
    print("="*60)
    
    scraper = EUTrademarkScraper(headless=False)  # Keep False to see progress
    result = scraper.scrape_all_pages(date=datetime.now(), max_pages=20)
    
    if result:
        print(f"\n{'='*60}")
        print(f"🎉 SUCCESS!")
        print(f"📁 Complete file: {result}")
        print('='*60)
        return result
    else:
        print("\n❌ Scraping failed")
        return None

if __name__ == "__main__":
    run_daily_scrape()