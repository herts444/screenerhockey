"""
API endpoint for getting both teams' lineups for a match.
GET /api/lineups/match?url=<match_url>
"""

from http.server import BaseHTTPRequestHandler
import json
import sys
import os

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

import asyncio
from app.services.flashscore_service import get_match_lineups


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Parse query parameters
            from urllib.parse import urlparse, parse_qs, unquote
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)

            match_url = params.get('url', [''])[0]
            if not match_url:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'success': False, 'error': 'Missing url parameter'}).encode('utf-8'))
                return

            match_url = unquote(match_url)

            # Get both teams' lineups
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            lineups = loop.run_until_complete(get_match_lineups(match_url))
            loop.close()

            response = {
                'success': True,
                'home': lineups.get('home'),
                'away': lineups.get('away')
            }

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            error_response = {'success': False, 'error': str(e)}
            self.wfile.write(json.dumps(error_response).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
