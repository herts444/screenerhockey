"""GET /api/leagues - Get available leagues"""
from http.server import BaseHTTPRequestHandler
import json


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "s-maxage=86400")
        self.end_headers()

        leagues = {
            "leagues": [
                {"code": "NHL", "name": "NHL", "name_ru": "НХЛ", "cached": True},
                {"code": "AHL", "name": "AHL", "name_ru": "АХЛ", "cached": True},
                {"code": "LIIGA", "name": "Liiga", "name_ru": "Лиига (Финляндия)", "cached": True}
            ]
        }
        self.wfile.write(json.dumps(leagues).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
