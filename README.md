# 🧠 Intelligent Wealth Advisor Scraper

An AI-powered web scraper that uses Claude 4 Opus reasoning and automatic URL discovery to extract wealth advisor information from UBS, Morgan Stanley, and Merrill Lynch websites.

## 🚀 NEW: Intelligent Features

### 🔍 **Automatic URL Discovery**
- **Problem Solved**: No more 404 errors or broken URLs!
- Uses Google search + Claude Opus reasoning to find current working advisor directory URLs
- Self-healing when websites change their structure
- Automatically updates and saves working URLs for future use

### 🧠 **Smart Navigation**
- Claude analyzes each webpage to understand navigation patterns
- Adapts to different website designs automatically
- Intelligent form filling and search execution
- Handles complex multi-step navigation flows

### 📊 **Enhanced Data Extraction**
- Claude Opus for superior advisor information extraction
- Handles different page layouts and designs
- Extracts: name, phone, street, city, state, email
- Smart pagination detection and handling

## ⚡ Quick Start

1. **Get Your Claude API Key**: https://console.anthropic.com/
2. **Setup**:
   ```bash
   cd ~/Downloads/code/web_scraper
   # Edit .env file and add your API key
   nano .env
   ```
3. **Run**:
   ```bash
   ./launch.sh test      # Intelligent test mode
   ./launch.sh discover  # Test URL discovery
   ./launch.sh full      # Full intelligent scrape
   ```

## 🎯 Usage Examples

```bash
# Test intelligent scraper (recommended first run)
./launch.sh test

# Test URL discovery for all companies
./launch.sh discover

# Full scrape with intelligent adaptation
./launch.sh full

# Specific states with intelligent mode
./launch.sh specific "New York" "California" "Texas"

# Fallback to simple mode if needed
./launch.sh simple
```

## 🌐 Target Companies & Coverage

- **UBS**: Financial advisor directory
- **Morgan Stanley**: Advisor search portal  
- **Merrill Lynch**: Advisor locator

**States Covered**: NY, NJ, FL, TX, CA, IL, MA, GA, WA, DC, VA, MD, MI, CT, PA, NC, OH, RI, MN

## 🛡️ Intelligent Error Handling

- **404 Detection**: Automatically discovers new working URLs
- **Rate Limiting**: Respectful delays between requests
- **Partial Recovery**: Saves data if interrupted
- **Comprehensive Logging**: Detailed execution logs

## 📊 Output Formats

- **CSV**: Structured data for analysis
- **JSON**: Machine-readable format
- **Discovered URLs**: Working URLs for future use
- **Execution Logs**: Detailed operation history

## ⚠️ Legal & Ethical Use

- **Terms of Service**: Ensure compliance with website ToS
- **Rate Limiting**: Built-in delays to respect servers
- **Data Protection**: Consider GDPR/CCPA requirements
- **Professional Use**: Verify licensing regulations

## 🔧 Configuration

Edit `.env` file to customize:
- `CLAUDE_API_KEY`: Your Anthropic API key
- `HEADLESS_MODE`: Browser visibility (true/false)
- `MIN_DELAY` / `MAX_DELAY`: Rate limiting settings
- `MAX_PAGES_PER_STATE`: Pagination limits

## 🆘 Troubleshooting

**API Key Issues**:
```bash
# Check your .env file
cat .env
# Make sure CLAUDE_API_KEY is set correctly
```

**Browser Issues**:
```bash
# Reinstall browser
source venv/bin/activate
playwright install chromium
```

**URL Discovery Problems**:
```bash
# Test URL discovery only
./launch.sh discover
```

## 📈 Performance

- **Smart Caching**: Discovered URLs are cached
- **Adaptive Pagination**: Handles different pagination styles
- **Error Recovery**: Continues on individual page failures
- **Resource Efficient**: Closes browsers properly

Built with ❤️ using Claude 4 Opus, Playwright, and Python
