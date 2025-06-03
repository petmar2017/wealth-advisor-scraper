import asyncio
import json
import time
import random
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import pandas as pd
import logging
import re
from urllib.parse import urljoin, urlparse

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

class IntelligentAdvisorScraper:
    """Enhanced scraper with CAPTCHA detection, intelligent URL discovery and adaptation."""
    
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
        
        # Company configurations - these will be updated dynamically
        self.companies = {
            "UBS": {
                "base_url": "https://www.ubs.com/us/en/wealth-management/find-an-advisor.html",
                "search_pattern": "find-an-advisor",
                "backup_search_terms": "UBS financial advisor directory United States",
                "verified": False
            },
            "Morgan Stanley": {
                "base_url": "https://advisor.morganstanley.com/search",
                "search_pattern": "advisor-search",
                "backup_search_terms": "Morgan Stanley financial advisor directory search",
                "verified": False
            },
            "Merrill Lynch": {
                "base_url": "https://advisor.ml.com/search?bylocation=true",
                "search_pattern": "advisor-search",
                "backup_search_terms": "Merrill Lynch financial advisor directory search location",
                "verified": False
            }
        }
        
        self.scraped_data = []
        self.discovered_urls = {}  # Cache for discovered working URLs
        self.captcha_encounters = 0  # Track CAPTCHA encounters

    async def setup_browser(self):
        """Setup and configure the browser instance."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=ScraperConfig.HEADLESS_MODE,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        return self.browser

    async def detect_captcha_or_blocking(self, page: Page) -> Dict:
        """Use Claude to detect CAPTCHAs, rate limiting, or blocking mechanisms."""
        try:
            html_content = await page.content()
            current_url = page.url
            page_title = await page.title()
            
            # Take a screenshot for better analysis if needed
            screenshot_buffer = await page.screenshot()
            
            captcha_detection_prompt = f"""
            Analyze this webpage to detect if there are any blocking mechanisms, CAPTCHAs, or anti-bot measures:
            
            URL: {current_url}
            Page Title: {page_title}
            HTML Content (first 3000 chars): {html_content[:3000]}
            
            Look for signs of:
            1. CAPTCHA challenges (reCAPTCHA, hCaptcha, custom CAPTCHAs)
            2. Rate limiting messages
            3. "Access denied" or "Blocked" messages
            4. Cloudflare protection pages
            5. "Please verify you are human" messages
            6. Unusual redirects or interstitial pages
            7. Empty pages that should have content
            8. JavaScript-heavy pages that might be blocking bots
            
            Check for these keywords/patterns:
            - "captcha", "recaptcha", "hcaptcha"
            - "verify", "verification"
            - "robot", "bot", "automated"
            - "access denied", "forbidden"
            - "rate limit", "too many requests"
            - "cloudflare", "protection"
            - "please wait", "checking your browser"
            
            Respond with JSON:
            {{
                "blocking_detected": boolean,
                "blocking_type": "captcha|rate_limit|access_denied|cloudflare|javascript_challenge|unknown|none",
                "confidence": "high|medium|low",
                "description": "detailed description of what was detected",
                "action_required": "wait|solve_captcha|retry_later|change_approach|none",
                "wait_time_seconds": number,
                "captcha_location": "description of where captcha is on page if found",
                "bypass_suggestions": ["list of potential workarounds"]
            }}
            """
            
            message = self.client.messages.create(
                model="claude-3-opus-20240229",  # Using Opus for better detection
                max_tokens=2000,
                messages=[
                    {"role": "user", "content": captcha_detection_prompt}
                ]
            )
            
            response_text = message.content[0].text
            
            # Extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start != -1 and json_end != -1:
                detection = json.loads(response_text[json_start:json_end])
                
                blocking_detected = detection.get("blocking_detected", False)
                blocking_type = detection.get("blocking_type", "unknown")
                confidence = detection.get("confidence", "low")
                description = detection.get("description", "No description")
                
                if blocking_detected:
                    logger.warning(f"🚫 Blocking detected: {blocking_type} (confidence: {confidence})")
                    logger.warning(f"📝 Description: {description}")
                    self.captcha_encounters += 1
                else:
                    logger.info("✅ No blocking mechanisms detected")
                
                return detection
            
            return {"blocking_detected": False, "blocking_type": "none"}
            
        except Exception as e:
            logger.error(f"Error in CAPTCHA detection: {e}")
            return {"blocking_detected": False, "blocking_type": "unknown", "error": str(e)}

    async def handle_captcha_or_blocking(self, page: Page, detection: Dict) -> bool:
        """Handle detected CAPTCHAs or blocking mechanisms."""
        if not detection.get("blocking_detected", False):
            return True
        
        blocking_type = detection.get("blocking_type", "unknown")
        action_required = detection.get("action_required", "wait")
        wait_time = detection.get("wait_time_seconds", 30)
        description = detection.get("description", "Blocking detected")
        
        logger.warning(f"🛑 BLOCKING DETECTED: {blocking_type}")
        logger.warning(f"📋 Action required: {action_required}")
        logger.warning(f"⏰ Recommended wait time: {wait_time} seconds")
        logger.warning(f"📝 Details: {description}")
        
        if action_required == "solve_captcha":
            logger.info("🧩 CAPTCHA detected - waiting 30 seconds for manual solving...")
            print(f"\n🧩 CAPTCHA DETECTED on {page.url}")
            print(f"📝 Type: {blocking_type}")
            print(f"📋 Description: {description}")
            
            if not ScraperConfig.HEADLESS_MODE:
                print("👀 Browser is visible - you can solve the CAPTCHA manually")
                print("⏳ Waiting 30 seconds for you to solve it...")
            else:
                print("⚠️  Browser is in headless mode - cannot solve CAPTCHA manually")
                print("💡 Consider setting HEADLESS_MODE=False in .env for manual solving")
            
            # Wait for 30 seconds
            for i in range(30, 0, -1):
                print(f"⏳ Waiting {i} seconds for CAPTCHA solving...", end='\r')
                await asyncio.sleep(1)
            print("\n✅ Wait completed - continuing...")
            
        elif action_required == "wait":
            logger.info(f"⏳ Rate limiting detected - waiting {wait_time} seconds...")
            print(f"\n⏳ RATE LIMITING DETECTED")
            print(f"📝 Type: {blocking_type}")
            print(f"⏰ Waiting {wait_time} seconds before retrying...")
            
            # Wait with countdown
            for i in range(wait_time, 0, -1):
                print(f"⏳ Waiting {i} seconds...", end='\r')
                await asyncio.sleep(1)
            print("\n✅ Wait completed - retrying...")
            
        elif action_required == "retry_later":
            logger.warning(f"🚫 Access denied - waiting {wait_time} seconds before retry...")
            print(f"\n🚫 ACCESS DENIED DETECTED")
            print(f"📝 Description: {description}")
            print(f"⏰ Waiting {wait_time} seconds before retry...")
            
            await asyncio.sleep(wait_time)
            
        elif action_required == "change_approach":
            logger.warning("🔄 Need to change approach due to blocking")
            print(f"\n🔄 BLOCKING DETECTED - CHANGING APPROACH")
            print(f"📝 Type: {blocking_type}")
            print(f"💡 Suggestions: {detection.get('bypass_suggestions', [])}")
            
            # Wait a bit and return False to trigger alternative approach
            await asyncio.sleep(10)
            return False
        
        # After handling, check if we're still blocked
        await asyncio.sleep(2)  # Brief pause before checking
        recheck = await self.detect_captcha_or_blocking(page)
        
        if recheck.get("blocking_detected", False):
            logger.warning("⚠️  Still blocked after handling - may need manual intervention")
            return False
        else:
            logger.info("✅ Blocking resolved - continuing...")
            return True

    async def navigate_with_captcha_handling(self, page: Page, url: str, max_retries: int = 3) -> bool:
        """Navigate to URL with automatic CAPTCHA detection and handling."""
        for attempt in range(max_retries):
            try:
                logger.info(f"🌐 Navigating to {url} (attempt {attempt + 1}/{max_retries})")
                
                response = await page.goto(url, wait_until='networkidle', timeout=30000)
                
                # Check for HTTP errors
                if response and response.status >= 400:
                    logger.warning(f"⚠️ HTTP {response.status} error for {url}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(5)
                        continue
                    return False
                
                # Check for blocking mechanisms
                detection = await self.detect_captcha_or_blocking(page)
                
                if detection.get("blocking_detected", False):
                    handled = await self.handle_captcha_or_blocking(page, detection)
                    if not handled and attempt < max_retries - 1:
                        logger.info(f"🔄 Retrying navigation after blocking (attempt {attempt + 2}/{max_retries})")
                        await asyncio.sleep(5)
                        continue
                    elif not handled:
                        logger.error(f"❌ Could not resolve blocking after {max_retries} attempts")
                        return False
                
                logger.info("✅ Successfully navigated without blocking")
                return True
                
            except Exception as e:
                logger.error(f"💥 Navigation error (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(5)
                    continue
                return False
        
        return False

    async def intelligent_url_discovery(self, company: str) -> Optional[str]:
        """Use Google search and Claude reasoning to find working advisor directory URLs."""
        logger.info(f"🔍 Discovering working URL for {company}...")
        
        company_config = self.companies[company]
        search_terms = company_config["backup_search_terms"]
        
        try:
            # Create a new page for URL discovery
            browser = await self.setup_browser()
            page = await browser.new_page()
            
            # Perform Google search with CAPTCHA handling
            google_search_url = f"https://www.google.com/search?q={search_terms.replace(' ', '+')}"
            
            if not await self.navigate_with_captcha_handling(page, google_search_url):
                logger.error(f"❌ Could not access Google search for {company}")
                await browser.close()
                return None
            
            # Get search results
            html_content = await page.content()
            
            # Use Claude to analyze search results and find the best URL
            analysis_prompt = f"""
            I'm looking for the official {company} financial advisor directory/search page.
            
            Here are Google search results (HTML snippet):
            {html_content[:4000]}
            
            Please analyze these search results and identify the best URL for finding {company} financial advisors.
            
            Look for:
            1. Official {company} website URLs that lead to advisor directories
            2. Pages that allow searching for advisors by location
            3. Avoid third-party sites or general company pages
            
            Respond with JSON:
            {{
                "recommended_url": "the best URL found",
                "confidence": "high|medium|low",
                "reasoning": "why this URL is the best choice",
                "alternative_urls": ["other potential URLs found"],
                "search_strategy": "how to use this URL to find advisors"
            }}
            """
            
            message = self.client.messages.create(
                model="claude-3-opus-20240229",  # Using Opus for better reasoning
                max_tokens=2000,
                messages=[
                    {"role": "user", "content": analysis_prompt}
                ]
            )
            
            response_text = message.content[0].text
            
            # Extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start != -1 and json_end != -1:
                analysis = json.loads(response_text[json_start:json_end])
                
                recommended_url = analysis.get("recommended_url")
                confidence = analysis.get("confidence", "low")
                reasoning = analysis.get("reasoning", "No reasoning provided")
                
                logger.info(f"🎯 Found URL for {company}: {recommended_url}")
                logger.info(f"📊 Confidence: {confidence}")
                logger.info(f"🧠 Reasoning: {reasoning}")
                
                # Verify the URL actually works
                if recommended_url and await self.verify_url_works(page, recommended_url):
                    # Update company config with working URL
                    self.companies[company]["base_url"] = recommended_url
                    self.companies[company]["verified"] = True
                    self.discovered_urls[company] = recommended_url
                    
                    logger.info(f"✅ Verified working URL for {company}")
                    await browser.close()
                    return recommended_url
                else:
                    # Try alternative URLs
                    for alt_url in analysis.get("alternative_urls", []):
                        if await self.verify_url_works(page, alt_url):
                            self.companies[company]["base_url"] = alt_url
                            self.companies[company]["verified"] = True
                            self.discovered_urls[company] = alt_url
                            logger.info(f"✅ Verified alternative URL for {company}: {alt_url}")
                            await browser.close()
                            return alt_url
            
            await browser.close()
            
        except Exception as e:
            logger.error(f"Error in URL discovery for {company}: {e}")
            if 'browser' in locals():
                await browser.close()
        
        logger.warning(f"⚠️ Could not find working URL for {company}")
        return None

    async def verify_url_works(self, page: Page, url: str) -> bool:
        """Verify that a URL is accessible and contains advisor-related content."""
        try:
            # Use CAPTCHA-aware navigation
            if not await self.navigate_with_captcha_handling(page, url):
                return False
            
            html_content = await page.content()
            
            # Use Claude to verify this is actually an advisor directory
            verification_prompt = f"""
            Check if this webpage is a financial advisor directory or search page:
            
            URL: {url}
            HTML content (first 2000 chars): {html_content[:2000]}
            
            Respond with JSON:
            {{
                "is_advisor_directory": boolean,
                "confidence": "high|medium|low",
                "has_search_functionality": boolean,
                "advisor_related_keywords_found": ["list", "of", "keywords"]
            }}
            """
            
            message = self.client.messages.create(
                model="claude-3-sonnet-20241022",
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": verification_prompt}
                ]
            )
            
            response_text = message.content[0].text
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                verification = json.loads(response_text[json_start:json_end])
                
                is_directory = verification.get("is_advisor_directory", False)
                confidence = verification.get("confidence", "low")
                
                logger.info(f"📋 URL verification: {is_directory} (confidence: {confidence})")
                
                return is_directory and confidence != "low"
            
            return False
            
        except Exception as e:
            logger.error(f"Error verifying URL {url}: {e}")
            return False

    async def smart_navigation_to_state_search(self, page: Page, company: str, state: str) -> bool:
        """Intelligently navigate to state search with CAPTCHA handling and adaptive URL discovery."""
        company_config = self.companies[company]
        base_url = company_config["base_url"]
        
        # First, check if we have a verified working URL
        if not company_config.get("verified", False):
            logger.info(f"🔄 URL not verified for {company}, discovering correct URL...")
            discovered_url = await self.intelligent_url_discovery(company)
            if not discovered_url:
                logger.error(f"❌ Could not find working URL for {company}")
                return False
            base_url = discovered_url
        
        try:
            logger.info(f"🌐 Navigating to {company} for state: {state}")
            
            # Use CAPTCHA-aware navigation
            if not await self.navigate_with_captcha_handling(page, base_url):
                logger.warning(f"⚠️ Navigation failed for {company}, trying URL discovery...")
                discovered_url = await self.intelligent_url_discovery(company)
                if discovered_url:
                    if not await self.navigate_with_captcha_handling(page, discovered_url):
                        return False
                else:
                    return False
            
            await asyncio.sleep(random.uniform(2, 4))
            
            # Check for blocking after initial navigation
            detection = await self.detect_captcha_or_blocking(page)
            if detection.get("blocking_detected", False):
                if not await self.handle_captcha_or_blocking(page, detection):
                    return False
            
            # Get current page content
            html_content = await page.content()
            current_url = page.url
            
            # Use Claude to intelligently figure out how to search
            search_strategy_prompt = f"""
            I'm on a {company} website and need to search for financial advisors in {state}.
            
            Current URL: {current_url}
            HTML content (first 3000 chars): {html_content[:3000]}
            
            Analyze this page and provide a step-by-step strategy to search for advisors in {state}.
            
            Look for:
            1. Search fields, forms, or filters
            2. Location/state selection options
            3. Navigation menus that might lead to advisor search
            4. Any buttons or links related to "find advisor", "search", etc.
            
            Respond with JSON:
            {{
                "strategy": "direct_search|navigate_first|complex_form",
                "steps": [
                    {{
                        "action": "fill|click|select|navigate",
                        "selector": "css_selector_or_text",
                        "value": "value_to_enter_or_click",
                        "description": "what this step does"
                    }}
                ],
                "confidence": "high|medium|low",
                "alternative_approach": "backup plan if main strategy fails"
            }}
            """
            
            message = self.client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=2000,
                messages=[
                    {"role": "user", "content": search_strategy_prompt}
                ]
            )
            
            response_text = message.content[0].text
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                strategy = json.loads(response_text[json_start:json_end])
                
                logger.info(f"🎯 Search strategy: {strategy.get('strategy', 'unknown')}")
                
                # Execute the strategy steps
                for step in strategy.get("steps", []):
                    try:
                        action = step.get("action")
                        selector = step.get("selector")
                        value = step.get("value", "")
                        description = step.get("description", "")
                        
                        logger.info(f"🔧 Executing: {description}")
                        
                        if action == "fill":
                            element = await page.wait_for_selector(selector, timeout=5000)
                            if element:
                                await element.clear()
                                await element.fill(value.replace("{state}", state))
                                
                        elif action == "click":
                            # Try different ways to find the element
                            element = None
                            try:
                                element = await page.wait_for_selector(selector, timeout=5000)
                            except:
                                # Try by text content if selector fails
                                try:
                                    element = await page.wait_for_selector(f"text={selector}", timeout=3000)
                                except:
                                    pass
                            
                            if element:
                                await element.click()
                                await page.wait_for_load_state('networkidle', timeout=10000)
                                
                                # Check for CAPTCHAs after clicks
                                detection = await self.detect_captcha_or_blocking(page)
                                if detection.get("blocking_detected", False):
                                    await self.handle_captcha_or_blocking(page, detection)
                                
                        elif action == "select":
                            element = await page.wait_for_selector(selector, timeout=5000)
                            if element:
                                await element.select_option(value.replace("{state}", state))
                                
                        elif action == "navigate":
                            await self.navigate_with_captcha_handling(page, value)
                        
                        await asyncio.sleep(1)  # Small delay between steps
                        
                    except Exception as step_error:
                        logger.warning(f"⚠️ Step failed: {description} - {step_error}")
                        continue
                
                # Check if we successfully navigated to search results
                final_html = await page.content()
                final_url = page.url
                
                # Final CAPTCHA check
                detection = await self.detect_captcha_or_blocking(page)
                if detection.get("blocking_detected", False):
                    if not await self.handle_captcha_or_blocking(page, detection):
                        return False
                
                # Use Claude to verify we're now on a search results page
                verification_prompt = f"""
                Check if we successfully navigated to a page showing financial advisor search results or a search interface:
                
                URL: {final_url}
                HTML (first 2000 chars): {final_html[:2000]}
                
                Respond with JSON:
                {{
                    "success": boolean,
                    "page_type": "search_results|search_form|other",
                    "advisor_count_estimate": "number or 'unknown'",
                    "next_action_needed": "description of what to do next"
                }}
                """
                
                verification_message = self.client.messages.create(
                    model="claude-3-sonnet-20241022",
                    max_tokens=1000,
                    messages=[
                        {"role": "user", "content": verification_prompt}
                    ]
                )
                
                verification_text = verification_message.content[0].text
                json_start = verification_text.find('{')
                json_end = verification_text.rfind('}') + 1
                
                if json_start != -1 and json_end != -1:
                    verification = json.loads(verification_text[json_start:json_end])
                    success = verification.get("success", False)
                    
                    logger.info(f"🎯 Navigation result: {'Success' if success else 'Failed'}")
                    return success
            
            # Fallback: try simple search patterns
            return await self.fallback_search_attempt(page, state)
            
        except Exception as e:
            logger.error(f"Error in smart navigation for {company} - {state}: {e}")
            return False

    async def fallback_search_attempt(self, page: Page, state: str) -> bool:
        """Fallback search attempt using common patterns with CAPTCHA handling."""
        logger.info("🔄 Attempting fallback search...")
        
        try:
            # Check for blocking before attempting fallback
            detection = await self.detect_captcha_or_blocking(page)
            if detection.get("blocking_detected", False):
                if not await self.handle_captcha_or_blocking(page, detection):
                    return False
            
            # Common search field selectors
            search_selectors = [
                "input[placeholder*='location' i]",
                "input[placeholder*='city' i]", 
                "input[placeholder*='state' i]",
                "input[name*='location' i]",
                "input[id*='location' i]",
                "input[type='search']",
                "input[name*='search']",
                "#location",
                "#search",
                ".search-input"
            ]
            
            for selector in search_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=3000)
                    if element:
                        await element.clear()
                        await element.fill(state)
                        
                        # Try to submit
                        await element.press('Enter')
                        await page.wait_for_load_state('networkidle', timeout=10000)
                        
                        # Check for CAPTCHAs after submission
                        detection = await self.detect_captcha_or_blocking(page)
                        if detection.get("blocking_detected", False):
                            await self.handle_captcha_or_blocking(page, detection)
                        
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"Fallback search failed: {e}")
            return False

    # [Rest of the methods with CAPTCHA handling integrated...]
    async def extract_advisors_from_page(self, page: Page, company: str) -> List[AdvisorInfo]:
        """Extract advisor information from current page with CAPTCHA handling."""
        try:
            # Check for blocking before extraction
            detection = await self.detect_captcha_or_blocking(page)
            if detection.get("blocking_detected", False):
                if not await self.handle_captcha_or_blocking(page, detection):
                    logger.warning("⚠️  Could not resolve blocking during extraction")
                    return []
            
            html_content = await page.content()
            current_url = page.url
            
            # Enhanced prompt for better extraction
            extraction_prompt = f"""
            Extract financial advisor information from this {company} directory page.
            
            URL: {current_url}
            HTML content (first 4000 chars): {html_content[:4000]}
            
            Look for advisor listings containing:
            - Full names
            - Phone numbers
            - Office addresses (street, city, state)
            - Email addresses
            - Branch/office information
            
            Respond with JSON:
            {{
                "has_advisors": boolean,
                "advisor_count": number,
                "advisors": [
                    {{
                        "name": "Full Name",
                        "phone": "phone number",
                        "street": "street address",
                        "city": "city",
                        "state": "state",
                        "email": "email address"
                    }}
                ],
                "page_info": {{
                    "total_results_mentioned": "number if shown",
                    "current_page": "page number if shown",
                    "has_more_pages": boolean
                }}
            }}
            
            Be thorough but only extract clear, complete information.
            """
            
            message = self.client.messages.create(
                model="claude-3-opus-20240229",  # Using Opus for better extraction
                max_tokens=4000,
                messages=[
                    {"role": "user", "content": extraction_prompt}
                ]
            )
            
            response_text = message.content[0].text
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                analysis = json.loads(response_text[json_start:json_end])
                
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
                
                logger.info(f"📊 Extracted {len(advisors)} advisors from {current_url}")
                
                # Log page info for debugging
                page_info = analysis.get("page_info", {})
                if page_info.get("total_results_mentioned"):
                    logger.info(f"📈 Total results mentioned: {page_info['total_results_mentioned']}")
                
                return advisors
            
            return []
            
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
        """Handle pagination with CAPTCHA detection."""
        try:
            # Check for blocking before pagination
            detection = await self.detect_captcha_or_blocking(page)
            if detection.get("blocking_detected", False):
                if not await self.handle_captcha_or_blocking(page, detection):
                    return False
            
            html_content = await page.content()
            current_url = page.url
            
            pagination_prompt = f"""
            Analyze this page for pagination or "load more" functionality:
            
            URL: {current_url}
            HTML: {html_content[:3000]}
            
            Look for:
            - "Next" buttons or links
            - "Load More" buttons
            - Page numbers (1, 2, 3...)
            - Infinite scroll indicators
            - "Show more results" options
            
            Respond with JSON:
            {{
                "has_pagination": boolean,
                "pagination_type": "next_button|load_more|page_numbers|infinite_scroll|none",
                "action_needed": "click|scroll|none",
                "selector": "css_selector_or_text_to_click",
                "confidence": "high|medium|low"
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
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                pagination_info = json.loads(response_text[json_start:json_end])
                
                if pagination_info.get("has_pagination", False):
                    action = pagination_info.get("action_needed", "none")
                    selector = pagination_info.get("selector", "")
                    confidence = pagination_info.get("confidence", "low")
                    
                    logger.info(f"🔄 Pagination detected: {pagination_info.get('pagination_type')} (confidence: {confidence})")
                    
                    if action == "click" and selector:
                        try:
                            # Try CSS selector first
                            element = None
                            try:
                                element = await page.wait_for_selector(selector, timeout=5000)
                            except:
                                # Try text selector
                                try:
                                    element = await page.wait_for_selector(f"text={selector}", timeout=3000)
                                except:
                                    pass
                            
                            if element:
                                await element.click()
                                await page.wait_for_load_state('networkidle', timeout=15000)
                                
                                # Check for CAPTCHAs after pagination
                                detection = await self.detect_captcha_or_blocking(page)
                                if detection.get("blocking_detected", False):
                                    await self.handle_captcha_or_blocking(page, detection)
                                
                                logger.info("✅ Successfully navigated to next page")
                                return True
                                
                        except Exception as click_error:
                            logger.warning(f"⚠️ Click failed: {click_error}")
                            
                    elif action == "scroll":
                        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        await asyncio.sleep(3)
                        
                        # Check if new content loaded
                        new_html = await page.content()
                        if len(new_html) > len(html_content):
                            logger.info("✅ New content loaded after scroll")
                            return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error handling pagination: {e}")
            return False

    async def scrape_company_state(self, company: str, state: str) -> List[AdvisorInfo]:
        """Scrape all advisors for a specific company and state with intelligent adaptation and CAPTCHA handling."""
        browser = await self.setup_browser()
        all_advisors = []
        
        try:
            page = await browser.new_page()
            
            # Smart navigation with URL discovery and CAPTCHA handling
            if await self.smart_navigation_to_state_search(page, company, state):
                page_count = 0
                max_pages = ScraperConfig.MAX_PAGES_PER_STATE
                consecutive_empty_pages = 0
                max_empty_pages = 3
                
                while page_count < max_pages:
                    logger.info(f"📄 Scraping {company} - {state} - Page {page_count + 1}")
                    
                    # Extract advisors from current page
                    advisors = await self.extract_advisors_from_page(page, company)
                    
                    if not advisors:
                        consecutive_empty_pages += 1
                        logger.warning(f"⚠️ No advisors found on page {page_count + 1}")
                        if consecutive_empty_pages >= max_empty_pages:
                            logger.info(f"🛑 Stopping after {consecutive_empty_pages} empty pages")
                            break
                    else:
                        consecutive_empty_pages = 0
                        all_advisors.extend(advisors)
                        logger.info(f"✅ Found {len(advisors)} advisors on this page")
                    
                    # Check if we've hit our limit
                    if len(all_advisors) >= ScraperConfig.MAX_ADVISORS_PER_COMPANY:
                        logger.info(f"🎯 Reached advisor limit for {company}")
                        break
                    
                    # Try to go to next page
                    if not await self.handle_pagination(page):
                        logger.info(f"🏁 No more pages for {company} - {state}")
                        break
                        
                    page_count += 1
                    
                    # Rate limiting
                    await asyncio.sleep(random.uniform(
                        ScraperConfig.MIN_DELAY, 
                        ScraperConfig.MAX_DELAY
                    ))
                    
            else:
                logger.error(f"❌ Failed to navigate to search for {company} - {state}")
                
        except Exception as e:
            logger.error(f"💥 Error scraping {company} - {state}: {e}")
        finally:
            await browser.close()
            await self.playwright.stop()
            
        return all_advisors

    async def scrape_all_companies_and_states(self):
        """Main scraping function with intelligent adaptation and CAPTCHA handling."""
        logger.info("🚀 Starting intelligent advisor scraping with CAPTCHA handling...")
        
        for company in self.companies.keys():
            for state in self.target_states:
                try:
                    logger.info(f"🎯 Starting {company} - {state}")
                    advisors = await self.scrape_company_state(company, state)
                    self.scraped_data.extend(advisors)
                    
                    logger.info(f"✅ Completed {company} - {state}: {len(advisors)} advisors found")
                    
                    # Save discovered URLs for future use
                    self.save_discovered_urls()
                    
                    # Longer delay between different company/state combinations
                    await asyncio.sleep(random.uniform(10, 20))
                    
                except Exception as e:
                    logger.error(f"💥 Error with {company} - {state}: {e}")
                    continue
        
        # Log CAPTCHA encounter statistics
        if self.captcha_encounters > 0:
            logger.info(f"🧩 Total CAPTCHA/blocking encounters: {self.captcha_encounters}")

    def save_discovered_urls(self):
        """Save discovered working URLs for future use."""
        if self.discovered_urls:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            with open(f"discovered_urls_{timestamp}.json", 'w') as f:
                json.dump(self.discovered_urls, f, indent=2)
                
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
        logger.info(f"💾 Data saved to {csv_filename}")
        
        # Save as JSON
        json_filename = f"{filename}.json"
        with open(json_filename, 'w') as f:
            json.dump(data_dicts, f, indent=2)
        logger.info(f"💾 Data saved to {json_filename}")
        
        # Print summary
        print(f"\n📊 SCRAPING SUMMARY:")
        print(f"Total advisors found: {len(self.scraped_data)}")
        print(f"CAPTCHA encounters: {self.captcha_encounters}")
        print(f"By company:")
        for company in self.companies.keys():
            count = len([a for a in self.scraped_data if a.company == company])
            print(f"  {company}: {count}")
        
        # Save discovered URLs summary
        if self.discovered_urls:
            print(f"\n🔍 DISCOVERED URLS:")
            for company, url in self.discovered_urls.items():
                print(f"  {company}: {url}")

# Usage example
async def main():
    # Initialize scraper with your Claude API key
    scraper = IntelligentAdvisorScraper(ScraperConfig.CLAUDE_API_KEY)
    
    # Run the scraping process
    await scraper.scrape_all_companies_and_states()
    
    # Save the results
    scraper.save_data()

if __name__ == "__main__":
    # Run the scraper
    asyncio.run(main())
