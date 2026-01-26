"""
Data service for leagues using API-Sports (KHL, Czech Extraliga, Denmark Metal Ligaen).
Handles syncing data to database and calculating statistics.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session

from ..models.database import Team, Game, DataUpdate
from .api_sports_service import KHLApiService, CzechApiService, DenmarkApiService
from .stats_calculator import StatsCalculator, GameResult


# Russian names for KHL teams
KHL_TEAM_NAMES_RU = {
    "Avangard Omsk": "Авангард",
    "Bars Kazan": "Ак Барс",
    "Barys Astana": "Барыс",
    "CSKA Moscow": "ЦСКА",
    "Dinamo Minsk": "Динамо Минск",
    "Dinamo Moscow": "Динамо Москва",
    "Dinamo Riga": "Динамо Рига",
    "Kunlun Red Star": "Куньлунь Ред Стар",
    "Shanghai Dragons": "Шанхай Драгонс",
    "Lada Togliatti": "Лада",
    "Lokomotiv Yaroslavl": "Локомотив",
    "Magnitogorsk": "Металлург Мг",
    "Metallurg Magnitogorsk": "Металлург Мг",
    "Neftekhimik": "Нефтехимик",
    "Nizhny Novgorod": "Торпедо",
    "Torpedo": "Торпедо",
    "Salavat Yulaev": "Салават Юлаев",
    "Severstal": "Северсталь",
    "Sibir": "Сибирь",
    "SKA St. Petersburg": "СКА",
    "SKA Saint Petersburg": "СКА",
    "Spartak Moscow": "Спартак",
    "Traktor": "Трактор",
    "Vityaz": "Витязь",
    "Amur Khabarovsk": "Амур",
    "Admiral Vladivostok": "Адмирал",
    "Avtomobilist": "Автомобилист",
    "Sochi": "Сочи",
}

# Czech team names in Russian
CZECH_TEAM_NAMES_RU = {
    "Sparta Praha": "Спарта Прага",
    "Trinec": "Тршинец",
    "Pardubice": "Пардубице",
    "Mlada Boleslav": "Млада Болеслав",
    "Liberec": "Либерец",
    "Mountfield HK": "Градец Кралове",
    "Brno": "Брно",
    "Kometa Brno": "Комета Брно",
    "Plzen": "Пльзень",
    "Litvinov": "Литвинов",
    "Energie Karlovy Vary": "Карловы Вары",
    "Karlovy Vary": "Карловы Вары",
    "Vitkovice": "Витковице",
    "Ceske Budejovice": "Ческе-Будеёвице",
    "Motor Ceske Budejovice": "Ческе-Будеёвице",
    "Olomouc": "Оломоуц",
    "Kladno": "Кладно",
}

# Denmark team names in Russian
DENMARK_TEAM_NAMES_RU = {
    "Aalborg Pirates": "Ольборг Пайретс",
    "Esbjerg Energy": "Эсбьерг",
    "Frederikshavn White Hawks": "Фредериксхавн",
    "Herning Blue Fox": "Хернинг",
    "Herlev Eagles": "Херлев",
    "Odense Bulldogs": "Оденсе",
    "Rodovre Mighty Bulls": "Рёдовре",
    "Rungsted Seier Capital": "Рунгстед",
    "Sonderjyske": "Сённерйюске",
}


class ApiSportsDataService:
    """Base data service for API-Sports leagues"""

    LEAGUE = "UNKNOWN"
    TEAM_NAMES_RU = {}

    def __init__(self, api_service):
        self.api = api_service

    def _generate_abbrev(self, team_name: str) -> str:
        """Generate abbreviation from team name"""
        # Remove common suffixes
        name = team_name.replace(" HC", "").replace(" HK", "").strip()
        words = name.split()
        if len(words) >= 2:
            return (words[0][:2] + words[1][:1]).upper()
        return name[:3].upper()

    async def sync_teams(self, db: Session) -> List[Team]:
        """Sync all teams to database"""
        teams_data = await self.api.get_all_teams()
        teams = []

        for team_data in teams_data:
            team_api_id = str(team_data["id"])
            team_name = team_data["name"]
            abbrev = self._generate_abbrev(team_name)

            existing = db.query(Team).filter(
                Team.league == self.LEAGUE,
                Team.team_id == team_api_id
            ).first()

            if existing:
                existing.name = team_name
                existing.abbrev = abbrev
                existing.logo_url = team_data.get("logo")
                existing.name_ru = self.TEAM_NAMES_RU.get(team_name)
                teams.append(existing)
            else:
                team = Team(
                    league=self.LEAGUE,
                    team_id=team_api_id,
                    abbrev=abbrev,
                    name=team_name,
                    name_ru=self.TEAM_NAMES_RU.get(team_name),
                    logo_url=team_data.get("logo")
                )
                db.add(team)
                teams.append(team)

        db.commit()

        # Log update
        update = DataUpdate(update_type=f"{self.LEAGUE.lower()}_teams_sync")
        db.add(update)
        db.commit()

        return teams

    async def sync_all_games(self, db: Session) -> int:
        """Sync all games for the league - ONE request for all games"""
        games_data = await self.api.get_all_games()
        synced_count = 0

        for game_data in games_data:
            game_api_id = str(game_data["id"])
            game_id = f"{self.LEAGUE.lower()}_{game_api_id}"

            existing = db.query(Game).filter(Game.game_id == game_id).first()

            # Get team IDs from API response
            home_team_api_id = str(game_data.get("teams", {}).get("home", {}).get("id"))
            away_team_api_id = str(game_data.get("teams", {}).get("away", {}).get("id"))

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
            game_date_str = game_data.get("date", "")
            try:
                game_date = datetime.fromisoformat(game_date_str.replace("Z", "+00:00"))
            except:
                continue

            # Get scores
            scores = game_data.get("scores", {})
            home_score = scores.get("home")
            away_score = scores.get("away")

            # Check if finished
            status = game_data.get("status", {}).get("short", "")
            is_finished = status == "FT"

            # Get season
            season_year = game_data.get("league", {}).get("season", 2024)
            season = f"{season_year}{season_year + 1}"

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
                    season=season
                )
                db.add(game)
                synced_count += 1

        db.commit()

        # Log update
        update = DataUpdate(update_type=f"{self.LEAGUE.lower()}_games_sync")
        db.add(update)
        db.commit()

        return synced_count

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
        """Get complete stats for a team"""
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
        """Get upcoming games for the next N days"""
        # Get all games and filter upcoming ones
        all_games = await self.api.get_all_games()
        now = datetime.now()
        end_date = now + timedelta(days=days)

        result = []
        for game_data in all_games:
            # Parse date
            game_date_str = game_data.get("date", "")
            try:
                game_date = datetime.fromisoformat(game_date_str.replace("Z", "+00:00"))
            except:
                continue

            # Filter by date range and not finished
            status = game_data.get("status", {}).get("short", "")
            if status == "FT":
                continue

            if not (now <= game_date.replace(tzinfo=None) <= end_date):
                continue

            home_data = game_data.get("teams", {}).get("home", {})
            away_data = game_data.get("teams", {}).get("away", {})

            home_team_api_id = str(home_data.get("id"))
            away_team_api_id = str(away_data.get("id"))

            home_team = db.query(Team).filter(
                Team.league == self.LEAGUE,
                Team.team_id == home_team_api_id
            ).first()
            away_team = db.query(Team).filter(
                Team.league == self.LEAGUE,
                Team.team_id == away_team_api_id
            ).first()

            result.append({
                "game_id": f"{self.LEAGUE.lower()}_{game_data['id']}",
                "date": game_date.strftime("%d.%m.%Y %H:%M"),
                "date_iso": game_date.isoformat(),
                "home_team": {
                    "abbrev": home_team.abbrev if home_team else self._generate_abbrev(home_data.get("name", "")),
                    "name": home_data.get("name", ""),
                    "name_ru": home_team.name_ru if home_team else self.TEAM_NAMES_RU.get(home_data.get("name", "")),
                    "logo_url": home_data.get("logo", "")
                },
                "away_team": {
                    "abbrev": away_team.abbrev if away_team else self._generate_abbrev(away_data.get("name", "")),
                    "name": away_data.get("name", ""),
                    "name_ru": away_team.name_ru if away_team else self.TEAM_NAMES_RU.get(away_data.get("name", "")),
                    "logo_url": away_data.get("logo", "")
                },
                "venue": ""
            })

        return result

    def get_match_analysis(
        self,
        db: Session,
        home_team_abbrev: str,
        away_team_abbrev: str,
        last_n: int = 0
    ) -> dict:
        """Get complete analysis for an upcoming match"""
        home_stats = self.get_team_stats(db, home_team_abbrev, last_n)
        away_stats = self.get_team_stats(db, away_team_abbrev, last_n)

        return {
            "home_team": home_stats,
            "away_team": away_stats
        }

    def get_last_update(self, db: Session) -> Optional[datetime]:
        """Get timestamp of last data update"""
        update = db.query(DataUpdate).filter(
            DataUpdate.update_type.like(f"{self.LEAGUE.lower()}_%")
        ).order_by(DataUpdate.updated_at.desc()).first()
        return update.updated_at if update else None

    async def close(self):
        await self.api.close()


class KHLDataService(ApiSportsDataService):
    """KHL data service"""
    LEAGUE = "KHL"
    TEAM_NAMES_RU = KHL_TEAM_NAMES_RU

    def __init__(self):
        super().__init__(KHLApiService())


class CzechDataService(ApiSportsDataService):
    """Czech Extraliga data service"""
    LEAGUE = "CZECH"
    TEAM_NAMES_RU = CZECH_TEAM_NAMES_RU

    def __init__(self):
        super().__init__(CzechApiService())


class DenmarkDataService(ApiSportsDataService):
    """Denmark Metal Ligaen data service"""
    LEAGUE = "DENMARK"
    TEAM_NAMES_RU = DENMARK_TEAM_NAMES_RU

    def __init__(self):
        super().__init__(DenmarkApiService())
