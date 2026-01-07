"""GET /api/status - Get API status"""
from http.server import BaseHTTPRequestHandler
import json
from datetime import datetime


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        status = {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0-serverless",
            "cache_loaded": {"NHL": True, "AHL": True, "LIIGA": True}
        }
        self.wfile.write(json.dumps(status).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
