#!/bin/bash
# Run LinkedIn scraper and generate RSS feed

echo "🚀 Starting LinkedIn scraper..."
venv/bin/python3 linkedin_scraper.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Scraping completed successfully!"
    echo ""
    echo "📡 Generating RSS feed..."
    venv/bin/python3 generate_rss.py

    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ All done! Feed is ready at linkedin_feed.xml"
        echo ""
        echo "To view the feed, run: python3 serve.py"
    fi
else
    echo ""
    echo "❌ Scraping failed. Please check the errors above."
fi
