"""
Example usage of the Intelligent Wealth Advisor Scraper with URL Discovery
"""
import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

from intelligent_scraper import IntelligentAdvisorScraper
from config import ScraperConfig

# Setup logging
def setup_logging():
    """Setup comprehensive logging."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"intelligent_scraper_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)

async def run_intelligent_test():
    """Run a test with intelligent URL discovery."""
    logger = setup_logging()
    logger.info("🧠 Starting intelligent scraper test...")
    
    # Validate API key
    if not ScraperConfig.CLAUDE_API_KEY or ScraperConfig.CLAUDE_API_KEY == 'your_claude_api_key_here':
        logger.error("Please set your Claude API key in the .env file")
        print("\n❌ Error: Claude API key not found!")
        print("Please edit .env file and add your Claude API key")
        return
    
    # Initialize intelligent scraper
    scraper = IntelligentAdvisorScraper(ScraperConfig.CLAUDE_API_KEY)
    
    # Test with just UBS and New York first
    company = "UBS"
    state = "New York"
    
    try:
        print(f"\n🧠 Testing intelligent scraper with {company} - {state}")
        print("🔍 This will automatically discover working URLs if needed...")
        
        advisors = await scraper.scrape_company_state(company, state)
        logger.info(f"Test completed: Found {len(advisors)} advisors")
        
        # Save test results
        if advisors:
            scraper.scraped_data = advisors
            scraper.save_data("intelligent_test_results")
            print(f"\n✅ Test successful! Found {len(advisors)} advisors")
            print("Check intelligent_test_results.csv for the data")
        else:
            print("\n⚠️  Test completed but no advisors found.")
            print("The URL discovery worked, but the specific search might need refinement.")
            
        # Show discovered URLs
        if scraper.discovered_urls:
            print(f"\n🔍 Discovered working URLs:")
            for comp, url in scraper.discovered_urls.items():
                print(f"  {comp}: {url}")
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        print(f"\n❌ Test failed: {e}")

async def run_url_discovery_only():
    """Test just the URL discovery feature."""
    logger = setup_logging()
    logger.info("🔍 Testing URL discovery feature...")
    
    # Validate API key
    if not ScraperConfig.CLAUDE_API_KEY or ScraperConfig.CLAUDE_API_KEY == 'your_claude_api_key_here':
        logger.error("Please set your Claude API key in the .env file")
        print("\n❌ Error: Claude API key not found!")
        return
    
    scraper = IntelligentAdvisorScraper(ScraperConfig.CLAUDE_API_KEY)
    
    print("\n🔍 Testing URL discovery for all companies...")
    
    for company in scraper.companies.keys():
        try:
            print(f"\n🔍 Discovering URL for {company}...")
            url = await scraper.intelligent_url_discovery(company)
            if url:
                print(f"✅ Found: {url}")
            else:
                print(f"❌ Could not find working URL for {company}")
        except Exception as e:
            print(f"❌ Error with {company}: {e}")
    
    # Save discovered URLs
    if scraper.discovered_urls:
        scraper.save_discovered_urls()
        print(f"\n💾 Saved discovered URLs to file")

async def run_full_intelligent_scrape():
    """Run the full scraping process with intelligent adaptation."""
    logger = setup_logging()
    logger.info("🚀 Starting full intelligent scraping process...")
    
    # Validate API key
    if not ScraperConfig.CLAUDE_API_KEY or ScraperConfig.CLAUDE_API_KEY == 'your_claude_api_key_here':
        logger.error("Please set your Claude API key in the .env file")
        print("\n❌ Error: Claude API key not found!")
        return
    
    # Initialize intelligent scraper
    scraper = IntelligentAdvisorScraper(ScraperConfig.CLAUDE_API_KEY)
    
    try:
        print("\n🧠 Starting intelligent full scrape...")
        print("🔍 Will automatically discover working URLs and adapt to website changes")
        print("This will take several hours. Press Ctrl+C to interrupt safely.")
        
        # Run the full scrape
        await scraper.scrape_all_companies_and_states()
        
        # Save results
        scraper.save_data("intelligent_full_results")
        
        logger.info("Intelligent scraping completed successfully!")
        print(f"\n✅ Intelligent scraping completed! Found {len(scraper.scraped_data)} total advisors")
        
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
        print("\n⚠️  Scraping interrupted by user")
        # Save partial results
        if scraper.scraped_data:
            scraper.save_data("intelligent_partial_results")
            print(f"Saved {len(scraper.scraped_data)} advisors to intelligent_partial_results files")
            
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        print(f"\n❌ Scraping failed: {e}")
        # Save any data we managed to collect
        if scraper.scraped_data:
            scraper.save_data("intelligent_error_recovery")
            print(f"Saved {len(scraper.scraped_data)} advisors to intelligent_error_recovery files")

async def run_specific_states_intelligent(states_list):
    """Run intelligent scraping for specific states only."""
    logger = setup_logging()
    
    # Validate API key
    if not ScraperConfig.CLAUDE_API_KEY or ScraperConfig.CLAUDE_API_KEY == 'your_claude_api_key_here':
        logger.error("Please set your Claude API key in the .env file")
        print("\n❌ Error: Claude API key not found!")
        return
    
    scraper = IntelligentAdvisorScraper(ScraperConfig.CLAUDE_API_KEY)
    scraper.target_states = states_list  # Override default states
    
    print(f"\n🎯 Intelligent scraping for states: {', '.join(states_list)}")
    
    try:
        await scraper.scrape_all_companies_and_states()
        scraper.save_data("intelligent_specific_states")
        print(f"\n✅ Completed! Found {len(scraper.scraped_data)} advisors")
    except Exception as e:
        logger.error(f"Specific states scraping failed: {e}")
        if scraper.scraped_data:
            scraper.save_data("intelligent_specific_partial")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Intelligent Wealth Advisor Scraper with URL Discovery")
    parser.add_argument("--mode", choices=["test", "discover", "full", "specific"], 
                       default="test", help="Scraping mode")
    parser.add_argument("--states", nargs="+", 
                       help="Specific states to scrape (for specific mode)")
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("🧠 INTELLIGENT WEALTH ADVISOR SCRAPER WITH URL DISCOVERY")
    print("=" * 70)
    print("✨ Features:")
    print("  🔍 Automatic URL discovery using Google + Claude reasoning")
    print("  🧠 Smart navigation adaptation")
    print("  🔄 Self-healing when URLs break")
    print("  📊 Enhanced data extraction")
    print("=" * 70)
    
    if args.mode == "test":
        print("🧪 Running intelligent test mode...")
        asyncio.run(run_intelligent_test())
    elif args.mode == "discover":
        print("🔍 Running URL discovery mode...")
        asyncio.run(run_url_discovery_only())
    elif args.mode == "full":
        print("🚀 Running full intelligent scrape mode...")
        asyncio.run(run_full_intelligent_scrape())
    elif args.mode == "specific":
        if args.states:
            asyncio.run(run_specific_states_intelligent(args.states))
        else:
            # Default specific states
            default_states = ["New York", "New Jersey", "California"]
            asyncio.run(run_specific_states_intelligent(default_states))
