from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session

from ..models.database import Team, Game, DataUpdate
from .ahl_api import AHLApiService, AHL_TEAM_NAMES_RU
from .stats_calculator import StatsCalculator, GameResult


def get_last_ahl_update(db: Session) -> Optional[datetime]:
    """Get timestamp of last AHL data update"""
    update = db.query(DataUpdate).filter(
        DataUpdate.update_type.like("ahl_%")
    ).order_by(DataUpdate.updated_at.desc()).first()
    return update.updated_at if update else None


class AHLDataService:
    """Service for managing AHL data and calculating statistics"""

    LEAGUE = "AHL"

    def __init__(self):
        self.api = AHLApiService()

    async def sync_teams(self, db: Session) -> List[Team]:
        """Sync all AHL teams to database"""
        teams_data = await self.api.get_teams()
        teams = []

        for team_data in teams_data:
            abbrev = team_data["abbrev"]
            team_id = team_data["id"]

            existing = db.query(Team).filter(
                Team.league == self.LEAGUE,
                Team.team_id == team_id
            ).first()

            if existing:
                existing.abbrev = abbrev
                existing.name = team_data["name"]
                existing.logo_url = team_data.get("logo_url")
                existing.name_ru = AHL_TEAM_NAMES_RU.get(abbrev)
                teams.append(existing)
            else:
                team = Team(
                    league=self.LEAGUE,
                    team_id=team_id,
                    abbrev=abbrev,
                    name=team_data["name"],
                    name_ru=AHL_TEAM_NAMES_RU.get(abbrev),
                    logo_url=team_data.get("logo_url")
                )
                db.add(team)
                teams.append(team)

        db.commit()

        # Log update
        update = DataUpdate(update_type="ahl_teams_sync")
        db.add(update)
        db.commit()

        return teams

    async def sync_team_games(self, db: Session, team_id: str) -> int:
        """Sync all games for a specific AHL team"""
        games_data = await self.api.get_team_game_log(team_id)
        synced_count = 0

        for game_data in games_data:
            game_id = f"ahl_{game_data.get('game_id')}"
            existing = db.query(Game).filter(Game.game_id == game_id).first()

            home_team_api_id = game_data.get("home_team")
            away_team_api_id = game_data.get("visiting_team")

            home_team = db.query(Team).filter(
                Team.league == self.LEAGUE,
                Team.team_id == home_team_api_id
            ).first()
            away_team = db.query(Team).filter(
                Team.league == self.LEAGUE,
                Team.team_id == away_team_api_id
            ).first()

            if not home_team or not away_team:
                continue

            # Parse date
            game_date_str = game_data.get("date_played")
            try:
                game_date = datetime.strptime(game_date_str, "%Y-%m-%d")
            except:
                continue

            home_score = int(game_data.get("home_goal_count", 0) or 0)
            away_score = int(game_data.get("visiting_goal_count", 0) or 0)
            is_finished = game_data.get("game_status") == "Final" or game_data.get("final") == "1"

            if existing:
                existing.home_score = home_score
                existing.away_score = away_score
                existing.is_finished = is_finished
            else:
                game = Game(
                    league=self.LEAGUE,
                    game_id=game_id,
                    date=game_date,
                    home_team_id=home_team.id,
                    away_team_id=away_team.id,
                    home_score=home_score,
                    away_score=away_score,
                    is_finished=is_finished,
                    season="20252026"
                )
                db.add(game)
                synced_count += 1

        db.commit()
        return synced_count

    async def sync_all_games(self, db: Session) -> int:
        """Sync games for all AHL teams"""
        teams = db.query(Team).filter(Team.league == self.LEAGUE).all()
        total_synced = 0

        for team in teams:
            try:
                synced = await self.sync_team_games(db, team.team_id)
                total_synced += synced
            except Exception as e:
                print(f"Error syncing AHL team {team.abbrev}: {e}")

        # Log update
        update = DataUpdate(update_type="ahl_games_sync")
        db.add(update)
        db.commit()

        return total_synced

    def get_team_matches(
        self,
        db: Session,
        team_id: int,
        last_n: int = 0,
        is_home: Optional[bool] = None
    ) -> List[GameResult]:
        """Get matches for a team with optional home/away filter

        Args:
            last_n: Number of last matches to return. 0 = all season matches (default)
        """
        team = db.query(Team).filter(Team.id == team_id).first()
        if not team:
            return []

        # Build query
        if is_home is True:
            games_query = db.query(Game).filter(
                Game.league == self.LEAGUE,
                Game.home_team_id == team.id,
                Game.is_finished == True
            )
        elif is_home is False:
            games_query = db.query(Game).filter(
                Game.league == self.LEAGUE,
                Game.away_team_id == team.id,
                Game.is_finished == True
            )
        else:
            games_query = db.query(Game).filter(
                Game.league == self.LEAGUE,
                ((Game.home_team_id == team.id) | (Game.away_team_id == team.id)),
                Game.is_finished == True
            )

        games_query = games_query.order_by(Game.date.desc())

        # Apply limit only if last_n > 0
        if last_n > 0:
            games = games_query.limit(last_n).all()
        else:
            games = games_query.all()

        results = []
        for game in games:
            is_home_game = game.home_team_id == team.id

            if is_home_game:
                team_score = game.home_score
                opponent_score = game.away_score
                opponent = game.away_team
            else:
                team_score = game.away_score
                opponent_score = game.home_score
                opponent = game.home_team

            results.append(GameResult(
                game_id=game.game_id,
                date=game.date,
                opponent=opponent.name_ru or opponent.name,
                opponent_abbrev=opponent.abbrev,
                is_home=is_home_game,
                team_score=team_score or 0,
                opponent_score=opponent_score or 0,
                total_goals=(team_score or 0) + (opponent_score or 0)
            ))

        return results

    def get_team_stats(self, db: Session, team_abbrev: str, last_n: int = 0) -> dict:
        """Get complete stats for an AHL team

        Args:
            last_n: Number of last matches to analyze. 0 = all season (default)
        """
        team = db.query(Team).filter(
            Team.league == self.LEAGUE,
            Team.abbrev == team_abbrev
        ).first()

        if not team:
            return {}

        home_matches = self.get_team_matches(db, team.id, last_n, is_home=True)
        away_matches = self.get_team_matches(db, team.id, last_n, is_home=False)

        stats = StatsCalculator.get_full_team_stats(home_matches, away_matches)

        return {
            "team": {
                "abbrev": team.abbrev,
                "name": team.name,
                "name_ru": team.name_ru,
                "logo_url": team.logo_url
            },
            "stats": stats
        }

    async def get_upcoming_games(self, db: Session, days: int = 7) -> List[dict]:
        """Get upcoming AHL games for the next N days"""
        games = await self.api.get_schedule_week()

        result = []
        seen_game_ids = set()

        for game in games:
            game_id = game.get("game_id")
            if game_id in seen_game_ids:
                continue
            seen_game_ids.add(game_id)

            # Skip finished games
            if game.get("game_status") == "Final" or game.get("final") == "1":
                continue

            home_abbrev = game.get("home_team_code")
            away_abbrev = game.get("visiting_team_code")

            home_team = db.query(Team).filter(
                Team.league == self.LEAGUE,
                Team.team_id == game.get("home_team")
            ).first()

            away_team = db.query(Team).filter(
                Team.league == self.LEAGUE,
                Team.team_id == game.get("visiting_team")
            ).first()

            game_date_str = game.get("GameDateISO8601", "")
            try:
                game_date = datetime.fromisoformat(game_date_str.replace("Z", "+00:00"))
            except:
                game_date_str = game.get("date_played", "")
                try:
                    game_date = datetime.strptime(game_date_str, "%Y-%m-%d")
                except:
                    game_date = None

            result.append({
                "game_id": f"ahl_{game_id}",
                "date": game_date.strftime("%d.%m.%Y %H:%M") if game_date else "",
                "date_iso": game_date.isoformat() if game_date else "",
                "home_team": {
                    "abbrev": home_abbrev,
                    "name": game.get("home_team_name", home_abbrev),
                    "name_ru": home_team.name_ru if home_team else game.get("home_team_name"),
                    "logo_url": home_team.logo_url if home_team else f"https://assets.leaguestat.com/ahl/logos/{game.get('home_team')}.png"
                },
                "away_team": {
                    "abbrev": away_abbrev,
                    "name": game.get("visiting_team_name", away_abbrev),
                    "name_ru": away_team.name_ru if away_team else game.get("visiting_team_name"),
                    "logo_url": away_team.logo_url if away_team else f"https://assets.leaguestat.com/ahl/logos/{game.get('visiting_team')}.png"
                },
                "venue": game.get("venue_name", "")
            })

        return result

    def get_match_analysis(
        self,
        db: Session,
        home_team_abbrev: str,
        away_team_abbrev: str,
        last_n: int = 0
    ) -> dict:
        """Get complete analysis for an upcoming AHL match

        Args:
            last_n: Number of last matches to analyze. 0 = all season (default)
        """
        home_stats = self.get_team_stats(db, home_team_abbrev, last_n)
        away_stats = self.get_team_stats(db, away_team_abbrev, last_n)

        return {
            "home_team": home_stats,
            "away_team": away_stats
        }

    def get_last_update(self, db: Session) -> Optional[datetime]:
        """Get timestamp of last AHL data update"""
        return get_last_ahl_update(db)

    async def close(self):
        await self.api.close()
