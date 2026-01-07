import httpx
from datetime import datetime, timedelta
from typing import Optional, List
import asyncio


class AHLApiService:
    """AHL API Service using HockeyTech API"""

    BASE_URL = "https://lscluster.hockeytech.com/feed/index.php"
    API_KEY = "50c2cd9b5e18e390"
    CLIENT_CODE = "ahl"
    CURRENT_SEASON_ID = "90"  # 2025-26 Regular Season

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)

    async def close(self):
        await self.client.aclose()

    def _build_url(self, view: str, **params) -> str:
        """Build API URL with common parameters"""
        base_params = {
            "feed": "modulekit",
            "view": view,
            "key": self.API_KEY,
            "fmt": "json",
            "client_code": self.CLIENT_CODE,
            "lang": "en"
        }
        base_params.update(params)
        query = "&".join(f"{k}={v}" for k, v in base_params.items())
        return f"{self.BASE_URL}?{query}"

    async def get_schedule(self, date: Optional[str] = None, season_id: str = None) -> List[dict]:
        """Get AHL schedule for a specific date"""
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        url = self._build_url(
            "schedule",
            season_id=season_id or self.CURRENT_SEASON_ID,
            date=date
        )

        response = await self.client.get(url)
        response.raise_for_status()
        data = response.json()

        return data.get("SiteKit", {}).get("Schedule", [])

    async def get_schedule_week(self, start_date: Optional[str] = None) -> List[dict]:
        """Get games for the next 7 days"""
        all_games = []
        start = datetime.strptime(start_date, "%Y-%m-%d") if start_date else datetime.now()

        for i in range(7):
            date = (start + timedelta(days=i)).strftime("%Y-%m-%d")
            try:
                games = await self.get_schedule(date)
                # Filter games for this specific date
                for game in games:
                    game_date = game.get("date_played", "")
                    if game_date == date:
                        all_games.append(game)
            except Exception as e:
                print(f"Error fetching AHL schedule for {date}: {e}")

        return all_games

    async def get_teams(self) -> List[dict]:
        """Get all AHL teams"""
        url = self._build_url("teamsbyseason", season_id=self.CURRENT_SEASON_ID)

        response = await self.client.get(url)
        response.raise_for_status()
        data = response.json()

        teams_data = data.get("SiteKit", {}).get("Teamsbyseason", [])
        teams = []

        for team in teams_data:
            teams.append({
                "id": team.get("id"),
                "abbrev": team.get("code"),
                "name": team.get("name"),
                "city": team.get("city"),
                "nickname": team.get("nickname"),
                "division": team.get("division_long_name"),
                "logo_url": team.get("team_logo_url") or f"https://assets.leaguestat.com/ahl/logos/{team.get('id')}.png"
            })

        return teams

    async def get_team_schedule(self, team_id: str, season_id: str = None) -> List[dict]:
        """Get full season schedule for a team"""
        url = self._build_url(
            "schedule",
            season_id=season_id or self.CURRENT_SEASON_ID,
            team_id=team_id
        )

        response = await self.client.get(url)
        response.raise_for_status()
        data = response.json()

        return data.get("SiteKit", {}).get("Schedule", [])

    async def get_team_game_log(self, team_id: str, season_id: str = None) -> List[dict]:
        """Get team's finished games for the season"""
        games = await self.get_team_schedule(team_id, season_id)

        # Filter only finished games
        finished_games = [
            g for g in games
            if g.get("game_status") == "Final" or g.get("final") == "1"
        ]

        return finished_games

    async def get_standings(self) -> List[dict]:
        """Get current AHL standings"""
        url = self._build_url("standings", season_id=self.CURRENT_SEASON_ID)

        response = await self.client.get(url)
        response.raise_for_status()
        data = response.json()

        return data.get("SiteKit", {}).get("Standings", [])


# AHL Team names in Russian (for consistency with NHL)
AHL_TEAM_NAMES_RU = {
    "ABB": "Эбботсфорд Кэнакс",
    "BAK": "Бейкерсфилд Кондорс",
    "BEL": "Беллвилл Сенаторз",
    "BRI": "Бриджпорт Айлендерс",
    "CGY": "Калгари Рэнглерс",
    "CHI": "Чикаго Вулвз",
    "CLE": "Кливленд Монстерс",
    "CLT": "Шарлотт Чекерз",
    "COA": "Коачелла Вэлли Файрбёрдс",
    "COL": "Колорадо Иглс",
    "GR": "Гранд Рапидс Гриффинс",
    "HER": "Херши Беарс",
    "HFD": "Хартфорд Вулф Пэк",
    "IA": "Айова Уайлд",
    "LAV": "Лаваль Рокет",
    "LV": "Хендерсон Силвер Найтс",
    "MB": "Манитоба Муз",
    "MIL": "Милуоки Эдмиралс",
    "ONT": "Онтарио Рейн",
    "PRO": "Провиденс Брюинз",
    "ROC": "Рочестер Американс",
    "SD": "Сан-Диего Галлз",
    "SJ": "Сан-Хосе Барракуда",
    "SPR": "Спрингфилд Тандербёрдс",
    "SYR": "Сиракьюз Кранч",
    "TEX": "Техас Старз",
    "TOR": "Торонто Марлиз",
    "TUC": "Тусон Роудраннерс",
    "UTC": "Ютика Кометс",
    "WBS": "Уилкс-Барре Пингвинз",
    "WPW": "Калгари Рэнглерс",
}
