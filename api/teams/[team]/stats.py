"""GET /api/teams/[team]/stats - Get team statistics"""
from http.server import BaseHTTPRequestHandler
import json
import asyncio
import unicodedata
from urllib.parse import urlparse, parse_qs
import re
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass

# Kyiv timezone (UTC+2, or UTC+3 during DST)
KYIV_TZ = timezone(timedelta(hours=2))  # Winter time, DST handled manually if needed
from typing import List, Dict, Tuple
import math
import httpx


def normalize_abbrev(text: str) -> str:
    """Normalize abbreviation by removing diacritics (ä->A, ö->O, etc.)"""
    normalized = unicodedata.normalize('NFD', text)
    ascii_text = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
    return ascii_text.upper()

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

DEL_TEAM_NAMES_RU = {
    "MAN": "Адлер Мангейм", "AEV": "Аугсбургер Пантерз", "EBB": "Айсберен Берлин",
    "ING": "ЭРЦ Ингольштадт", "WOB": "Гриззлис Вольфсбург", "IEC": "Изерлон Рустерс",
    "KEC": "Кёльнер Хайе", "FRA": "Лёвен Франкфурт", "NIT": "Нюрнберг Айс Тайгерс",
    "BHV": "Пингвинс Бремерхафен", "RBM": "Ред Булл Мюнхен", "SWW": "Швеннингер Уайлд Уингс",
    "STR": "Штраубинг Тайгерс", "DRESDNER": "Дрезднер Айслёвен",
}

# DEL shortName to teamId mapping
DEL_TEAM_ABBREV_MAP = {
    "MAN": 338, "AEV": 348, "DRESDNER": 332, "EBB": 641, "ING": 345,
    "WOB": 5042, "IEC": 347, "KEC": 344, "FRA": 5283, "NIT": 5450,
    "BHV": 5041, "RBM": 2773, "SWW": 2781, "STR": 351,
}

# KHL Team Names (matching Flashscore Russian short names)
KHL_TEAM_NAMES_RU = {
    "Tractor Chelyabinsk": "Трактор",  # Flashscore uses short "Трактор"
    "Magnitogorsk": "Металлург",  # Flashscore uses short "Металлург"
    "Bars Kazan": "Ак Барс",  # Flashscore uses "Ак Барс"
    "Nizhny Novgorod": "Торпедо",  # Flashscore uses short "Торпедо"
    "SKA St. Petersburg": "СКА",  # Flashscore uses short "СКА"
    "CSKA Moscow": "ЦСКА",  # Flashscore uses short "ЦСКА"
    "Dynamo Moscow": "Динамо Москва",
    "Lokomotiv Yaroslavl": "Локомотив",  # Flashscore uses short "Локомотив"
    "Avangard Omsk": "Авангард",  # Flashscore uses short "Авангард"
    "Novosibirsk": "Сибирь",  # Flashscore uses short "Сибирь"
    "Yekaterinburg": "Автомобилист",  # Flashscore uses short "Автомобилист"
    "Vladivostok": "Адмирал",  # Flashscore uses short "Адмирал"
    "Khabarovsk": "Амур",  # Flashscore uses short "Амур"
    "Niznekamsk": "Нефтехимик",  # Flashscore uses short "Нефтехимик"
    "Severstal": "Северсталь",  # Flashscore uses short "Северсталь"
    "Dinamo Minsk": "Динамо Минск",
    "Barys Astana": "Барыс",  # Flashscore uses short "Барыс"
    "Kunlun Red Star": "Куньлунь Ред Стар",
    "Shanghai": "Шанхайские Драконы",  # Flashscore uses this name
    "Spartak Moscow": "Спартак Москва",
    "Vityaz": "Витязь",  # Flashscore uses short "Витязь"
    "Salavat Yulaev": "Салават Юлаев",  # Flashscore uses short version
    "Sochi": "Сочи",  # Direct match
    "Lada": "Лада",  # Direct match
}

# Czech Extraliga Team Names (mapping to Flashscore English API names)
# Key: our input name, Value: Flashscore API name (English)
CZECH_TEAM_NAMES_RU = {
    "Sparta Praha": "Sparta Prague",  # Flashscore uses "Sparta Prague"
    "Trinec": "Trinec",
    "Pardubice": "Pardubice",
    "Liberec": "Liberec",
    "Mlada Boleslav": "Mlada Boleslav",
    "Brno": "Kometa Brno",  # Flashscore uses "Kometa Brno"
    "Hradec Kralove": "Mountfield HK",  # Flashscore uses "Mountfield HK"
    "Plzen": "Plzen",
    "Litvinov": "Litvinov",
    "Ceske Budejovice": "Ceske Budejovice",
    "Olomouc": "Olomouc",
    "Vitkovice": "Vitkovice",
    "Kladno": "Kladno",
    "Karlovy Vary": "Karlovy Vary",
}

