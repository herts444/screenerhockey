"""GET /api/teams - Get all teams for a league"""
from http.server import BaseHTTPRequestHandler
import json
import asyncio
from urllib.parse import urlparse, parse_qs
import httpx

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
    "STR": "Штраубинг Тайгерс", "Dresdner": "Дрезднер Айслёвен",
}


async def get_nhl_teams():
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get("https://api-web.nhle.com/v1/standings/now")
        response.raise_for_status()
        standings = response.json()

    teams = []
    for team_data in standings.get("standings", []):
        abbrev = team_data.get("teamAbbrev", {}).get("default")
        teams.append({
            "abbrev": abbrev,
            "name": team_data.get("teamName", {}).get("default"),
            "name_ru": TEAM_NAMES_RU.get(abbrev),
            "logo_url": team_data.get("teamLogo")
        })
    return teams


async def get_ahl_teams():
    async with httpx.AsyncClient(timeout=30.0) as client:
        url = "https://lscluster.hockeytech.com/feed/index.php?feed=modulekit&view=teamsbyseason&key=50c2cd9b5e18e390&fmt=json&client_code=ahl&lang=en&season_id=90"
        response = await client.get(url)
        response.raise_for_status()
        data = response.json()

    teams = []
    for team in data.get("SiteKit", {}).get("Teamsbyseason", []):
        abbrev = team.get("code")
        teams.append({
            "abbrev": abbrev,
            "name": team.get("name"),
            "name_ru": AHL_TEAM_NAMES_RU.get(abbrev),
            "logo_url": team.get("team_logo_url") or f"https://assets.leaguestat.com/ahl/logos/{team.get('id')}.png"
        })
    return teams


async def get_liiga_teams():
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        response = await client.get("https://liiga.fi/api/v2/games?tournament=runkosarja&season=2026")
        response.raise_for_status()
        games = response.json()

    teams = {}
    for game in games:
        for team_data in [game.get("homeTeam", {}), game.get("awayTeam", {})]:
            team_id = team_data.get("teamId", "")
            if team_id and team_id not in teams:
                abbrev = team_id.split(":")[-1].upper() if ":" in team_id else team_id
                teams[team_id] = {
                    "abbrev": abbrev,
                    "name": team_data.get("teamName", ""),
                    "name_ru": LIIGA_TEAM_NAMES_RU.get(abbrev),
                    "logo_url": team_data.get("logos", {}).get("darkBg", "")
                }
    return list(teams.values())


async def get_del_teams():
    """Get DEL teams from OpenLigaDB"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get("https://api.openligadb.de/getavailableteams/del/2025")
        response.raise_for_status()
        teams_data = response.json()

    teams = []
    for team in teams_data:
        abbrev = team.get("shortName", "")
        teams.append({
            "abbrev": abbrev,
            "name": team.get("teamName", ""),
            "name_ru": DEL_TEAM_NAMES_RU.get(abbrev, team.get("teamName", "")),
            "logo_url": team.get("teamIconUrl", "")
        })
    return teams


async def get_teams(league: str):
    if league == "NHL":
        return await get_nhl_teams()
    elif league == "AHL":
        return await get_ahl_teams()
    elif league == "LIIGA":
        return await get_liiga_teams()
    elif league == "DEL":
        return await get_del_teams()
    return []


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        league = params.get("league", ["NHL"])[0].upper()

        try:
            teams = asyncio.run(get_teams(league))
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "s-maxage=3600, stale-while-revalidate")
            self.end_headers()
            self.wfile.write(json.dumps(teams).encode())
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
