"""GET /api/teams/[team]/stats - Get team statistics"""
from http.server import BaseHTTPRequestHandler
import json
import asyncio
from urllib.parse import urlparse, parse_qs
import re
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Tuple
import math
import httpx

# Team names
TEAM_NAMES_RU = {
    "ANA": "Анахайм Дакс", "ARI": "Аризона Койотс", "BOS": "Бостон Брюинз",
    "BUF": "Баффало Сейбрз", "CGY": "Калгари Флэймз", "CAR": "Каролина Харрикейнз",
    "CHI": "Чикаго Блэкхокс", "COL": "Колорадо Эвеланш", "CBJ": "Коламбус Блю Джекетс",
    "DAL": "Даллас Старз", "DET": "Детройт Ред Уингз", "EDM": "Эдмонтон Ойлерз",
    "FLA": "Флорида Пантерз", "LAK": "Лос-Анджелес Кингз", "MIN": "Миннесота Уайлд",
    "MTL": "Монреаль Канадиенс", "NSH": "Нэшвилл Предаторз", "NJD": "Нью-Джерси Девилз",
    "NYI": "Нью-Йорк Айлендерс", "NYR": "Нью-Йорк Рейнджерс", "OTT": "Оттава Сенаторз",
    "PHI": "Филадельфия Флайерз", "PIT": "Питтсбург Пингвинз", "SJS": "Сан-Хосе Шаркс",
    "SEA": "Сиэтл Кракен", "STL": "Сент-Луис Блюз", "TBL": "Тампа-Бэй Лайтнинг",
    "TOR": "Торонто Мейпл Лифс", "UTA": "Юта Хоккей Клаб", "VAN": "Ванкувер Кэнакс",
    "VGK": "Вегас Голден Найтс", "WSH": "Вашингтон Кэпиталз", "WPG": "Виннипег Джетс"
}

AHL_TEAM_NAMES_RU = {
    "ABB": "Эбботсфорд Кэнакс", "BAK": "Бейкерсфилд Кондорс", "BEL": "Беллвилл Сенаторз",
    "BRI": "Бриджпорт Айлендерс", "CGY": "Калгари Рэнглерс", "CHI": "Чикаго Вулвз",
    "CLE": "Кливленд Монстерс", "CLT": "Шарлотт Чекерз", "COA": "Коачелла Вэлли Файрбёрдс",
    "COL": "Колорадо Иглс", "GR": "Гранд Рапидс Гриффинс", "HER": "Херши Беарс",
    "HFD": "Хартфорд Вулф Пэк", "IA": "Айова Уайлд", "LAV": "Лаваль Рокет",
    "LV": "Хендерсон Силвер Найтс", "MB": "Манитоба Муз", "MIL": "Милуоки Эдмиралс",
    "ONT": "Онтарио Рейн", "PRO": "Провиденс Брюинз", "ROC": "Рочестер Американс",
    "SD": "Сан-Диего Галлз", "SJ": "Сан-Хосе Барракуда", "SPR": "Спрингфилд Тандербёрдс",
    "SYR": "Сиракьюз Кранч", "TEX": "Техас Старз", "TOR": "Торонто Марлиз",
    "TUC": "Тусон Роудраннерс", "UTC": "Ютика Кометс", "WBS": "Уилкс-Барре Пингвинз",
}

LIIGA_TEAM_NAMES_RU = {
    "HIFK": "ХИФК Хельсинки", "K-ESPOO": "К-Эспоо", "KALPA": "КалПа Куопио",
    "HPK": "ХПК Хямеэнлинна", "ILVES": "Ильвес Тампере", "JYP": "ЮП Ювяскюля",
    "JUKURIT": "Юкурит Миккели", "LUKKO": "Лукко Раума", "PELICANS": "Пеликанс Лахти",
    "SAIPA": "СайПа Лаппеэнранта", "SPORT": "Спорт Вааса", "TAPPARA": "Таппара Тампере",
    "TPS": "ТПС Турку", "ASSAT": "Ассат Пори", "KARPAT": "Кярпят Оулу",
    "KOOKOO": "Кукоо Коувола", "ÄSSÄT": "Ассат Пори", "KÄRPÄT": "Кярпят Оулу",
}


@dataclass
class GameResult:
    game_id: str
    date: datetime
    opponent: str
    opponent_abbrev: str
    is_home: bool
    team_score: int
    opponent_score: int
    total_goals: int


def calculate_weight(index: int, total: int, decay_factor: float = 0.1) -> float:
    position_from_end = total - index - 1
    return math.exp(-decay_factor * position_from_end)


def calculate_weighted_percentage(matches: List[GameResult], condition_func, decay_factor: float = 0.1) -> Tuple[float, float]:
    if not matches:
        return 0.0, 0.0

    total = len(matches)
    matches_meeting_condition = 0
    weighted_sum = 0.0
    total_weight = 0.0
    sorted_matches = sorted(matches, key=lambda m: m.date)

    for i, match in enumerate(sorted_matches):
        weight = calculate_weight(i, total, decay_factor)
        total_weight += weight
        if condition_func(match):
            matches_meeting_condition += 1
            weighted_sum += weight

    simple_pct = (matches_meeting_condition / total) * 100 if total > 0 else 0
    weighted_pct = (weighted_sum / total_weight) * 100 if total_weight > 0 else 0
    return round(simple_pct, 1), round(weighted_pct, 1)


