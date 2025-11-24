#!/usr/bin/env python3
"""
Generate Dynamic Index Page
Creates an index.html page listing all available RSS feeds with metadata
"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
import re


def extract_feed_info(xml_path):
    """
    Extract feed information from RSS XML file

    Returns:
        dict with keys: title, link, post_count, last_updated, posts
    """
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Find channel element
        channel = root.find('channel')
        if channel is None:
            return None

        # Extract title
        title_elem = channel.find('title')
        title = title_elem.text if title_elem is not None else "Unknown"

        # Extract post count from title (e.g., "Master Concept - LinkedIn Posts (12 posts)")
        post_count_match = re.search(r'\((\d+)\s+posts?\)', title)
        post_count = int(post_count_match.group(1)) if post_count_match else 0

        # Clean up title - remove the post count part
        clean_title = re.sub(r'\s*-\s*LinkedIn Posts.*$', '', title)

        # Extract link
        link_elem = channel.find('link')
        link = link_elem.text if link_elem is not None else ""

        # Get feed filename
        feed_filename = xml_path.name

        # Extract all posts
        posts = []
        latest_post_date = None
        for item in channel.findall('item'):
            post_title_elem = item.find('title')
            post_link_elem = item.find('link')
            post_date_elem = item.find('pubDate')

            if post_title_elem is not None and post_link_elem is not None:
                post_date_dt = None
                if post_date_elem is not None and post_date_elem.text:
                    try:
                        post_date_dt = datetime.strptime(post_date_elem.text, "%a, %d %b %Y %H:%M:%S %z")
                        # Track latest post date
                        if latest_post_date is None or post_date_dt > latest_post_date:
                            latest_post_date = post_date_dt
                    except ValueError:
                        pass

                posts.append({
                    'title': post_title_elem.text,
                    'link': post_link_elem.text,
                    'date': post_date_dt,
                    'feed_name': clean_title
                })

        # Use latest post date as last updated
        last_updated = latest_post_date.strftime("%Y-%m-%d %I:%M %p") if latest_post_date else "Unknown"
        last_updated_dt = latest_post_date

        return {
            'title': clean_title,
            'link': link,
            'post_count': post_count,
            'last_updated': last_updated,
            'last_updated_dt': last_updated_dt,
            'feed_url': f'feed/{feed_filename}',
            'posts': posts
        }
    except Exception as e:
        print(f"Error parsing {xml_path}: {e}")
        return None


def get_base_url():
    """
    Detect the base URL from git remote or use default
    Returns the GitHub Pages URL
    """
    try:
        import subprocess
        result = subprocess.run(
            ['git', 'remote', 'get-url', 'origin'],
            capture_output=True,
            text=True,
            check=True
        )
        remote_url = result.stdout.strip()

        # Parse GitHub URL
        # Format: https://github.com/username/repo.git or git@github.com:username/repo.git
        if 'github.com' in remote_url:
            # Extract username and repo
            if remote_url.startswith('https://'):
                # https://github.com/username/repo.git
                parts = remote_url.replace('https://github.com/', '').replace('.git', '').split('/')
            elif remote_url.startswith('git@'):
                # git@github.com:username/repo.git
                parts = remote_url.replace('git@github.com:', '').replace('.git', '').split('/')
            else:
                return None

            if len(parts) >= 2:
                username = parts[0]
                repo = parts[1]
                # GitHub Pages URL format
                return f"https://{username}.github.io/{repo}"
    except Exception as e:
        print(f"Could not detect base URL: {e}")

    return None


def generate_index_html(feeds, base_url=None):
    """Generate HTML content for index page"""

    # Calculate totals
    total_feeds = len(feeds)
    total_posts = sum(feed['post_count'] for feed in feeds)

    # Get latest update time
    latest_update = None
    for feed in feeds:
        if feed['last_updated_dt']:
            if latest_update is None or feed['last_updated_dt'] > latest_update:
                latest_update = feed['last_updated_dt']

    latest_update_str = latest_update.strftime("%Y-%m-%d %I:%M %p HKT") if latest_update else "Unknown"

    # Collect all posts and sort by date
    all_posts = []
    for feed in feeds:
        all_posts.extend(feed['posts'])

    # Sort by date (newest first) and take top 10
    all_posts.sort(key=lambda x: x['date'] if x['date'] else datetime.min.replace(tzinfo=None), reverse=True)
    latest_posts = all_posts[:10]

    # Determine full feed URLs for copying
    feed_url_prefix = base_url if base_url else ""

    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LinkedIn RSS Feeds Directory</title>
    <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%230077b5'%3E%3Cpath d='M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z'/%3E%3C/svg%3E">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 4px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .header {
            background: #0077b5;
            color: white;
            padding: 24px 20px;
            border-radius: 4px 4px 0 0;
        }
        .header h1 {
            font-size: 1.5em;
            margin-bottom: 6px;
            font-weight: 600;
        }
        .header p {
            font-size: 0.9em;
            opacity: 0.9;
        }
        .section {
            padding: 20px;
            border-bottom: 1px solid #e9ecef;
        }
        .section:last-child {
            border-bottom: none;
        }
        .section-title {
            font-size: 1.1em;
            font-weight: 600;
            margin-bottom: 12px;
            color: #2c3e50;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th {
            text-align: left;
            padding: 8px 0;
            font-size: 0.85em;
            color: #666;
            font-weight: 600;
            border-bottom: 2px solid #e9ecef;
        }
        td {
            padding: 12px 0;
            border-bottom: 1px solid #f0f0f0;
        }
        tbody tr:last-child td {
            border-bottom: none;
        }
        .feed-name {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .linkedin-icon {
            width: 18px;
            height: 18px;
            flex-shrink: 0;
            cursor: pointer;
            transition: transform 0.2s ease;
        }
        .linkedin-icon:hover {
            transform: scale(1.2);
        }
        .linkedin-icon:active {
            transform: scale(0.95);
        }
        .feed-link {
            color: #0077b5;
            text-decoration: none;
            font-weight: 500;
            font-size: 0.95em;
        }
        .feed-link:hover {
            text-decoration: underline;
        }
        .post-count {
            color: #666;
            font-size: 0.85em;
            margin-left: 6px;
        }
        .last-updated {
            color: #666;
            font-size: 0.85em;
        }
        .latest-posts {
            list-style: none;
        }
        .latest-posts li {
            padding: 10px 0;
            border-bottom: 1px solid #f0f0f0;
        }
        .latest-posts li:last-child {
            border-bottom: none;
        }
        .post-link {
            color: #0077b5;
            text-decoration: none;
            font-size: 0.9em;
            display: block;
            line-height: 1.4;
        }
        .post-link:hover {
            text-decoration: underline;
        }
        .post-meta {
            color: #999;
            font-size: 0.8em;
            margin-top: 4px;
        }
        .footer {
            background: #f8f9fa;
            padding: 16px 20px;
            text-align: center;
            color: #666;
            font-size: 0.85em;
            border-radius: 0 0 4px 4px;
        }
        .footer-stats {
            display: flex;
            justify-content: center;
            gap: 20px;
            flex-wrap: wrap;
        }
        .footer-stat {
            display: inline-block;
        }
        .toast {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #0077b5;
            color: white;
            padding: 12px 20px;
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            opacity: 0;
            transition: opacity 0.3s ease;
            pointer-events: none;
            z-index: 1000;
        }
        .toast.show {
            opacity: 1;
        }
        @media (max-width: 600px) {
            body {
                padding: 10px;
            }
            .header {
                padding: 16px;
            }
            .section {
                padding: 16px;
            }
            .footer {
                padding: 12px 16px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>LinkedIn RSS Feeds</h1>
            <p>Subscribe to company updates via RSS</p>
        </div>

        <div class="section">
            <h2 class="section-title">Available Feeds</h2>
            <table>
                <thead>
                    <tr>
                        <th>Feed Name</th>
                        <th>Latest Post</th>
                    </tr>
                </thead>
                <tbody>
"""

    # Sort feeds by title
    sorted_feeds = sorted(feeds, key=lambda x: x['title'])

    # Add feed rows
    for feed in sorted_feeds:
        full_feed_url = f"{feed_url_prefix}/{feed['feed_url']}" if feed_url_prefix else feed['feed_url']
        html += f"""                    <tr>
                        <td>
                            <div class="feed-name">
                                <svg class="linkedin-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#0077b5"
                                     onclick="copyFeedUrl('{full_feed_url}')"
                                     title="Click to copy RSS feed URL">
                                    <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/>
                                </svg>
                                <a href="{feed['feed_url']}" target="_blank" class="feed-link">{feed['title']}</a>
                                <span class="post-count">({feed['post_count']} posts)</span>
                            </div>
                        </td>
                        <td>
                            <span class="last-updated">{feed['last_updated']}</span>
                        </td>
                    </tr>
"""

    html += """                </tbody>
            </table>
        </div>

        <div class="section">
            <h2 class="section-title">Latest Posts</h2>
            <ul class="latest-posts">
"""

    # Add latest posts
    for post in latest_posts:
        post_date_str = post['date'].strftime("%Y-%m-%d %I:%M %p") if post['date'] else "Unknown"
        html += f"""                <li>
                    <a href="{post['link']}" target="_blank" class="post-link">{post['title']}</a>
                    <div class="post-meta">{post['feed_name']} • {post_date_str}</div>
                </li>
"""

    html += """            </ul>
        </div>

        <div class="footer">
            <div class="footer-stats">
                <span class="footer-stat">Feeds: """ + str(total_feeds) + """</span>
                <span class="footer-stat">Posts: """ + str(total_posts) + """</span>
                <span class="footer-stat">Last Update: """ + latest_update_str + """</span>
            </div>
        </div>
    </div>

    <div id="toast" class="toast">Feed URL copied to clipboard!</div>

    <script>
        function copyFeedUrl(url) {
            // Create temporary input element
            const input = document.createElement('input');
            input.value = url;
            document.body.appendChild(input);
            input.select();

            try {
                // Copy to clipboard
                document.execCommand('copy');
                showToast();
            } catch (err) {
                console.error('Failed to copy:', err);
            }

            document.body.removeChild(input);
        }

        function showToast() {
            const toast = document.getElementById('toast');
            toast.classList.add('show');
            setTimeout(() => {
                toast.classList.remove('show');
            }, 2000);
        }
    </script>
</body>
</html>
"""

    return html


