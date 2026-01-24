"""
Flashscore parsing service for team lineups and player statistics.
Adapted from tg_bot_parsing_flashscore project.
"""

import json
import re
from datetime import datetime
from typing import Optional
import httpx
from bs4 import BeautifulSoup


# Flashscore feed codes for different leagues
# f_4_0_3_en_5 is the hockey feed (4=hockey, 0=day offset, 3=?, en=language, 5=?)
LEAGUE_FEEDS = {
    "KHL": "f_4_0_3_en_5",      # КХЛ (Russia)
    "NHL": "f_1_0_3_en_5",      # НХЛ (North America)
    "AHL": "f_3_0_3_en_5",      # АХЛ (North America)
    "LIIGA": "f_4_0_3_en_5",    # Финская лига
    "DEL": "f_4_0_3_en_5",      # Германия
    "CZECH": "f_4_0_3_en_5",    # Чехия Extraliga
    "DENMARK": "f_4_0_3_en_5",  # Дания Metal Ligaen
    "AUSTRIA": "f_4_0_3_en_5",  # Австрия ICE Hockey League
}

# League name patterns for filtering (what Flashscore returns in ~ZA field)
LEAGUE_NAME_PATTERNS = {
    "KHL": ["KHL"],
    "NHL": ["NHL"],
    "AHL": ["AHL"],
    "LIIGA": ["Liiga"],
    "DEL": ["DEL"],
    "CZECH": ["Extraliga"],
    "DENMARK": ["Metal Ligaen"],
    "AUSTRIA": ["ICE Hockey League"],
}

HEADERS = {"x-fsign": "SW9D1eZo"}

# Headers for HTML page parsing (need User-Agent for regular pages)
PAGE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
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

    Args:
        league: League code (KHL, NHL, AHL, LIIGA, DEL, CZECH, DENMARK, AUSTRIA)
        day_offset: 0 = today, 1 = tomorrow, etc.

    Returns:
        List of match dictionaries filtered by league
    """
    base_feed = LEAGUE_FEEDS.get(league.upper(), LEAGUE_FEEDS["KHL"])
    # Replace day offset in feed code
    feed = base_feed.replace("_0_", f"_{day_offset}_")

    url = f'https://2.flashscore.ninja/2/x/feed/{feed}'

    # Get league name patterns for filtering
    target_patterns = LEAGUE_NAME_PATTERNS.get(league.upper(), [])

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            response = await client.get(url, headers=HEADERS)
            data = response.text

            # If response is empty or just "0", Flashscore has no data
            # This could mean: no matches scheduled, API changed, or rate limited
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

            result.append({
                'id': event_id,
                'url': match_url,
                'home': team_1,
                'away': team_2,
                'league': league_name,
                'league_id': league_id
            })

    return result


async def get_team_urls(match_url: str) -> dict:
    """
    Get team page URLs from a match page.

    Returns:
        Dict with 'home' and 'away' team URLs
    """
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.get(match_url, headers=PAGE_HEADERS, timeout=30.0)
        html_content = response.text

    soup = BeautifulSoup(html_content, 'lxml')
    result_string = soup.find('script', string=re.compile(r"window\.environment"))

    if not result_string:
        return {}

    match = re.search(r"window\.environment\s*=\s*(\{.*\});", result_string.string)

    if match:
        json_data = json.loads(match.group(1))
        home_link = json_data.get('participantsData', {}).get('home', [{}])[0].get('detail_link', '')
        away_link = json_data.get('participantsData', {}).get('away', [{}])[0].get('detail_link', '')

        return {
            'home': f'https://www.flashscore.com.ua{home_link}' if home_link else '',
            'away': f'https://www.flashscore.com.ua{away_link}' if away_link else ''
        }

    return {}


async def get_player_stats(player_url: str, player_name: str, team_name: str) -> dict:
    """
    Get individual player statistics.

    Returns:
        Dict with player stats including status, games, goals, assists, points
    """
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.get(player_url, headers=PAGE_HEADERS, timeout=30.0)
        player_html = response.text

    soup = BeautifulSoup(player_html, 'lxml')
    result_string = soup.find('script', string=re.compile(r"window\.playerProfilePageEnvironment"))

    json_data = {}
    if result_string:
        script_content = result_string.string
        match = re.search(r"window\.playerProfilePageEnvironment\s*=\s*(\{.*\});", script_content)
        if match:
            json_data = json.loads(match.group(1))

    # Determine player status from last matches
    last_match_status = ''
    last_matches = json_data.get('lastMatchesData', {}).get('lastMatches', [])

    for step in last_matches:
        home_participant = step.get('homeParticipantName', '')
        away_participant = step.get('awayParticipantName', '')

        if team_name in (home_participant, away_participant):
            absence = step.get('absenceCategory', '')
            if absence == '':
                last_match_status = 'заявлен'
            else:
                last_match_status = absence
            break

    # Get season statistics
    matches_played = 0
    goals = 0
    assists = 0
    points = 0
    season_name = ''

    seasons = json_data.get('careerTables', [{}])[0].get('seasons', []) if json_data.get('careerTables') else []

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

    Returns:
        Dict with team name and categorized players
    """
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.get(team_url, headers=PAGE_HEADERS, timeout=30.0)
        html_content = response.text

    soup = BeautifulSoup(html_content, 'lxml')

    # Get team name
    team_name_elem = soup.find("div", class_="heading__name")
    team_name = team_name_elem.text.strip() if team_name_elem else "Unknown"

    # Get all players
    players_elements = soup.find_all("a", class_="lineupTable__cell--name")

    players = []
    seen_links = set()

    for player_elem in players_elements:
        player_name = player_elem.get_text(strip=True)
        player_link = f'https://www.flashscore.com.ua{player_elem.get("href", "")}'

        if player_link in seen_links:
            continue
        seen_links.add(player_link)

        try:
            player_stats = await get_player_stats(player_link, player_name, team_name)
            players.append(player_stats)
        except Exception as e:
            # Skip players with parsing errors
            print(f"Error parsing player {player_name}: {e}")
            continue

    # Categorize players according to requirements
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
    3. absent - injured/not in roster, sorted by points (red)
    4. others - <0.5 ppg, in roster (no color)
    """
    leaders_active = []      # Yellow: top players who played
    leaders_questionable = [] # Orange: top players who missed last match
    absent = []              # Red: injured/not available
    others = []              # No color: low-efficiency players

    EFFICIENCY_THRESHOLD = 0.5

    for player in players:
        efficiency = player.get('efficiency', 0)
        status = player.get('status', '').lower()

        is_available = status == 'заявлен'
        is_top_player = efficiency > EFFICIENCY_THRESHOLD
        is_absent = status in ['травма', 'не заявлен', 'injury', 'missing'] or (status != 'заявлен' and status != '')

        if is_absent or (status != 'заявлен' and status != ''):
            # Red group - absent players
            absent.append(player)
        elif is_top_player and is_available:
            # Yellow group - top players in roster
            leaders_active.append(player)
        elif is_top_player and not is_available:
            # Orange group - top players questionable
            leaders_questionable.append(player)
        else:
            # No color - other players
            others.append(player)

    # Sort each group
    leaders_active.sort(key=lambda x: x.get('efficiency', 0), reverse=True)
    leaders_questionable.sort(key=lambda x: x.get('efficiency', 0), reverse=True)
    absent.sort(key=lambda x: x.get('points', 0), reverse=True)  # By total points
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

    Returns:
        Dict with home and away team lineups
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
