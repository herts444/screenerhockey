import httpx
from datetime import datetime, timedelta
from typing import Optional
import asyncio


class NHLApiService:
    BASE_URL = "https://api-web.nhle.com/v1"

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)

    async def close(self):
        await self.client.aclose()

    async def get_schedule(self, date: Optional[str] = None) -> dict:
        """Get NHL schedule for a specific date or current week"""
        if date:
            url = f"{self.BASE_URL}/schedule/{date}"
        else:
            url = f"{self.BASE_URL}/schedule/now"

        response = await self.client.get(url)
        response.raise_for_status()
        return response.json()

    async def get_schedule_week(self, start_date: Optional[str] = None) -> list:
        """Get games for the next 7 days"""
        games = []
        start = datetime.strptime(start_date, "%Y-%m-%d") if start_date else datetime.now()

        for i in range(7):
            date = (start + timedelta(days=i)).strftime("%Y-%m-%d")
            try:
                schedule = await self.get_schedule(date)
                if "gameWeek" in schedule:
                    for day in schedule["gameWeek"]:
                        if day.get("date") == date:
                            games.extend(day.get("games", []))
                            break
            except Exception as e:
                print(f"Error fetching schedule for {date}: {e}")

        return games

    async def get_team_schedule(self, team_abbrev: str, season: str = "20242025") -> dict:
        """Get full season schedule for a team"""
        url = f"{self.BASE_URL}/club-schedule-season/{team_abbrev}/{season}"
        response = await self.client.get(url)
        response.raise_for_status()
        return response.json()

    async def get_game_boxscore(self, game_id: str) -> dict:
        """Get detailed game boxscore"""
        url = f"{self.BASE_URL}/gamecenter/{game_id}/boxscore"
        response = await self.client.get(url)
        response.raise_for_status()
        return response.json()

    async def get_game_landing(self, game_id: str) -> dict:
        """Get game landing page with basic info"""
        url = f"{self.BASE_URL}/gamecenter/{game_id}/landing"
        response = await self.client.get(url)
        response.raise_for_status()
        return response.json()

    async def get_standings(self) -> dict:
        """Get current NHL standings"""
        url = f"{self.BASE_URL}/standings/now"
        response = await self.client.get(url)
        response.raise_for_status()
        return response.json()

    async def get_all_teams(self) -> list:
        """Get all NHL teams from standings"""
        standings = await self.get_standings()
        teams = []

        for team_data in standings.get("standings", []):
            teams.append({
                "id": team_data.get("teamAbbrev", {}).get("default"),
                "abbrev": team_data.get("teamAbbrev", {}).get("default"),
                "name": team_data.get("teamName", {}).get("default"),
                "logo": team_data.get("teamLogo")
            })

        return teams

    async def get_team_game_log(self, team_abbrev: str, season: str = "20242025", game_type: int = 2) -> list:
        """
        Get team's game log for the season
        game_type: 2 = regular season, 3 = playoffs
        """
        schedule = await self.get_team_schedule(team_abbrev, season)
        games = schedule.get("games", [])

        finished_games = [
            g for g in games
            if g.get("gameState") in ["OFF", "FINAL"]
        ]

        return finished_games


TEAM_NAMES_RU = {
    "ANA": "Анахайм Дакс",
    "ARI": "Аризона Койотс",
    "BOS": "Бостон Брюинз",
    "BUF": "Баффало Сейбрз",
    "CGY": "Калгари Флэймз",
    "CAR": "Каролина Харрикейнз",
    "CHI": "Чикаго Блэкхокс",
    "COL": "Колорадо Эвеланш",
    "CBJ": "Коламбус Блю Джекетс",
    "DAL": "Даллас Старз",
    "DET": "Детройт Ред Уингз",
    "EDM": "Эдмонтон Ойлерз",
    "FLA": "Флорида Пантерз",
    "LAK": "Лос-Анджелес Кингз",
    "MIN": "Миннесота Уайлд",
    "MTL": "Монреаль Канадиенс",
    "NSH": "Нэшвилл Предаторз",
    "NJD": "Нью-Джерси Девилз",
    "NYI": "Нью-Йорк Айлендерс",
    "NYR": "Нью-Йорк Рейнджерс",
    "OTT": "Оттава Сенаторз",
    "PHI": "Филадельфия Флайерз",
    "PIT": "Питтсбург Пингвинз",
    "SJS": "Сан-Хосе Шаркс",
    "SEA": "Сиэтл Кракен",
    "STL": "Сент-Луис Блюз",
    "TBL": "Тампа-Бэй Лайтнинг",
    "TOR": "Торонто Мейпл Лифс",
    "UTA": "Юта Хоккей Клаб",
    "VAN": "Ванкувер Кэнакс",
    "VGK": "Вегас Голден Найтс",
    "WSH": "Вашингтон Кэпиталз",
    "WPG": "Виннипег Джетс"
}
