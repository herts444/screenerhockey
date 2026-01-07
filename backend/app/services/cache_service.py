"""
Cache service for storing precomputed statistics and schedules.
Data is loaded on startup and refreshed on schedule or manual trigger.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import asyncio
from dataclasses import dataclass, field


@dataclass
class CacheEntry:
    data: Any
    updated_at: datetime


class CacheService:
    """In-memory cache for hockey data"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        # Cache storage
        self._teams: Dict[str, List[dict]] = {}  # league -> teams list
        self._schedules: Dict[str, CacheEntry] = {}  # league -> schedule
        self._team_stats: Dict[str, Dict[str, CacheEntry]] = {}  # league -> {abbrev -> stats}
        self._last_sync: Dict[str, datetime] = {}  # league -> last sync time

        # Lock for thread safety
        self._lock = asyncio.Lock()

    @property
    def is_loaded(self) -> Dict[str, bool]:
        """Check if data is loaded for each league"""
        return {
            "NHL": "NHL" in self._teams and len(self._teams.get("NHL", [])) > 0,
            "AHL": "AHL" in self._teams and len(self._teams.get("AHL", [])) > 0
        }

    def get_last_sync(self, league: str) -> Optional[datetime]:
        """Get last sync time for a league"""
        return self._last_sync.get(league)

    # Teams cache
    def set_teams(self, league: str, teams: List[dict]):
        """Cache teams list"""
        self._teams[league] = teams

    def get_teams(self, league: str) -> Optional[List[dict]]:
        """Get cached teams"""
        return self._teams.get(league)

    # Schedule cache
    def set_schedule(self, league: str, games: List[dict]):
        """Cache schedule"""
        self._schedules[league] = CacheEntry(data=games, updated_at=datetime.now())

    def get_schedule(self, league: str) -> Optional[List[dict]]:
        """Get cached schedule"""
        entry = self._schedules.get(league)
        return entry.data if entry else None

    # Team stats cache
    def set_team_stats(self, league: str, abbrev: str, stats: dict):
        """Cache team statistics"""
        if league not in self._team_stats:
            self._team_stats[league] = {}
        self._team_stats[league][abbrev] = CacheEntry(data=stats, updated_at=datetime.now())

    def get_team_stats(self, league: str, abbrev: str) -> Optional[dict]:
        """Get cached team stats"""
        league_stats = self._team_stats.get(league, {})
        entry = league_stats.get(abbrev)
        return entry.data if entry else None

    def get_all_team_stats(self, league: str) -> Dict[str, dict]:
        """Get all cached team stats for a league"""
        league_stats = self._team_stats.get(league, {})
        return {abbrev: entry.data for abbrev, entry in league_stats.items()}

    # Sync tracking
    def mark_synced(self, league: str):
        """Mark league as synced"""
        self._last_sync[league] = datetime.now()

    def needs_sync(self, league: str, max_age_hours: int = 12) -> bool:
        """Check if league needs sync"""
        last_sync = self._last_sync.get(league)
        if not last_sync:
            return True
        return datetime.now() - last_sync > timedelta(hours=max_age_hours)

    # Clear cache
    def clear_league(self, league: str):
        """Clear all cache for a league"""
        self._teams.pop(league, None)
        self._schedules.pop(league, None)
        self._team_stats.pop(league, None)
        self._last_sync.pop(league, None)

    def clear_all(self):
        """Clear entire cache"""
        self._teams.clear()
        self._schedules.clear()
        self._team_stats.clear()
        self._last_sync.clear()


# Global cache instance
cache = CacheService()
