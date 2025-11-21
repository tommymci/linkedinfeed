#!/usr/bin/env python3
"""
Test the RSS feed page to check for errors
"""
from playwright.sync_api import sync_playwright
import time

def test_feed():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Listen for console messages
        def handle_console(msg):
            print(f"CONSOLE [{msg.type}]: {msg.text}")

        # Listen for page errors
        def handle_error(error):
            print(f"PAGE ERROR: {error}")

        page.on("console", handle_console)
        page.on("pageerror", handle_error)

        print("Opening RSS feed page...")
        page.goto("http://localhost:8000/linkedin_feed.xml")

        # Wait a bit for page to load
        time.sleep(5)

        # Check page content
        print("\nPage title:", page.title())

        # Check if posts are visible
        posts = page.query_selector_all('.post')
        print(f"\nFound {len(posts)} posts on page")

        # Check if there's any content
        body = page.query_selector('body')
        if body:
            text = body.inner_text()
            print(f"\nBody text length: {len(text)} characters")
            if len(text) < 100:
                print("Body content:", text)

        # Take screenshot
        page.screenshot(path="feed_screenshot.png")
        print("\nScreenshot saved to feed_screenshot.png")

        # Keep browser open for manual inspection
        print("\nBrowser will stay open for 10 seconds...")
        time.sleep(10)

        browser.close()

if __name__ == "__main__":
    test_feed()
