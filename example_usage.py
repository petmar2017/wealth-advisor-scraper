"""
Example usage of the Intelligent Wealth Advisor Scraper
"""
import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

from scraper import IntelligentAdvisorScraper
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
    
    # Initialize scraper
    scraper = IntelligentAdvisorScraper(ScraperConfig.CLAUDE_API_KEY)
    
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
            
    except Exception as e:
        logger.error(f"Test failed: {e}")

async def run_full_scrape():
    """Run the full scraping process."""
    logger = setup_logging()
    logger.info("Starting full scraping process...")
    
    # Validate API key
    if not ScraperConfig.CLAUDE_API_KEY or ScraperConfig.CLAUDE_API_KEY == 'your_claude_api_key_here':
        logger.error("Please set your Claude API key in the .env file or config.py")
        return
    
    # Initialize scraper
    scraper = IntelligentAdvisorScraper(ScraperConfig.CLAUDE_API_KEY)
    
    try:
        # Run the full scrape
        await scraper.scrape_all_companies_and_states()
        
        # Save results
        scraper.save_data()
        
        logger.info("Scraping completed successfully!")
        
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
        # Save partial results
        if scraper.scraped_data:
            scraper.save_data("partial_results")
            
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        # Save any data we managed to collect
        if scraper.scraped_data:
            scraper.save_data("error_recovery")

async def run_specific_states():
    """Run scraping for specific states only."""
    logger = setup_logging()
    
    # Specify which states you want to scrape
    target_states = ["New York", "New Jersey", "California"]
    
    scraper = IntelligentAdvisorScraper(ScraperConfig.CLAUDE_API_KEY)
    scraper.target_states = target_states  # Override default states
    
    await scraper.scrape_all_companies_and_states()
    scraper.save_data("specific_states")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Wealth Advisor Scraper")
    parser.add_argument("--mode", choices=["test", "full", "specific"], 
                       default="test", help="Scraping mode")
    parser.add_argument("--states", nargs="+", 
                       help="Specific states to scrape (for specific mode)")
    
    args = parser.parse_args()
    
    if args.mode == "test":
        asyncio.run(run_simple_test())
    elif args.mode == "full":
        asyncio.run(run_full_scrape())
    elif args.mode == "specific":
        if args.states:
            async def run_custom():
                scraper = IntelligentAdvisorScraper(ScraperConfig.CLAUDE_API_KEY)
                scraper.target_states = args.states
                await scraper.scrape_all_companies_and_states()
                scraper.save_data("custom_states")
            
            asyncio.run(run_custom())
        else:
            asyncio.run(run_specific_states())