def get_full_team_stats(home_matches: List[GameResult], away_matches: List[GameResult]) -> Dict:
    stats = {
        "home": {"total_matches": len(home_matches), "individual_totals": {}, "match_totals": {}},
        "away": {"total_matches": len(away_matches), "individual_totals": {}, "match_totals": {}}
    }

    for threshold in [2, 3, 4, 5, 6]:
        for location, matches in [("home", home_matches), ("away", away_matches)]:
            condition = lambda m, t=threshold: m.team_score >= t
            matching = [m for m in matches if condition(m)]
            simple_pct, weighted_pct = calculate_weighted_percentage(matches, condition)
            stats[location]["individual_totals"][f"{threshold}+"] = {
                "count": len(matching),
                "percentage": simple_pct,
                "weighted_percentage": weighted_pct,
                "matches": [{"date": m.date.strftime("%d.%m.%Y"), "opponent": m.opponent, "opponent_abbrev": m.opponent_abbrev, "score": f"{m.team_score}:{m.opponent_score}"} for m in matching]
            }

    for threshold in [5, 6, 7, 8]:
        for location, matches in [("home", home_matches), ("away", away_matches)]:
            condition = lambda m, t=threshold: m.total_goals >= t
            matching = [m for m in matches if condition(m)]
            simple_pct, weighted_pct = calculate_weighted_percentage(matches, condition)
            stats[location]["match_totals"][f"{threshold}+"] = {
                "count": len(matching),
                "percentage": simple_pct,
                "weighted_percentage": weighted_pct,
                "matches": [{"date": m.date.strftime("%d.%m.%Y"), "opponent": m.opponent, "opponent_abbrev": m.opponent_abbrev, "score": f"{m.team_score}:{m.opponent_score}", "total": m.total_goals} for m in matching]
            }

    return stats


async def get_nhl_team_stats(team_abbrev: str, last_n: int = 0):
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"https://api-web.nhle.com/v1/club-schedule-season/{team_abbrev}/20242025")
        response.raise_for_status()
        schedule = response.json()

    games = schedule.get("games", [])
    # Filter only regular season games (gameType == 2), exclude preseason (1) and playoffs (3)
    finished = [g for g in games if g.get("gameState") in ["OFF", "FINAL"] and g.get("gameType") == 2]

    home_matches, away_matches = [], []
    for game in finished:
        home_abbrev = game.get("homeTeam", {}).get("abbrev")
        away_abbrev = game.get("awayTeam", {}).get("abbrev")
        is_home = home_abbrev == team_abbrev
        home_score = game.get("homeTeam", {}).get("score", 0) or 0
        away_score = game.get("awayTeam", {}).get("score", 0) or 0

        if is_home:
            team_score, opp_score = home_score, away_score
            opp_abbrev = away_abbrev
        else:
            team_score, opp_score = away_score, home_score
            opp_abbrev = home_abbrev

        try:
            game_date = datetime.strptime(game.get("gameDate"), "%Y-%m-%d")
        except:
            continue

        result = GameResult(str(game.get("id")), game_date, TEAM_NAMES_RU.get(opp_abbrev, opp_abbrev), opp_abbrev, is_home, team_score, opp_score, team_score + opp_score)
        if is_home:
            home_matches.append(result)
        else:
            away_matches.append(result)

    home_matches.sort(key=lambda x: x.date, reverse=True)
    away_matches.sort(key=lambda x: x.date, reverse=True)
    if last_n > 0:
        home_matches = home_matches[:last_n]
        away_matches = away_matches[:last_n]

    return {"team": {"abbrev": team_abbrev, "name": team_abbrev, "name_ru": TEAM_NAMES_RU.get(team_abbrev, team_abbrev), "logo_url": None}, "stats": get_full_team_stats(home_matches, away_matches)}