# Denmark Metal Ligaen Team Names (mapping to Flashscore English API names)
# Key: our input name, Value: Flashscore API name (English)
DENMARK_TEAM_NAMES_RU = {
    "Rungsted": "Rungsted",
    "Aalborg": "Aalborg",
    "Frederikshavn": "Frederikshavn",
    "Herning": "Herning Blue Fox",  # Flashscore uses "Herning Blue Fox"
    "Odense": "Odense Bulldogs",  # Flashscore uses "Odense Bulldogs"
    "Esbjerg": "Esbjerg",
    "SonderjyskE": "Sonderjyske Ishockey",  # Flashscore uses "Sonderjyske Ishockey"
    "Rodovre": "Rodovre Mighty Bulls",  # Flashscore uses "Rodovre Mighty Bulls"
    "Herlev": "Herlev",
}

# Austria ICE Hockey League Team Names
AUSTRIA_TEAM_NAMES_RU = {
    "Salzburg": "Ред Булл Зальцбург",
    "Vienna Capitals": "Вена Кэпиталз",
    "KAC": "КАЦ Клагенфурт",
    "Villach": "ВСВ Филлах",
    "Graz 99ers": "Грац 99ерс",
    "Innsbruck": "ХК Инсбрук",
    "Dornbirn": "Дорнбирн Бульдогс",
    "Linz": "Блэк Уингс Линц",
    "Fehervar AV19": "Фехервар АВ19",
    "Val Pusteria": "Пустерталь Вёльфе",
    "Znojmo": "Орли Знойимо",
    "Bratislava Capitals": "Братислава Кэпиталз",
    "Bolzano": "ХК Больцано",
    "Asiago": "Азиаго Хоккей",
    # ICE HL S3 API abbreviations
    "RBS": "Ред Булл Зальцбург",
    "VIC": "Вена Кэпиталз",
    "KAC": "КАЦ Клагенфурт",
    "VSV": "ВСВ Филлах",
    "G99": "Грац 99ерс",
    "HCI": "ХК Инсбрук",
    "DEC": "Дорнбирн Бульдогс",
    "BWL": "Блэк Уингс Линц",
    "AVS": "Фехервар АВ19",
    "PUS": "Пустерталь Вёльфе",
    "ZNO": "Орли Знойимо",
    "BRC": "Братислава Кэпиталз",
    "HCB": "ХК Больцано",
    "ASH": "Азиаго Хоккей",
    "TWK": "ТВК Инсбрук",
}

# Swiss National League Team Names
SWISS_TEAM_NAMES_RU = {
    "ZSC": "Цюрих Лайонс",
    "SCB": "СК Берн",
    "EVZ": "ЭВ Цуг",
    "HCL": "ХК Лугано",
    "FRI": "Фрибур-Готтерон",
    "LAU": "Лозанна",
    "LHC": "Лозанна ХК",
    "KLO": "ЭХК Клотен",
    "SCRJ": "Раппершвиль-Йона Лейкерс",
    "GEN": "Женева-Сервет",
    "GSH": "Женева-Сервет",
    "BIE": "ЭХК Биль",
    "EHCB": "ЭХК Биль",
    "DAV": "ХК Давос",
    "HCD": "ХК Давос",
    "AMB": "ХК Амбри-Пиотта",
    "HCA": "ХК Амбри-Пиотта",
    "SCL": "СЦЛ Тигерс",
    "LAN": "СЦЛ Тигерс",
    "AJO": "ХК Ажуа",
}

# Known Swiss National League teams (for filtering)
NL_TEAMS = {
    "ZSC Lions", "SC Bern", "EV Zug", "HC Lugano",
    "Fribourg-Gottéron", "Lausanne HC", "EHC Kloten",
    "SC Rapperswil-Jona Lakers", "Genève-Servette HC",
    "EHC Biel-Bienne", "HC Davos", "HC Ambri-Piotta",
    "SCL Tigers", "HC Ajoie"
}

