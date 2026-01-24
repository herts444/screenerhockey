"""
Swiss National League (SIHF) API Service.
Uses official data.sihf.ch API.
"""
import httpx
from datetime import datetime, timedelta
from typing import Optional, List


# Known Swiss National League teams (2025-26 season)
# Used to filter results from API which returns all leagues
NL_TEAMS = {
    "ZSC Lions", "SC Bern", "EV Zug", "HC Lugano",
    "Fribourg-Gottéron", "Lausanne HC", "EHC Kloten",
    "SC Rapperswil-Jona Lakers", "Genève-Servette HC",
    "EHC Biel-Bienne", "HC Davos", "HC Ambri-Piotta",
    "SCL Tigers", "HC Ajoie"
}


def is_nl_team(team_name: str) -> bool:
    """Check if team is in National League"""
    if not team_name:
        return False
    # Direct match
    if team_name in NL_TEAMS:
        return True
    # Partial match (for slight name variations)
    name_lower = team_name.lower()
    for nl_team in NL_TEAMS:
        if nl_team.lower() in name_lower or name_lower in nl_team.lower():
            return True
    return False


class SwissApiService:
    """Swiss National League API Service"""

    BASE_URL = "https://data.sihf.ch/Statistic/api/cms"
    LEAGUE_ID = "1"  # National League

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0, follow_redirects=True)
        self._teams_cache = None
        self._matches_cache = None

    async def close(self):
        await self.client.aclose()

    async def get_all_results(self, page: int = 1) -> dict:
        """Get results page from SIHF API"""
        url = f"{self.BASE_URL}/cache600?alias=results&searchQuery={self.LEAGUE_ID}//&page={page}"
        response = await self.client.get(url)
        response.raise_for_status()
        return response.json()

    async def get_all_matches(self) -> List[dict]:
        """Get all National League matches for the season (paginated)"""
        if self._matches_cache:
            return self._matches_cache

        all_matches = []
        page = 1

        # Get first page to know total pages
        data = await self.get_all_results(page)
        total_pages = data.get("pages", 1)

        # Parse first page
        matches = self._parse_results_data(data)
        all_matches.extend(matches)

        # Get remaining pages
        for page in range(2, total_pages + 1):
            try:
                data = await self.get_all_results(page)
                matches = self._parse_results_data(data)
                all_matches.extend(matches)
            except Exception:
                continue

        # Filter for National League matches only
        nl_matches = [
            m for m in all_matches
            if is_nl_team(m.get("home", {}).get("name", "")) and
               is_nl_team(m.get("away", {}).get("name", ""))
        ]

        self._matches_cache = nl_matches
        return nl_matches

    def _parse_results_data(self, data: dict) -> List[dict]:
        """Parse results data from SIHF response format"""
        rows = data.get("data", [])
        matches = []

        for row in rows:
            if not isinstance(row, list) or len(row) < 9:
                continue

            try:
                # Parse row based on column structure:
                # [0]=day, [1]=date, [2]=time, [3]=home_team, [4]=away_team,
                # [5]=score, [6]=periods, [7]=OT/SO, [8]=status, [9]=details
                date_str = row[1] if isinstance(row[1], str) else ""
                time_str = row[2] if isinstance(row[2], str) else ""

                home_team = row[3] if isinstance(row[3], dict) else {}
                away_team = row[4] if isinstance(row[4], dict) else {}
                score = row[5] if isinstance(row[5], dict) else {}
                periods = row[6] if isinstance(row[6], dict) else {}
                ot_so = row[7] if isinstance(row[7], str) else ""
                status = row[8] if isinstance(row[8], dict) else {}
                details = row[9] if len(row) > 9 and isinstance(row[9], dict) else {}

                # Check if game is finished (status.id == 12 means "Ende" = finished)
                is_finished = status.get("id") == 12 or status.get("percent", 0) == 100

                match = {
                    "id": details.get("gameId", ""),
                    "date": date_str,
                    "time": time_str,
                    "start_date": f"{date_str} {time_str}" if date_str and time_str else "",
                    "home": {
                        "id": str(home_team.get("id", "")),
                        "name": home_team.get("name", ""),
                        "abbrev": home_team.get("acronym", "")
                    },
                    "away": {
                        "id": str(away_team.get("id", "")),
                        "name": away_team.get("name", ""),
                        "abbrev": away_team.get("acronym", "")
                    },
                    "home_score": int(score.get("homeTeam", 0)) if score.get("homeTeam") else None,
                    "away_score": int(score.get("awayTeam", 0)) if score.get("awayTeam") else None,
                    "periods_home": periods.get("homeTeam", []),
                    "periods_away": periods.get("awayTeam", []),
                    "overtime": ot_so,
                    "is_finished": is_finished,
                    "status": status
                }
                matches.append(match)

            except (IndexError, ValueError, TypeError):
                continue

        return matches

    async def get_teams(self) -> List[dict]:
        """Get all Swiss NL teams from match data"""
        if self._teams_cache:
            return self._teams_cache

        matches = await self.get_all_matches()

        teams = {}
        for match in matches:
            for team_key in ["home", "away"]:
                team = match.get(team_key, {})
                team_id = team.get("id", "")
                team_name = team.get("name", "")
                if team_id and team_id not in teams and is_nl_team(team_name):
                    teams[team_id] = {
                        "id": team_id,
                        "abbrev": team.get("abbrev", ""),
                        "name": team_name,
                        "logo_url": None
                    }

        self._teams_cache = list(teams.values())
        return self._teams_cache

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
            if match.get("is_finished"):
                continue

            # Parse date (format: "DD.MM.YYYY")
            date_str = match.get("date", "")
            if not date_str:
                continue

            try:
                match_date = datetime.strptime(date_str, "%d.%m.%Y")
                if start <= match_date < end:
                    upcoming.append(self._format_game(match))
            except ValueError:
                continue

        return sorted(upcoming, key=lambda g: g.get("startTimeUTC", ""))

    async def get_team_game_log(self, team_id: str) -> List[dict]:
        """Get team's finished games for the season"""
        all_matches = await self.get_all_matches()

        finished_games = []
        for match in all_matches:
            if not match.get("is_finished"):
                continue

            home_id = match.get("home", {}).get("id", "")
            away_id = match.get("away", {}).get("id", "")

            if home_id == team_id or away_id == team_id:
                finished_games.append(match)

        return finished_games

    def _format_game(self, match: dict) -> dict:
        """Format match data for schedule display"""
        home = match.get("home", {})
        away = match.get("away", {})

        # Convert DD.MM.YYYY HH:MM to ISO format
        date_str = match.get("date", "")
        time_str = match.get("time", "00:00")
        start_time = ""
        if date_str:
            try:
                dt = datetime.strptime(f"{date_str} {time_str}", "%d.%m.%Y %H:%M")
                start_time = dt.isoformat()
            except ValueError:
                pass

        return {
            "id": match.get("id"),
            "startTimeUTC": start_time,
            "gameState": "FINAL" if match.get("is_finished") else "SCHEDULED",
            "homeTeam": {
                "id": home.get("id", ""),
                "abbrev": home.get("abbrev", ""),
                "name": home.get("name", ""),
                "score": match.get("home_score")
            },
            "awayTeam": {
                "id": away.get("id", ""),
                "abbrev": away.get("abbrev", ""),
                "name": away.get("name", ""),
                "score": match.get("away_score")
            },
            "venue": ""
        }


# Swiss National League team names in Russian
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
