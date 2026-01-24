"""
Sync service for loading and refreshing data from APIs.
Handles initial load on startup and scheduled updates.
"""

import asyncio
from datetime import datetime, time
from typing import Optional
from sqlalchemy.orm import Session

from ..models.database import SessionLocal, Team
from .cache_service import cache
from .data_service import DataService
from .ahl_data_service import AHLDataService
from .liiga_data_service import LiigaDataService
from .austria_data_service import AustriaDataService
from .swiss_data_service import SwissDataService


class SyncService:
    """Service for syncing and caching hockey data"""

    _instance = None
    _scheduler_task: Optional[asyncio.Task] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.nhl_service = DataService()
        self.ahl_service = AHLDataService()
        self.liiga_service = LiigaDataService()
        self.austria_service = AustriaDataService()
        self.swiss_service = SwissDataService()

    def _get_service(self, league: str):
        """Get appropriate service for league"""
        league_upper = league.upper()
        if league_upper == "AHL":
            return self.ahl_service
        elif league_upper == "LIIGA":
            return self.liiga_service
        elif league_upper == "AUSTRIA":
            return self.austria_service
        elif league_upper == "SWISS":
            return self.swiss_service
        return self.nhl_service

    async def sync_league(self, league: str, force: bool = False) -> dict:
        """Sync all data for a league"""
        if not force and not cache.needs_sync(league):
            return {"status": "skipped", "reason": "Cache is fresh"}

        db = SessionLocal()
        try:
            service = self._get_service(league)
            result = {"league": league, "teams": 0, "games": 0}

            # Sync teams
            print(f"[{datetime.now()}] Syncing {league} teams...")
            teams = await service.sync_teams(db)
            result["teams"] = len(teams)

            # Cache teams
            teams_data = [
                {
                    "abbrev": t.abbrev,
                    "name": t.name,
                    "name_ru": t.name_ru,
                    "logo_url": t.logo_url
                }
                for t in teams
            ]
            cache.set_teams(league, teams_data)

            # Sync games
            print(f"[{datetime.now()}] Syncing {league} games...")
            if league == "NHL":
                games_count = await service.sync_all_games(db, "20242025")
            else:
                # AHL and LIIGA don't need season parameter
                games_count = await service.sync_all_games(db)
            result["games"] = games_count

            # Load schedule into cache
            print(f"[{datetime.now()}] Loading {league} schedule...")
            schedule = await service.get_upcoming_games(db, 7)
            cache.set_schedule(league, schedule)

            # Precompute stats for teams in upcoming games
            print(f"[{datetime.now()}] Computing {league} team stats...")
            teams_in_schedule = set()
            for game in schedule:
                teams_in_schedule.add(game["home_team"]["abbrev"])
                teams_in_schedule.add(game["away_team"]["abbrev"])

            for abbrev in teams_in_schedule:
                try:
                    # Calculate full season stats (last_n=0)
                    stats = service.get_team_stats(db, abbrev, 0)
                    if stats:
                        cache.set_team_stats(league, abbrev, stats)
                except Exception as e:
                    print(f"Error computing stats for {abbrev}: {e}")

            cache.mark_synced(league)
            print(f"[{datetime.now()}] {league} sync completed: {result}")
            return result

        except Exception as e:
            print(f"[{datetime.now()}] Error syncing {league}: {e}")
            raise
        finally:
            db.close()

    async def sync_all(self, force: bool = False) -> dict:
        """Sync all leagues"""
        results = {}
        for league in ["NHL", "AHL", "LIIGA", "AUSTRIA", "SWISS"]:
            try:
                results[league] = await self.sync_league(league, force)
            except Exception as e:
                results[league] = {"error": str(e)}
        return results

    async def load_team_stats(self, league: str, abbrev: str, last_n: int = 0) -> Optional[dict]:
        """Load stats for a specific team

        Args:
            last_n: Number of last matches. 0 = all season (default, uses cache)
        """
        # Check cache only for full season stats
        if last_n == 0:
            cached = cache.get_team_stats(league, abbrev)
            if cached:
                return cached

        # Load from database
        db = SessionLocal()
        try:
            service = self._get_service(league)
            stats = service.get_team_stats(db, abbrev, last_n)
            # Cache only full season stats
            if stats and last_n == 0:
                cache.set_team_stats(league, abbrev, stats)
            return stats
        finally:
            db.close()

    async def get_schedule_cached(self, league: str) -> list:
        """Get schedule from cache, load if needed"""
        cached = cache.get_schedule(league)
        if cached is not None:
            return cached

        # Load from API
        db = SessionLocal()
        try:
            service = self._get_service(league)
            schedule = await service.get_upcoming_games(db, 7)
            cache.set_schedule(league, schedule)
            return schedule
        finally:
            db.close()

    async def get_teams_cached(self, league: str) -> list:
        """Get teams from cache, load if needed"""
        cached = cache.get_teams(league)
        if cached is not None:
            return cached

        # Load from database
        db = SessionLocal()
        try:
            teams = db.query(Team).filter(Team.league == league).all()
            teams_data = [
                {
                    "abbrev": t.abbrev,
                    "name": t.name,
                    "name_ru": t.name_ru,
                    "logo_url": t.logo_url
                }
                for t in teams
            ]
            cache.set_teams(league, teams_data)
            return teams_data
        finally:
            db.close()

    # Scheduler methods
    async def _scheduler_loop(self):
        """Background task that runs sync at scheduled time"""
        while True:
            try:
                now = datetime.now()
                # Calculate seconds until next 12:00
                target_time = time(12, 0)
                target_datetime = datetime.combine(now.date(), target_time)

                if now.time() >= target_time:
                    # Already past 12:00 today, schedule for tomorrow
                    target_datetime = datetime.combine(
                        now.date().replace(day=now.day + 1),
                        target_time
                    )

                wait_seconds = (target_datetime - now).total_seconds()
                print(f"[{now}] Next scheduled sync at {target_datetime} (in {wait_seconds/3600:.1f} hours)")

                await asyncio.sleep(wait_seconds)

                # Run sync
                print(f"[{datetime.now()}] Running scheduled sync...")
                await self.sync_all(force=True)

            except asyncio.CancelledError:
                print("Scheduler stopped")
                break
            except Exception as e:
                print(f"Scheduler error: {e}")
                # Wait a bit before retrying
                await asyncio.sleep(60)

    def start_scheduler(self):
        """Start the background scheduler"""
        if self._scheduler_task is None or self._scheduler_task.done():
            self._scheduler_task = asyncio.create_task(self._scheduler_loop())
            print("Scheduler started")

    def stop_scheduler(self):
        """Stop the background scheduler"""
        if self._scheduler_task and not self._scheduler_task.done():
            self._scheduler_task.cancel()
            print("Scheduler stopped")

    async def close(self):
        """Cleanup resources"""
        self.stop_scheduler()
        await self.nhl_service.close()
        await self.ahl_service.close()
        await self.liiga_service.close()
        await self.austria_service.close()
        await self.swiss_service.close()


# Global sync service instance
sync_service = SyncService()
