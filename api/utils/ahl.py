"""AHL API client - stateless version"""
import httpx
from datetime import datetime, timedelta
from typing import List
from .stats import GameResult, StatsCalculator


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


class AHLService:
    BASE_URL = "https://lscluster.hockeytech.com/feed/index.php"
    API_KEY = "50c2cd9b5e18e390"
    CLIENT_CODE = "ahl"
    SEASON_ID = "90"

    @classmethod
    def _build_url(cls, view: str, **params) -> str:
        base_params = {
            "feed": "modulekit", "view": view, "key": cls.API_KEY,
            "fmt": "json", "client_code": cls.CLIENT_CODE, "lang": "en"
        }
        base_params.update(params)
        query = "&".join(f"{k}={v}" for k, v in base_params.items())
        return f"{cls.BASE_URL}?{query}"

    @classmethod
    async def get_teams(cls) -> List[dict]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = cls._build_url("teamsbyseason", season_id=cls.SEASON_ID)
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
                "logo_url": team.get("team_logo_url") or f"https://assets.leaguestat.com/ahl/logos/{team.get('id')}.png",
                "team_id": team.get("id")
            })
        return teams

    @classmethod
    async def get_schedule(cls, days: int = 7) -> List[dict]:
        games = []
        seen_ids = set()

        async with httpx.AsyncClient(timeout=30.0) as client:
            for i in range(days):
                date = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
                try:
                    url = cls._build_url("schedule", season_id=cls.SEASON_ID, date=date)
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
                            game_date = datetime.fromisoformat(game_date_str.replace("Z", "+00:00"))
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

    @classmethod
    async def get_team_stats(cls, team_abbrev: str, last_n: int = 0) -> dict:
        # First get team_id from teams list
        teams = await cls.get_teams()
        team_info = next((t for t in teams if t["abbrev"] == team_abbrev), None)
        if not team_info:
            return {}

        team_id = team_info["team_id"]

        async with httpx.AsyncClient(timeout=30.0) as client:
            url = cls._build_url("schedule", season_id=cls.SEASON_ID, team_id=team_id)
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        games = data.get("SiteKit", {}).get("Schedule", [])
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

            game_date_str = game.get("date_played")
            try:
                game_date = datetime.strptime(game_date_str, "%Y-%m-%d")
            except:
                continue

            result = GameResult(
                game_id=str(game.get("game_id")),
                date=game_date,
                opponent=AHL_TEAM_NAMES_RU.get(opp_abbrev, opp_name),
                opponent_abbrev=opp_abbrev,
                is_home=is_home,
                team_score=team_score,
                opponent_score=opp_score,
                total_goals=team_score + opp_score
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

        stats = StatsCalculator.get_full_team_stats(home_matches, away_matches)

        return {
            "team": {
                "abbrev": team_abbrev,
                "name": team_info["name"],
                "name_ru": team_info["name_ru"],
                "logo_url": team_info["logo_url"]
            },
            "stats": stats
        }
