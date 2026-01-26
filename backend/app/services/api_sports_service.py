"""
API-Sports Hockey service for KHL, Czech Extraliga, Denmark Metal Ligaen.
https://api-sports.io/documentation/hockey/v1
"""

import httpx
import asyncio
from datetime import datetime
from typing import List, Optional
import os


class ApiSportsService:
    """Base service for API-Sports Hockey API"""

    BASE_URL = "https://v1.hockey.api-sports.io"
    API_KEY = os.getenv("API_SPORTS_KEY", "58586d14273e6cff445ae9c658b00a11")

    # League IDs in API-Sports
    LEAGUE_IDS = {
        "KHL": 35,
        "CZECH": 10,
        "DENMARK": 12,
    }

    # Current season (starts in September, so 2024 = 2024-2025 season)
    CURRENT_SEASON = 2024

    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={"x-apisports-key": self.API_KEY}
        )

    async def close(self):
        await self.client.aclose()

    async def _request(self, endpoint: str, params: dict = None) -> dict:
        """Make API request with rate limiting (10 req/min for free tier)"""
        url = f"{self.BASE_URL}/{endpoint}"
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if data.get("errors") and len(data["errors"]) > 0:
            # Check for rate limit error
            if "rateLimit" in str(data["errors"]):
                print("Rate limit hit, waiting 60 seconds...")
                await asyncio.sleep(60)
                # Retry once
                response = await self.client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                if data.get("errors") and len(data["errors"]) > 0:
                    raise Exception(f"API-Sports error: {data['errors']}")
            else:
                raise Exception(f"API-Sports error: {data['errors']}")

        # Small delay between requests to avoid rate limit (free tier: 10 req/min)
        await asyncio.sleep(7)  # 60/10 = 6 sec minimum, use 7 for safety

        return data

    async def get_leagues(self) -> List[dict]:
        """Get all available leagues"""
        data = await self._request("leagues")
        return data.get("response", [])

    async def get_teams(self, league_id: int, season: int = None) -> List[dict]:
        """Get teams for a league"""
        season = season or self.CURRENT_SEASON
        data = await self._request("teams", {"league": league_id, "season": season})
        return data.get("response", [])

    async def get_games(self, league_id: int, season: int = None) -> List[dict]:
        """Get all games for a league in a season"""
        season = season or self.CURRENT_SEASON
        data = await self._request("games", {"league": league_id, "season": season})
        return data.get("response", [])

    async def get_games_by_date(self, date: str) -> List[dict]:
        """Get games for a specific date (YYYY-MM-DD)"""
        data = await self._request("games", {"date": date})
        return data.get("response", [])

    async def get_game(self, game_id: int) -> Optional[dict]:
        """Get single game by ID"""
        data = await self._request("games", {"id": game_id})
        games = data.get("response", [])
        return games[0] if games else None


class KHLApiService(ApiSportsService):
    """KHL-specific API service"""

    LEAGUE_ID = 35

    async def get_all_teams(self) -> List[dict]:
        """Get all KHL teams"""
        teams = await self.get_teams(self.LEAGUE_ID)
        # Filter out all-star teams and divisions
        return [
            t for t in teams
            if t.get("national") is False
            and "Division" not in t.get("name", "")
            and "All Star" not in t.get("name", "")
        ]

    async def get_all_games(self, season: int = None) -> List[dict]:
        """Get all KHL games for the season"""
        return await self.get_games(self.LEAGUE_ID, season)

    async def get_finished_games(self, season: int = None) -> List[dict]:
        """Get only finished games"""
        games = await self.get_all_games(season)
        return [g for g in games if g.get("status", {}).get("short") == "FT"]


class CzechApiService(ApiSportsService):
    """Czech Extraliga-specific API service"""

    LEAGUE_ID = 10

    async def get_all_teams(self) -> List[dict]:
        """Get all Czech Extraliga teams"""
        teams = await self.get_teams(self.LEAGUE_ID)
        return [t for t in teams if t.get("national") is False]

    async def get_all_games(self, season: int = None) -> List[dict]:
        """Get all Czech Extraliga games for the season"""
        return await self.get_games(self.LEAGUE_ID, season)

    async def get_finished_games(self, season: int = None) -> List[dict]:
        """Get only finished games"""
        games = await self.get_all_games(season)
        return [g for g in games if g.get("status", {}).get("short") == "FT"]


class DenmarkApiService(ApiSportsService):
    """Denmark Metal Ligaen-specific API service"""

    LEAGUE_ID = 12

    async def get_all_teams(self) -> List[dict]:
        """Get all Denmark Metal Ligaen teams"""
        teams = await self.get_teams(self.LEAGUE_ID)
        return [t for t in teams if t.get("national") is False]

    async def get_all_games(self, season: int = None) -> List[dict]:
        """Get all Denmark Metal Ligaen games for the season"""
        return await self.get_games(self.LEAGUE_ID, season)

    async def get_finished_games(self, season: int = None) -> List[dict]:
        """Get only finished games"""
        games = await self.get_all_games(season)
        return [g for g in games if g.get("status", {}).get("short") == "FT"]
