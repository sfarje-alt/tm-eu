# EU Trademark Scraper - Free Deployment Guide

## Overview
This system scrapes EU trademark publications daily and provides a REST API to access the data. All components can be deployed completely free of charge.

## Architecture
1. **Scraper**: Python + Selenium automated browser scraping
2. **Storage**: GitHub repository (free, unlimited public repos)
3. **Automation**: GitHub Actions (free tier: 2000 minutes/month)
4. **API**: Flask REST API
5. **Hosting Options**: Multiple free platforms available

## Deployment Options

### Option 1: GitHub Actions + GitHub Pages (Recommended - 100% Free)
This option uses GitHub Actions to scrape daily and GitHub Pages to serve static JSON files.

**Steps:**
1. Create a GitHub repository
2. Upload all the provided files
3. Enable GitHub Actions in your repository
4. Enable GitHub Pages (Settings > Pages > Source: Deploy from branch)
5. Modify `scrape_and_upload.py` to also generate JSON files
6. Access data via: `https://[username].github.io/[repo-name]/data/[date].json`

**Pros:**
- Completely free forever
- No server management
- Automatic daily updates
- Version controlled data

**Cons:**
- Static files only (no dynamic API)
- Public repository required

### Option 2: Render.com (Free Tier)
Deploy the Flask API on Render's free tier.

**Steps:**
1. Create account at render.com
2. Connect your GitHub repository
3. Create new Web Service
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `gunicorn api_server:app`
6. Deploy

**Free Tier Limits:**
- 750 hours/month
- Spins down after 15 mins of inactivity
- 512 MB RAM
- Limited to 100 GB bandwidth/month

### Option 3: Railway.app (Free Trial)
Deploy using Railway's trial credits.

**Steps:**
1. Create account at railway.app
2. New Project > Deploy from GitHub
3. Select your repository
4. Railway auto-detects Python and deploys
5. Add environment variable: `PORT=5000`

**Free Trial:**
- $5 trial credit (~500 hours of usage)
- After trial: $5/month minimum

### Option 4: Google Cloud Run (Free Tier)
Serverless container deployment.

**Steps:**
1. Install Google Cloud SDK
2. Build container: `docker build -t eu-scraper .`
3. Push to Google Container Registry
4. Deploy to Cloud Run: `gcloud run deploy`

**Free Tier:**
- 2 million requests/month
- 360,000 GB-seconds memory
- 180,000 vCPU-seconds

### Option 5: Hybrid Approach (Best Free Solution)
Combine GitHub Actions for scraping with a lightweight API.

**Architecture:**
- GitHub Actions: Daily automated scraping (free)
- GitHub Repository: Data storage (free)
- Vercel/Netlify Functions: Serverless API (free tier)
- Alternative: GitHub API to fetch data directly

## Implementation Steps

### 1. Set Up GitHub Repository
```bash
# Create new repository
git init eu-trademark-scraper
cd eu-trademark-scraper

# Add all files
git add .
git commit -m "Initial commit"

# Create GitHub repo and push
gh repo create eu-trademark-scraper --public
git push -u origin main
```

### 2. Configure GitHub Actions
- The workflow file is already created in `.github/workflows/daily_scraper.yml`
- It will run automatically at 2 AM UTC daily
- Manual trigger available in Actions tab

### 3. Set Up Free API Hosting

#### Using Vercel (Recommended for API)
Create `vercel.json`:
```json
{
  "functions": {
    "api/index.py": {
      "maxDuration": 30
    }
  },
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/api/index"
    }
  ]
}
```

Create `api/index.py`:
```python
from flask import Flask, jsonify
import requests
import json

app = Flask(__name__)

@app.route('/api/trademarks/<date>')
def get_trademarks(date):
    # Fetch from GitHub repository
    url = f"https://raw.githubusercontent.com/[username]/[repo]/main/data/eu_trademarks_{date}.json"
    response = requests.get(url)
    if response.status_code == 200:
        return jsonify(response.json())
    return jsonify({"error": "Data not found"}), 404

# Vercel serverless function handler
def handler(request, response):
    return app(request, response)
```

Deploy:
```bash
npm i -g vercel
vercel --prod
```

### 4. Create Static JSON Files
Modify the scraper to also save JSON:
```python
# Add to eu_trademark_scraper.py after saving Excel
import json

# Save as JSON too
json_path = output_path.replace('.xlsx', '.json')
merged_df.to_json(json_path, orient='records', date_format='iso')
```

## API Usage Examples

### JavaScript/Fetch
```javascript
// Fetch today's data
fetch('https://your-api.vercel.app/api/trademarks/20251208')
  .then(res => res.json())
  .then(data => {
    console.log(`Found ${data.total_records} trademarks`);
    data.data.forEach(tm => {
      console.log(`${tm.TradeMark} - ${tm.Applicant}`);
    });
  });
```

### Python
```python
import requests

# Get trademark data
response = requests.get('https://your-api.vercel.app/api/trademarks/20251208')
data = response.json()

# Search with filters
params = {'name': 'tech', 'applicant': 'microsoft'}
response = requests.get('https://your-api.vercel.app/api/trademarks/search', params=params)
```

### cURL
```bash
# Get today's data
curl https://your-api.vercel.app/api/trademarks/today

# Download Excel file
curl -O https://your-api.vercel.app/api/trademarks/download/20251208
```

## Environment Variables
Set these in your hosting platform:

```
FLASK_ENV=production
PORT=5000
DOWNLOAD_DIR=/tmp/downloads
DATA_DIR=/tmp/data
```

## Monitoring & Logs

### GitHub Actions
- Check Actions tab in GitHub for run history
- Email notifications for failures (configure in Settings)

### API Monitoring (Free)
- UptimeRobot: 50 monitors free
- Freshping: 50 monitors free
- StatusCake: Basic monitoring free

## Cost Breakdown

| Component | Service | Cost | Limits |
|-----------|---------|------|--------|
| Scraping | GitHub Actions | Free | 2000 mins/month |
| Storage | GitHub Repo | Free | Unlimited public |
| API | Vercel | Free | 100GB bandwidth |
| Alternative API | Render | Free | 750 hours/month |
| Monitoring | UptimeRobot | Free | 50 monitors |

**Total Monthly Cost: $0**

## Troubleshooting

### Selenium Issues
- Ensure Chrome and ChromeDriver versions match
- Use `webdriver-manager` for automatic driver management
- Add `--no-sandbox` flag for containerized environments

### GitHub Actions Failures
- Check Actions logs for errors
- Verify Chrome installation in workflow
- Ensure sufficient permissions for git push

### API Response Times
- Free tier services may have cold starts (5-10s delay)
- Consider caching responses
- Use CDN for static JSON files

## Security Considerations

1. **Rate Limiting**: Implement rate limiting to prevent abuse
2. **CORS**: Configure CORS properly for your domains
3. **API Keys**: Add optional API key authentication if needed
4. **Data Privacy**: Ensure compliance with EU data regulations

## Scaling (When Needed)

If you outgrow free tiers:
1. **AWS Lambda**: Pay-per-request pricing
2. **Google Cloud Functions**: Similar to Lambda
3. **DigitalOcean App Platform**: $5/month minimum
4. **Self-hosted VPS**: $5/month for basic VPS

## Support & Updates

- GitHub Issues for bug reports
- Weekly dependency updates via Dependabot
- Monitor EU trademark site for structure changes

## License
MIT License - Free to use and modify

## Contact
For issues or questions, create an issue in the GitHub repository.