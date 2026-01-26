"""GET /api/schedule/upcoming - Get upcoming games"""
from http.server import BaseHTTPRequestHandler
import json
import asyncio
import unicodedata
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta, timezone
import httpx


def normalize_abbrev(text: str) -> str:
    """Normalize abbreviation by removing diacritics (ä->A, ö->O, etc.)"""
    normalized = unicodedata.normalize('NFD', text)
    ascii_text = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
    return ascii_text.upper()

# Kyiv timezone (UTC+2, or UTC+3 during DST - using +2 for winter)
KYIV_TZ = timezone(timedelta(hours=2))


def to_kyiv_time(dt):
    """Convert datetime to Kyiv timezone"""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(KYIV_TZ)


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
    "STR": "Штраубинг Тайгерс", "Dresdner": "Дрезднер Айслёвен",
}

# DEL team ID to shortName mapping (from OpenLigaDB)
DEL_TEAM_ID_MAP = {
    338: "MAN", 348: "AEV", 332: "Dresdner", 641: "EBB", 345: "ING",
    5042: "WOB", 347: "IEC", 344: "KEC", 5283: "FRA", 5450: "NIT",
    5041: "BHV", 2773: "RBM", 2781: "SWW", 351: "STR",
}

# KHL Team Names
KHL_TEAM_NAMES_RU = {
    "Tractor Chelyabinsk": "Трактор Челябинск",
    "Magnitogorsk": "Металлург Магнитогорск",
    "Bars Kazan": "Ак Барс Казань",
    "Nizhny Novgorod": "Торпедо Нижний Новгород",
    "SKA St. Petersburg": "СКА Санкт-Петербург",
    "CSKA Moscow": "ЦСКА Москва",
    "Dynamo Moscow": "Динамо Москва",
    "Lokomotiv Yaroslavl": "Локомотив Ярославль",
    "Avangard Omsk": "Авангард Омск",
    "Novosibirsk": "Сибирь Новосибирск",
    "Yekaterinburg": "Автомобилист Екатеринбург",
    "Vladivostok": "Адмирал Владивосток",
    "Khabarovsk": "Амур Хабаровск",
    "Niznekamsk": "Нефтехимик Нижнекамск",
    "Severstal": "Северсталь Череповец",
    "Dinamo Minsk": "Динамо Минск",
    "Barys Astana": "Барыс Астана",
    "Kunlun Red Star": "Куньлунь Ред Стар",
    "Shanghai": "Куньлунь Шанхай",
    "Spartak Moscow": "Спартак Москва",
    "Vityaz": "Витязь Подольск",
    "Salavat Yulaev": "Салават Юлаев Уфа",
}

# Czech Extraliga Team Names
CZECH_TEAM_NAMES_RU = {
    "Sparta Praha": "Спарта Прага",
    "Trinec": "Оцеларжи Тршинец",
    "Pardubice": "Пардубице",
    "Liberec": "Били Тигржи Либерец",
    "Mlada Boleslav": "Млада Болеслав",
    "Brno": "Комета Брно",
    "Hradec Kralove": "Градец Кралове",
    "Plzen": "Шкода Пльзень",
    "Litvinov": "Литвинов",
    "Ceske Budejovice": "Мотор Ческе-Будеёвице",
    "Olomouc": "Оломоуц",
    "Vítkovice": "Витковице Ридера",
    "Kladno": "Рытиржи Кладно",
    "Karlovy Vary": "Энергие Карловы Вары",
}

