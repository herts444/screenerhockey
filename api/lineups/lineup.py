"""
API endpoint for getting lineups from Flashscore.
GET /api/lineups/lineup?type=match&url=<match_url>  - Get both teams
GET /api/lineups/lineup?type=team&url=<team_url>    - Get single team
"""

from http.server import BaseHTTPRequestHandler
import json
import re
import asyncio
from datetime import datetime
import httpx
from bs4 import BeautifulSoup


HEADERS = {"x-fsign": "SW9D1eZo"}
EFFICIENCY_THRESHOLD = 0.3


def is_in_season(season):
    try:
        start_year, end_year = map(int, season.split('/'))
        season_start = datetime(start_year, 7, 1)
        season_end = datetime(end_year, 6, 30)
        return season_start <= datetime.now() <= season_end
    except (ValueError, AttributeError):
        return False


async def get_team_urls(match_url):
    async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
        response = await client.get(match_url, headers=HEADERS)
        html_content = response.text

    soup = BeautifulSoup(html_content, 'html.parser')
    result_string = soup.find('script', string=re.compile(r"window\.environment"))

    if not result_string:
        return {}

    match = re.search(r"window\.environment\s*=\s*(\{.*\});", result_string.string)

    result_dict = {}
    if match:
        json_data = json.loads(match.group(1))
        home_link = json_data['participantsData']['home'][0]['detail_link']
        away_link = json_data['participantsData']['away'][0]['detail_link']
        result_dict = {
            'home': f'https://www.flashscore.com{home_link}',
            'away': f'https://www.flashscore.com{away_link}'
        }

    return result_dict


async def get_player_stats(player_url, player_name, team_name):
    async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
        response = await client.get(player_url, headers=HEADERS)
        player_html = response.text

    soup = BeautifulSoup(player_html, 'html.parser')
    result_string = soup.find('script', string=re.compile(r"window\.playerProfilePageEnvironment"))

    json_data = {}
    if result_string:
        script_content = result_string.string
        match = re.search(r"window\.playerProfilePageEnvironment\s*=\s*(\{.*\});", script_content)
        if match:
            json_data = json.loads(match.group(1))

    last_match_status = ''
    try:
        steps = json_data.get('lastMatchesData', {}).get('lastMatches', [])
        for step in steps:
            home_participant = step.get('homeParticipantName', '')
            away_participant = step.get('awayParticipantName', '')
            if team_name in (home_participant, away_participant):
                if step.get('absenceCategory', '') == '':
                    last_match_status = 'заявлен'
                else:
                    last_match_status = step.get('absenceCategory', '')
                break
    except Exception:
        pass

    matches_played = 0
    goals = 0
    assists = 0
    points = 0
    season_name = ''

    try:
        seasons = json_data.get('careerTables', [{}])[0].get('seasons', [])
    except (IndexError, KeyError):
        seasons = []

    for season in seasons:
        try:
            if is_in_season(season.get('season_name', '')) and season.get('team_name') == team_name:
                matches_played = int(season.get('matches_played', 0) or 0)
                goals = int(season.get('goals', 0) or 0)
                assists = int(season.get('assists', 0) or 0)
                points = int(season.get('points', 0) or 0)
                season_name = season.get('season_name', '')
                break
        except (ValueError, TypeError):
            continue

    efficiency = round(points / matches_played, 2) if matches_played > 0 else 0.0

    return {
        'name': player_name,
        'status': last_match_status,
        'matches': matches_played,
        'goals': goals,
        'assists': assists,
        'points': points,
        'efficiency': efficiency,
        'season': season_name
    }


def categorize_players(players):
    leaders_active = []
    leaders_questionable = []
    absent = []
    others = []

    for player in players:
        efficiency = player.get('efficiency', 0)
        status = player.get('status', '').lower()
        is_available = status == 'заявлен'
        is_top_player = efficiency > EFFICIENCY_THRESHOLD
        is_absent = status in ['травма', 'не заявлен', 'injury', 'missing'] or (status != 'заявлен' and status != '')

        if is_absent:
            absent.append(player)
        elif is_top_player and is_available:
            leaders_active.append(player)
        elif is_top_player and not is_available:
            leaders_questionable.append(player)
        else:
            others.append(player)

    leaders_active.sort(key=lambda x: x.get('efficiency', 0), reverse=True)
    leaders_questionable.sort(key=lambda x: x.get('efficiency', 0), reverse=True)
    absent.sort(key=lambda x: x.get('points', 0), reverse=True)
    others.sort(key=lambda x: x.get('efficiency', 0), reverse=True)

    return {
        'leaders_active': leaders_active,
        'leaders_questionable': leaders_questionable,
        'absent': absent,
        'others': others
    }


async def get_team_lineup(team_url):
    async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
        response = await client.get(team_url, headers=HEADERS)
        html_content = response.text

    soup = BeautifulSoup(html_content, 'html.parser')
    team_name_elem = soup.find("div", class_="heading__name")
    team_name = team_name_elem.text.strip() if team_name_elem else "Unknown"

    players_elements = soup.find_all("a", class_="lineupTable__cell--name")
    player_data = []
    seen_links = set()

    for player_elem in players_elements:
        pname = player_elem.get_text(strip=True)
        player_link = f'https://www.flashscore.com{player_elem.get("href", "")}'
        if player_link in seen_links:
            continue
        seen_links.add(player_link)
        player_data.append((player_link, pname))

    async def safe_get_player(link, name):
        try:
            return await get_player_stats(link, name, team_name)
        except Exception as e:
            print(f"Error parsing player {name}: {e}")
            return None

    tasks = [safe_get_player(link, name) for link, name in player_data]
    results = await asyncio.gather(*tasks)
    players = [p for p in results if p is not None]
    categorized = categorize_players(players)

    return {
        'team': team_name,
        'players': categorized,
        'total_players': len(players)
    }


async def get_match_lineups(match_url):
    team_urls = await get_team_urls(match_url)
    result = {'home': None, 'away': None}
    if team_urls.get('home'):
        result['home'] = await get_team_lineup(team_urls['home'])
    if team_urls.get('away'):
        result['away'] = await get_team_lineup(team_urls['away'])
    return result


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            from urllib.parse import urlparse, parse_qs, unquote
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)

            lineup_type = params.get('type', ['match'])[0]
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
                lineup = loop.run_until_complete(get_team_lineup(url))
                response = {'success': True, **lineup}
            else:
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
            import traceback
            error_details = {
                'success': False,
                'error': str(e),
                'type': type(e).__name__,
                'traceback': traceback.format_exc()
            }
            print(f"Lineup API error: {error_details}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(error_details, ensure_ascii=False).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
