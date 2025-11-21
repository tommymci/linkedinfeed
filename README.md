# LinkedIn Feed Scraper & RSS Generator

Scrape posts from your LinkedIn company/showcase pages and convert them to RSS feeds.

## Features

- 🔐 Persistent login (login once, reuse session across pages)
- 📝 Scrapes company/showcase posts with title, content, link, date, and images
- 🖼️ Extracts and displays post images in the feed
- 📡 Generates styled RSS feed with XSLT for browser viewing
- 📊 Automatic sorting by date (newest first)
- ⏰ Full timestamps with date and time
- 🎨 Beautiful compact web interface for viewing feeds
- 💾 Saves posts to JSON with metadata for tracking
- ♻️ **Incremental scraping** - only fetch new posts after initial run
- 🏷️ **Multi-page support** - scrape multiple company/showcase pages
- 🎯 **Smart exit conditions** - avoids infinite loops (max 20 scrolls or 100 posts)
- 📛 **Automatic page name extraction** - uses real page names in feeds

## Prerequisites

- Python 3.8 or higher
- Homebrew (for macOS)

## Installation

### Step 1: Install Python Dependencies

```bash
cd LinkedinFeed

# Install required packages
pip3 install -r requirements.txt

# Install Playwright browsers
python3 -m playwright install chromium
```

### Step 2: First Run (Login & Scrape)

Run the scraper for the first time. A browser window will open:

```bash
# Default: scrapes Master Concept page
python3 linkedin_scraper.py

# Or specify a different page
python3 linkedin_scraper.py "https://www.linkedin.com/showcase/digital-action-lab/posts/"
```

**What will happen:**
1. Browser opens and navigates to LinkedIn
2. You'll see the LinkedIn login page (first time only)
3. **Log in manually** with your credentials
4. After login, the script continues automatically
5. Extracts page name (e.g., "Master Concept Group")
6. Scrapes the **latest 10 posts** (initial run)
7. Saves your login session for future runs

**Files created:**
- `{slug}_posts.json` - Scraped posts data with metadata (e.g., `master-concept_posts.json`)
- `browser_state/linkedin_state.json` - Saved login session (shared across pages)
- `after_sort_screenshot.png` - Screenshot after clicking sort button

### Step 3: Generate RSS Feed

After scraping posts, generate the RSS feed:

```bash
# Auto-detects latest scraped page
python3 generate_rss.py

# Or specify the slug
python3 generate_rss.py master-concept
python3 generate_rss.py digital-action-lab
```

**Output:**
- `{slug}.xml` - RSS feed file (e.g., `master-concept.xml`)

## Usage

### Scraping Multiple Pages

You can scrape multiple company/showcase pages. Each page gets its own files:

```bash
# Scrape Master Concept (company page)
python3 linkedin_scraper.py "https://www.linkedin.com/company/master-concept/posts/"

# Scrape Digital Action Lab (showcase page)
python3 linkedin_scraper.py "https://www.linkedin.com/showcase/digital-action-lab/posts/"

# Generate RSS feeds for both
python3 generate_rss.py master-concept
python3 generate_rss.py digital-action-lab
```

### Incremental Scraping

After the initial run, the scraper intelligently fetches only NEW posts:

```bash
# First run: scrapes 10 posts
python3 linkedin_scraper.py

# Subsequent runs: scrapes until reaching existing latest post
python3 linkedin_scraper.py
# Output: "🎯 Found target post! Stopping here."
```

**How it works:**
- Checks existing XML for latest post link
- Scrolls and scrapes until finding that post
- Stops immediately (no duplicates)
- Merges new posts at the beginning (recent-first order)
- **Exit conditions:** Stops after 20 scrolls OR 100 posts if target not found

### Automated Scraping

Run both scripts together:

```bash
# Default page
python3 linkedin_scraper.py && python3 generate_rss.py

# Specific page
python3 linkedin_scraper.py "URL" && python3 generate_rss.py slug
```

### View Feed in Browser

Start a local server to view the styled RSS feed:

```bash
python3 serve.py
```

Then open the feed in your browser:
- Master Concept: http://localhost:8000/master-concept.xml
- Digital Action Lab: http://localhost:8000/digital-action-lab.xml

