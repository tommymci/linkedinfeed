#!/usr/bin/env python3
"""
Cleanup script to remove old generic files and migrate to slug-based naming
"""

from pathlib import Path
import os

def main():
    """Remove old generic files"""
    base_dir = Path(__file__).parent

    # Files to remove
    old_files = [
        "posts.json",
        "linkedin_feed.xml",
        "debug_posts.txt",
        "debug_screenshot.png",
        "error_screenshot.png",
        "after_sort_screenshot.png",
        "feed_screenshot.png"
    ]

    print("🧹 Cleaning up old generic files...")
    print("=" * 60)

    removed_count = 0
    for filename in old_files:
        filepath = base_dir / filename
        if filepath.exists():
            print(f"  🗑️  Removing: {filename}")
            filepath.unlink()
            removed_count += 1
        else:
            print(f"  ⏭️  Skipping: {filename} (doesn't exist)")

    print("=" * 60)
    print(f"✅ Cleanup complete! Removed {removed_count} file(s)")

    # Show remaining files
    print("\n📁 Remaining data files:")
    json_files = list(base_dir.glob("*_posts.json"))
    xml_files = list(base_dir.glob("*.xml"))

    if json_files:
        print("  Posts JSON files:")
        for f in json_files:
            print(f"    - {f.name}")

    if xml_files:
        print("  RSS XML files:")
        for f in xml_files:
            print(f"    - {f.name}")

    if not json_files and not xml_files:
        print("  (No data files found - run scraper first)")


if __name__ == "__main__":
    main()
