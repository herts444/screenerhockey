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

AUSTRIA_TEAM_NAMES_RU = {
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


async def get_austria_teams():
    """Get Austria ICE HL teams from S3 API"""
    base_url = "https://s3.dualstack.eu-west-1.amazonaws.com/icehl.hokejovyzapis.cz"
    season = "2025"
    league_id = "1"

    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
        url = f"{base_url}/data/export/season/{season}/league/{league_id}/schedule_export.json"
        response = await client.get(url)
        response.raise_for_status()
        all_matches = response.json()

    teams = {}
    for match in all_matches:
        for team_key in ["home", "guest"]:
            team = match.get(team_key, {})
            team_id = str(team.get("id", ""))
            abbrev = team.get("abbr", "")
            if team_id and team_id not in teams:
                teams[team_id] = {
                    "abbrev": abbrev,
                    "name": team.get("name", ""),
                    "name_ru": AUSTRIA_TEAM_NAMES_RU.get(abbrev, team.get("name", "")),
                    "logo_url": team.get("logo", "")
                }

    return list(teams.values())


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


async def get_swiss_teams():
    """Get Swiss National League teams from SIHF API"""
    base_url = "https://data.sihf.ch/Statistic/api/cms"
    league_id = "1"

    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
        # Get first page to collect teams
        url = f"{base_url}/cache600?alias=results&searchQuery={league_id}//&page=1"
        response = await client.get(url)
        response.raise_for_status()
        data = response.json()
        total_pages = data.get("pages", 1)

        teams = {}
        for page in range(1, total_pages + 1):
            if page > 1:
                url = f"{base_url}/cache600?alias=results&searchQuery={league_id}//&page={page}"
                response = await client.get(url)
                data = response.json()

            rows = data.get("data", [])
            for row in rows:
                if not isinstance(row, list) or len(row) < 5:
                    continue

                try:
                    home_team = row[3] if isinstance(row[3], dict) else {}
                    away_team = row[4] if isinstance(row[4], dict) else {}

                    for team in [home_team, away_team]:
                        team_id = str(team.get("id", ""))
                        team_name = team.get("name", "")
                        abbrev = team.get("acronym", "")

                        if team_id and team_id not in teams and is_nl_team(team_name):
                            teams[team_id] = {
                                "abbrev": abbrev,
                                "name": team_name,
                                "name_ru": SWISS_TEAM_NAMES_RU.get(abbrev, team_name),
                                "logo_url": None
                            }
                except:
                    continue

    return list(teams.values())


async def get_teams(league: str):
    if league == "NHL":
        return await get_nhl_teams()
    elif league == "AHL":
        return await get_ahl_teams()
    elif league == "LIIGA":
        return await get_liiga_teams()
    elif league == "DEL":
        return await get_del_teams()
    elif league == "AUSTRIA":
        return await get_austria_teams()
    elif league == "SWISS":
        return await get_swiss_teams()
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