# Flashscore API configuration
FLASHSCORE_BASE_URL = "https://2.flashscore.ninja/2/x/feed"
FLASHSCORE_HEADERS = {"x-fsign": "SW9D1eZo"}


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
        "home": {"total_matches": len(home_matches), "individual_totals": {}, "individual_conceded": {}, "match_totals": {}},
        "away": {"total_matches": len(away_matches), "individual_totals": {}, "individual_conceded": {}, "match_totals": {}}
    }

    # Individual totals (goals scored by team)
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

    # Individual conceded (goals conceded by team)
    for threshold in [2, 3, 4, 5, 6]:
        for location, matches in [("home", home_matches), ("away", away_matches)]:
            condition = lambda m, t=threshold: m.opponent_score >= t
            matching = [m for m in matches if condition(m)]
            simple_pct, weighted_pct = calculate_weighted_percentage(matches, condition)
            stats[location]["individual_conceded"][f"{threshold}+"] = {
                "count": len(matching),
                "percentage": simple_pct,
                "weighted_percentage": weighted_pct,
                "matches": [{"date": m.date.strftime("%d.%m.%Y"), "opponent": m.opponent, "opponent_abbrev": m.opponent_abbrev, "score": f"{m.team_score}:{m.opponent_score}"} for m in matching]
            }

    # Match totals
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
        response = await client.get(f"https://api-web.nhle.com/v1/club-schedule-season/{team_abbrev}/20252026")
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
            raw_abbrev = tid.split(":")[-1] if ":" in tid else tid
            abbrev = normalize_abbrev(raw_abbrev)
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

        raw_opp = opp_id.split(":")[-1] if ":" in opp_id else opp_id
        opp_abbrev = normalize_abbrev(raw_opp)

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


async def get_del_team_stats(team_abbrev: str, last_n: int = 0):
    """Get DEL team stats from OpenLigaDB"""
    team_id = DEL_TEAM_ABBREV_MAP.get(team_abbrev.upper())
    if not team_id:
        return {}

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get("https://api.openligadb.de/getmatchdata/del/2025")
        response.raise_for_status()
        all_games = response.json()

    # Filter finished games for this team
    finished = [g for g in all_games if g.get("matchIsFinished", False)]
    team_games = [g for g in finished if g.get("team1", {}).get("teamId") == team_id or g.get("team2", {}).get("teamId") == team_id]

    home_matches, away_matches = [], []
    team_info = None

    for game in team_games:
        team1 = game.get("team1", {})
        team2 = game.get("team2", {})
        is_home = team1.get("teamId") == team_id

        # Get final score from matchResults
        results = game.get("matchResults", [])
        final_result = next((r for r in results if r.get("resultTypeID") == 2), None)
        if not final_result:
            continue

        home_score = final_result.get("pointsTeam1", 0)
        away_score = final_result.get("pointsTeam2", 0)

        if is_home:
            team_score, opp_score = home_score, away_score
            opp_abbrev = team2.get("shortName", "")
            opp_name = team2.get("teamName", "")
            if not team_info:
                team_info = {
                    "abbrev": team1.get("shortName", team_abbrev),
                    "name": team1.get("teamName", ""),
                    "name_ru": DEL_TEAM_NAMES_RU.get(team_abbrev.upper()),
                    "logo_url": team1.get("teamIconUrl", "")
                }
        else:
            team_score, opp_score = away_score, home_score
            opp_abbrev = team1.get("shortName", "")
            opp_name = team1.get("teamName", "")
            if not team_info:
                team_info = {
                    "abbrev": team2.get("shortName", team_abbrev),
                    "name": team2.get("teamName", ""),
                    "name_ru": DEL_TEAM_NAMES_RU.get(team_abbrev.upper()),
                    "logo_url": team2.get("teamIconUrl", "")
                }

        try:
            game_date = datetime.fromisoformat(game.get("matchDateTimeUTC", "").replace("Z", "+00:00")).replace(tzinfo=None)
        except:
            continue

        result = GameResult(
            str(game.get("matchID")),
            game_date,
            DEL_TEAM_NAMES_RU.get(opp_abbrev.upper(), opp_name),
            opp_abbrev,
            is_home,
            team_score,
            opp_score,
            team_score + opp_score
        )
        if is_home:
            home_matches.append(result)
        else:
            away_matches.append(result)

    home_matches.sort(key=lambda x: x.date, reverse=True)
    away_matches.sort(key=lambda x: x.date, reverse=True)
    if last_n > 0:
        home_matches = home_matches[:last_n]
        away_matches = away_matches[:last_n]

    if not team_info:
        team_info = {"abbrev": team_abbrev, "name": team_abbrev, "name_ru": DEL_TEAM_NAMES_RU.get(team_abbrev.upper()), "logo_url": None}

    return {"team": team_info, "stats": get_full_team_stats(home_matches, away_matches)}