# Denmark Metal Ligaen Team Names
DENMARK_TEAM_NAMES_RU = {
    "Rungsted": "Рунгстед Сеир Капитал",
    "Aalborg": "Ольборг Пайретс",
    "Frederikshavn": "Фредериксхавн Уайт Хокс",
    "Herning": "Хернинг Блю Фокс",
    "Odense": "Оденсе Бульдогс",
    "Esbjerg": "Эсбьерг Энерджи",
    "SonderjyskE": "Сённерйюске",
    "Rodovre": "Рёдовре Майти Буллз",
    "Gentofte": "Гентофте Старс",
    "Hvidovre": "Хвидовре Файтерс",
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


async def get_nhl_schedule(days: int):
    games = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        for i in range(days):
            # Use Kyiv timezone for date calculation
            date = (datetime.now(KYIV_TZ) + timedelta(days=i)).strftime("%Y-%m-%d")
            try:
                response = await client.get(f"https://api-web.nhle.com/v1/schedule/{date}")
                response.raise_for_status()
                schedule = response.json()

                for day in schedule.get("gameWeek", []):
                    if day.get("date") == date:
                        for game in day.get("games", []):
                            game_date_str = game.get("startTimeUTC", "")
                            try:
                                game_date_utc = datetime.fromisoformat(game_date_str.replace("Z", "+00:00"))
                                game_date = to_kyiv_time(game_date_utc)
                            except:
                                game_date = None

                            home = game.get("homeTeam", {})
                            away = game.get("awayTeam", {})
                            home_abbrev = home.get("abbrev")
                            away_abbrev = away.get("abbrev")

                            games.append({
                                "game_id": game.get("id"),
                                "date": game_date.strftime("%d.%m.%Y %H:%M") if game_date else "",
                                "date_iso": game_date.isoformat() if game_date else "",
                                "home_team": {
                                    "abbrev": home_abbrev,
                                    "name": home.get("placeName", {}).get("default", home_abbrev),
                                    "name_ru": TEAM_NAMES_RU.get(home_abbrev, home_abbrev),
                                    "logo_url": home.get("logo")
                                },
                                "away_team": {
                                    "abbrev": away_abbrev,
                                    "name": away.get("placeName", {}).get("default", away_abbrev),
                                    "name_ru": TEAM_NAMES_RU.get(away_abbrev, away_abbrev),
                                    "logo_url": away.get("logo")
                                },
                                "venue": game.get("venue", {}).get("default", "")
                            })
            except Exception as e:
                print(f"Error fetching NHL schedule for {date}: {e}")
    return games


async def get_ahl_schedule(days: int):
    games = []
    seen_ids = set()
    base_url = "https://lscluster.hockeytech.com/feed/index.php"

    async with httpx.AsyncClient(timeout=30.0) as client:
        for i in range(days):
            # Use Kyiv timezone for date calculation
            date = (datetime.now(KYIV_TZ) + timedelta(days=i)).strftime("%Y-%m-%d")
            try:
                url = f"{base_url}?feed=modulekit&view=schedule&key=50c2cd9b5e18e390&fmt=json&client_code=ahl&lang=en&season_id=90&date={date}"
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()

                for game in data.get("SiteKit", {}).get("Schedule", []):
                    game_id = game.get("game_id")
                    if game_id in seen_ids or game.get("date_played") != date:
                        continue
                    if game.get("game_status") == "Final":
                        continue

                    seen_ids.add(game_id)
                    game_date_str = game.get("GameDateISO8601", "")
                    try:
                        game_date_utc = datetime.fromisoformat(game_date_str.replace("Z", "+00:00"))
                        game_date = to_kyiv_time(game_date_utc)
                    except:
                        game_date = None

                    home_abbrev = game.get("home_team_code")
                    away_abbrev = game.get("visiting_team_code")

                    games.append({
                        "game_id": f"ahl_{game_id}",
                        "date": game_date.strftime("%d.%m.%Y %H:%M") if game_date else "",
                        "date_iso": game_date.isoformat() if game_date else "",
                        "home_team": {
                            "abbrev": home_abbrev,
                            "name": game.get("home_team_name", home_abbrev),
                            "name_ru": AHL_TEAM_NAMES_RU.get(home_abbrev, game.get("home_team_name")),
                            "logo_url": f"https://assets.leaguestat.com/ahl/logos/{game.get('home_team')}.png"
                        },
                        "away_team": {
                            "abbrev": away_abbrev,
                            "name": game.get("visiting_team_name", away_abbrev),
                            "name_ru": AHL_TEAM_NAMES_RU.get(away_abbrev, game.get("visiting_team_name")),
                            "logo_url": f"https://assets.leaguestat.com/ahl/logos/{game.get('visiting_team')}.png"
                        },
                        "venue": game.get("venue_name", "")
                    })
            except Exception as e:
                print(f"Error fetching AHL schedule for {date}: {e}")
    return games


async def get_liiga_schedule(days: int):
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        response = await client.get("https://liiga.fi/api/v2/games?tournament=runkosarja&season=2026")
        response.raise_for_status()
        all_games = response.json()

    # Use Kyiv time for date calculations
    now_kyiv = datetime.now(KYIV_TZ)
    start = datetime(now_kyiv.year, now_kyiv.month, now_kyiv.day, tzinfo=KYIV_TZ)
    end = start + timedelta(days=days + 1)

    result = []
    seen_ids = set()

    for game in all_games:
        game_id = game.get("id")
        if game_id in seen_ids or game.get("ended", False):
            continue

        game_start = game.get("start", "")
        if not game_start:
            continue

        try:
            game_date_utc = datetime.fromisoformat(game_start.replace("Z", "+00:00"))
            game_date = to_kyiv_time(game_date_utc)
            if not (start <= game_date < end):
                continue
        except:
            continue

        seen_ids.add(game_id)

        home_data = game.get("homeTeam", {})
        away_data = game.get("awayTeam", {})
        home_id = home_data.get("teamId", "")
        away_id = away_data.get("teamId", "")
        raw_home = home_id.split(":")[-1] if ":" in home_id else home_id
        raw_away = away_id.split(":")[-1] if ":" in away_id else away_id
        home_abbrev = normalize_abbrev(raw_home)
        away_abbrev = normalize_abbrev(raw_away)

        result.append({
            "game_id": f"liiga_{game_id}",
            "date": game_date.strftime("%d.%m.%Y %H:%M"),
            "date_iso": game_date.isoformat(),
            "home_team": {
                "abbrev": home_abbrev,
                "name": home_data.get("teamName", home_abbrev),
                "name_ru": LIIGA_TEAM_NAMES_RU.get(home_abbrev),
                "logo_url": home_data.get("logos", {}).get("darkBg", "")
            },
            "away_team": {
                "abbrev": away_abbrev,
                "name": away_data.get("teamName", away_abbrev),
                "name_ru": LIIGA_TEAM_NAMES_RU.get(away_abbrev),
                "logo_url": away_data.get("logos", {}).get("darkBg", "")
            },
            "venue": game.get("iceRink", {}).get("name", "")
        })

    return sorted(result, key=lambda g: g.get("date_iso", ""))


async def get_del_schedule(days: int):
    """Get DEL (German) schedule from OpenLigaDB"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get("https://api.openligadb.de/getmatchdata/del/2025")
        response.raise_for_status()
        all_games = response.json()

    # Use Kyiv time for date calculations
    now_kyiv = datetime.now(KYIV_TZ)
    start = datetime(now_kyiv.year, now_kyiv.month, now_kyiv.day, tzinfo=KYIV_TZ)
    end = start + timedelta(days=days + 1)

    result = []
    seen_ids = set()

    for game in all_games:
        game_id = game.get("matchID")
        if game_id in seen_ids or game.get("matchIsFinished", False):
            continue

        match_time_utc = game.get("matchDateTimeUTC", "")
        if not match_time_utc:
            continue

        try:
            game_date_utc = datetime.fromisoformat(match_time_utc.replace("Z", "+00:00"))
            game_date = to_kyiv_time(game_date_utc)
            if not (start <= game_date < end):
                continue
        except:
            continue

        seen_ids.add(game_id)

        team1 = game.get("team1", {})
        team2 = game.get("team2", {})
        home_abbrev = team1.get("shortName", "")
        away_abbrev = team2.get("shortName", "")

        result.append({
            "game_id": f"del_{game_id}",
            "date": game_date.strftime("%d.%m.%Y %H:%M"),
            "date_iso": game_date.isoformat(),
            "home_team": {
                "abbrev": home_abbrev,
                "name": team1.get("teamName", home_abbrev),
                "name_ru": DEL_TEAM_NAMES_RU.get(home_abbrev, team1.get("teamName", home_abbrev)),
                "logo_url": team1.get("teamIconUrl", "")
            },
            "away_team": {
                "abbrev": away_abbrev,
                "name": team2.get("teamName", away_abbrev),
                "name_ru": DEL_TEAM_NAMES_RU.get(away_abbrev, team2.get("teamName", away_abbrev)),
                "logo_url": team2.get("teamIconUrl", "")
            },
            "venue": game.get("location", {}).get("locationCity", "") if game.get("location") else ""
        })

    return sorted(result, key=lambda g: g.get("date_iso", ""))


FLASHSCORE_LOGO_BASE = "https://static.flashscore.com/res/image/data/"


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


async def get_austria_schedule(days: int):
    """Get Austria ICE HL schedule from S3 API"""
    base_url = "https://s3.dualstack.eu-west-1.amazonaws.com/icehl.hokejovyzapis.cz"
    season = "2025"
    league_id = "1"

    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
        url = f"{base_url}/data/export/season/{season}/league/{league_id}/schedule_export.json"
        response = await client.get(url)
        response.raise_for_status()
        all_matches = response.json()

    # Use Kyiv time for date calculations
    now_kyiv = datetime.now(KYIV_TZ)
    start = datetime(now_kyiv.year, now_kyiv.month, now_kyiv.day, tzinfo=KYIV_TZ)
    end = start + timedelta(days=days + 1)

    result = []
    seen_ids = set()

    for match in all_matches:
        match_id = match.get("id")
        if match_id in seen_ids:
            continue

        # Skip finished matches
        if match.get("status") == "AFTER_MATCH":
            continue

        game_date_str = match.get("start_date", "")
        if not game_date_str:
            continue

        try:
            # Format: "2025-09-12 19:15:00"
            game_date = datetime.strptime(game_date_str, "%Y-%m-%d %H:%M:%S")
            game_date = game_date.replace(tzinfo=KYIV_TZ)
            if not (start <= game_date < end):
                continue
        except:
            continue

        seen_ids.add(match_id)

        home = match.get("home", {})
        away = match.get("guest", {})
        home_abbrev = home.get("abbr", "")
        away_abbrev = away.get("abbr", "")

        result.append({
            "game_id": f"austria_{match_id}",
            "date": game_date.strftime("%d.%m.%Y %H:%M"),
            "date_iso": game_date.isoformat(),
            "home_team": {
                "abbrev": home_abbrev,
                "name": home.get("name", home_abbrev),
                "name_ru": AUSTRIA_TEAM_NAMES_RU.get(home_abbrev, home.get("name", home_abbrev)),
                "logo_url": home.get("logo", "")
            },
            "away_team": {
                "abbrev": away_abbrev,
                "name": away.get("name", away_abbrev),
                "name_ru": AUSTRIA_TEAM_NAMES_RU.get(away_abbrev, away.get("name", away_abbrev)),
                "logo_url": away.get("logo", "")
            },
            "venue": ""
        })

    return sorted(result, key=lambda g: g.get("date_iso", ""))


async def get_swiss_schedule(days: int):
    """Get Swiss National League schedule from SIHF API"""
    base_url = "https://data.sihf.ch/Statistic/api/cms"
    league_id = "1"

    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
        # Get all pages of results
        all_matches = []
        page = 1

        url = f"{base_url}/cache600?alias=results&searchQuery={league_id}//&page={page}"
        response = await client.get(url)
        response.raise_for_status()
        data = response.json()
        total_pages = data.get("pages", 1)

        for page in range(1, total_pages + 1):
            if page > 1:
                url = f"{base_url}/cache600?alias=results&searchQuery={league_id}//&page={page}"
                response = await client.get(url)
                data = response.json()

            rows = data.get("data", [])
            for row in rows:
                if not isinstance(row, list) or len(row) < 9:
                    continue

                try:
                    date_str = row[1] if isinstance(row[1], str) else ""
                    time_str = row[2] if isinstance(row[2], str) else ""
                    home_team = row[3] if isinstance(row[3], dict) else {}
                    away_team = row[4] if isinstance(row[4], dict) else {}
                    status = row[8] if isinstance(row[8], dict) else {}

                    is_finished = status.get("id") == 12 or status.get("percent", 0) == 100
                    if is_finished:
                        continue

                    home_name = home_team.get("name", "")
                    away_name = away_team.get("name", "")

                    # Filter for National League only
                    if not is_nl_team(home_name) or not is_nl_team(away_name):
                        continue

                    all_matches.append({
                        "date": date_str,
                        "time": time_str,
                        "home": {
                            "id": str(home_team.get("id", "")),
                            "name": home_name,
                            "abbrev": home_team.get("acronym", "")
                        },
                        "away": {
                            "id": str(away_team.get("id", "")),
                            "name": away_name,
                            "abbrev": away_team.get("acronym", "")
                        }
                    })
                except:
                    continue

    # Use Kyiv time for date calculations
    now_kyiv = datetime.now(KYIV_TZ)
    start = datetime(now_kyiv.year, now_kyiv.month, now_kyiv.day, tzinfo=KYIV_TZ)
    end = start + timedelta(days=days + 1)

    result = []
    for match in all_matches:
        date_str = match.get("date", "")
        time_str = match.get("time", "00:00")

        try:
            # Format: "DD.MM.YYYY HH:MM"
            game_date = datetime.strptime(f"{date_str} {time_str}", "%d.%m.%Y %H:%M")
            game_date = game_date.replace(tzinfo=KYIV_TZ)
            if not (start <= game_date < end):
                continue
        except:
            continue

        home = match.get("home", {})
        away = match.get("away", {})
        home_abbrev = home.get("abbrev", "")
        away_abbrev = away.get("abbrev", "")

        result.append({
            "game_id": f"swiss_{home.get('id')}_{away.get('id')}_{date_str}",
            "date": game_date.strftime("%d.%m.%Y %H:%M"),
            "date_iso": game_date.isoformat(),
            "home_team": {
                "abbrev": home_abbrev,
                "name": home.get("name", home_abbrev),
                "name_ru": SWISS_TEAM_NAMES_RU.get(home_abbrev, home.get("name", home_abbrev)),
                "logo_url": None
            },
            "away_team": {
                "abbrev": away_abbrev,
                "name": away.get("name", away_abbrev),
                "name_ru": SWISS_TEAM_NAMES_RU.get(away_abbrev, away.get("name", away_abbrev)),
                "logo_url": None
            },
            "venue": ""
        })

    return sorted(result, key=lambda g: g.get("date_iso", ""))


async def parse_flashscore_data(data: str, target_league: str, team_names_ru: dict) -> list:
    """Parse Flashscore feed data and extract matches for a specific league.
    Uses same parsing approach as flashscore_service.py which works correctly.
    """
    if not data or data.strip() in ('0', ''):
        return []

    items = data.split('¬')

    # Group items into dicts like flashscore_service.py does
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

    result = []
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

            match_id = game.get('~AA', '')
            home = game.get('AE', '')
            away = game.get('AF', '')
            timestamp = game.get('AD', '')
            status = game.get('AB', '')
            home_logo = game.get('OA', '')
            away_logo = game.get('OB', '')
            home_score = game.get('AG', '')
            away_score = game.get('AH', '')

            try:
                game_date = datetime.fromtimestamp(int(timestamp), tz=timezone.utc)
                game_date = to_kyiv_time(game_date)
            except:
                continue

            result.append({
                "game_id": f"fs_{match_id}",
                "date": game_date.strftime("%d.%m.%Y %H:%M"),
                "date_iso": game_date.isoformat(),
                "home_team": {
                    "abbrev": home,
                    "name": home,
                    "name_ru": team_names_ru.get(home, home),
                    "logo_url": f"{FLASHSCORE_LOGO_BASE}{home_logo}" if home_logo else ""
                },
                "away_team": {
                    "abbrev": away,
                    "name": away,
                    "name_ru": team_names_ru.get(away, away),
                    "logo_url": f"{FLASHSCORE_LOGO_BASE}{away_logo}" if away_logo else ""
                },
                "venue": "",
                "status": status,
                "home_score": home_score,
                "away_score": away_score,
                "league": league_name
            })

    return sorted(result, key=lambda g: g.get("date_iso", ""))


def get_db_schedule(league: str, days: int) -> list:
    """Get schedule from database (synced from API-Sports).

    Reads upcoming games from pre-synced database for KHL, Czech Extraliga, Denmark Metal Ligaen.
    """
    import sys
    import os

    # Add backend to path for database models
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

    from app.models.database import SessionLocal, Team, Game

    # Team name mappings for Russian names
    team_names_ru = {
        "KHL": KHL_TEAM_NAMES_RU,
        "CZECH": CZECH_TEAM_NAMES_RU,
        "DENMARK": DENMARK_TEAM_NAMES_RU,
    }

    league_upper = league.upper()
    if league_upper not in team_names_ru:
        return []

    names_ru = team_names_ru.get(league_upper, {})

    db = SessionLocal()
    try:
        # Calculate date range in Kyiv time
        now_kyiv = datetime.now(KYIV_TZ)
        start = datetime(now_kyiv.year, now_kyiv.month, now_kyiv.day, tzinfo=KYIV_TZ)
        end = start + timedelta(days=days + 1)

        # Convert to UTC for database query
        start_utc = start.astimezone(timezone.utc).replace(tzinfo=None)
        end_utc = end.astimezone(timezone.utc).replace(tzinfo=None)

        # Get upcoming games (not finished, within date range)
        games = db.query(Game).filter(
            Game.league == league_upper,
            Game.is_finished == False,
            Game.date >= start_utc,
            Game.date < end_utc
        ).order_by(Game.date).all()

        result = []
        for game in games:
            home_team = game.home_team
            away_team = game.away_team

            if not home_team or not away_team:
                continue

            # Convert game date to Kyiv time
            game_date_utc = game.date.replace(tzinfo=timezone.utc) if game.date.tzinfo is None else game.date
            game_date = to_kyiv_time(game_date_utc)

            result.append({
                "game_id": game.game_id,
                "date": game_date.strftime("%d.%m.%Y %H:%M"),
                "date_iso": game_date.isoformat(),
                "home_team": {
                    "abbrev": home_team.abbrev,
                    "name": home_team.name,
                    "name_ru": home_team.name_ru or names_ru.get(home_team.name, home_team.name),
                    "logo_url": home_team.logo_url
                },
                "away_team": {
                    "abbrev": away_team.abbrev,
                    "name": away_team.name,
                    "name_ru": away_team.name_ru or names_ru.get(away_team.name, away_team.name),
                    "logo_url": away_team.logo_url
                },
                "venue": ""
            })

        return result

    except Exception as e:
        print(f"Database error: {e}")
        return []
    finally:
        db.close()


async def get_schedule(league: str, days: int):
    if league == "NHL":
        return await get_nhl_schedule(days)
    elif league == "AHL":
        return await get_ahl_schedule(days)
    elif league == "LIIGA":
        return await get_liiga_schedule(days)
    elif league == "DEL":
        return await get_del_schedule(days)
    elif league.upper() == "AUSTRIA":
        return await get_austria_schedule(days)
    elif league.upper() == "SWISS":
        return await get_swiss_schedule(days)
    elif league.upper() in ("KHL", "CZECH", "DENMARK"):
        return get_db_schedule(league, days)
    return []


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        league = params.get("league", ["NHL"])[0].upper()
        days = int(params.get("days", ["7"])[0])

        try:
            games = asyncio.run(get_schedule(league, days))
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "s-maxage=300, stale-while-revalidate")
            self.end_headers()
            self.wfile.write(json.dumps({"games": games, "league": league}).encode())
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
