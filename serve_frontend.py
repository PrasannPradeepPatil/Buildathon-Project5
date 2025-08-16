
#!/usr/bin/env python3
"""
Simple HTTP server to serve the frontend
"""
import http.server
import socketserver
import os
from pathlib import Path

PORT = 3000
FRONTEND_DIR = Path(__file__).parent / "frontend"

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)

if __name__ == "__main__":
    os.chdir(FRONTEND_DIR)
    with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
        print(f"Serving frontend at http://0.0.0.0:{PORT}")
        print(f"Frontend directory: {FRONTEND_DIR}")
        httpd.serve_forever()