async def fetch_flashscore_day(client, day_offset: int, target_league: str) -> list:
    """Fetch one day of Flashscore results using same parsing as parse_flashscore_data."""
    try:
        url = f"{FLASHSCORE_BASE_URL}/f_4_{day_offset}_3_en_5"
        response = await client.get(url, headers=FLASHSCORE_HEADERS)
        data = response.text

        if not data or data.strip() in ('0', ''):
            return []

        items = data.split('¬')

        # Group items into dicts like parse_flashscore_data does
        data_list = [{}]
        for item in items:
            if '÷' not in item:
                continue
            parts = item.split('÷')
            key = parts[0]
            value = parts[-1] if len(parts) > 1 else ''

            if '~' in key:
                data_list.append({key: value})
            else:
                data_list[-1].update({key: value})

        matches = []
        league_name = ''

        for game in data_list:
            keys = list(game.keys())
            if not keys:
                continue

            # Check for league header
            if '~ZA' in keys[0]:
                league_name = game.get('~ZA', '')

            # Check for match entry
            if 'AA' in keys[0]:
                # Filter by target league
                if target_league.lower() not in league_name.lower():
                    continue

                matches.append({
                    'id': game.get('~AA', ''),
                    'home': game.get('AE', ''),
                    'away': game.get('AF', ''),
                    'home_score': game.get('AG', ''),
                    'away_score': game.get('AH', ''),
                    'status': game.get('AB', ''),
                    'timestamp': game.get('AD', '')
                })

        return matches
    except Exception:
        return []


def is_nl_team(team_name: str) -> bool:
    """Check if team is in Swiss National League"""
    if not team_name:
        return False
    if team_name in NL_TEAMS:
        return True
    name_lower = team_name.lower()
    for nl_team in NL_TEAMS:
        if nl_team.lower() in name_lower or name_lower in nl_team.lower():
            return True
    return False


async def get_flashscore_team_stats(team_name: str, league: str, last_n: int = 0):
    """Get team stats from Flashscore API for Austria and Swiss leagues."""

    # League configuration
    league_config = {
        "AUSTRIA": ("AUSTRIA: ICE Hockey League", AUSTRIA_TEAM_NAMES_RU),
        "SWISS": ("SWITZERLAND: National League", SWISS_TEAM_NAMES_RU),
    }

    league_upper = league.upper()
    if league_upper not in league_config:
        return {}

    target_league, names_ru = league_config[league_upper]
    team_name_lower = team_name.lower()

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Fetch past 60 days of results in parallel batches
        all_matches = []
        batch_size = 10  # Fetch 10 days at a time to avoid overwhelming the API
        for batch_start in range(-60, 1, batch_size):
            batch_end = min(batch_start + batch_size, 1)
            tasks = [fetch_flashscore_day(client, day_offset, target_league)
                     for day_offset in range(batch_start, batch_end)]
            results = await asyncio.gather(*tasks)
            for matches in results:
                all_matches.extend(matches)

    # Find team and collect matches
    team_info = None
    home_matches = []
    away_matches = []

    for match in all_matches:
        home = match.get('home', '')
        away = match.get('away', '')
        home_score_str = match.get('home_score', '')
        away_score_str = match.get('away_score', '')
        timestamp = match.get('timestamp', '')
        status = match.get('status', '')

        # Only finished matches (status 3 = finished)
        if status != '3':
            continue

        # Check if team is in this match
        is_home = team_name_lower in home.lower() or home.lower() in team_name_lower
        is_away = team_name_lower in away.lower() or away.lower() in team_name_lower

        if not is_home and not is_away:
            continue

        # Set team info if not set
        if not team_info:
            matched_name = home if is_home else away
            team_info = {
                "abbrev": matched_name[:3].upper(),
                "name": matched_name,
                "name_ru": names_ru.get(matched_name, matched_name),
                "logo_url": None
            }

        # Parse scores
        try:
            home_score = int(home_score_str) if home_score_str else 0
            away_score = int(away_score_str) if away_score_str else 0
            game_date = datetime.fromtimestamp(int(timestamp)) if timestamp else datetime.now()
        except:
            continue

        if is_home:
            opp_name = away
            result = GameResult(
                match.get('id', ''),
                game_date,
                names_ru.get(opp_name, opp_name),
                opp_name[:3].upper(),
                True,
                home_score,
                away_score,
                home_score + away_score
            )
            home_matches.append(result)
        else:
            opp_name = home
            result = GameResult(
                match.get('id', ''),
                game_date,
                names_ru.get(opp_name, opp_name),
                opp_name[:3].upper(),
                False,
                away_score,
                home_score,
                home_score + away_score
            )
            away_matches.append(result)

    if not team_info:
        return {}

    home_matches.sort(key=lambda x: x.date, reverse=True)
    away_matches.sort(key=lambda x: x.date, reverse=True)

    if last_n > 0:
        home_matches = home_matches[:last_n]
        away_matches = away_matches[:last_n]

    return {"team": team_info, "stats": get_full_team_stats(home_matches, away_matches)}




