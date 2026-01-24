"""
Data service for Swiss National League (SIHF).
"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session

from ..models.database import Team, Game, DataUpdate
from .swiss_api import SwissApiService, SWISS_TEAM_NAMES_RU
from .stats_calculator import StatsCalculator, GameResult


class SwissDataService:
    """Service for managing Swiss NL data and calculating statistics"""

    LEAGUE = "SWISS"

    def __init__(self):
        self.api = SwissApiService()

    async def sync_teams(self, db: Session) -> List[Team]:
        """Sync all Swiss NL teams to database"""
        teams_data = await self.api.get_teams()
        teams = []

        for team_data in teams_data:
            team_id = team_data["id"]
            abbrev = team_data["abbrev"]

            existing = db.query(Team).filter(
                Team.league == self.LEAGUE,
                Team.team_id == team_id
            ).first()

            if existing:
                existing.abbrev = abbrev
                existing.name = team_data["name"]
                existing.logo_url = team_data.get("logo_url")
                existing.name_ru = SWISS_TEAM_NAMES_RU.get(abbrev)
                teams.append(existing)
            else:
                team = Team(
                    league=self.LEAGUE,
                    team_id=team_id,
                    abbrev=abbrev,
                    name=team_data["name"],
                    name_ru=SWISS_TEAM_NAMES_RU.get(abbrev),
                    logo_url=team_data.get("logo_url")
                )
                db.add(team)
                teams.append(team)

        db.commit()

        # Log update
        update = DataUpdate(update_type="swiss_teams_sync")
        db.add(update)
        db.commit()

        return teams

    async def sync_team_games(self, db: Session, team_id: str) -> int:
        """Sync all games for a specific Swiss NL team"""
        games_data = await self.api.get_team_game_log(team_id)
        synced_count = 0

        for game_data in games_data:
            game_id = f"swiss_{game_data.get('id')}"
            existing = db.query(Game).filter(Game.game_id == game_id).first()

            home_team_api_id = str(game_data.get("home", {}).get("id", ""))
            away_team_api_id = str(game_data.get("away", {}).get("id", ""))

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

            # Parse date (format: "DD.MM.YYYY")
            game_date_str = game_data.get("date", "")
            try:
                game_date = datetime.strptime(game_date_str, "%d.%m.%Y")
            except ValueError:
                continue

            home_score = game_data.get("home_score") or 0
            away_score = game_data.get("away_score") or 0
            is_finished = game_data.get("is_finished", False)

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
        """Sync games for all Swiss NL teams"""
        teams = db.query(Team).filter(Team.league == self.LEAGUE).all()
        total_synced = 0

        for team in teams:
            try:
                synced = await self.sync_team_games(db, team.team_id)
                total_synced += synced
            except Exception as e:
                print(f"Error syncing Swiss team {team.abbrev}: {e}")

        # Log update
        update = DataUpdate(update_type="swiss_games_sync")
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
        """Get matches for a team with optional home/away filter"""
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
        """Get complete stats for a Swiss NL team"""
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
        """Get upcoming Swiss NL games for the next N days"""
        games = await self.api.get_schedule_week()

        result = []
        seen_game_ids = set()

        for game in games:
            game_id = game.get("id")
            if game_id in seen_game_ids:
                continue
            seen_game_ids.add(game_id)

            if game.get("gameState") == "FINAL":
                continue

            home_data = game.get("homeTeam", {})
            away_data = game.get("awayTeam", {})

            home_abbrev = home_data.get("abbrev", "")
            away_abbrev = away_data.get("abbrev", "")

            home_team = db.query(Team).filter(
                Team.league == self.LEAGUE,
                Team.abbrev == home_abbrev
            ).first()

            away_team = db.query(Team).filter(
                Team.league == self.LEAGUE,
                Team.abbrev == away_abbrev
            ).first()

            game_date_str = game.get("startTimeUTC", "")
            try:
                game_date = datetime.fromisoformat(game_date_str)
            except (ValueError, TypeError):
                game_date = None

            result.append({
                "game_id": f"swiss_{game_id}",
                "date": game_date.strftime("%d.%m.%Y %H:%M") if game_date else "",
                "date_iso": game_date.isoformat() if game_date else "",
                "home_team": {
                    "abbrev": home_abbrev,
                    "name": home_data.get("name", home_abbrev),
                    "name_ru": home_team.name_ru if home_team else SWISS_TEAM_NAMES_RU.get(home_abbrev),
                    "logo_url": home_team.logo_url if home_team else None
                },
                "away_team": {
                    "abbrev": away_abbrev,
                    "name": away_data.get("name", away_abbrev),
                    "name_ru": away_team.name_ru if away_team else SWISS_TEAM_NAMES_RU.get(away_abbrev),
                    "logo_url": away_team.logo_url if away_team else None
                },
                "venue": game.get("venue", "")
            })

        return result

    def get_match_analysis(
        self,
        db: Session,
        home_team_abbrev: str,
        away_team_abbrev: str,
        last_n: int = 0
    ) -> dict:
        """Get complete analysis for an upcoming Swiss NL match"""
        home_stats = self.get_team_stats(db, home_team_abbrev, last_n)
        away_stats = self.get_team_stats(db, away_team_abbrev, last_n)

        return {
            "home_team": home_stats,
            "away_team": away_stats
        }

    async def close(self):
        await self.api.close()
