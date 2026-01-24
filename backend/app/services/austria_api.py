"""
Austrian ICE Hockey League API Service.
Uses official S3 bucket data from ice.hockey.
"""
import httpx
from datetime import datetime, timedelta
from typing import Optional, List


class AustriaApiService:
    """Austrian ICE Hockey League API Service using S3 bucket"""

    BASE_URL = "https://s3.dualstack.eu-west-1.amazonaws.com/icehl.hokejovyzapis.cz"
    CURRENT_SEASON = "2025"
    LEAGUE_ID = "1"  # ICE HL main league

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0, follow_redirects=True)
        self._teams_cache = None
        self._matches_cache = None

    async def close(self):
        await self.client.aclose()

    async def get_teams(self) -> List[dict]:
        """Get all ICE HL teams"""
        if self._teams_cache:
            return self._teams_cache

        url = f"{self.BASE_URL}/league-all-team-stats/{self.CURRENT_SEASON}/{self.LEAGUE_ID}.json"
        response = await self.client.get(url)
        response.raise_for_status()

        teams_data = response.json()
        teams = []

        for team in teams_data:
            teams.append({
                "id": str(team.get("teamId")),
                "abbrev": team.get("teamShortcut", ""),
                "name": team.get("teamName", ""),
                "country": team.get("country", ""),
                "logo_url": None  # Can be added later if available
            })

        self._teams_cache = teams
        return teams

    async def get_all_matches(self) -> List[dict]:
        """Get all matches for the season"""
        if self._matches_cache:
            return self._matches_cache

        url = f"{self.BASE_URL}/league-matches/{self.CURRENT_SEASON}/{self.LEAGUE_ID}.json"
        response = await self.client.get(url)
        response.raise_for_status()

        data = response.json()
        matches = data.get("matches", data) if isinstance(data, dict) else data

        self._matches_cache = matches
        return matches

    async def get_schedule_week(self, start_date: Optional[str] = None) -> List[dict]:
        """Get upcoming games for the next 7 days"""
        all_matches = await self.get_all_matches()

        if start_date:
            start = datetime.strptime(start_date, "%Y-%m-%d")
        else:
            start = datetime.now()

        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=8)

        upcoming = []
        for match in all_matches:
            # Check if game is not finished
            status = match.get("status", "")
            if status == "AFTER_MATCH":
                continue

            # Parse date
            date_str = match.get("start_date", "")
            if not date_str:
                continue

            try:
                match_date = datetime.strptime(date_str.split()[0], "%Y-%m-%d")
                if start <= match_date < end:
                    upcoming.append(self._format_game(match))
            except (ValueError, IndexError):
                continue

        return sorted(upcoming, key=lambda g: g.get("startTimeUTC", ""))

    async def get_team_schedule(self, team_id: str) -> List[dict]:
        """Get all games for a specific team"""
        all_matches = await self.get_all_matches()

        team_games = []
        for match in all_matches:
            home_id = str(match.get("home", {}).get("id", ""))
            away_id = str(match.get("guest", {}).get("id", ""))

            if home_id == team_id or away_id == team_id:
                team_games.append(match)

        return team_games

    async def get_team_game_log(self, team_id: str) -> List[dict]:
        """Get team's finished games for the season"""
        team_games = await self.get_team_schedule(team_id)

        # Filter only finished games
        finished_games = [
            g for g in team_games
            if g.get("status") == "AFTER_MATCH"
        ]

        return finished_games

    def _format_game(self, match: dict) -> dict:
        """Format match data for schedule display"""
        home = match.get("home", {})
        away = match.get("guest", {})
        results = match.get("results", {})
        score = results.get("score", {}).get("final", {})

        return {
            "id": match.get("id"),
            "startTimeUTC": match.get("start_date", ""),
            "gameState": "FINAL" if match.get("status") == "AFTER_MATCH" else "SCHEDULED",
            "homeTeam": {
                "id": str(home.get("id", "")),
                "abbrev": home.get("shortcut", ""),
                "name": home.get("name", ""),
                "score": score.get("score_home")
            },
            "awayTeam": {
                "id": str(away.get("id", "")),
                "abbrev": away.get("shortcut", ""),
                "name": away.get("name", ""),
                "score": score.get("score_guest")
            },
            "venue": match.get("arena", "")
        }


# Austrian ICE HL team names in Russian
AUSTRIA_TEAM_NAMES_RU = {
    "KAC": "EC-KAC Клагенфурт",
    "RBS": "Ред Булл Зальцбург",
    "G99": "Грац 99ers",
    "HCB": "Больцано",
    "PUS": "Пустерталь",
    "OLJ": "Олимпия Любляна",
    "AVS": "Фехервар AV19",
    "VIC": "Вена Кэпиталз",
    "FTC": "Ференцварош",
    "VSV": "EC VSV Филлах",
    "BWL": "Блэк Уингз Линц",
    "PIO": "Пионирс Форарльберг",
    "TIW": "Инсбрук",
}
