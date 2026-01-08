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


async def get_schedule(league: str, days: int):
    if league == "NHL":
        return await get_nhl_schedule(days)
    elif league == "AHL":
        return await get_ahl_schedule(days)
    elif league == "LIIGA":
        return await get_liiga_schedule(days)
    elif league == "DEL":
        return await get_del_schedule(days)
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
