#!/usr/bin/env python3
"""
Scrape All Pages Wrapper Script
Reads pages from pages_config.json and scrapes them sequentially
"""

import json
import re
import subprocess
import sys
from pathlib import Path


def extract_slug_from_url(url):
    """Extract slug from LinkedIn URL"""
    patterns = [
        r'/company/([^/]+)',
        r'/showcase/([^/]+)'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return 'linkedin-feed'


def normalize_url(url):
    """
    Normalize LinkedIn URL to ensure it has the posts page with proper parameters

    Examples:
        https://www.linkedin.com/company/master-concept/
        -> https://www.linkedin.com/company/master-concept/posts/?feedView=all&sortBy=recent&viewAsMember=true
    """
    # Remove trailing slash
    url = url.rstrip('/')

    # If already has posts/ in it, return as is
    if '/posts' in url:
        return url

    # Add posts page with parameters
    return f"{url}/posts/?feedView=all&sortBy=recent&viewAsMember=true"


def scrape_all_pages(specific_page=None, force=False):
    """
    Scrape all pages from config or a specific page

    Args:
        specific_page: Optional slug to scrape only one page, or 'all' for all pages
        force: If True, scrape even paused pages
    """
    config_file = Path(__file__).parent / "pages_config.json"

    if not config_file.exists():
        print(f"❌ Config file not found: {config_file}")
        print("   Please create pages_config.json with your LinkedIn pages")
        sys.exit(1)

    with open(config_file) as f:
        config = json.load(f)

    # Process pages: extract slug, normalize URL, and get status
    pages = []
    for page in config['pages']:
        url = page['url']
        slug = extract_slug_from_url(url)
        normalized_url = normalize_url(url)
        status = page.get('status', 'active')
        pages.append({
            'url': normalized_url,
            'slug': slug,
            'original_url': url,
            'status': status
        })

    # Filter to specific page if requested
    if specific_page and specific_page != 'all':
        pages = [p for p in pages if p['slug'] == specific_page]
        if not pages:
            print(f"❌ Page '{specific_page}' not found in config")
            all_slugs = [extract_slug_from_url(p['url']) for p in config['pages']]
            print(f"   Available pages: {', '.join(all_slugs)}")
            sys.exit(1)

    print("=" * 60)
    print(f"🚀 LinkedIn Feed Scraper - Processing {len(pages)} page(s)")
    print("=" * 60)
    print()

    success_count = 0
    failed_pages = []
    skipped_pages = []

    for i, page in enumerate(pages, 1):
        print(f"[{i}/{len(pages)}] 📄 {page['slug']}")
        print(f"  URL: {page['original_url']}")
        print(f"  Status: {page['status']}")
        print("-" * 60)

        # Check if page is paused and force mode is not enabled
        if page['status'] == 'paused' and not force:
            print(f"  ⏸️  Skipping {page['slug']} (paused)")
            skipped_pages.append(page['slug'])
            print()
            continue

        # Run scraper
        print(f"  🔍 Scraping posts...")
        result = subprocess.run(
            ['python3', 'linkedin_scraper.py', page['url']],
            capture_output=False
        )

        if result.returncode != 0:
            print(f"  ❌ Failed to scrape {page['slug']}")
            failed_pages.append(page['slug'])
            print()
            continue

        # Generate RSS
        print(f"  📡 Generating RSS feed...")
        result = subprocess.run(
            ['python3', 'generate_rss.py', page['slug']],
            capture_output=False
        )

        if result.returncode != 0:
            print(f"  ❌ Failed to generate RSS for {page['slug']}")
            failed_pages.append(page['slug'])
        else:
            success_count += 1
            print(f"  ✅ Completed: {page['slug']}")

        print()

    # Generate index page (always regenerate to reflect status changes)
    print("=" * 60)
    print("🏠 Generating index page...")
    print("=" * 60)
    result = subprocess.run(
        ['python3', 'generate_index.py'],
        capture_output=False
    )
    if result.returncode != 0:
        print("⚠️  Warning: Failed to generate index page")
    print()

    # Summary
    print("=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)

    # Calculate expected success count (active pages only)
    active_pages = len(pages) - len(skipped_pages)
    print(f"✅ Success: {success_count}/{active_pages} active pages")
    if skipped_pages:
        print(f"⏸️  Skipped: {', '.join(skipped_pages)} (paused)")
    if failed_pages:
        print(f"❌ Failed: {', '.join(failed_pages)}")
    print("=" * 60)

    # Return success (0) if all active pages succeeded
    return 0 if success_count == active_pages else 1


if __name__ == "__main__":
    # Parse command line arguments
    page = 'all'
    force = False

    for arg in sys.argv[1:]:
        if arg == '--force':
            force = True
        else:
            page = arg

    if force:
        print("🔓 Force mode enabled: will scrape even paused pages")
        print()

    exit_code = scrape_all_pages(page, force=force)
    sys.exit(exit_code)
