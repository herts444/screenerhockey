from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from ..models.database import get_db, Team
from ..services.cache_service import cache
from ..services.sync_service import sync_service

router = APIRouter()


@router.get("/teams")
async def get_teams(
    league: str = Query("NHL", description="League: NHL or AHL")
):
    """Get all teams for a league (from cache)"""
    league_upper = league.upper()

    # Try cache first
    teams = await sync_service.get_teams_cached(league_upper)
    return teams


@router.get("/teams/{team_abbrev}/stats")
async def get_team_stats(
    team_abbrev: str,
    league: str = Query("NHL", description="League: NHL or AHL"),
    last_n: int = Query(0, ge=0, le=100, description="Number of last matches to analyze. 0 = full season (default)")
):
    """Get statistics for a specific team (from cache or computed on demand)"""
    league_upper = league.upper()

    # For default (full season), try cache first
    if last_n == 0:
        stats = cache.get_team_stats(league_upper, team_abbrev.upper())
        if stats:
            return stats

    # Load fresh stats with specific last_n
    stats = await sync_service.load_team_stats(league_upper, team_abbrev.upper(), last_n)
    if not stats:
        raise HTTPException(status_code=404, detail="Team not found")
    return stats


@router.get("/schedule/upcoming")
async def get_upcoming_games(
    league: str = Query("NHL", description="League: NHL or AHL"),
    days: int = Query(7, ge=1, le=14, description="Number of days ahead")
):
    """Get upcoming games (from cache)"""
    league_upper = league.upper()

    # Get from cache
    games = await sync_service.get_schedule_cached(league_upper)
    return {"games": games, "league": league_upper}


@router.get("/match/analysis")
async def get_match_analysis(
    home_team: str = Query(..., description="Home team abbreviation"),
    away_team: str = Query(..., description="Away team abbreviation"),
    league: str = Query("NHL", description="League: NHL or AHL"),
    last_n: int = Query(0, ge=0, le=100, description="Number of last matches to analyze. 0 = full season (default)")
):
    """Get complete analysis for an upcoming match"""
    league_upper = league.upper()

    # Load stats with specified last_n (sync_service handles caching for full season)
    home_stats = await sync_service.load_team_stats(league_upper, home_team.upper(), last_n)
    away_stats = await sync_service.load_team_stats(league_upper, away_team.upper(), last_n)

    if not home_stats or not away_stats:
        raise HTTPException(status_code=404, detail="One or both teams not found")

    return {
        "home_team": home_stats,
        "away_team": away_stats
    }


@router.post("/sync/teams")
async def sync_teams(
    league: str = Query("NHL", description="League: NHL or AHL")
):
    """Force sync teams from API"""
    league_upper = league.upper()
    try:
        result = await sync_service.sync_league(league_upper, force=True)
        return {
            "synced": result.get("teams", 0),
            "league": league_upper,
            "message": f"{league_upper} teams synced successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/games")
async def sync_games(
    league: str = Query("NHL", description="League: NHL or AHL"),
    season: str = Query("20242025", description="Season in format YYYYYYYY")
):
    """Force sync games - actually syncs everything for the league"""
    league_upper = league.upper()
    try:
        result = await sync_service.sync_league(league_upper, force=True)
        return {
            "synced": result.get("games", 0),
            "league": league_upper,
            "message": f"Games synced successfully for {league_upper}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/all")
async def sync_all():
    """Force sync all leagues"""
    try:
        results = await sync_service.sync_all(force=True)
        return {
            "results": results,
            "message": "All leagues synced"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_status(
    league: str = Query("NHL", description="League: NHL or AHL")
):
    """Get system status and cache info"""
    league_upper = league.upper()

    last_sync = cache.get_last_sync(league_upper)
    is_loaded = cache.is_loaded

    # Get teams count from cache
    teams = cache.get_teams(league_upper)
    teams_count = len(teams) if teams else 0

    return {
        "status": "ok",
        "league": league_upper,
        "teams_count": teams_count,
        "last_update": last_sync.isoformat() if last_sync else None,
        "cache_loaded": is_loaded
    }


@router.get("/leagues")
async def get_leagues():
    """Get list of available leagues with their cache status"""
    return {
        "leagues": [
            {
                "code": "NHL",
                "name": "NHL",
                "name_ru": "НХЛ",
                "cached": cache.is_loaded.get("NHL", False)
            },
            {
                "code": "AHL",
                "name": "AHL",
                "name_ru": "АХЛ",
                "cached": cache.is_loaded.get("AHL", False)
            },
            {
                "code": "LIIGA",
                "name": "Liiga",
                "name_ru": "Лиига (Финляндия)",
                "cached": cache.is_loaded.get("LIIGA", False)
            }
        ]
    }