async def get_ahl_team_stats(team_abbrev: str, last_n: int = 0):
    base_url = "https://lscluster.hockeytech.com/feed/index.php"

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Get teams
        url = f"{base_url}?feed=modulekit&view=teamsbyseason&key=50c2cd9b5e18e390&fmt=json&client_code=ahl&lang=en&season_id=90"
        response = await client.get(url)
        teams = response.json().get("SiteKit", {}).get("Teamsbyseason", [])
        team_info = next((t for t in teams if t.get("code") == team_abbrev), None)
        if not team_info:
            return {}

        team_id = team_info.get("id")
        url = f"{base_url}?feed=modulekit&view=schedule&key=50c2cd9b5e18e390&fmt=json&client_code=ahl&lang=en&season_id=90&team_id={team_id}"
        response = await client.get(url)
        games = response.json().get("SiteKit", {}).get("Schedule", [])

    finished = [g for g in games if g.get("game_status") == "Final" or g.get("final") == "1"]
    home_matches, away_matches = [], []

    for game in finished:
        is_home = game.get("home_team") == team_id
        home_score = int(game.get("home_goal_count", 0) or 0)
        away_score = int(game.get("visiting_goal_count", 0) or 0)

        if is_home:
            team_score, opp_score = home_score, away_score
            opp_abbrev = game.get("visiting_team_code")
            opp_name = game.get("visiting_team_name")
        else:
            team_score, opp_score = away_score, home_score
            opp_abbrev = game.get("home_team_code")
            opp_name = game.get("home_team_name")

        try:
            game_date = datetime.strptime(game.get("date_played"), "%Y-%m-%d")
        except:
            continue

        result = GameResult(str(game.get("game_id")), game_date, AHL_TEAM_NAMES_RU.get(opp_abbrev, opp_name), opp_abbrev, is_home, team_score, opp_score, team_score + opp_score)
        if is_home:
            home_matches.append(result)
        else:
            away_matches.append(result)

    home_matches.sort(key=lambda x: x.date, reverse=True)
    away_matches.sort(key=lambda x: x.date, reverse=True)
    if last_n > 0:
        home_matches = home_matches[:last_n]
        away_matches = away_matches[:last_n]

    return {"team": {"abbrev": team_abbrev, "name": team_info.get("name"), "name_ru": AHL_TEAM_NAMES_RU.get(team_abbrev), "logo_url": team_info.get("team_logo_url")}, "stats": get_full_team_stats(home_matches, away_matches)}


async def get_liiga_team_stats(team_abbrev: str, last_n: int = 0):
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        response = await client.get("https://liiga.fi/api/v2/games?tournament=runkosarja&season=2026")
        response.raise_for_status()
        games = response.json()

    team_id, team_info = None, None
    for game in games:
        for team_data in [game.get("homeTeam", {}), game.get("awayTeam", {})]:
            tid = team_data.get("teamId", "")
            abbrev = tid.split(":")[-1].upper() if ":" in tid else tid
            if abbrev == team_abbrev:
                team_id = tid
                team_info = {"abbrev": abbrev, "name": team_data.get("teamName", ""), "name_ru": LIIGA_TEAM_NAMES_RU.get(abbrev), "logo_url": team_data.get("logos", {}).get("darkBg", "")}
                break
        if team_id:
            break

    if not team_id:
        return {}

    finished = [g for g in games if g.get("ended", False)]
    team_games = [g for g in finished if g.get("homeTeam", {}).get("teamId") == team_id or g.get("awayTeam", {}).get("teamId") == team_id]

    home_matches, away_matches = [], []
    for game in team_games:
        home_data, away_data = game.get("homeTeam", {}), game.get("awayTeam", {})
        is_home = home_data.get("teamId") == team_id
        home_score = home_data.get("goals", 0) or 0
        away_score = away_data.get("goals", 0) or 0

        if is_home:
            team_score, opp_score = home_score, away_score
            opp_id = away_data.get("teamId", "")
            opp_name = away_data.get("teamName", "")
        else:
            team_score, opp_score = away_score, home_score
            opp_id = home_data.get("teamId", "")
            opp_name = home_data.get("teamName", "")

        opp_abbrev = opp_id.split(":")[-1].upper() if ":" in opp_id else opp_id

        try:
            game_date = datetime.fromisoformat(game.get("start", "").replace("Z", "+00:00")).replace(tzinfo=None)
        except:
            continue

        result = GameResult(str(game.get("id")), game_date, LIIGA_TEAM_NAMES_RU.get(opp_abbrev, opp_name), opp_abbrev, is_home, team_score, opp_score, team_score + opp_score)
        if is_home:
            home_matches.append(result)
        else:
            away_matches.append(result)

    home_matches.sort(key=lambda x: x.date, reverse=True)
    away_matches.sort(key=lambda x: x.date, reverse=True)
    if last_n > 0:
        home_matches = home_matches[:last_n]
        away_matches = away_matches[:last_n]

    return {"team": team_info, "stats": get_full_team_stats(home_matches, away_matches)}


async def get_team_stats(league: str, team_abbrev: str, last_n: int = 0):
    if league == "NHL":
        return await get_nhl_team_stats(team_abbrev, last_n)
    elif league == "AHL":
        return await get_ahl_team_stats(team_abbrev, last_n)
    elif league == "LIIGA":
        return await get_liiga_team_stats(team_abbrev, last_n)
    return {}


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        match = re.search(r'/api/teams/([^/]+)/stats', self.path)
        if not match:
            self.send_response(400)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Invalid path"}).encode())
            return

        team_abbrev = match.group(1).upper()
        league = params.get("league", ["NHL"])[0].upper()
        last_n = int(params.get("last_n", ["0"])[0])

        try:
            stats = asyncio.run(get_team_stats(league, team_abbrev, last_n))
            if not stats:
                self.send_response(404)
                self.send_header("Content-type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Team not found"}).encode())
                return

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "s-maxage=600, stale-while-revalidate")
            self.end_headers()
            self.wfile.write(json.dumps(stats).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
