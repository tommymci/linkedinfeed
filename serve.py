#!/usr/bin/env python3
"""
Simple HTTP server to view the RSS feed with styling in browser
"""

import http.server
import socketserver
import os
from pathlib import Path

PORT = 8000

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers to allow local file access
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

    def guess_type(self, path):
        # Ensure proper MIME types
        if path.endswith('.xml'):
            return 'application/xml'
        elif path.endswith('.xsl'):
            return 'application/xslt+xml'
        return super().guess_type(path)

def serve():
    """Start HTTP server"""
    # Change to feed directory
    feed_dir = Path(__file__).parent / "feed"
    if feed_dir.exists():
        os.chdir(feed_dir)
    else:
        # Fallback to parent directory if feed folder doesn't exist
        os.chdir(Path(__file__).parent)

    Handler = MyHTTPRequestHandler

    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print("=" * 60)
        print("🌐 RSS Feed Server Started")
        print("=" * 60)
        print(f"\n📡 Server running at: http://localhost:{PORT}/")
        print(f"\n🔗 View your RSS feeds at:")

        # List available feeds
        if feed_dir.exists():
            feeds = list(feed_dir.glob("*.xml"))
            if feeds:
                for feed in sorted(feeds):
                    print(f"   http://localhost:{PORT}/{feed.name}")
            else:
                print(f"   (No feeds found in feed/ folder)")
        else:
            print(f"   http://localhost:{PORT}/linkedin_feed.xml")

        print("\n💡 Press Ctrl+C to stop the server\n")
        print("=" * 60)

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n✅ Server stopped")
            print("=" * 60)

if __name__ == "__main__":
    serve()
