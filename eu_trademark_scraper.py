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
import json  # ADD THIS LINE!


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
        for i, file in enumerate(excel_files):
            try:
                # Read the Excel file
                df = pd.read_excel(file, header=1)  # Header is in row 2 (index 1)
                
                # Remove the metadata rows at the top
                # The actual data starts after the header row
                df = df[df['Filing number'].notna()]  # Remove rows where Filing number is NaN
                
                # Remove the search criteria columns (usually last 2-3 columns)
                # Keep only the standard columns
                expected_columns = [
                    'Filing number', 'Graphic representation', 'Name', 'Basis', 'Type',
                    'Application reference', 'Filing date/ Designation date', 
                    'Registration date', 'Expiry date', 'Nice classes', 'Status',
                    'Publications', 'Owner name', 'Owner ID', 'Owner country',
                    'Representative name', 'Representative ID', 'Filing language',
                    'Second language', 'Kind of mark', 'Acquired distinctiveness'
                ]
                
                # Keep only columns that match expected names
                valid_cols = [col for col in df.columns if any(exp in str(col) for exp in expected_columns)]
                df = df[valid_cols]
                
                dfs.append(df)
                print(f"✅ Loaded {os.path.basename(file)}: {len(df)} rows")
            except Exception as e:
                print(f"❌ Error reading {file}: {e}")
        
        if dfs:
            # Concatenate all dataframes
            merged_df = pd.concat(dfs, ignore_index=True)
            
            # Remove duplicates based on Filing number
            merged_df = merged_df.drop_duplicates(subset=['Filing number'], keep='first')
            
            # Create data directory if it doesn't exist
            data_dir = os.path.join(self.project_dir, 'data')
            os.makedirs(data_dir, exist_ok=True)
            
            # Save with date in filename to data folder
            date_str = self.current_date.strftime('%Y%m%d')
            output_file = f'eu_trademarks_{date_str}.xlsx'
            output_path = os.path.join(data_dir, output_file)
            
            # Save with proper formatting
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                merged_df.to_excel(writer, index=False, sheet_name='Trademarks')
            
            print(f"\n🎉 Merged {len(dfs)} files → {output_file}")
            print(f"📊 Total unique records: {len(merged_df)}")
            
            # Also save as JSON in data folder
            json_path = output_path.replace('.xlsx', '.json')
            merged_df.to_json(json_path, orient='records', date_format='iso')
            print(f"📄 JSON saved: {os.path.basename(json_path)}")
            
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
            for page_num in range(1, max_pages + 1):
                file_path = self.scrape_page(driver, page_num, date_range)
                
                if file_path:
                    downloaded_files.append(file_path)
                    print(f"✅ Page {page_num} complete")
                    if page_num < max_pages:
                        time.sleep(2)
                else:
                    if page_num > 1:
                        print(f"📍 Reached end at page {page_num - 1}")
                        break
                    else:
                        print("❌ First page failed - stopping")
                        break
            
            # Create a summary/manifest file instead of merging
            if downloaded_files:
                print(f"\n{'='*60}")
                print(f"✅ Downloaded {len(downloaded_files)} pages successfully")
                print('='*60)
                
                # Move files to data folder organized by date
                date_str = self.current_date.strftime('%Y%m%d')
                data_dir = os.path.join(self.project_dir, 'data', date_str)
                os.makedirs(data_dir, exist_ok=True)
                
                final_files = []
                for file in downloaded_files:
                    filename = os.path.basename(file)
                    new_path = os.path.join(data_dir, filename)
                    shutil.move(file, new_path)
                    final_files.append(new_path)
                    print(f"📁 Moved to: {new_path}")
                
                # Create a manifest file with metadata
                manifest = {
                    'date': date_str,
                    'total_pages': len(final_files),
                    'files': [os.path.basename(f) for f in final_files],
                    'scraped_at': datetime.now().isoformat()
                }
                
                manifest_path = os.path.join(data_dir, 'manifest.json')
                with open(manifest_path, 'w') as f:
                    json.dump(manifest, f, indent=2)
                
                print(f"📄 Manifest saved: {manifest_path}")
                print(f"\n📁 All files saved in: {data_dir}")
                
                return data_dir
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
