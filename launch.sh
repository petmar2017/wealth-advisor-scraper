#!/bin/bash

# Intelligent Wealth Advisor Scraper Launch Script

echo "🕷️  INTELLIGENT WEALTH ADVISOR SCRAPER"
echo "======================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Copying from template..."
    cp .env.template .env
    echo "📝 Please edit .env file and add your Claude API key before running again."
    exit 1
fi

# Check for Claude API key
if grep -q "your_claude_api_key_here" .env; then
    echo "❌ Please edit .env file and add your Claude API key first."
    exit 1
fi

echo "✅ Environment ready!"
echo ""
echo "Available modes:"
echo "  test     - Quick test with one company/state"
echo "  full     - Full scrape of all companies and states" 
echo "  specific - Scrape specific states only"
echo ""

# Default to test mode if no arguments
if [ $# -eq 0 ]; then
    echo "🧪 Running in TEST mode (default)..."
    python run_scraper.py --mode test
else
    echo "🚀 Running with provided arguments..."
    python run_scraper.py "$@"
fi
