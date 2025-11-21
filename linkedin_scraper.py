#!/usr/bin/env python3
"""
LinkedIn Company Page Scraper
Scrapes posts from a LinkedIn company page and generates RSS feed
Supports both company and showcase pages with incremental scraping
"""

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import time
import xml.etree.ElementTree as ET

def extract_slug_from_url(url):
    """
    Extract slug from LinkedIn URL
    Supports both /company/slug/ and /showcase/slug/ formats

    Args:
        url: LinkedIn company or showcase page URL

    Returns:
        slug: The company/showcase slug (e.g., 'master-concept', 'digital-action-lab')
    """
    # Pattern to match both company and showcase URLs
    patterns = [
        r'/company/([^/]+)',
        r'/showcase/([^/]+)'
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    # Fallback: use a generic name
    return 'linkedin-feed'


def decode_linkedin_activity_id(activity_id):
    """
    Decode LinkedIn activity ID to extract timestamp.
    LinkedIn activity IDs are base64-encoded and contain timestamp info.
    Activity IDs are roughly: (timestamp_ms << 22) + random_bits
    """
    try:
        # LinkedIn activity IDs are numeric
        activity_num = int(activity_id)
        # The timestamp is in the upper bits (shift right by 22)
        timestamp_ms = activity_num >> 22
        # Convert to datetime
        dt = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
        return dt.isoformat()
    except Exception as e:
        print(f"    ⚠️  Could not decode activity ID: {e}")
        return None

class LinkedInScraper:
    def __init__(self, company_url, headless=False, max_posts_initial=10):
        """
        Initialize the LinkedIn scraper

        Args:
            company_url: Full LinkedIn company page URL
            headless: Run browser in headless mode (True for automation, False for debugging)
            max_posts_initial: Maximum posts to scrape on initial run (default: 10)
        """
        self.company_url = company_url
        self.headless = headless
        self.max_posts_initial = max_posts_initial

        # Extract slug from URL for file naming
        self.slug = extract_slug_from_url(company_url)

        # File paths using slug
        self.state_dir = Path(__file__).parent / "browser_state"
        self.state_file = self.state_dir / "linkedin_state.json"  # Shared session
        self.feed_dir = Path(__file__).parent / "feed"
        self.posts_file = self.feed_dir / f"{self.slug}_posts.json"
        self.xml_file = self.feed_dir / f"{self.slug}.xml"

        # Create directories if they don't exist
        self.state_dir.mkdir(exist_ok=True)
        self.feed_dir.mkdir(exist_ok=True)

        # Page information (will be extracted during scraping)
        self.page_name = None

    def save_posts(self, posts):
        """Save scraped posts to JSON file with metadata"""
        # Load existing posts if any and merge
        existing_posts = self.load_existing_posts()

        # Merge: new posts first, then existing posts (avoiding duplicates)
        existing_links = {p['link'] for p in existing_posts}
        merged_posts = posts.copy()  # Start with new posts
        for existing_post in existing_posts:
            if existing_post['link'] not in {p['link'] for p in posts}:
                merged_posts.append(existing_post)

        # Save with metadata
        data = {
            "page_name": self.page_name or self.slug.replace('-', ' ').title(),
            "slug": self.slug,
            "updated_at": datetime.now().isoformat(),
            "posts": merged_posts
        }

        with open(self.posts_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"✅ Saved {len(posts)} NEW posts to {self.posts_file}")
        print(f"   Total posts in file: {len(merged_posts)}")

    def load_existing_posts(self):
        """Load existing posts from JSON file (handles both old and new formats)"""
        if self.posts_file.exists():
            with open(self.posts_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Handle both old format (list) and new format (dict with metadata)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return data.get('posts', [])
        return []

    def get_latest_post_link_from_xml(self):
        """
        Get the latest (first) post link from existing XML file
        Returns None if XML doesn't exist or can't be parsed

        Returns:
            str: Latest post link, or None
        """
        if not self.xml_file.exists():
            print("📝 No existing XML found - this is an initial run")
            return None

        try:
            tree = ET.parse(self.xml_file)
            root = tree.getroot()

            # Find the first <item> element (latest post)
            # RSS structure: <rss><channel><item>
            channel = root.find('channel')
            if channel is not None:
                item = channel.find('item')
                if item is not None:
                    link = item.find('link')
                    if link is not None and link.text:
                        print(f"✅ Found latest post in existing XML: {link.text[:80]}...")
                        return link.text

            print("⚠️  Could not find latest post link in XML")
            return None
        except Exception as e:
            print(f"⚠️  Error reading existing XML: {e}")
            return None

    def scrape_posts(self):
        """
        Scrape posts from LinkedIn company page with incremental logic

        Initial run: Scrapes only max_posts_initial posts (default: 10)
        Subsequent runs: Scrapes until reaching existing latest post

        Exit conditions:
        - Found existing latest post → stop
        - 20 scrolls without finding target → stop
        - 100 posts scraped → stop

        Returns list of posts with title, link, date, and content
        """
        print(f"🚀 Starting LinkedIn scraper for: {self.company_url}")
        print(f"📂 Slug: {self.slug}")

        # Check for existing XML to determine mode
        target_post_link = self.get_latest_post_link_from_xml()
        is_initial_run = (target_post_link is None)

        if is_initial_run:
            print(f"🆕 Initial run mode: will scrape max {self.max_posts_initial} posts")
        else:
            print(f"♻️  Incremental run mode: will scrape until reaching existing post")
            print(f"🎯 Target post: {target_post_link[:80]}...")

        with sync_playwright() as p:
            # Launch browser
            print("🌐 Launching browser...")
            browser = p.chromium.launch(headless=self.headless)

            # Create context with state persistence
            context_options = {
                "viewport": {"width": 1280, "height": 720},
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }

            # Load saved state if exists
            if self.state_file.exists():
                print("📂 Loading saved browser state...")
                context = browser.new_context(
                    storage_state=str(self.state_file),
                    **context_options
                )
            else:
                print("🆕 Creating new browser context...")
                context = browser.new_context(**context_options)

            page = context.new_page()

            try:
                # Navigate to company page
                print(f"📄 Navigating to {self.company_url}")
                page.goto(self.company_url, wait_until="domcontentloaded", timeout=30000)

                # Wait a bit for page to load
                time.sleep(3)

                # Check if we need to login (check for login modal or auth wall)
                login_selectors = [
                    "text=Sign in",
                    "text=Continue with Google",
                    "[data-test-id='login-form']",
                    ".authwall"
                ]

                needs_login = False
                for selector in login_selectors:
                    if page.query_selector(selector):
                        needs_login = True
                        break

                if needs_login or "login" in page.url or "authwall" in page.url:
                    print("🔐 LinkedIn login required!")
                    print("=" * 60)
                    print("Please log in to LinkedIn in the browser window.")
                    print("The script will wait up to 3 minutes for login...")
                    print("=" * 60)

                    # Wait for actual successful login by checking for logged-in indicators
                    max_wait = 180  # 3 minutes
                    waited = 0
                    login_successful = False

                    while waited < max_wait:
                        time.sleep(3)
                        waited += 3

                        try:
                            # Check for indicators that user is logged in
                            # Look for navigation bar, profile icon, or feed elements
                            logged_in_indicators = [
                                "[data-control-name='nav.settings']",  # Settings icon
                                ".global-nav__me",  # Profile menu
                                ".feed-identity-module",  # Feed identity
                                "nav.global-nav",  # Main navigation
                            ]

                            for indicator in logged_in_indicators:
                                elem = page.query_selector(indicator)
                                if elem:
                                    login_successful = True
                                    print("✅ Login successful!")
                                    break

                            if login_successful:
                                break

                            # Also check URL - should not contain authwall or login
                            current_url = page.url
                            if "authwall" not in current_url and "login" not in current_url and "signup" not in current_url:
                                # Double-check by looking for any logged-in indicator
                                if page.query_selector(".global-nav"):
                                    login_successful = True
                                    print("✅ Login successful!")
                                    break

                        except Exception as e:
                            # Page might be navigating, just continue waiting
                            if "Execution context was destroyed" in str(e) or "Target closed" in str(e):
                                print("  🔄 Page is navigating...")
                                continue
                            else:
                                print(f"  ⚠️  Error checking login: {e}")

                        if waited % 10 == 0:
                            print(f"  ⏳ Waiting for login... ({waited}s elapsed)")

                    if not login_successful:
                        print("⚠️  Login timeout or not detected. Continuing anyway...")

                    # Save the logged-in state
                    context.storage_state(path=str(self.state_file))
                    print(f"💾 Saved login state to {self.state_file}")

                    # Navigate back to company page
                    print("🔄 Navigating to company page...")
                    page.goto(self.company_url, wait_until="domcontentloaded")
                    time.sleep(3)

                # Extract page name for RSS feed title
                print("📝 Extracting page name...")
                try:
                    page_name_selectors = [
                        "h1.org-top-card-summary__title",
                        "h1[class*='top-card']",
                        ".org-top-card-summary__title",
                        "h1"
                    ]

                    for selector in page_name_selectors:
                        name_elem = page.query_selector(selector)
                        if name_elem:
                            self.page_name = name_elem.inner_text().strip()
                            if self.page_name and len(self.page_name) > 2:
                                print(f"  ✅ Found page name: {self.page_name}")
                                break

                    # Fallback to slug if no name found
                    if not self.page_name:
                        self.page_name = self.slug.replace('-', ' ').title()
                        print(f"  ⚠️  Using slug as fallback name: {self.page_name}")
                except Exception as e:
                    self.page_name = self.slug.replace('-', ' ').title()
                    print(f"  ⚠️  Error extracting page name, using slug: {e}")

                # Click "All" tab to ensure we see all posts (not filtered by content type)
                print("🔘 Clicking 'All' tab to view all posts...")
                try:
                    all_tab_selectors = [
                        "button:has-text('All')",
                        "li:has-text('All') button",
                        "[aria-label='All']",
                        "nav button:has-text('All')",
                        ".artdeco-tab:has-text('All')"
                    ]

                    all_tab_clicked = False
                    for selector in all_tab_selectors:
                        try:
                            all_tab = page.query_selector(selector)
                            if all_tab:
                                all_tab.click()
                                print(f"  ✅ Clicked 'All' tab using selector: {selector}")
                                time.sleep(2)
                                all_tab_clicked = True
                                break
                        except:
                            continue

                    if not all_tab_clicked:
                        print("  ⚠️  Could not find 'All' tab - it may already be selected")
                except Exception as e:
                    print(f"  ⚠️  Error clicking 'All' tab: {e}")

                # Click "Sort by: Recent" button to ensure we get chronological order
                print("🔘 Clicking 'Sort by: Recent' button...")
                try:
                    # Try to find and click the sort button
                    sort_button_selectors = [
                        "button:has-text('Recent')",
                        "button:has-text('recent')",
                        "[aria-label*='Sort by']",
                        "button.artdeco-dropdown__trigger",
                        ".feed-sort-toggle button"
                    ]

                    clicked = False
                    for selector in sort_button_selectors:
                        try:
                            sort_button = page.query_selector(selector)
                            if sort_button:
                                sort_button.click()
                                print(f"  ✅ Clicked sort button using selector: {selector}")
                                time.sleep(2)

                                # If a dropdown opened, click "Recent" option
                                try:
                                    recent_option = page.query_selector("li:has-text('Recent'), div:has-text('Recent'), span:has-text('Recent')")
                                    if recent_option:
                                        recent_option.click()
                                        print("  ✅ Selected 'Recent' from dropdown")
                                        time.sleep(2)
                                except:
                                    pass

                                clicked = True
                                break
                        except:
                            continue

                    if not clicked:
                        print("  ⚠️  Could not find sort button - will rely on URL parameters")

                    # Take screenshot after sort to verify
                    screenshot_path = Path(__file__).parent / "after_sort_screenshot.png"
                    page.screenshot(path=str(screenshot_path))
                    print(f"  📸 Saved screenshot after sort to {screenshot_path}")

                except Exception as e:
                    print(f"  ⚠️  Error clicking sort button: {e}")

                # Scroll to load posts with dynamic logic
                print("📜 Scrolling to load posts...")
                max_scrolls = 20  # Exit condition: max 20 scrolls
                if is_initial_run:
                    # Initial run: fewer scrolls needed (only need 10 posts)
                    max_scrolls = 5
                else:
                    # Incremental run: may need more scrolls to find target
                    max_scrolls = 20

                for i in range(max_scrolls):
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(2.5)  # Wait for content to load
                    if (i + 1) % 2 == 0:
                        print(f"  📜 Scrolled {i+1} times...")

                # Extract posts
                print("🔍 Extracting posts...")
                posts = []

                # Try to find ALL post elements including videos, articles, etc.
                # Use the most comprehensive selector that includes all content types
                post_selector = "[data-urn*='urn:li:activity']"
                post_elements = page.query_selector_all(post_selector)

                if post_elements:
                    print(f"✅ Found {len(post_elements)} posts using selector: {post_selector}")
                else:
                    # Fallback to older selectors
                    fallback_selectors = [
                        ".feed-shared-update-v2",
                        ".occludable-update"
                    ]
                    for selector in fallback_selectors:
                        post_elements = page.query_selector_all(selector)
                        if post_elements:
                            print(f"✅ Found {len(post_elements)} posts using fallback selector: {selector}")
                            break

                if not post_elements:
                    print("⚠️  No posts found. LinkedIn structure may have changed.")
                    print("🔍 Page URL:", page.url)

                    # Take a screenshot for debugging
                    screenshot_path = Path(__file__).parent / "debug_screenshot.png"
                    page.screenshot(path=str(screenshot_path))
                    print(f"📸 Saved debug screenshot to {screenshot_path}")

                    return []

                # Parse each post with incremental logic
                print(f"  🔍 Processing {len(post_elements)} posts...")

                # Exit conditions
                MAX_POSTS_TO_SCRAPE = 100  # Safety limit
                found_target = False
                processed_count = 0

                for idx, post_element in enumerate(post_elements, 1):
                    try:
                        # Exit condition: reached max posts limit
                        if processed_count >= MAX_POSTS_TO_SCRAPE:
                            print(f"  ⚠️  Reached max posts limit ({MAX_POSTS_TO_SCRAPE}), stopping")
                            break

                        # Exit condition (initial run): reached desired number of posts
                        if is_initial_run and processed_count >= self.max_posts_initial:
                            print(f"  ✅ Initial run: collected {self.max_posts_initial} posts, stopping")
                            break

                        # Exit condition (incremental): found target post
                        if found_target:
                            print(f"  ✅ Found target post, stopping")
                            break

                        # Extract post link - try to get the full URL with hashtags
                        post_link = None
                        activity_id = None

                        # Strategy 1: Extract link from the post element's HTML
                        try:
                            # Get the data-urn to identify this specific post
                            data_urn = post_element.get_attribute("data-urn")
                            if data_urn and "activity" in data_urn:
                                activity_id = data_urn.split(":")[-1]

                                # Get the HTML of this specific post element
                                post_html = post_element.inner_html()

                                # Look for the full URL pattern with hashtags in this post's HTML
                                # Pattern: /posts/master-concept_something-activity-NUMBER
                                pattern = rf'/posts/master-concept_[a-z0-9\-]+activity-{activity_id}[a-zA-Z0-9\-]*'
                                matches = re.findall(pattern, post_html)

                                if matches:
                                    # Take the first match and clean it
                                    post_url = matches[0]
                                    # Remove any trailing characters after the activity ID that aren't part of the URL
                                    # LinkedIn URLs end with activity-NUMBER or activity-NUMBER-HASH
                                    post_link = "https://www.linkedin.com" + post_url.split('"')[0].split("'")[0]
                        except Exception as e:
                            print(f"    ⚠️  Could not extract link from HTML: {e}")

                        # Strategy 2: Look for links in the post HTML
                        if not post_link:
                            all_links = post_element.query_selector_all("a[href]")
                            for link in all_links:
                                href = link.get_attribute("href")
                                # Look for the pattern with hashtags
                                if href and "/posts/master-concept_" in href and "activity-" in href:
                                    base_href = href.split("?")[0] if "?" in href else href
                                    if not base_href.startswith("http"):
                                        base_href = "https://www.linkedin.com" + base_href
                                    post_link = base_href
                                    try:
                                        activity_id = base_href.split("activity-")[1].rstrip("/")
                                    except:
                                        pass
                                    break

                        # Strategy 3: Look for any post link
                        if not post_link:
                            for link in all_links:
                                href = link.get_attribute("href")
                                if href and "/posts/" in href and "activity-" in href:
                                    base_href = href.split("?")[0] if "?" in href else href
                                    if not base_href.startswith("http"):
                                        base_href = "https://www.linkedin.com" + base_href
                                    post_link = base_href
                                    try:
                                        activity_id = base_href.split("activity-")[1].rstrip("/")
                                    except:
                                        pass
                                    break

                        # Strategy 4: Fallback - build feed update link from data-urn (most reliable)
                        if not post_link:
                            data_urn = post_element.get_attribute("data-urn")
                            if data_urn and "activity" in data_urn:
                                activity_id = data_urn.split(":")[-1]
                                # Use feed/update format which always works and redirects to the proper URL
                                post_link = f"https://www.linkedin.com/feed/update/urn:li:activity:{activity_id}"

                        # Extract post text - try multiple strategies
                        text_selectors = [
                            ".feed-shared-text",
                            ".break-words",
                            "[dir='ltr']",
                            ".attributed-text-segment-list__content",
                            ".update-components-text",
                            ".feed-shared-update-v2__description-wrapper",
                            ".feed-shared-inline-show-more-text"
                        ]
                        post_text = ""
                        for selector in text_selectors:
                            text_elem = post_element.query_selector(selector)
                            if text_elem:
                                post_text = text_elem.inner_text().strip()
                                if post_text:  # Only use if non-empty
                                    break

                        # If still no text, try getting all text content from the post
                        if not post_text:
                            try:
                                post_text = post_element.inner_text().strip()
                                # Filter out very short or empty text
                                if len(post_text) < 10:
                                    post_text = "[Post without text description]"
                            except:
                                post_text = "[Post without text description]"

                        # Extract post images
                        post_images = []
                        image_selectors = [
                            "img.feed-shared-image__image",
                            "img[class*='ivm-view-attr__img']",
                            ".feed-shared-update-v2__content img",
                            "article img"
                        ]
                        for img_selector in image_selectors:
                            img_elements = post_element.query_selector_all(img_selector)
                            for img_elem in img_elements:
                                img_src = img_elem.get_attribute("src")
                                # Filter out small icons, logos, and profile pictures
                                if img_src and "media.licdn.com/dms/image" in img_src:
                                    # Skip company logos (100x100 size) and small profile pics
                                    if "company-logo_100_100" in img_src or "profile-" in img_src:
                                        continue
                                    # Keep the full URL with parameters for proper loading
                                    if img_src not in post_images:
                                        post_images.append(img_src)
                            if post_images:
                                break

                        # Extract timestamp - get actual publish date
                        post_date = None

                        # Try multiple approaches to get the publish date
                        # 1. Look for time element with datetime attribute
                        time_elems = post_element.query_selector_all("time")
                        for time_elem in time_elems:
                            dt_attr = time_elem.get_attribute("datetime")
                            if dt_attr:
                                post_date = dt_attr
                                break

                        # 2. Decode date from activity ID
                        if not post_date and activity_id:
                            post_date = decode_linkedin_activity_id(activity_id)

                        # 3. Fallback: use scraped time
                        if not post_date:
                            post_date = datetime.now().isoformat()

                        # Check if this is the target post (incremental mode)
                        if not is_initial_run and target_post_link and post_link:
                            # Normalize URLs for comparison (remove trailing slashes, query params)
                            current_link_normalized = post_link.split('?')[0].rstrip('/')
                            target_link_normalized = target_post_link.split('?')[0].rstrip('/')

                            if current_link_normalized == target_link_normalized:
                                print(f"  🎯 Found target post! Stopping here.")
                                found_target = True
                                break  # Don't include this post (it's already in XML)

                        # Save post if we have a link (text is optional)
                        if post_link:
                            # Ensure we have at least some text for the title
                            if not post_text or len(post_text) < 5:
                                post_text = "[Post without text]"

                            post_data = {
                                "title": post_text[:100] + "..." if len(post_text) > 100 else post_text,
                                "link": post_link,
                                "description": post_text,
                                "published": post_date,
                                "images": post_images,
                                "scraped_at": datetime.now().isoformat()
                            }
                            posts.append(post_data)
                            processed_count += 1

                            if processed_count % 5 == 0:  # Show progress every 5 posts
                                print(f"  📝 Scraped {processed_count} posts...")
                        else:
                            print(f"  ⚠️  Post {idx}: No link found")

                    except Exception as e:
                        print(f"  ⚠️  Error parsing post {idx}: {str(e)}")
                        continue

                print(f"\n✅ Successfully scraped {len(posts)} posts")
                return posts

            except Exception as e:
                print(f"❌ Error during scraping: {str(e)}")

                # Take a screenshot for debugging
                screenshot_path = Path(__file__).parent / "error_screenshot.png"
                try:
                    page.screenshot(path=str(screenshot_path))
                    print(f"📸 Saved error screenshot to {screenshot_path}")
                except:
                    pass

                return []

            finally:
                context.close()
                browser.close()


def main():
    """Main execution function"""
    import sys

    # Default configuration
    COMPANY_URL = "https://www.linkedin.com/company/master-concept/posts/?feedView=all&sortBy=recent&viewAsMember=true"
    HEADLESS = os.getenv('HEADLESS', 'false').lower() == 'true'
    MAX_POSTS_INITIAL = 10

    # Allow URL as command line argument
    if len(sys.argv) > 1:
        COMPANY_URL = sys.argv[1]
        print(f"📎 Using URL from argument: {COMPANY_URL}")

    # Ensure URL has proper parameters
    if '?' not in COMPANY_URL:
        COMPANY_URL += "?feedView=all&sortBy=recent&viewAsMember=true"
    elif 'feedView' not in COMPANY_URL:
        COMPANY_URL += "&feedView=all&sortBy=recent&viewAsMember=true"

    print("\n💡 TIP: If you see a browser window, DO NOT close it manually!")
    print("    The script will close it automatically when done.\n")

    # Create scraper instance
    scraper = LinkedInScraper(COMPANY_URL, headless=HEADLESS, max_posts_initial=MAX_POSTS_INITIAL)

    # Scrape posts
    posts = scraper.scrape_posts()

    # Save posts
    if posts:
        scraper.save_posts(posts)

        print("\n" + "=" * 60)
        print("📊 SUMMARY")
        print("=" * 60)
        print(f"Slug: {scraper.slug}")
        print(f"Page name: {scraper.page_name}")
        print(f"Total NEW posts scraped: {len(posts)}")
        print(f"Posts saved to: {scraper.posts_file}")
        print(f"Latest post: {posts[0]['title'][:60]}..." if posts else "No posts")
        print("\n💡 Next step: Run generate_rss.py to create/update the RSS feed")
        print(f"   python3 generate_rss.py {scraper.slug}")
        print("=" * 60)
    else:
        print("\n⚠️  No NEW posts were scraped.")
        print("   This is normal if you're up to date or reached the target post.")


if __name__ == "__main__":
    main()
