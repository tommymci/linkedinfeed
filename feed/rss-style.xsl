<?xml version="1.0" encoding="UTF-8"?>
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
</xsl:stylesheet>