def get_db_team_stats(team_name: str, league: str, last_n: int = 0):
    """Get team stats from database (synced from API-Sports).

    Reads from pre-synced database for KHL, Czech Extraliga, Denmark Metal Ligaen.
    Data is synced daily via cron job at 10:00 UTC.
    """
    import sys
    import os

    # Add backend to path for database models
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend'))

    from app.models.database import SessionLocal, Team, Game

    # Team name mappings for Russian names
    team_names_ru = {
        "KHL": KHL_TEAM_NAMES_RU,
        "CZECH": CZECH_TEAM_NAMES_RU,
        "DENMARK": DENMARK_TEAM_NAMES_RU,
    }

    league_upper = league.upper()
    if league_upper not in team_names_ru:
        return {}

    names_ru = team_names_ru.get(league_upper, {})

    db = SessionLocal()
    try:
        # Find team by name (case-insensitive partial match)
        team_name_lower = team_name.lower()
        teams = db.query(Team).filter(Team.league == league_upper).all()

        team = None
        for t in teams:
            # Match by name, abbrev, or name_ru
            if (team_name_lower in (t.name or "").lower() or
                (t.name or "").lower() in team_name_lower or
                team_name_lower == (t.abbrev or "").lower() or
                team_name_lower in (t.name_ru or "").lower()):
                team = t
                break

        if not team:
            return {}

        # Get home matches
        home_games = db.query(Game).filter(
            Game.league == league_upper,
            Game.home_team_id == team.id,
            Game.is_finished == True
        ).order_by(Game.date.desc())

        if last_n > 0:
            home_games = home_games.limit(last_n)
        home_games = home_games.all()

        # Get away matches
        away_games = db.query(Game).filter(
            Game.league == league_upper,
            Game.away_team_id == team.id,
            Game.is_finished == True
        ).order_by(Game.date.desc())

        if last_n > 0:
            away_games = away_games.limit(last_n)
        away_games = away_games.all()

        # Convert to GameResult format
        home_matches = []
        for game in home_games:
            opponent = game.away_team
            home_matches.append(GameResult(
                game.game_id,
                game.date,
                opponent.name_ru or opponent.name if opponent else "Unknown",
                opponent.abbrev if opponent else "UNK",
                True,
                game.home_score or 0,
                game.away_score or 0,
                (game.home_score or 0) + (game.away_score or 0)
            ))

        away_matches = []
        for game in away_games:
            opponent = game.home_team
            away_matches.append(GameResult(
                game.game_id,
                game.date,
                opponent.name_ru or opponent.name if opponent else "Unknown",
                opponent.abbrev if opponent else "UNK",
                False,
                game.away_score or 0,
                game.home_score or 0,
                (game.home_score or 0) + (game.away_score or 0)
            ))

        team_info = {
            "abbrev": team.abbrev,
            "name": team.name,
            "name_ru": team.name_ru or names_ru.get(team.name, team.name),
            "logo_url": team.logo_url
        }

        return {"team": team_info, "stats": get_full_team_stats(home_matches, away_matches)}

    except Exception as e:
        print(f"Database error: {e}")
        return {}
    finally:
        db.close()


async def get_team_stats(league: str, team_abbrev: str, last_n: int = 0):
    if league == "NHL":
        return await get_nhl_team_stats(team_abbrev, last_n)
    elif league == "AHL":
        return await get_ahl_team_stats(team_abbrev, last_n)
    elif league == "LIIGA":
        return await get_liiga_team_stats(team_abbrev, last_n)
    elif league == "DEL":
        return await get_del_team_stats(team_abbrev, last_n)
    elif league.upper() in ("AUSTRIA", "SWISS"):
        return await get_flashscore_team_stats(team_abbrev, league.upper(), last_n)
    elif league.upper() in ("KHL", "CZECH", "DENMARK"):
        return get_db_team_stats(team_abbrev, league, last_n)
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

        from urllib.parse import unquote
        team_abbrev = unquote(match.group(1))  # URL decode team name
        league = params.get("league", ["NHL"])[0].upper()
        last_n = int(params.get("last_n", ["0"])[0])

        # Uppercase only for leagues with standardized abbrevs
        if league not in ("KHL", "CZECH", "DENMARK", "AUSTRIA", "SWISS"):
            team_abbrev = team_abbrev.upper()

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
