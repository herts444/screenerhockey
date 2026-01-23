"""
API endpoint for getting lineups from Flashscore.
GET /api/lineups/lineup?type=match&url=<match_url>  - Get both teams
GET /api/lineups/lineup?type=team&url=<team_url>    - Get single team
"""

from http.server import BaseHTTPRequestHandler
import json
import sys
import os

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

import asyncio
from app.services.flashscore_service import get_team_lineup, get_match_lineups


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            from urllib.parse import urlparse, parse_qs, unquote
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)

            lineup_type = params.get('type', ['match'])[0]  # 'match' or 'team'
            url = params.get('url', [''])[0]

            if not url:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'success': False, 'error': 'Missing url parameter'}).encode('utf-8'))
                return

            url = unquote(url)

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            if lineup_type == 'team':
                # Single team lineup
                lineup = loop.run_until_complete(get_team_lineup(url))
                response = {'success': True, **lineup}
            else:
                # Both teams (match)
                lineups = loop.run_until_complete(get_match_lineups(url))
                response = {
                    'success': True,
                    'home': lineups.get('home'),
                    'away': lineups.get('away')
                }

            loop.close()

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
            self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
