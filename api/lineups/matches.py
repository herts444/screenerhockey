"""
API endpoint for getting matches list from Flashscore.
GET /api/lineups/matches?league=KHL&day=0
"""

from http.server import BaseHTTPRequestHandler
import json
import asyncio
import httpx


# Flashscore config
HEADERS = {"x-fsign": "SW9D1eZo"}

LEAGUE_NAME_PATTERNS = {
    "KHL": ["KHL"],
    "NHL": ["NHL"],
    "AHL": ["AHL"],
    "LIIGA": ["Liiga"],
    "DEL": ["DEL"],
    "CZECH": ["Extraliga"],
    "DENMARK": ["Metal Ligaen"],
    "AUSTRIA": ["ICE Hockey League"],
    "SWISS": ["National League"],
}


async def get_matches_list(league, day_offset=0):
    feed = f'f_4_{day_offset}_3_en_5'
    url = f'https://2.flashscore.ninja/2/x/feed/{feed}'
    target_patterns = LEAGUE_NAME_PATTERNS.get(league.upper(), [])

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            response = await client.get(url, headers=HEADERS)
            data = response.text
            if not data or data.strip() in ('0', ''):
                return []
            data = data.split('¬')
    except Exception as e:
        print(f"Error fetching feed: {e}")
        return []

    data_list = [{}]
    result = []

    for item in data:
        parts = item.split('÷')
        key = parts[0]
        value = parts[-1] if len(parts) > 1 else ''
        if '~' in key:
            data_list.append({key: value})
        else:
            data_list[-1].update({key: value})

    league_name = ''
    league_id = ''

    for game in data_list:
        keys = list(game.keys())
        if not keys:
            continue
        if '~ZA' in keys[0]:
            league_name = game.get('~ZA', '')
            league_id = game.get('ZC', '')
        if 'AA' in keys[0]:
            is_target_league = any(p.lower() in league_name.lower() for p in target_patterns)
            if not is_target_league:
                continue
            event_id = game.get("~AA", "")
            match_url = f'https://www.flashscore.com/match/{event_id}/#/match-summary/match-summary'
            result.append({
                'id': event_id,
                'url': match_url,
                'home': game.get("AE", ""),
                'away': game.get("AF", ""),
                'league': league_name,
                'league_id': league_id,
                'timestamp': int(game.get("AD", "")) if game.get("AD", "") else None
            })

    return result


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)

            league = params.get('league', ['KHL'])[0].upper()
            day = int(params.get('day', ['0'])[0])

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            matches = loop.run_until_complete(get_matches_list(league, day))
            loop.close()

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
