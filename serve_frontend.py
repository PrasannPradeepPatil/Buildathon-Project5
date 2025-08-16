
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
    
    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

if __name__ == "__main__":
    print(f"Starting frontend server on port {PORT}")
    print(f"Frontend directory: {FRONTEND_DIR}")
    
    if not FRONTEND_DIR.exists():
        print(f"Error: Frontend directory {FRONTEND_DIR} does not exist!")
        exit(1)
    
    try:
        with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
            print(f"Frontend server running at http://0.0.0.0:{PORT}")
            httpd.serve_forever()
    except Exception as e:
        print(f"Error starting frontend server: {e}")
