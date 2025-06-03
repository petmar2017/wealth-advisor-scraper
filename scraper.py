import asyncio
import json
import time
import random
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
import logging

# LangChain imports
from langchain.llms import Anthropic
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain

# Browser automation
from browser_use import Browser, BrowserConfig
from browser_use.agent import Agent
from browser_use.controller import Controller

# Web scraping
import requests
from bs4 import BeautifulSoup
import re

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

class IntelligentAdvisorScraper:
    def __init__(self, claude_api_key: str):
        """Initialize the intelligent scraper with Claude API key."""
        self.claude_api_key = claude_api_key
        self.llm = Anthropic(
            anthropic_api_key=claude_api_key,
            model="claude-3-opus-20240229"  # Claude 4 Opus
        )
        
        # Browser configuration
        self.browser_config = BrowserConfig(
            headless=False,  # Set to True for production
            disable_security=True,
            additional_args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        
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
        self.memory = ConversationBufferMemory()

    async def setup_browser(self):
        """Setup and configure the browser instance."""
        self.browser = Browser(config=self.browser_config)
        await self.browser.start()
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

    async def analyze_page_with_llm(self, html_content: str, current_url: str) -> Dict:
        """Use Claude to intelligently analyze the current page."""
        prompt = self.create_intelligence_prompt(html_content, current_url)
        
        try:
            response = await self.llm.agenerate([HumanMessage(content=prompt)])
            response_text = response.generations[0][0].text
            
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

    async def navigate_to_state_search(self, browser: Browser, company: str, state: str) -> bool:
        """Navigate to search results for a specific state."""
        company_config = self.companies[company]
        base_url = company_config["base_url"]
        
        try:
            logger.info(f"Navigating to {company} for state: {state}")
            await browser.go_to(base_url)
            await asyncio.sleep(random.uniform(2, 4))  # Random delay
            
            # Get current page content
            html_content = await browser.get_html()
            current_url = await browser.get_url()
            
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
            
            search_analysis = await self.llm.agenerate([HumanMessage(content=search_prompt)])
            search_instructions = search_analysis.generations[0][0].text
            
            # Try to extract and execute search instructions
            # This is a simplified version - you'd want more robust parsing
            try:
                # Look for common search patterns
                search_inputs = await browser.find_elements("input[placeholder*='location'], input[placeholder*='city'], input[placeholder*='state'], input[name*='location']")
                if search_inputs:
                    await search_inputs[0].type(state)
                    await asyncio.sleep(1)
                    
                    # Look for search button
                    search_buttons = await browser.find_elements("button[type='submit'], input[type='submit'], button:contains('Search'), button:contains('Find')")
                    if search_buttons:
                        await search_buttons[0].click()
                        await asyncio.sleep(3)
                        return True
                        
            except Exception as e:
                logger.error(f"Error executing search: {e}")
                
            return False
            
        except Exception as e:
            logger.error(f"Error navigating to {company} for {state}: {e}")
            return False

    async def extract_advisors_from_page(self, browser: Browser, company: str) -> List[AdvisorInfo]:
        """Extract advisor information from current page using LLM analysis."""
        try:
            html_content = await browser.get_html()
            current_url = await browser.get_url()
            
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

    async def handle_pagination(self, browser: Browser) -> bool:
        """Handle pagination using LLM to identify next page elements."""
        try:
            html_content = await browser.get_html()
            current_url = await browser.get_url()
            
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
            
            response = await self.llm.agenerate([HumanMessage(content=pagination_prompt)])
            response_text = response.generations[0][0].text
            
            # Extract JSON response (simplified parsing)
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start != -1 and json_end != -1:
                pagination_info = json.loads(response_text[json_start:json_end])
                
                if pagination_info.get("has_pagination", False):
                    selector = pagination_info.get("selector", "")
                    action = pagination_info.get("action", "click")
                    
                    if selector and action == "click":
                        elements = await browser.find_elements(selector)
                        if elements:
                            await elements[0].click()
                            await asyncio.sleep(3)
                            return True
                    elif action == "scroll":
                        await browser.scroll_down()
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
            # Navigate to state search
            if await self.navigate_to_state_search(browser, company, state):
                page_count = 0
                max_pages = 50  # Limit to prevent infinite loops
                
                while page_count < max_pages:
                    logger.info(f"Scraping {company} - {state} - Page {page_count + 1}")
                    
                    # Extract advisors from current page
                    advisors = await self.extract_advisors_from_page(browser, company)
                    all_advisors.extend(advisors)
                    
                    # Try to go to next page
                    if not await self.handle_pagination(browser):
                        logger.info(f"No more pages for {company} - {state}")
                        break
                        
                    page_count += 1
                    
                    # Rate limiting
                    await asyncio.sleep(random.uniform(3, 6))
                    
            else:
                logger.error(f"Failed to navigate to search for {company} - {state}")
                
        except Exception as e:
            logger.error(f"Error scraping {company} - {state}: {e}")
        finally:
            await browser.close()
            
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
            data_dicts.append({
                'Name': advisor.name,
                'Phone': advisor.phone,
                'Street': advisor.street,
                'City': advisor.city,
                'State': advisor.state,
                'Email': advisor.email,
                'Company': advisor.company,
                'Source_URL': advisor.url
            })
        
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
    CLAUDE_API_KEY = "your_claude_api_key_here"
    
    scraper = IntelligentAdvisorScraper(CLAUDE_API_KEY)
    
    # Run the scraping process
    await scraper.scrape_all_companies_and_states()
    
    # Save the results
    scraper.save_data()

if __name__ == "__main__":
    # Run the scraper
    asyncio.run(main())
