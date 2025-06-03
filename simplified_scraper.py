import asyncio
import json
import time
import random
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import pandas as pd
import logging
import re

# Core imports
from playwright.async_api import async_playwright, Browser, Page
import anthropic
from bs4 import BeautifulSoup
import requests
from tenacity import retry, stop_after_attempt, wait_exponential
from config import ScraperConfig

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AdvisorInfo:
    name: str = ""
    phone: str = ""
    street: str = ""
    city: str = ""
    state: str = ""
    email: str = ""
    company: str = ""
    url: str = ""

class SimplifiedAdvisorScraper:
    """Simplified version using pure Playwright and Anthropic."""
    
    def __init__(self, claude_api_key: str):
        """Initialize the scraper with Claude API key."""
        self.claude_api_key = claude_api_key
        self.client = anthropic.Anthropic(api_key=claude_api_key)
        
        # Target states
        self.target_states = [
            "New York", "New Jersey", "Florida", "Texas", "California",
            "Illinois", "Massachusetts", "Georgia", "Washington", "Washington DC",
            "Virginia", "Maryland", "Michigan", "Connecticut", "Pennsylvania",
            "North Carolina", "Ohio", "Rhode Island", "Minnesota"
        ]
        
        # Company URLs and configurations
        self.companies = {
            "UBS": {
                "base_url": "https://www.ubs.com/us/en/wealth-management/find-an-advisor.html",
                "search_pattern": "find-an-advisor"
            },
            "Morgan Stanley": {
                "base_url": "https://advisor.morganstanley.com/search",
                "search_pattern": "advisor-search"
            },
            "Merrill Lynch": {
                "base_url": "https://advisor.ml.com/search?bylocation=true",
                "search_pattern": "advisor-search"
            }
        }
        
        self.scraped_data = []

    async def setup_browser(self):
        """Setup and configure the browser instance."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=ScraperConfig.HEADLESS_MODE,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        return self.browser

    def create_intelligence_prompt(self, html_content: str, current_url: str) -> str:
        """Create a prompt for Claude to analyze the page and extract advisor info."""
        prompt = f"""
        You are an expert web scraper analyzing a financial advisor directory page.
        
        Current URL: {current_url}
        
        HTML Content (first 3000 chars): {html_content[:3000]}
        
        Your task is to:
        1. Identify if this page contains financial advisor listings
        2. Extract advisor information including: name, phone, street, city, state, email
        3. Identify pagination or "load more" elements
        4. Suggest next navigation steps
        
        Respond with a JSON object containing:
        {{
            "has_advisors": boolean,
            "advisors": [
                {{
                    "name": "string",
                    "phone": "string", 
                    "street": "string",
                    "city": "string",
                    "state": "string",
                    "email": "string"
                }}
            ],
            "pagination_present": boolean,
            "next_action": "string (description of what to do next)",
            "css_selectors": {{
                "advisor_container": "string",
                "name": "string",
                "phone": "string",
                "address": "string",
                "email": "string"
            }}
        }}
        
        Be precise with CSS selectors and extraction logic.
        """
        return prompt

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def analyze_page_with_llm(self, html_content: str, current_url: str) -> Dict:
        """Use Claude to intelligently analyze the current page."""
        prompt = self.create_intelligence_prompt(html_content, current_url)
        
        try:
            message = self.client.messages.create(
                model="claude-3-sonnet-20241022",  # Using Sonnet for cost efficiency
                max_tokens=2000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            response_text = message.content[0].text
            
            # Try to extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start != -1 and json_end != -1:
                json_str = response_text[json_start:json_end]
                return json.loads(json_str)
            else:
                logger.warning("Could not extract JSON from LLM response")
                return {"has_advisors": False, "advisors": [], "next_action": "manual_inspection_needed"}
                
        except Exception as e:
            logger.error(f"Error analyzing page with LLM: {e}")
            return {"has_advisors": False, "advisors": [], "next_action": "error_occurred"}

    async def navigate_to_state_search(self, page: Page, company: str, state: str) -> bool:
        """Navigate to search results for a specific state."""
        company_config = self.companies[company]
        base_url = company_config["base_url"]
        
        try:
            logger.info(f"Navigating to {company} for state: {state}")
            await page.goto(base_url, wait_until='networkidle', timeout=30000)
            await asyncio.sleep(random.uniform(2, 4))  # Random delay
            
            # Get current page content
            html_content = await page.content()
            current_url = page.url
            
            # Use LLM to understand how to search for the state
            search_prompt = f"""
            You are on a {company} advisor search page. 
            Current URL: {current_url}
            HTML snippet: {html_content[:2000]}
            
            I need to search for financial advisors in {state}.
            
            Provide instructions on how to:
            1. Find the location/state search field
            2. Enter "{state}" 
            3. Submit the search
            
            Respond with specific CSS selectors and actions in JSON format:
            {{
                "search_field_selector": "string",
                "search_button_selector": "string", 
                "actions": ["step1", "step2", "step3"]
            }}
            """
            
            message = self.client.messages.create(
                model="claude-3-sonnet-20241022",
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": search_prompt}
                ]
            )
            
            search_instructions = message.content[0].text
            
            # Try to extract and execute search instructions
            try:
                # Look for common search patterns
                search_selectors = [
                    "input[placeholder*='location' i]",
                    "input[placeholder*='city' i]", 
                    "input[placeholder*='state' i]",
                    "input[name*='location' i]",
                    "input[id*='location' i]",
                    "input[type='search']"
                ]
                
                search_input = None
                for selector in search_selectors:
                    try:
                        search_input = await page.wait_for_selector(selector, timeout=3000)
                        if search_input:
                            break
                    except:
                        continue
                
                if search_input:
                    await search_input.clear()
                    await search_input.fill(state)
                    await asyncio.sleep(1)
                    
                    # Look for search button
                    button_selectors = [
                        "button[type='submit']",
                        "input[type='submit']", 
                        "button:has-text('Search')",
                        "button:has-text('Find')",
                        "button:has-text('Go')",
                        ".search-button",
                        "#search-button"
                    ]
                    
                    for selector in button_selectors:
                        try:
                            button = await page.wait_for_selector(selector, timeout=2000)
                            if button:
                                await button.click()
                                await page.wait_for_load_state('networkidle', timeout=10000)
                                return True
                        except:
                            continue
                            
                    # Try pressing Enter if no button found
                    await search_input.press('Enter')
                    await page.wait_for_load_state('networkidle', timeout=10000)
                    return True
                        
            except Exception as e:
                logger.error(f"Error executing search: {e}")
                
            return False
            
        except Exception as e:
            logger.error(f"Error navigating to {company} for {state}: {e}")
            return False

    async def extract_advisors_from_page(self, page: Page, company: str) -> List[AdvisorInfo]:
        """Extract advisor information from current page using LLM analysis."""
        try:
            html_content = await page.content()
            current_url = page.url
            
            # Analyze page with LLM
            analysis = await self.analyze_page_with_llm(html_content, current_url)
            
            advisors = []
            if analysis.get("has_advisors", False):
                for advisor_data in analysis.get("advisors", []):
                    advisor = AdvisorInfo(
                        name=advisor_data.get("name", ""),
                        phone=self.clean_phone(advisor_data.get("phone", "")),
                        street=advisor_data.get("street", ""),
                        city=advisor_data.get("city", ""),
                        state=advisor_data.get("state", ""),
                        email=advisor_data.get("email", ""),
                        company=company,
                        url=current_url
                    )
                    advisors.append(advisor)
                    
            logger.info(f"Extracted {len(advisors)} advisors from {current_url}")
            return advisors
            
        except Exception as e:
            logger.error(f"Error extracting advisors: {e}")
            return []

    def clean_phone(self, phone: str) -> str:
        """Clean and format phone numbers."""
        if not phone:
            return ""
        # Remove all non-digit characters except + and spaces
        cleaned = re.sub(r'[^\d+\s-()]', '', phone)
        return cleaned.strip()

    async def handle_pagination(self, page: Page) -> bool:
        """Handle pagination using LLM to identify next page elements."""
        try:
            html_content = await page.content()
            current_url = page.url
            
            pagination_prompt = f"""
            Analyze this page for pagination elements:
            URL: {current_url}
            HTML: {html_content[:2000]}
            
            Look for:
            - "Next" buttons
            - "Load More" buttons  
            - Page number navigation
            - Infinite scroll indicators
            
            Respond with JSON:
            {{
                "has_pagination": boolean,
                "pagination_type": "next_button|load_more|page_numbers|infinite_scroll",
                "selector": "css_selector_for_next_action",
                "action": "click|scroll"
            }}
            """
            
            message = self.client.messages.create(
                model="claude-3-sonnet-20241022",
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": pagination_prompt}
                ]
            )
            
            response_text = message.content[0].text
            
            # Extract JSON response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start != -1 and json_end != -1:
                pagination_info = json.loads(response_text[json_start:json_end])
                
                if pagination_info.get("has_pagination", False):
                    selector = pagination_info.get("selector", "")
                    action = pagination_info.get("action", "click")
                    
                    if selector and action == "click":
                        try:
                            element = await page.wait_for_selector(selector, timeout=5000)
                            if element:
                                await element.click()
                                await page.wait_for_load_state('networkidle', timeout=10000)
                                return True
                        except:
                            pass
                    elif action == "scroll":
                        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        await asyncio.sleep(2)
                        return True
                        
            return False
            
        except Exception as e:
            logger.error(f"Error handling pagination: {e}")
            return False

    async def scrape_company_state(self, company: str, state: str) -> List[AdvisorInfo]:
        """Scrape all advisors for a specific company and state."""
        browser = await self.setup_browser()
        all_advisors = []
        
        try:
            page = await browser.new_page()
            
            # Navigate to state search
            if await self.navigate_to_state_search(page, company, state):
                page_count = 0
                max_pages = ScraperConfig.MAX_PAGES_PER_STATE
                
                while page_count < max_pages:
                    logger.info(f"Scraping {company} - {state} - Page {page_count + 1}")
                    
                    # Extract advisors from current page
                    advisors = await self.extract_advisors_from_page(page, company)
                    all_advisors.extend(advisors)
                    
                    # Check if we've hit our limit
                    if len(all_advisors) >= ScraperConfig.MAX_ADVISORS_PER_COMPANY:
                        logger.info(f"Reached advisor limit for {company}")
                        break
                    
                    # Try to go to next page
                    if not await self.handle_pagination(page):
                        logger.info(f"No more pages for {company} - {state}")
                        break
                        
                    page_count += 1
                    
                    # Rate limiting
                    await asyncio.sleep(random.uniform(
                        ScraperConfig.MIN_DELAY, 
                        ScraperConfig.MAX_DELAY
                    ))
                    
            else:
                logger.error(f"Failed to navigate to search for {company} - {state}")
                
        except Exception as e:
            logger.error(f"Error scraping {company} - {state}: {e}")
        finally:
            await browser.close()
            await self.playwright.stop()
            
        return all_advisors

    async def scrape_all_companies_and_states(self):
        """Main scraping function for all companies and states."""
        logger.info("Starting comprehensive advisor scraping...")
        
        for company in self.companies.keys():
            for state in self.target_states:
                try:
                    logger.info(f"Starting {company} - {state}")
                    advisors = await self.scrape_company_state(company, state)
                    self.scraped_data.extend(advisors)
                    
                    logger.info(f"Completed {company} - {state}: {len(advisors)} advisors found")
                    
                    # Longer delay between different company/state combinations
                    await asyncio.sleep(random.uniform(10, 20))
                    
                except Exception as e:
                    logger.error(f"Error with {company} - {state}: {e}")
                    continue

    def save_data(self, filename: str = None):
        """Save scraped data to CSV and JSON files."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"wealth_advisors_{timestamp}"
        
        # Convert to DataFrame
        data_dicts = []
        for advisor in self.scraped_data:
            data_dicts.append(asdict(advisor))
        
        df = pd.DataFrame(data_dicts)
        
        # Save as CSV
        csv_filename = f"{filename}.csv"
        df.to_csv(csv_filename, index=False)
        logger.info(f"Data saved to {csv_filename}")
        
        # Save as JSON
        json_filename = f"{filename}.json"
        with open(json_filename, 'w') as f:
            json.dump(data_dicts, f, indent=2)
        logger.info(f"Data saved to {json_filename}")
        
        # Print summary
        print(f"\nScraping Summary:")
        print(f"Total advisors found: {len(self.scraped_data)}")
        print(f"By company:")
        for company in self.companies.keys():
            count = len([a for a in self.scraped_data if a.company == company])
            print(f"  {company}: {count}")

# Usage example
async def main():
    # Initialize scraper with your Claude API key
    scraper = SimplifiedAdvisorScraper(ScraperConfig.CLAUDE_API_KEY)
    
    # Run the scraping process
    await scraper.scrape_all_companies_and_states()
    
    # Save the results
    scraper.save_data()

if __name__ == "__main__":
    # Run the scraper
    asyncio.run(main())
