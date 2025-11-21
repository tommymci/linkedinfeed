#!/usr/bin/env python3
"""
One-time login setup script
Opens browser, lets you log in, and saves the session
"""

from playwright.sync_api import sync_playwright
from pathlib import Path
import time

def setup_login():
    """Interactive login setup"""
    state_dir = Path(__file__).parent / "browser_state"
    state_file = state_dir / "linkedin_state.json"

    state_dir.mkdir(exist_ok=True)

    print("=" * 70)
    print("🔐 LINKEDIN LOGIN SETUP")
    print("=" * 70)
    print("\nThis will open a browser window.")
    print("Please log in to LinkedIn and navigate around a bit.")
    print("When you're done, come back here and press CTRL+C to save.\n")
    print("=" * 70)

    with sync_playwright() as p:
        # Launch browser in non-headless mode
        browser = p.chromium.launch(headless=False)

        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )

        page = context.new_page()

        # Navigate to LinkedIn
        print("\n📄 Opening LinkedIn...")
        page.goto("https://www.linkedin.com/login")

        print("\n✅ Browser opened!")
        print("👉 Please log in to LinkedIn in the browser window")
        print("👉 After logging in, press CTRL+C here to save the session\n")

        try:
            # Wait indefinitely for user to login
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n💾 Saving login session...")
            context.storage_state(path=str(state_file))
            print(f"✅ Session saved to: {state_file}")
            print("\n🎉 Setup complete! You can now run linkedin_scraper.py")
            print("=" * 70)

        finally:
            context.close()
            browser.close()

if __name__ == "__main__":
    setup_login()
