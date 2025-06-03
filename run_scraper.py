"""
Example usage of the Simplified Wealth Advisor Scraper
"""
import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

from simplified_scraper import SimplifiedAdvisorScraper
from config import ScraperConfig

# Setup logging
def setup_logging():
    """Setup comprehensive logging."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"scraper_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)

async def run_simple_test():
    """Run a simple test with just one company and state."""
    logger = setup_logging()
    logger.info("Starting simple test...")
    
    # Validate API key
    if not ScraperConfig.CLAUDE_API_KEY or ScraperConfig.CLAUDE_API_KEY == 'your_claude_api_key_here':
        logger.error("Please set your Claude API key in the .env file")
        print("\n❌ Error: Claude API key not found!")
        print("Please copy .env.template to .env and add your Claude API key")
        return
    
    # Initialize scraper
    scraper = SimplifiedAdvisorScraper(ScraperConfig.CLAUDE_API_KEY)
    
    # Test with just one company and state
    company = "UBS"
    state = "New York"
    
    try:
        advisors = await scraper.scrape_company_state(company, state)
        logger.info(f"Test completed: Found {len(advisors)} advisors")
        
        # Save test results
        if advisors:
            scraper.scraped_data = advisors
            scraper.save_data("test_results")
            print(f"\n✅ Test successful! Found {len(advisors)} advisors")
            print("Check test_results.csv and test_results.json for the data")
        else:
            print("\n⚠️  Test completed but no advisors found. This might be normal for the test.")
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        print(f"\n❌ Test failed: {e}")

async def run_full_scrape():
    """Run the full scraping process."""
    logger = setup_logging()
    logger.info("Starting full scraping process...")
    
    # Validate API key
    if not ScraperConfig.CLAUDE_API_KEY or ScraperConfig.CLAUDE_API_KEY == 'your_claude_api_key_here':
        logger.error("Please set your Claude API key in the .env file")
        print("\n❌ Error: Claude API key not found!")
        print("Please copy .env.template to .env and add your Claude API key")
        return
    
    # Initialize scraper
    scraper = SimplifiedAdvisorScraper(ScraperConfig.CLAUDE_API_KEY)
    
    try:
        print("\n🚀 Starting full scrape of all companies and states...")
        print("This will take several hours. Press Ctrl+C to interrupt safely.")
        
        # Run the full scrape
        await scraper.scrape_all_companies_and_states()
        
        # Save results
        scraper.save_data()
        
        logger.info("Scraping completed successfully!")
        print(f"\n✅ Scraping completed! Found {len(scraper.scraped_data)} total advisors")
        
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
        print("\n⚠️  Scraping interrupted by user")
        # Save partial results
        if scraper.scraped_data:
            scraper.save_data("partial_results")
            print(f"Saved {len(scraper.scraped_data)} advisors to partial_results files")
            
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        print(f"\n❌ Scraping failed: {e}")
        # Save any data we managed to collect
        if scraper.scraped_data:
            scraper.save_data("error_recovery")
            print(f"Saved {len(scraper.scraped_data)} advisors to error_recovery files")

async def run_specific_states(states_list):
    """Run scraping for specific states only."""
    logger = setup_logging()
    
    # Validate API key
    if not ScraperConfig.CLAUDE_API_KEY or ScraperConfig.CLAUDE_API_KEY == 'your_claude_api_key_here':
        logger.error("Please set your Claude API key in the .env file")
        print("\n❌ Error: Claude API key not found!")
        return
    
    scraper = SimplifiedAdvisorScraper(ScraperConfig.CLAUDE_API_KEY)
    scraper.target_states = states_list  # Override default states
    
    print(f"\n🎯 Scraping specific states: {', '.join(states_list)}")
    
    try:
        await scraper.scrape_all_companies_and_states()
        scraper.save_data("specific_states")
        print(f"\n✅ Completed! Found {len(scraper.scraped_data)} advisors")
    except Exception as e:
        logger.error(f"Specific states scraping failed: {e}")
        if scraper.scraped_data:
            scraper.save_data("specific_states_partial")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Wealth Advisor Scraper")
    parser.add_argument("--mode", choices=["test", "full", "specific"], 
                       default="test", help="Scraping mode")
    parser.add_argument("--states", nargs="+", 
                       help="Specific states to scrape (for specific mode)")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🕷️  INTELLIGENT WEALTH ADVISOR SCRAPER")
    print("=" * 60)
    
    if args.mode == "test":
        print("Running test mode...")
        asyncio.run(run_simple_test())
    elif args.mode == "full":
        print("Running full scrape mode...")
        asyncio.run(run_full_scrape())
    elif args.mode == "specific":
        if args.states:
            asyncio.run(run_specific_states(args.states))
        else:
            # Default specific states
            default_states = ["New York", "New Jersey", "California"]
            asyncio.run(run_specific_states(default_states))
