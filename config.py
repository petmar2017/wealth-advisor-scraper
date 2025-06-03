import os
from dotenv import load_dotenv

load_dotenv()

class ScraperConfig:
    """Configuration class for the wealth advisor scraper."""
    
    # API Keys
    CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY', 'your_claude_api_key_here')
    
    # Browser settings
    HEADLESS_MODE = os.getenv('HEADLESS_MODE', 'False').lower() == 'true'
    BROWSER_TIMEOUT = int(os.getenv('BROWSER_TIMEOUT', '30'))
    
    # Rate limiting
    MIN_DELAY = float(os.getenv('MIN_DELAY', '2.0'))
    MAX_DELAY = float(os.getenv('MAX_DELAY', '5.0'))
    PAGE_DELAY = float(os.getenv('PAGE_DELAY', '10.0'))
    
    # CAPTCHA & Blocking Handling
    CAPTCHA_WAIT_TIME = int(os.getenv('CAPTCHA_WAIT_TIME', '30'))
    CAPTCHA_MAX_RETRIES = int(os.getenv('CAPTCHA_MAX_RETRIES', '3'))
    RATE_LIMIT_WAIT_TIME = int(os.getenv('RATE_LIMIT_WAIT_TIME', '60'))
    ACCESS_DENIED_WAIT_TIME = int(os.getenv('ACCESS_DENIED_WAIT_TIME', '120'))
    
    # Output settings
    OUTPUT_DIRECTORY = os.getenv('OUTPUT_DIRECTORY', './scraped_data')
    SAVE_FORMAT = os.getenv('SAVE_FORMAT', 'both')  # csv, json, or both
    
    # Scraping limits
    MAX_PAGES_PER_STATE = int(os.getenv('MAX_PAGES_PER_STATE', '50'))
    MAX_ADVISORS_PER_COMPANY = int(os.getenv('MAX_ADVISORS_PER_COMPANY', '10000'))
    
    # Target states (can be overridden via environment)
    TARGET_STATES = os.getenv('TARGET_STATES', 
        'New York,New Jersey,Florida,Texas,California,Illinois,Massachusetts,Georgia,Washington,Washington DC,Virginia,Maryland,Michigan,Connecticut,Pennsylvania,North Carolina,Ohio,Rhode Island,Minnesota'
    ).split(',')
    
    # Companies to scrape
    TARGET_COMPANIES = os.getenv('TARGET_COMPANIES', 'UBS,Morgan Stanley,Merrill Lynch').split(',')
    
    # Advanced CAPTCHA Settings
    AUTO_SOLVE_SIMPLE_CAPTCHAS = os.getenv('AUTO_SOLVE_SIMPLE_CAPTCHAS', 'false').lower() == 'true'
    MANUAL_CAPTCHA_SOLVING = os.getenv('MANUAL_CAPTCHA_SOLVING', 'true').lower() == 'true'
    CAPTCHA_DETECTION_SENSITIVITY = os.getenv('CAPTCHA_DETECTION_SENSITIVITY', 'high').lower()
