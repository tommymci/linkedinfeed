#!/usr/bin/env python3
"""
RSS Feed Generator for LinkedIn Posts
Converts scraped LinkedIn posts to RSS feed format
"""

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from feedgen.feed import FeedGenerator
from dateutil import parser as date_parser


class RSSFeedGenerator:
    def __init__(self, slug=None, posts_file=None, output_file=None):
        """
        Initialize RSS Feed Generator

        Args:
            slug: Page slug (e.g., 'master-concept', 'digital-action-lab')
                  Used to determine file names if posts_file/output_file not provided
            posts_file: JSON file containing scraped posts (optional, derived from slug)
            output_file: Output RSS feed XML file (optional, derived from slug)
        """
        self.feed_dir = Path(__file__).parent / "feed"

        if slug:
            self.slug = slug
            self.posts_file = self.feed_dir / f"{slug}_posts.json"
            self.output_file = self.feed_dir / f"{slug}.xml"
        else:
            # Legacy support: use provided file names or defaults
            self.slug = "linkedin-feed"
            self.posts_file = Path(__file__).parent / (posts_file or "posts.json")
            self.output_file = Path(__file__).parent / (output_file or "linkedin_feed.xml")

        self.page_name = None

    def load_posts(self):
        """Load posts from JSON file and extract page name"""
        if not self.posts_file.exists():
            print(f"❌ Posts file not found: {self.posts_file}")
            print("   Please run linkedin_scraper.py first!")
            return []

        with open(self.posts_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Handle both old format (list) and new format (dict with metadata)
        if isinstance(data, list):
            posts = data
            self.page_name = self.slug.replace('-', ' ').title()
        elif isinstance(data, dict):
            posts = data.get('posts', [])
            self.page_name = data.get('page_name', self.slug.replace('-', ' ').title())
        else:
            posts = []
            self.page_name = self.slug.replace('-', ' ').title()

        print(f"✅ Loaded {len(posts)} posts from {self.posts_file}")
        print(f"📝 Page name: {self.page_name}")
        return posts

    def generate_feed(self):
        """Generate RSS feed from posts"""
        posts = self.load_posts()

        if not posts:
            print("⚠️  No posts to generate feed from")
            return False

        # Sort posts by published date (oldest first, RSS library will reverse to newest first)
        try:
            posts.sort(key=lambda x: date_parser.parse(x['published']), reverse=False)
            print(f"✅ Sorted {len(posts)} posts by date")
        except Exception as e:
            print(f"⚠️  Could not sort posts: {e}")

        print("🔨 Generating RSS feed...")

        # Create feed generator
        fg = FeedGenerator()

        # Construct LinkedIn URL from slug
        if 'showcase' in self.posts_file.name or 'showcase' in self.slug:
            linkedin_url = f"https://www.linkedin.com/showcase/{self.slug}/"
        else:
            linkedin_url = f"https://www.linkedin.com/company/{self.slug}/"

        # Set feed metadata using page name with last updated timestamp
        now_hkt = datetime.now(timezone(timedelta(hours=8)))  # HKT timezone
        last_updated = now_hkt.strftime("%Y-%m-%d %I:%M %p HKT")

        fg.id(linkedin_url)
        fg.title(f"{self.page_name}")
        fg.author({"name": self.page_name, "email": "noreply@linkedin.com"})
        fg.link(href=linkedin_url, rel="alternate")
        fg.description(f"Posts: {len(posts)} | Last Update: {last_updated}")
        fg.language("en")
        fg.updated(now_hkt)

        # Add posts to feed
        for post in posts:
            fe = fg.add_entry()

            # Set entry ID (use link as unique identifier)
            fe.id(post['link'])

            # Set title
            fe.title(post['title'])

            # Set link
            fe.link(href=post['link'])

            # Set description/content with only first image
            description_html = post['description']

            # Add only the first image to description if available
            if 'images' in post and post['images'] and len(post['images']) > 0:
                first_image = post['images'][0]
                image_html = f'<br/><br/><img src="{first_image}" style="max-width: 100%; height: auto; margin: 10px 0;" /><br/>'
                description_html += image_html

            fe.description(description_html)
            fe.content(description_html, type="html")

            # Add enclosure tag for first image (for Pabbly/RSS readers)
            if 'images' in post and post['images'] and len(post['images']) > 0:
                first_image_url = post['images'][0]
                # Add enclosure tag with image URL
                # Type is image/jpeg (LinkedIn typically uses JPEG)
                # Length is unknown, so use 0 as placeholder
                fe.enclosure(url=first_image_url, length='0', type='image/jpeg')

            # Set published date - convert to Hong Kong timezone (UTC+8)
            try:
                pub_date = date_parser.parse(post['published'])
                # Convert to Hong Kong timezone (UTC+8)
                hk_tz = timezone(timedelta(hours=8))
                pub_date_hk = pub_date.astimezone(hk_tz)
                fe.published(pub_date_hk)
                fe.updated(pub_date_hk)
            except Exception as e:
                print(f"  ⚠️  Error parsing date for post: {e}")
                hk_tz = timezone(timedelta(hours=8))
                fe.published(datetime.now(hk_tz))
                fe.updated(datetime.now(hk_tz))

        # Generate RSS feed
        fg.rss_file(str(self.output_file), pretty=True)

        # Add XSLT stylesheet reference for browser viewing
        self._add_stylesheet()

        print(f"✅ RSS feed generated: {self.output_file}")
        print(f"   Contains {len(posts)} posts")

        return True

    def _add_stylesheet(self):
        """Add XSLT stylesheet reference to XML for browser viewing and fix HTML entities"""
        try:
            # Read the generated XML
            with open(self.output_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Fix HTML entities in description - unescape them so XSLT can parse
            import re
            # Replace &lt; and &gt; in description tags with actual < >
            content = re.sub(
                r'<description>(.*?)</description>',
                lambda m: '<description><![CDATA[' + m.group(1).replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&') + ']]></description>',
                content,
                flags=re.DOTALL
            )
            content = re.sub(
                r'<content:encoded>(.*?)</content:encoded>',
                lambda m: '<content:encoded><![CDATA[' + m.group(1).replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&') + ']]></content:encoded>',
                content,
                flags=re.DOTALL
            )

            # Add stylesheet reference after XML declaration
            if '<?xml' in content:
                content = content.replace(
                    '<?xml version=\'1.0\' encoding=\'UTF-8\'?>',
                    '<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<?xml-stylesheet type="text/xsl" href="rss-style.xsl"?>'
                )

            # Write back
            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.write(content)

            # Create the XSLT stylesheet file
            self._create_xslt_file()
        except Exception as e:
            print(f"  ⚠️  Could not add stylesheet: {e}")

    def _create_xslt_file(self):
        """Create XSLT stylesheet for RSS feed"""
        xsl_file = self.output_file.parent / "rss-style.xsl"

        xsl_content = '''<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:content="http://purl.org/rss/1.0/modules/content/"
    xmlns:atom="http://www.w3.org/2005/Atom"
    exclude-result-prefixes="content atom">
    <xsl:output method="html" encoding="UTF-8" indent="yes"/>

    <xsl:template match="/rss">
        <html>
            <head>
                <title><xsl:value-of select="channel/title"/></title>
                <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
                <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%230077b5'%3E%3Cpath d='M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z'/%3E%3C/svg%3E"/>
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
                    .posts {
                        padding: 0;
                    }
                    .post {
                        padding: 16px;
                        border-bottom: 1px solid #e9ecef;
                        background: white;
                        display: flex;
                        gap: 12px;
                        align-items: stretch;
                    }
                    .post:last-child {
                        border-bottom: none;
                    }
                    .post-thumbnail {
                        flex-shrink: 0;
                        width: 180px;
                        max-height: 120px;
                        overflow: hidden;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        background: #f0f0f0;
                        border-radius: 4px;
                    }
                    .post-thumbnail img {
                        width: 100%;
                        height: 100%;
                        object-fit: cover;
                        border-radius: 4px;
                    }
                    .post-content {
                        flex: 1;
                        min-width: 0;
                        display: flex;
                        flex-direction: column;
                        position: relative;
                    }
                    .post-title {
                        font-size: 0.95em;
                        font-weight: 600;
                        margin-bottom: 4px;
                        color: #2c3e50;
                        display: -webkit-box;
                        -webkit-line-clamp: 2;
                        -webkit-box-orient: vertical;
                        overflow: hidden;
                        text-overflow: ellipsis;
                    }
                    .post-title a {
                        color: #0077b5;
                        text-decoration: none;
                    }
                    .post-title a:hover {
                        text-decoration: underline;
                    }
                    .post-meta {
                        color: #999;
                        font-size: 0.65em;
                        position: absolute;
                        bottom: 0;
                        right: 0;
                    }
                    .post-description {
                        color: #495057;
                        font-size: 0.85em;
                        line-height: 1.5;
                        flex: 1;
                        padding-bottom: 18px;
                    }
                    .post-text-preview,
                    .post-text-full {
                        line-height: 1.5;
                        white-space: pre-wrap;
                    }
                    .post-text-full {
                        display: none;
                    }
                    .read-more {
                        color: #0077b5;
                        text-decoration: none;
                        font-size: 0.85em;
                        font-weight: 500;
                        display: inline-block;
                        margin-top: 4px;
                        cursor: pointer;
                    }
                    .read-more:hover {
                        text-decoration: underline;
                    }
                    .footer {
                        background: #f8f9fa;
                        padding: 16px 20px;
                        text-align: center;
                        color: #6c757d;
                        font-size: 0.85em;
                        border-top: 1px solid #e9ecef;
                        border-radius: 0 0 4px 4px;
                    }
                    .footer a {
                        color: #0077b5;
                        text-decoration: none;
                    }
                    .footer a:hover {
                        text-decoration: underline;
                    }
                    @media (max-width: 768px) {
                        body {
                            padding: 10px;
                        }
                        .header h1 {
                            font-size: 1.3em;
                        }
                        .post {
                            padding: 12px;
                            flex-direction: column;
                        }
                        .post-thumbnail {
                            width: 100%;
                            align-self: auto;
                        }
                        .post-thumbnail img {
                            aspect-ratio: 16 / 9;
                            height: auto;
                        }
                        .post-meta {
                            position: static;
                            margin-top: 8px;
                        }
                    }
                </style>
                <script><![CDATA[
                    // Function to extract and display truncated text with images
                    function processPostContent() {
                        try {
                            console.log('Processing post content...');
                            const postElements = document.querySelectorAll('.post');
                            console.log('Found ' + postElements.length + ' posts');

                            postElements.forEach(function(postDiv, index) {
                                try {
                                    // Get the hidden description element
                                    const descElem = postDiv.querySelector('.post-description');
                                    if (!descElem) return;

                                    const content = descElem.innerHTML;

                                    // Extract image if exists
                                    const imgMatch = content.match(/<img[^>]*src="([^"]*)"[^>]*>/);
                                    let imageSrc = null;
                                    if (imgMatch) {
                                        imageSrc = imgMatch[1];
                                    }

                                    // Extract text content (remove HTML tags)
                                    let textContent = content.replace(/<[^>]*>/g, '').trim();

                                    // Truncate text to 100 characters for preview (shorter for compact layout)
                                    const maxLength = 100;
                                    let truncatedText = textContent;
                                    let needsExpansion = textContent.length > maxLength;

                                    if (needsExpansion) {
                                        truncatedText = textContent.substring(0, maxLength) + '...';
                                    }

                                    // Build new compact layout
                                    let newHTML = '';

                                    // Add thumbnail on left if image exists
                                    if (imageSrc) {
                                        newHTML += '<div class="post-thumbnail"><img src="' + imageSrc + '" alt="Post thumbnail" /></div>';
                                    }

                                    // Get existing post-content div
                                    const postContent = postDiv.querySelector('.post-content');
                                    if (!postContent) return;

                                    // Add text content with expansion to post-content
                                    const textHTML = '<div class="post-text-preview">' + truncatedText + '</div>' +
                                        (needsExpansion ? '<div class="post-text-full">' + textContent + '</div>' +
                                        '<a href="#" class="read-more" onclick="toggleContent(this, event); return false;">Read more →</a>' : '');

                                    postContent.insertAdjacentHTML('beforeend', textHTML);

                                    // Rebuild the post with thumbnail first, then content
                                    if (imageSrc) {
                                        postDiv.innerHTML = newHTML + postContent.outerHTML;
                                    }

                                    // Remove the hidden description element
                                    const descToRemove = postDiv.querySelector('.post-description');
                                    if (descToRemove) descToRemove.remove();
                                } catch (e) {
                                    console.error('Error processing post ' + index + ':', e);
                                }
                            });
                            console.log('Finished processing posts');
                        } catch (e) {
                            console.error('Error in processPostContent:', e);
                        }
                    }

                    // Toggle content expansion
                    function toggleContent(element, event) {
                        event.preventDefault();
                        const container = element.closest('.post-content');
                        const preview = container.querySelector('.post-text-preview');
                        const full = container.querySelector('.post-text-full');

                        if (full.style.display === 'none' || full.style.display === '') {
                            // Expand
                            preview.style.display = 'none';
                            full.style.display = 'block';
                            element.textContent = 'Show less ↑';
                        } else {
                            // Collapse
                            preview.style.display = 'block';
                            full.style.display = 'none';
                            element.textContent = 'Read more →';
                        }
                    }

                    // Run when DOM is loaded
                    window.addEventListener('load', function() {
                        console.log('Page loaded, starting content processing');
                        processPostContent();
                    });
                ]]></script>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>
                            <a href="{channel/link}" target="_blank" style="color: white; text-decoration: none;">
                                <xsl:value-of select="channel/title"/>
                            </a>
                        </h1>
                        <p><xsl:value-of select="channel/description"/></p>
                    </div>

                    <div class="posts">
                        <xsl:for-each select="channel/item">
                            <div class="post">
                                <!-- Thumbnail and content will be restructured by JavaScript -->
                                <div class="post-description" style="display:none;">
                                    <xsl:value-of select="description" disable-output-escaping="yes"/>
                                </div>
                                <div class="post-content">
                                    <div class="post-title">
                                        <a href="{link}" target="_blank">
                                            <xsl:value-of select="title"/>
                                        </a>
                                    </div>
                                    <div class="post-meta">
                                        <xsl:value-of select="substring(pubDate, 1, 25)"/>
                                    </div>
                                </div>
                            </div>
                        </xsl:for-each>
                    </div>

                    <div class="footer">
                        © 2025 LinkedIn Feed. All rights reserved.
                    </div>
                </div>
            </body>
        </html>
    </xsl:template>
</xsl:stylesheet>'''

        with open(xsl_file, 'w', encoding='utf-8') as f:
            f.write(xsl_content)

        print(f"✅ Created stylesheet: {xsl_file}")


