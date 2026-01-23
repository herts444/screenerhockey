"""
API endpoint for getting team lineup from Flashscore.
GET /api/lineups/team?url=<team_url>
"""

from http.server import BaseHTTPRequestHandler
import json
import sys
import os

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

import asyncio
from app.services.flashscore_service import get_team_lineup


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Parse query parameters
            from urllib.parse import urlparse, parse_qs, unquote
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)

            team_url = params.get('url', [''])[0]
            if not team_url:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'success': False, 'error': 'Missing url parameter'}).encode('utf-8'))
                return

            team_url = unquote(team_url)

            # Get team lineup
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            lineup = loop.run_until_complete(get_team_lineup(team_url))
            loop.close()

            response = {
                'success': True,
                **lineup
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
