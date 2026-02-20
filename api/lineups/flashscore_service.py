"""
Flashscore parsing service for team lineups and player statistics.
Copied from working tg_bot_parsing_flashscore bot.
"""

import json
import re
from datetime import datetime
import httpx
from bs4 import BeautifulSoup


# Simple headers - same as working bot
HEADERS = {"x-fsign": "SW9D1eZo"}

# League name patterns for filtering
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


def is_in_season(season: str) -> bool:
    """Check if current date is within the season."""
    try:
        start_year, end_year = map(int, season.split('/'))
        season_start = datetime(start_year, 7, 1)
        season_end = datetime(end_year, 6, 30)
        return season_start <= datetime.now() <= season_end
    except (ValueError, AttributeError):
        return False


async def get_matches_list(league: str, day_offset: int = 0) -> list:
    """
    Get list of matches for a league on a specific day.
    Uses same endpoint as working bot: d.flashscore.ru.com
    """
    # Feed format: f_4_{day}_3_en_5 for hockey
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
            # Filter by league name patterns
            is_target_league = any(pattern.lower() in league_name.lower() for pattern in target_patterns)
            if not is_target_league:
                continue

            event_id = game.get("~AA", "")
            match_url = f'https://www.flashscore.com.ua/match/{event_id}/#/match-summary/match-summary'
            team_1 = game.get("AE", "")
            team_2 = game.get("AF", "")
            timestamp = game.get("AD", "")

            result.append({
                'id': event_id,
                'url': match_url,
                'home': team_1,
                'away': team_2,
                'league': league_name,
                'league_id': league_id,
                'timestamp': int(timestamp) if timestamp else None
            })

    return result


async def get_team_urls(match_url: str) -> dict:
    """
    Get team page URLs from a match page.
    Same logic as working bot.
    """
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
            'home': f'https://www.flashscore.com.ua{home_link}',
            'away': f'https://www.flashscore.com.ua{away_link}'
        }

    return result_dict


async def get_player_stats(player_url: str, player_name: str, team_name: str) -> dict:
    """
    Get individual player statistics.
    Same logic as working bot's player_status function.
    """
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

    # Determine player status from last matches
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

    # Get season statistics
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

    # Calculate efficiency (points per game)
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


async def get_team_lineup(team_url: str) -> dict:
    """
    Get full team lineup with player statistics.
    Optimized: load all players in parallel.
    """
    async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
        response = await client.get(team_url, headers=HEADERS)
        html_content = response.text

    soup = BeautifulSoup(html_content, 'html.parser')

    # Get team name
    team_name_elem = soup.find("div", class_="heading__name")
    team_name = team_name_elem.text.strip() if team_name_elem else "Unknown"

    # Get all players
    players_elements = soup.find_all("a", class_="lineupTable__cell--name")

    # Collect unique players
    player_data = []
    seen_links = set()

    for player_elem in players_elements:
        player_name = player_elem.get_text(strip=True)
        player_link = f'https://www.flashscore.com.ua{player_elem.get("href", "")}'

        if player_link in seen_links:
            continue
        seen_links.add(player_link)
        player_data.append((player_link, player_name))

    # Load all player stats in parallel
    import asyncio

    async def safe_get_player(link, name):
        try:
            return await get_player_stats(link, name, team_name)
        except Exception as e:
            print(f"Error parsing player {name}: {e}")
            return None

    tasks = [safe_get_player(link, name) for link, name in player_data]
    results = await asyncio.gather(*tasks)

    players = [p for p in results if p is not None]

    # Categorize players
    categorized = categorize_players(players)

    return {
        'team': team_name,
        'players': categorized,
        'total_players': len(players)
    }


def categorize_players(players: list) -> dict:
    """
    Categorize players into groups:
    1. leaders_active - >0.5 ppg + played last match (yellow)
    2. leaders_questionable - >0.5 ppg + missed last match (orange)
    3. absent - injured/not in roster (red)
    4. others - <0.5 ppg, in roster (no color)
    """
    leaders_active = []
    leaders_questionable = []
    absent = []
    others = []

    EFFICIENCY_THRESHOLD = 0.3

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

    # Sort each group
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


async def get_match_lineups(match_url: str) -> dict:
    """
    Get lineups for both teams in a match.
    """
    team_urls = await get_team_urls(match_url)

    result = {
        'home': None,
        'away': None
    }

    if team_urls.get('home'):
        result['home'] = await get_team_lineup(team_urls['home'])

    if team_urls.get('away'):
        result['away'] = await get_team_lineup(team_urls['away'])

    return result
