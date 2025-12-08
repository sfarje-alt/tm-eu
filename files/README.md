# EU Trademark Publication Scraper API 🇪🇺

A completely free, automated scraper for EU trademark publications with REST API access. Scrapes daily trademark data from EUIPO and provides it through a simple API.

## Features ✨

- 🤖 **Automated Daily Scraping** - GitHub Actions runs scraper daily at 2 AM UTC
- 📊 **Excel Export** - Downloads and merges all trademark data into single Excel file  
- 🔍 **REST API** - Search and filter trademarks via API endpoints
- 💰 **100% Free** - Runs entirely on free tier services
- 📈 **Scalable** - Handles pagination automatically (100 results per page)
- 🗂️ **Data Storage** - Stores historical data for trend analysis
- 🌐 **Web Client** - Simple HTML interface for searching trademarks

## Quick Start 🚀

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/eu-trademark-scraper.git
cd eu-trademark-scraper
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Locally
```bash
# Run scraper once
python eu_trademark_scraper.py

# Start API server
python api_server.py

# Open client
open client.html
```

### 4. Deploy (Free Options)

#### Option A: GitHub Actions + Vercel (Recommended)
1. Push to GitHub repository
2. Enable GitHub Actions (automatic)
3. Deploy API to Vercel: `vercel --prod`
4. Update `client.html` with your API URL

#### Option B: Render.com
1. Connect GitHub repo to Render
2. Deploy as Web Service
3. Use provided URL in client

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed instructions.

## API Endpoints 📡

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | Get scraping status |
| `/api/scrape` | POST | Trigger manual scrape |
| `/api/trademarks/today` | GET | Get today's trademarks |
| `/api/trademarks/date/<YYYYMMDD>` | GET | Get trademarks by date |
| `/api/trademarks/search` | GET | Search with filters |
| `/api/trademarks/download/<YYYYMMDD>` | GET | Download Excel file |
| `/api/trademarks/available-dates` | GET | List available dates |

### Example API Calls

```bash
# Get today's data
curl http://your-api.com/api/trademarks/today

# Search by name and applicant
curl "http://your-api.com/api/trademarks/search?name=tech&applicant=microsoft"

# Download Excel
curl -O http://your-api.com/api/trademarks/download/20251208
```

## How It Works 🔧

1. **Daily Trigger**: GitHub Actions runs at 2 AM UTC
2. **Scraping Process**:
   - Navigates to EUIPO search with today's date filter
   - For each page (up to 100 results per page):
     - Selects all results
     - Downloads Excel file
     - Continues until no more results
3. **Data Processing**:
   - Merges all Excel files into one
   - Saves with date stamp
   - Optionally converts to JSON
4. **API Service**:
   - Serves data via REST endpoints
   - Provides search and filtering
   - Allows Excel download

## File Structure 📁

```
eu-trademark-scraper/
├── eu_trademark_scraper.py    # Main scraper logic
├── api_server.py              # Flask API server
├── scrape_and_upload.py       # GitHub Actions script
├── client.html                # Web interface
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Container deployment
├── .github/
│   └── workflows/
│       └── daily_scraper.yml  # GitHub Actions workflow
├── data/                      # Scraped data storage
│   └── eu_trademarks_*.xlsx
└── DEPLOYMENT_GUIDE.md        # Deployment instructions
```

## Configuration ⚙️

### Environment Variables
```bash
FLASK_ENV=production
PORT=5000
DOWNLOAD_DIR=/tmp/downloads
DATA_DIR=/tmp/data
```

### Scraper Settings
Edit `eu_trademark_scraper.py`:
```python
# Run in headless mode (no browser window)
scraper = EUTrademarkScraper(headless=True)

# Set max pages to scrape
scraper.scrape_all_pages(max_pages=100)
```

## Free Hosting Limits 📊

| Service | Free Tier | Limits |
|---------|-----------|--------|
| GitHub Actions | 2000 mins/month | More than enough for daily scraping |
| GitHub Storage | Unlimited | Public repositories |
| Vercel | 100 GB bandwidth | ~1M API requests |
| Render | 750 hours/month | Sleeps after 15 mins inactivity |
| Railway | $5 credit | ~500 hours usage |

## Troubleshooting 🔨

### Common Issues

1. **Chrome/ChromeDriver Mismatch**
   ```bash
   pip install webdriver-manager
   ```

2. **GitHub Actions Failing**
   - Check Actions tab for logs
   - Verify Chrome installation in workflow

3. **Slow API Response**
   - Free tier services have cold starts
   - First request may take 5-10 seconds

4. **No Data Found**
   - Check if EUIPO website structure changed
   - Verify date format in URL

## Development 👨‍💻

### Run Tests
```bash
python -m pytest tests/
```

### Local Development
```bash
# Use Chrome in non-headless mode for debugging
scraper = EUTrademarkScraper(headless=False)
```

### Contributing
1. Fork repository
2. Create feature branch
3. Submit pull request

## Legal & Compliance ⚖️

- This scraper accesses publicly available data
- Respects robots.txt and rate limits
- For commercial use, review EUIPO terms of service
- Ensure GDPR compliance when storing applicant data

## Support 💬

- 🐛 [Report Issues](https://github.com/yourusername/eu-trademark-scraper/issues)
- 📖 [Documentation](DEPLOYMENT_GUIDE.md)
- 💡 [Feature Requests](https://github.com/yourusername/eu-trademark-scraper/discussions)

## License 📄

MIT License - See [LICENSE](LICENSE) file

## Credits 👏

Built with:
- 🐍 Python + Selenium
- 🌶️ Flask
- 🐙 GitHub Actions
- 🚀 Free hosting services

---

**Note**: This tool is for educational purposes. Always respect website terms of service and rate limits.