The feed displays with a beautifully styled compact layout:
- Thumbnail images (16:9) on the left
- Title and truncated description on the right
- "Read more →" to expand inline (no page navigation)
- Date in bottom-right corner

### Configuration

You can customize settings in `linkedin_scraper.py`:

```python
# Line ~656: Default URL
COMPANY_URL = "https://www.linkedin.com/company/master-concept/posts/?feedView=all&sortBy=recent&viewAsMember=true"

# Line ~657: Run headless (no browser window)
HEADLESS = False  # Set True for automation

# Line ~658: Initial posts limit
MAX_POSTS_INITIAL = 10  # Number of posts to scrape on first run
```

## Files Structure

```
LinkedinFeed/
├── linkedin_scraper.py          # Main scraper script (multi-page support)
├── generate_rss.py              # RSS feed generator
├── cleanup_old_files.py         # Cleanup script for old generic files
├── serve.py                     # Local HTTP server
├── test_feed.py                 # Test feed page for debugging
├── requirements.txt             # Python dependencies
├── README.md                    # This file
├── rss-style.xsl                # XSLT stylesheet for RSS (generated)
├── {slug}_posts.json            # Scraped posts per page (generated)
│   ├── master-concept_posts.json
│   └── digital-action-lab_posts.json
├── {slug}.xml                   # RSS feed per page (generated)
│   ├── master-concept.xml
│   └── digital-action-lab.xml
├── browser_state/               # Saved login session (generated, shared)
│   └── linkedin_state.json
└── .gitignore                   # Git ignore file
```

## Troubleshooting

### "No posts found"

1. Check if you're logged in successfully
2. LinkedIn may have changed their page structure
3. View `debug_screenshot.png` to see what the scraper sees

### "Login timeout"

- The script waits 2 minutes for login
- If you need more time, edit line ~110 in `linkedin_scraper.py`:
  ```python
  page.wait_for_url(..., timeout=300000)  # 5 minutes
  ```

### Posts not updating

- Check if incremental mode found the target post (shows "🎯 Found target post!")
- Delete `{slug}.xml` to force re-scraping all posts
- Delete `{slug}_posts.json` to start fresh
- Delete `browser_state/` folder to re-login

### Cleaning up old files

If you upgraded from the old version, run:

```bash
python3 cleanup_old_files.py
```

This removes:
- `posts.json` (old format)
- `linkedin_feed.xml` (old format)
- Debug screenshots

### LinkedIn asks for verification

- Complete the verification manually in the browser
- The script will wait for you to complete it

## How It Works

### Incremental Scraping Logic

1. **Initial Run** (no existing XML):
   - Scrapes only 10 posts (configurable)
   - Creates `{slug}_posts.json` with metadata
   - Generates `{slug}.xml`

2. **Subsequent Runs** (XML exists):
   - Reads latest post link from existing XML
   - Scrolls through LinkedIn posts
   - Scrapes each post until finding the target
   - Stops immediately when target found
   - Merges new posts at beginning (recent-first)
   - Updates both JSON and XML

3. **Exit Conditions** (safety):
   - Found target post → stop
   - 20 scrolls completed → stop
   - 100 posts scraped → stop

### File Naming

- **Slug extraction**: `master-concept` from `/company/master-concept/`
- **Posts JSON**: `master-concept_posts.json` (one per page)
- **RSS XML**: `master-concept.xml` (one per page)
- **Session**: `browser_state/linkedin_state.json` (shared across pages)

## Limitations & Future Work

### Current Limitations

- **Session expiration**: LinkedIn sessions for automation expire in 1-8 hours (not suitable for long-term GitHub Actions without re-authentication)
- **Initial posts limit**: First run only fetches 10 posts (configurable)
- **Manual login required**: No automated login (for security)

### Future Enhancements

1. GitHub Actions workflow with session management
2. Email/webhook notifications for new posts
3. Configurable scroll/post limits per page
4. Support for personal profiles (currently only company/showcase pages)

## Security Notes

- Never commit `browser_state/` folder (contains login session)
- The `.gitignore` file is configured to exclude sensitive files
- Use environment variables for sensitive data in production

## Support

If you encounter issues:
1. Check the console output for error messages
2. Review the debug screenshots
3. Ensure Python and Playwright are properly installed
