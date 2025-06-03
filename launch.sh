#!/bin/bash

# Enhanced Intelligent Wealth Advisor Scraper Launch Script

echo "🧠 INTELLIGENT WEALTH ADVISOR SCRAPER"
echo "======================================"
echo "✨ Now with CAPTCHA detection & handling!"

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
    echo "💡 Get your API key from: https://console.anthropic.com/"
    exit 1
fi

echo "✅ Environment ready!"
echo ""
echo "🚀 AVAILABLE MODES:"
echo "  🧪 test         - Quick test with intelligent features"
echo "  🔍 discover     - Test URL discovery for all companies"  
echo "  🌐 full         - Full intelligent scrape (all companies/states)"
echo "  🎯 specific     - Intelligent scrape for specific states"
echo "  🧩 captcha-test - Test CAPTCHA detection capabilities"
echo "  🛡️  captcha      - Full scrape with CAPTCHA handling"
echo "  📝 simple       - Fallback to basic scraper"
echo ""
echo "🧩 CAPTCHA & BLOCKING FEATURES:"
echo "  • Automatic CAPTCHA detection using Claude Opus"
echo "  • 30-second wait for manual CAPTCHA solving"
echo "  • Rate limiting and access denial detection"
echo "  • Cloudflare protection handling"
echo "  • JavaScript challenge detection"
echo "  • Smart retry mechanisms"
echo ""
echo "🧠 INTELLIGENT FEATURES:"
echo "  • Automatic working URL discovery via Google + Claude"
echo "  • Smart navigation adaptation"
echo "  • Self-healing when websites change"
echo "  • Enhanced data extraction with Claude Opus reasoning"
echo ""

# Parse arguments or default to test mode
if [ $# -eq 0 ]; then
    echo "🧪 Running in INTELLIGENT TEST mode (recommended first run)..."
    python run_intelligent.py --mode test
elif [ "$1" = "test" ]; then
    echo "🧪 Running intelligent test..."
    python run_intelligent.py --mode test
elif [ "$1" = "discover" ]; then
    echo "🔍 Running URL discovery test..."
    python run_intelligent.py --mode discover
elif [ "$1" = "full" ]; then
    echo "🌐 Running full intelligent scrape..."
    python run_intelligent.py --mode full
elif [ "$1" = "specific" ]; then
    shift
    if [ $# -gt 0 ]; then
        echo "🎯 Running intelligent scrape for specific states: $@"
        python run_intelligent.py --mode specific --states "$@"
    else
        echo "🎯 Running intelligent scrape for default states..."
        python run_intelligent.py --mode specific
    fi
elif [ "$1" = "captcha-test" ]; then
    echo "🧩 Running CAPTCHA detection test..."
    python run_captcha_aware.py --mode captcha-test
elif [ "$1" = "captcha" ]; then
    shift
    if [ "$1" = "test" ]; then
        echo "🧩 Running CAPTCHA-aware test..."
        python run_captcha_aware.py --mode test
    elif [ "$1" = "full" ]; then
        echo "🛡️  Running full CAPTCHA-aware scrape..."
        python run_captcha_aware.py --mode full
    elif [ "$1" = "specific" ]; then
        shift
        if [ $# -gt 0 ]; then
            echo "🎯 Running CAPTCHA-aware scrape for specific states: $@"
            python run_captcha_aware.py --mode specific --states "$@"
        else
            echo "🎯 Running CAPTCHA-aware scrape for default states..."
            python run_captcha_aware.py --mode specific
        fi
    else
        echo "🧩 Running CAPTCHA-aware test (default)..."
        python run_captcha_aware.py --mode test
    fi
elif [ "$1" = "simple" ]; then
    # Fallback to simple scraper
    echo "📝 Running simple scraper (fallback mode)..."
    python run_scraper.py --mode test
else
    echo "🚀 Running with custom arguments..."
    python run_intelligent.py "$@"
fi

echo ""
echo "✅ Scraping session completed!"
echo "📄 Check the generated CSV/JSON files for results"
echo "📋 Check logs/ directory for detailed execution logs"
echo ""
echo "💡 TIPS:"
echo "  • Use 'captcha' mode for websites with heavy protection"
echo "  • Set HEADLESS_MODE=False in .env to solve CAPTCHAs manually"
echo "  • Check discovered_urls_*.json for working URL cache"
echo "  • Review logs for CAPTCHA encounter statistics"
