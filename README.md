# Intelligent Wealth Advisor Scraper

An intelligent web scraping tool that uses browser automation, LangChain, and Claude 4 Opus to extract wealth advisor information from UBS, Morgan Stanley, and Merrill Lynch websites.

## Features

- 🧠 **LLM-Powered Intelligence**: Uses Claude 4 Opus for smart decision making
- 🌐 **Multi-Company Support**: UBS, Morgan Stanley, Merrill Lynch
- 🗺️ **Multi-State Scraping**: Covers 19 US states including NY, CA, FL, TX
- 🛡️ **Robust Error Handling**: Retry logic, partial data saving, comprehensive logging
- 📊 **Smart Data Extraction**: Extracts name, phone, address, email automatically

## Quick Start

1. **Setup Environment**:
   ```bash
   cd ~/Downloads/code/web_scraper
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   playwright install chromium
   ```

2. **Configure API Key**:
   ```bash
   cp .env.template .env
   # Edit .env and add your Claude API key
   ```

3. **Run Test**:
   ```bash
   python example_usage.py --mode test
   ```

4. **Full Scrape**:
   ```bash
   python example_usage.py --mode full
   ```

## Usage Examples

- **Test with one state**: `python example_usage.py --mode test`
- **Full scrape**: `python example_usage.py --mode full`
- **Specific states**: `python example_usage.py --mode specific --states "New York" "California"`

## Output

Data is saved in both CSV and JSON formats with timestamps.

## Legal Notice

⚠️ **Important**: Ensure compliance with website Terms of Service and applicable laws before scraping.

## Requirements

- Python 3.8+
- Claude API key
- Chrome/Chromium browser