def main():
    """Main execution function"""
    import sys

    # Check for slug argument
    slug = None
    if len(sys.argv) > 1:
        slug = sys.argv[1]
        print(f"📎 Using slug from argument: {slug}")
        generator = RSSFeedGenerator(slug=slug)
    else:
        # Try to auto-detect from available files
        feed_dir = Path(__file__).parent / "feed"
        available_files = list(feed_dir.glob("*_posts.json")) if feed_dir.exists() else []
        if available_files:
            # Use the most recently modified posts file
            latest_file = max(available_files, key=lambda p: p.stat().st_mtime)
            slug = latest_file.stem.replace('_posts', '')
            print(f"🔍 Auto-detected slug: {slug} (from {latest_file.name})")
            generator = RSSFeedGenerator(slug=slug)
        else:
            # Fallback to old default
            print("⚠️  No slug provided and no *_posts.json files found")
            print("   Using legacy default: posts.json → linkedin_feed.xml")
            generator = RSSFeedGenerator()

    success = generator.generate_feed()

    if success:
        print("\n" + "=" * 60)
        print("✅ RSS FEED GENERATED SUCCESSFULLY")
        print("=" * 60)
        print(f"Feed file: {generator.output_file}")
        print(f"Page name: {generator.page_name}")
        print("\nYou can now:")
        print("1. View the feed in an RSS reader")
        print("2. Start local server: python3 serve.py")
        print(f"3. View in browser: http://localhost:8000/{generator.output_file.name}")
        print("=" * 60)
    else:
        print("\n❌ Failed to generate RSS feed")


if __name__ == "__main__":
    main()
