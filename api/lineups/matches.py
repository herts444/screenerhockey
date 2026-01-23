"""
API endpoint for getting matches list from Flashscore.
GET /api/lineups/matches?league=KHL&day=0
"""

from http.server import BaseHTTPRequestHandler
import json
import sys
import os

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

import asyncio
from app.services.flashscore_service import get_matches_list


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Parse query parameters
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)

            league = params.get('league', ['KHL'])[0].upper()
            day = int(params.get('day', ['0'])[0])

            # Get matches
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            matches = loop.run_until_complete(get_matches_list(league, day))
            loop.close()

            # Group by league
            leagues = {}
            for match in matches:
                league_name = match.get('league', 'Unknown')
                if league_name not in leagues:
                    leagues[league_name] = []
                leagues[league_name].append(match)

            response = {
                'success': True,
                'league': league,
                'day': day,
                'leagues': leagues,
                'total_matches': len(matches)
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