def main():
    """Main function to generate index.html"""
    print("🔍 Scanning for RSS feeds...")

    # Find all XML feed files
    feed_dir = Path(__file__).parent / 'feed'
    if not feed_dir.exists():
        print(f"❌ Feed directory not found: {feed_dir}")
        return 1

    xml_files = list(feed_dir.glob('*.xml'))
    if not xml_files:
        print(f"❌ No XML feed files found in {feed_dir}")
        return 1

    print(f"📄 Found {len(xml_files)} feed file(s)")

    # Extract feed information
    feeds = []
    for xml_file in xml_files:
        print(f"  📡 Processing {xml_file.name}...")
        feed_info = extract_feed_info(xml_file)
        if feed_info:
            feeds.append(feed_info)
            print(f"    ✅ {feed_info['title']} ({feed_info['post_count']} posts)")

    if not feeds:
        print("❌ No valid feeds found")
        return 1

    # Detect base URL from git remote
    base_url = get_base_url()
    if base_url:
        print(f"📍 Detected base URL: {base_url}")
    else:
        print("⚠️  Could not detect base URL, using relative URLs")

    # Generate HTML
    print(f"\n📝 Generating index.html...")
    html_content = generate_index_html(feeds, base_url)

    # Write to file
    output_file = Path(__file__).parent / 'index.html'
    output_file.write_text(html_content, encoding='utf-8')

    print(f"✅ Generated: {output_file}")
    print(f"📊 Total feeds: {len(feeds)}")
    print(f"📊 Total posts: {sum(feed['post_count'] for feed in feeds)}")
    print("\n" + "=" * 60)
    print("🎉 Index page generated successfully!")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
