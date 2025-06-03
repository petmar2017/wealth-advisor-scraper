# 🧠 Intelligent Wealth Advisor Scraper

An AI-powered web scraper that uses Claude 4 Opus reasoning, automatic URL discovery, and **CAPTCHA detection & handling** to extract wealth advisor information from UBS, Morgan Stanley, and Merrill Lynch websites.

## 🚀 NEW: CAPTCHA & Blocking Protection

### 🧩 **Automatic CAPTCHA Detection**
- **Problem Solved**: No more stuck sessions on CAPTCHA pages!
- Uses Claude Opus to detect CAPTCHAs, rate limiting, and blocking mechanisms
- Handles: reCAPTCHA, hCaptcha, Cloudflare protection, access denied pages
- **30-second automatic wait** for manual CAPTCHA solving
- Smart retry logic with progressive delays

### 🛡️ **Comprehensive Blocking Detection**
- **CAPTCHA challenges** (all types)
- **Rate limiting** messages
- **Access denied** or blocked pages
- **Cloudflare protection** pages
- **JavaScript challenges**
- **"Please verify you are human"** interstitials

### 🔍 **Intelligent URL Discovery**
- Automatic URL discovery using Google search + Claude reasoning
- Self-healing when websites change their structure
- Smart navigation adaptation for different site designs
- Working URL caching for future sessions

## ⚡ Quick Start

1. **Get Your Claude API Key**: https://console.anthropic.com/
2. **Setup**:
   ```bash
   cd ~/Downloads/code/web_scraper
   # Edit .env file and add your API key
   nano .env
   ```
3. **Run with CAPTCHA protection**:
   ```bash
   ./launch.sh captcha test      # CAPTCHA-aware test
   ./launch.sh captcha full      # Full scrape with CAPTCHA handling
   ./launch.sh captcha-test      # Test CAPTCHA detection only
   ```

## 🎯 Usage Examples

```bash
# CAPTCHA-AWARE MODES (Recommended for financial sites)
./launch.sh captcha test                    # Test with CAPTCHA handling
./launch.sh captcha full                    # Full scrape with CAPTCHA protection
./launch.sh captcha specific "New York"     # Specific states with CAPTCHA handling
./launch.sh captcha-test                    # Test CAPTCHA detection capabilities

# INTELLIGENT MODES
./launch.sh test                            # Intelligent test with URL discovery
./launch.sh discover                        # Test URL discovery only
./launch.sh full                            # Full intelligent scrape
./launch.sh specific "NY" "CA" "TX"         # Specific states intelligent mode

# BASIC MODE
./launch.sh simple                          # Fallback to basic scraper
```

## 🧩 CAPTCHA Handling Features

### **Automatic Detection**
- Analyzes page content to identify blocking mechanisms
- Detects various CAPTCHA types and protection systems
- Provides confidence scores and detailed descriptions

### **Smart Response**
- **CAPTCHAs**: 30-second wait with manual solving option
- **Rate Limiting**: Progressive delays (60+ seconds)
- **Access Denied**: Extended waits (120+ seconds)
- **Retry Logic**: Multiple attempts with different approaches

### **Manual Integration**
- Set `HEADLESS_MODE=False` to see browser and solve CAPTCHAs manually
- Visual countdown timers during wait periods
- Clear status messages about blocking type and action needed

## 🌐 Target Companies & Coverage

- **UBS**: Financial advisor directory
- **Morgan Stanley**: Advisor search portal  
- **Merrill Lynch**: Advisor locator

**States Covered**: NY, NJ, FL, TX, CA, IL, MA, GA, WA, DC, VA, MD, MI, CT, PA, NC, OH, RI, MN

## 🔧 Configuration

Edit `.env` file to customize CAPTCHA handling:

```bash
# CAPTCHA Settings
CAPTCHA_WAIT_TIME=30                    # Seconds to wait for CAPTCHA solving
CAPTCHA_MAX_RETRIES=3                   # Max retry attempts
RATE_LIMIT_WAIT_TIME=60                 # Wait time for rate limiting
ACCESS_DENIED_WAIT_TIME=120             # Wait time for access denied

# Browser Settings  
HEADLESS_MODE=False                     # Set to False for manual CAPTCHA solving
CAPTCHA_DETECTION_SENSITIVITY=high     # high|medium|low
MANUAL_CAPTCHA_SOLVING=true             # Enable manual solving
```

## 📊 Output & Monitoring

### **Data Formats**
- **CSV**: Structured advisor data
- **JSON**: Machine-readable format
- **Discovered URLs**: Working URL cache
- **CAPTCHA Statistics**: Encounter logs

### **Real-time Monitoring**
- Live CAPTCHA detection alerts
- Blocking type identification
- Wait time countdowns
- Success/failure statistics

## 🛡️ Advanced Protection Handling

### **Detection Capabilities**
```
✅ reCAPTCHA v2/v3          ✅ Cloudflare challenges
✅ hCaptcha                 ✅ Rate limiting messages
✅ Custom CAPTCHAs          ✅ Access denied pages
✅ JavaScript challenges    ✅ "Verify human" prompts
✅ Bot detection systems    ✅ Unusual redirects
```

### **Response Strategies**
- **Immediate**: Smart retry with different approach
- **Short Wait**: 30-60 seconds for rate limits
- **Extended Wait**: 2+ minutes for access denial
- **Manual Mode**: User interaction for complex CAPTCHAs
- **Alternative URLs**: Discover new working endpoints

## 🆘 Troubleshooting

**CAPTCHA Issues**:
```bash
# Test CAPTCHA detection
./launch.sh captcha-test

# Run with visible browser for manual solving
# Set HEADLESS_MODE=False in .env
./launch.sh captcha test
```

**Persistent Blocking**:
```bash
# Try URL discovery mode
./launch.sh discover

# Use extended wait times
# Increase RATE_LIMIT_WAIT_TIME in .env
```

**API Key Issues**:
```bash
# Verify API key
cat .env | grep CLAUDE_API_KEY
```

## 📈 Performance & Statistics

- **CAPTCHA Encounter Tracking**: Logs all blocking instances
- **Success Rate Monitoring**: Tracks resolution effectiveness  
- **URL Discovery Caching**: Reuses working URLs
- **Progressive Delay Logic**: Adapts to website behavior
- **Partial Data Recovery**: Saves progress on interruption

## ⚠️ Legal & Ethical Use

- **Terms of Service**: Ensure compliance with website ToS
- **Respectful Scraping**: Built-in delays and CAPTCHA respect
- **Data Protection**: Consider GDPR/CCPA requirements
- **Professional Use**: Verify licensing regulations

---

Built with ❤️ using Claude 4 Opus, Playwright, and intelligent automation

**🧩 CAPTCHA Protection • 🔍 Smart Discovery • 🧠 AI Reasoning**
