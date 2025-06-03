"""
CAPTCHA-Aware Intelligent Wealth Advisor Scraper
"""
import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

from captcha_aware_scraper import IntelligentAdvisorScraper
from config import ScraperConfig

# Setup logging
def setup_logging():
    """Setup comprehensive logging."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"captcha_aware_scraper_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)

async def run_captcha_aware_test():
    """Run a test with CAPTCHA detection and handling."""
    logger = setup_logging()
    logger.info("🧩 Starting CAPTCHA-aware scraper test...")
    
    # Validate API key
    if not ScraperConfig.CLAUDE_API_KEY or ScraperConfig.CLAUDE_API_KEY == 'your_claude_api_key_here':
        logger.error("Please set your Claude API key in the .env file")
        print("\n❌ Error: Claude API key not found!")
        print("Please edit .env file and add your Claude API key")
        return
    
    # Initialize CAPTCHA-aware scraper
    scraper = IntelligentAdvisorScraper(ScraperConfig.CLAUDE_API_KEY)
    
    # Test with just UBS and New York first
    company = "UBS"
    state = "New York"
    
    try:
        print(f"\n🧩 Testing CAPTCHA-aware scraper with {company} - {state}")
        print("✨ Features enabled:")
        print("  🛡️  Automatic CAPTCHA detection")
        print("  ⏰ 30-second wait for manual CAPTCHA solving")
        print("  🔍 Intelligent URL discovery")
        print("  🧠 Smart navigation adaptation")
        print("  🔄 Rate limiting handling")
        
        if not ScraperConfig.HEADLESS_MODE:
            print("  👀 Browser visible - you can solve CAPTCHAs manually")
        else:
            print("  🤖 Headless mode - automatic CAPTCHA handling only")
        
        print("\n🚀 Starting test...")
        
        advisors = await scraper.scrape_company_state(company, state)
        logger.info(f"Test completed: Found {len(advisors)} advisors")
        
        # Save test results
        if advisors:
            scraper.scraped_data = advisors
            scraper.save_data("captcha_aware_test_results")
            print(f"\n✅ Test successful! Found {len(advisors)} advisors")
            print("Check captcha_aware_test_results.csv for the data")
        else:
            print("\n⚠️  Test completed but no advisors found.")
            print("This might be due to CAPTCHAs or website protection.")
            
        # Show statistics
        if scraper.captcha_encounters > 0:
            print(f"\n🧩 CAPTCHA/Blocking Statistics:")
            print(f"  Total encounters: {scraper.captcha_encounters}")
            print("  All CAPTCHAs were handled automatically")
        else:
            print(f"\n✅ No CAPTCHAs encountered during test")
            
        # Show discovered URLs
        if scraper.discovered_urls:
            print(f"\n🔍 Discovered working URLs:")
            for comp, url in scraper.discovered_urls.items():
                print(f"  {comp}: {url}")
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        print(f"\n❌ Test failed: {e}")

async def run_captcha_aware_full():
    """Run the full CAPTCHA-aware scraping process."""
    logger = setup_logging()
    logger.info("🚀 Starting full CAPTCHA-aware scraping process...")
    
    # Validate API key
    if not ScraperConfig.CLAUDE_API_KEY or ScraperConfig.CLAUDE_API_KEY == 'your_claude_api_key_here':
        logger.error("Please set your Claude API key in the .env file")
        print("\n❌ Error: Claude API key not found!")
        return
    
    # Initialize CAPTCHA-aware scraper
    scraper = IntelligentAdvisorScraper(ScraperConfig.CLAUDE_API_KEY)
    
    try:
        print("\n🧩 Starting full CAPTCHA-aware scrape...")
        print("🛡️  Will automatically detect and handle CAPTCHAs")
        print("⏰ 30-second waits for CAPTCHA solving")
        print("🔍 Automatic URL discovery when needed")
        print("🔄 Rate limiting and blocking detection")
        
        if not ScraperConfig.HEADLESS_MODE:
            print("👀 Browser visible - you can solve CAPTCHAs manually")
        
        print("\nThis will take several hours. Press Ctrl+C to interrupt safely.")
        print("=" * 60)
        
        # Run the full scrape
        await scraper.scrape_all_companies_and_states()
        
        # Save results
        scraper.save_data("captcha_aware_full_results")
        
        logger.info("CAPTCHA-aware scraping completed successfully!")
        print(f"\n✅ CAPTCHA-aware scraping completed!")
        print(f"📊 Total advisors found: {len(scraper.scraped_data)}")
        print(f"🧩 CAPTCHA encounters: {scraper.captcha_encounters}")
        
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
        print("\n⚠️  Scraping interrupted by user")
        # Save partial results
        if scraper.scraped_data:
            scraper.save_data("captcha_aware_partial_results")
            print(f"💾 Saved {len(scraper.scraped_data)} advisors to partial results")
            
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        print(f"\n❌ Scraping failed: {e}")
        # Save any data we managed to collect
        if scraper.scraped_data:
            scraper.save_data("captcha_aware_error_recovery")
            print(f"💾 Saved {len(scraper.scraped_data)} advisors to error recovery files")

async def run_specific_states_captcha_aware(states_list):
    """Run CAPTCHA-aware scraping for specific states only."""
    logger = setup_logging()
    
    # Validate API key
    if not ScraperConfig.CLAUDE_API_KEY or ScraperConfig.CLAUDE_API_KEY == 'your_claude_api_key_here':
        logger.error("Please set your Claude API key in the .env file")
        print("\n❌ Error: Claude API key not found!")
        return
    
    scraper = IntelligentAdvisorScraper(ScraperConfig.CLAUDE_API_KEY)
    scraper.target_states = states_list  # Override default states
    
    print(f"\n🎯 CAPTCHA-aware scraping for states: {', '.join(states_list)}")
    print("🧩 Will handle CAPTCHAs and blocking automatically")
    
    try:
        await scraper.scrape_all_companies_and_states()
        scraper.save_data("captcha_aware_specific_states")
        print(f"\n✅ Completed! Found {len(scraper.scraped_data)} advisors")
        print(f"🧩 CAPTCHA encounters: {scraper.captcha_encounters}")
    except Exception as e:
        logger.error(f"Specific states scraping failed: {e}")
        if scraper.scraped_data:
            scraper.save_data("captcha_aware_specific_partial")

async def test_captcha_detection_only():
    """Test just the CAPTCHA detection feature on various websites."""
    logger = setup_logging()
    logger.info("🧩 Testing CAPTCHA detection feature...")
    
    # Validate API key
    if not ScraperConfig.CLAUDE_API_KEY or ScraperConfig.CLAUDE_API_KEY == 'your_claude_api_key_here':
        logger.error("Please set your Claude API key in the .env file")
        print("\n❌ Error: Claude API key not found!")
        return
    
    scraper = IntelligentAdvisorScraper(ScraperConfig.CLAUDE_API_KEY)
    
    print("\n🧩 Testing CAPTCHA detection capabilities...")
    print("🔍 Will test detection on company websites")
    
    browser = await scraper.setup_browser()
    page = await browser.new_page()
    
    # Test each company URL for CAPTCHA detection
    for company, config in scraper.companies.items():
        try:
            print(f"\n🌐 Testing {company}: {config['base_url']}")
            
            # Navigate with CAPTCHA handling
            success = await scraper.navigate_with_captcha_handling(page, config['base_url'])
            
            if success:
                print(f"✅ {company}: Successfully navigated without blocking")
            else:
                print(f"⚠️  {company}: Blocking detected and handled")
                
        except Exception as e:
            print(f"❌ {company}: Error - {e}")
    
    await browser.close()
    await scraper.playwright.stop()
    
    print(f"\n📊 CAPTCHA Detection Test Results:")
    print(f"Total CAPTCHA/blocking encounters: {scraper.captcha_encounters}")
    print("✅ CAPTCHA detection test completed")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="CAPTCHA-Aware Intelligent Wealth Advisor Scraper")
    parser.add_argument("--mode", choices=["test", "full", "specific", "captcha-test"], 
                       default="test", help="Scraping mode")
    parser.add_argument("--states", nargs="+", 
                       help="Specific states to scrape (for specific mode)")
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("🧩 CAPTCHA-AWARE INTELLIGENT WEALTH ADVISOR SCRAPER")
    print("=" * 80)
    print("🛡️  ENHANCED FEATURES:")
    print("  🧩 Automatic CAPTCHA detection using Claude Opus")
    print("  ⏰ 30-second wait for manual CAPTCHA solving")
    print("  🔍 Intelligent URL discovery via Google + Claude")
    print("  🧠 Smart navigation adaptation")
    print("  🔄 Rate limiting and blocking detection")
    print("  📊 Comprehensive blocking statistics")
    print("  💾 Partial data recovery on interruption")
    print("=" * 80)
    
    if args.mode == "test":
        print("🧩 Running CAPTCHA-aware test mode...")
        asyncio.run(run_captcha_aware_test())
    elif args.mode == "captcha-test":
        print("🔍 Running CAPTCHA detection test...")
        asyncio.run(test_captcha_detection_only())
    elif args.mode == "full":
        print("🚀 Running full CAPTCHA-aware scrape mode...")
        asyncio.run(run_captcha_aware_full())
    elif args.mode == "specific":
        if args.states:
            asyncio.run(run_specific_states_captcha_aware(args.states))
        else:
            # Default specific states
            default_states = ["New York", "New Jersey", "California"]
            asyncio.run(run_specific_states_captcha_aware(default_states))
