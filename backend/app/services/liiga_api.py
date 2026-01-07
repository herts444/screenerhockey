import httpx
from datetime import datetime, timedelta
from typing import Optional, List


class LiigaApiService:
    """Finnish Liiga API Service"""

    BASE_URL = "https://liiga.fi/api/v2"
    CURRENT_SEASON = 2026  # Season 2025-26

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)

    async def close(self):
        await self.client.aclose()

    async def get_games(self, season: int = None, tournament: str = "runkosarja") -> List[dict]:
        """Get all games for a season

        Args:
            season: Season year (e.g., 2025 for 2024-25 season)
            tournament: Tournament type (runkosarja = regular season)
        """
        season = season or self.CURRENT_SEASON
        url = f"{self.BASE_URL}/games?tournament={tournament}&season={season}"

        response = await self.client.get(url)
        response.raise_for_status()
        return response.json()

    async def get_schedule_week(self, start_date: Optional[str] = None) -> List[dict]:
        """Get upcoming games for the next 7 days"""
        games = await self.get_games()

        start = datetime.strptime(start_date, "%Y-%m-%d") if start_date else datetime.now()
        end = start + timedelta(days=7)

        upcoming = []
        for game in games:
            game_start = game.get("start", "")
            if not game_start:
                continue

            try:
                game_date = datetime.fromisoformat(game_start.replace("Z", "+00:00"))
                if start <= game_date.replace(tzinfo=None) <= end:
                    # Only include non-finished games
                    if not game.get("ended", False):
                        upcoming.append(game)
            except Exception:
                continue

        return sorted(upcoming, key=lambda g: g.get("start", ""))

    async def get_teams(self) -> List[dict]:
        """Get all Liiga teams from games data"""
        games = await self.get_games()

        teams = {}
        for game in games:
            home = game.get("homeTeam", {})
            away = game.get("awayTeam", {})

            for team_data in [home, away]:
                team_id = team_data.get("teamId", "")
                if team_id and team_id not in teams:
                    # Parse team abbrev from teamId (format: "1234567:abbrev")
                    abbrev = team_id.split(":")[-1].upper() if ":" in team_id else team_id

                    teams[team_id] = {
                        "id": team_id,
                        "abbrev": abbrev,
                        "name": team_data.get("teamName", ""),
                        "logo_url": team_data.get("logos", {}).get("darkBg", "")
                    }

        return list(teams.values())

    async def get_team_games(self, team_id: str, season: int = None) -> List[dict]:
        """Get all games for a specific team"""
        games = await self.get_games(season)

        team_games = []
        for game in games:
            home_id = game.get("homeTeam", {}).get("teamId", "")
            away_id = game.get("awayTeam", {}).get("teamId", "")

            if home_id == team_id or away_id == team_id:
                team_games.append(game)

        return team_games

    async def get_team_game_log(self, team_id: str, season: int = None) -> List[dict]:
        """Get team's finished games for the season"""
        games = await self.get_team_games(team_id, season)

        # Filter only finished games
        finished_games = [
            g for g in games
            if g.get("ended", False) == True
        ]

        return finished_games


# Finnish Liiga team names in Russian
LIIGA_TEAM_NAMES_RU = {
    "HIFK": "ХИФК Хельсинки",
    "K-ESPOO": "К-Эспоо",
    "KALPA": "КалПа Куопио",
    "HPK": "ХПК Хямеэнлинна",
    "ILVES": "Ильвес Тампере",
    "JYP": "ЮП Ювяскюля",
    "JUKURIT": "Юкурит Миккели",
    "LUKKO": "Лукко Раума",
    "PELICANS": "Пеликанс Лахти",
    "SAIPA": "СайПа Лаппеэнранта",
    "SPORT": "Спорт Вааса",
    "TAPPARA": "Таппара Тампере",
    "TPS": "ТПС Турку",
    "ASSAT": "Ассат Пори",
    "KARPAT": "Кярпят Оулу",
    "KOOKOO": "Кукоо Коувола",
}
