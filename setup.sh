#!/bin/bash

# EU Trademark Scraper - Quick Setup Script
echo "================================"
echo "EU Trademark Scraper Setup"
echo "================================"
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install Git first:"
    echo "   Visit: https://git-scm.com/downloads"
    exit 1
fi

# Get GitHub username
read -p "Enter your GitHub username: " GITHUB_USER
echo ""

# Update the API configuration
echo "📝 Updating API configuration..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s/YOUR_GITHUB_USERNAME/$GITHUB_USER/g" api/index.py
else
    # Linux/Windows Git Bash
    sed -i "s/YOUR_GITHUB_USERNAME/$GITHUB_USER/g" api/index.py
fi

# Initialize git repository
echo "📦 Initializing Git repository..."
git init

# Add all files
echo "📁 Adding files..."
git add .

# Commit
echo "💾 Creating initial commit..."
git commit -m "Initial commit - EU Trademark Scraper"

# Set up remote
echo "🔗 Setting up GitHub remote..."
git branch -M main
git remote add origin https://github.com/$GITHUB_USER/eu-trademark-scraper.git

echo ""
echo "================================"
echo "✅ Local setup complete!"
echo "================================"
echo ""
echo "Next steps:"
echo "1. Create a new PUBLIC repository on GitHub:"
echo "   https://github.com/new"
echo "   Name: eu-trademark-scraper"
echo "   Visibility: PUBLIC (important!)"
echo "   DON'T initialize with README"
echo ""
echo "2. Push to GitHub by running:"
echo "   git push -u origin main"
echo ""
echo "3. Follow the instructions in QUICK_SETUP.md to:"
echo "   - Set up GitHub Actions"
echo "   - Deploy API to Vercel"
echo "   - Test everything"
echo ""
echo "📖 Open QUICK_SETUP.md for detailed instructions!"