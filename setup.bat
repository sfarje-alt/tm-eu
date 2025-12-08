@echo off
echo ================================
echo EU Trademark Scraper Setup
echo ================================
echo.

REM Check if git is installed
where git >nul 2>nul
if %errorlevel% neq 0 (
    echo Git is not installed. Please install Git first:
    echo Visit: https://git-scm.com/downloads
    pause
    exit /b 1
)

REM Get GitHub username
set /p GITHUB_USER="Enter your GitHub username: "
echo.

REM Update the API configuration
echo Updating API configuration...
powershell -Command "(Get-Content api\index.py) -replace 'YOUR_GITHUB_USERNAME', '%GITHUB_USER%' | Set-Content api\index.py"

REM Initialize git repository
echo Initializing Git repository...
git init

REM Add all files
echo Adding files...
git add .

REM Commit
echo Creating initial commit...
git commit -m "Initial commit - EU Trademark Scraper"

REM Set up remote
echo Setting up GitHub remote...
git branch -M main
git remote add origin https://github.com/%GITHUB_USER%/eu-trademark-scraper.git

echo.
echo ================================
echo Setup complete!
echo ================================
echo.
echo Next steps:
echo 1. Create a new PUBLIC repository on GitHub:
echo    https://github.com/new
echo    Name: eu-trademark-scraper
echo    Visibility: PUBLIC (important!)
echo    DON'T initialize with README
echo.
echo 2. Push to GitHub by running:
echo    git push -u origin main
echo.
echo 3. Follow the instructions in QUICK_SETUP.md to:
echo    - Set up GitHub Actions
echo    - Deploy API to Vercel
echo    - Test everything
echo.
echo Open QUICK_SETUP.md for detailed instructions!
pause