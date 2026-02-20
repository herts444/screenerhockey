"""Test endpoint to check dependencies"""
from http.server import BaseHTTPRequestHandler
import json


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        results = {}

        try:
            import httpx
            results['httpx'] = 'OK'
        except Exception as e:
            results['httpx'] = str(e)

        try:
            from bs4 import BeautifulSoup
            results['bs4'] = 'OK'
        except Exception as e:
            results['bs4'] = str(e)

        try:
            import re
            results['re'] = 'OK'
        except Exception as e:
            results['re'] = str(e)

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(results).encode('utf-8'))
