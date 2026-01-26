"""
Cron job to sync KHL, Czech Extraliga, Denmark Metal Ligaen data from API-Sports.
Run once daily via Vercel cron.
"""
from http.server import BaseHTTPRequestHandler
import json
import os
import sys
from datetime import datetime
import httpx

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from app.models.database import SessionLocal, Team, Game, DataUpdate


# API-Sports configuration
API_SPORTS_KEY = os.getenv("API_SPORTS_KEY", "58586d14273e6cff445ae9c658b00a11")
API_SPORTS_BASE_URL = "https://v1.hockey.api-sports.io"
CURRENT_SEASON = 2024

# League configuration
LEAGUES = {
    "KHL": {"id": 35, "names_ru": {
        "Avangard Omsk": "Авангард",
        "Bars Kazan": "Ак Барс",
        "Barys Astana": "Барыс",
        "CSKA Moscow": "ЦСКА",
        "Dinamo Minsk": "Динамо Минск",
        "Dynamo Moscow": "Динамо Москва",
        "Lokomotiv Yaroslavl": "Локомотив",
        "Magnitogorsk": "Металлург Мг",
        "SKA St. Petersburg": "СКА",
        "Spartak Moscow": "Спартак",
        "Traktor": "Трактор",
        "Salavat Yulaev": "Салават Юлаев",
        "Severstal": "Северсталь",
        "Sibir": "Сибирь",
        "Torpedo": "Торпедо",
        "Vityaz": "Витязь",
        "Amur Khabarovsk": "Амур",
        "Admiral Vladivostok": "Адмирал",
        "Avtomobilist": "Автомобилист",
        "Sochi": "Сочи",
        "Lada": "Лада",
        "Neftekhimik": "Нефтехимик",
    }},
    "CZECH": {"id": 10, "names_ru": {
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
        "Karlovy Vary": "Карловы Вары",
        "Vitkovice": "Витковице",
        "Ceske Budejovice": "Ческе-Будеёвице",
        "Olomouc": "Оломоуц",
        "Kladno": "Кладно",
    }},
    "DENMARK": {"id": 12, "names_ru": {
        "Aalborg": "Ольборг Пайретс",
        "Esbjerg": "Эсбьерг",
        "Frederikshavn": "Фредериксхавн",
        "Herning Blue Fox": "Хернинг",
        "Herlev": "Херлев",
        "Odense": "Оденсе",
        "Rodovre Mighty Bulls": "Рёдовре",
        "Rungsted": "Рунгстед",
        "Sonderjyske": "Сённерйюске",
    }},
}


def generate_abbrev(team_name: str) -> str:
    """Generate abbreviation from team name"""
    name = team_name.replace(" HC", "").replace(" HK", "").strip()
    words = name.split()
    if len(words) >= 2:
        return (words[0][:2] + words[1][:1]).upper()
    return name[:3].upper()


async def sync_league(db, league_code: str, league_config: dict) -> dict:
    """Sync a single league from API-Sports"""
    league_id = league_config["id"]
    names_ru = league_config["names_ru"]

    headers = {"x-apisports-key": API_SPORTS_KEY}
    result = {"league": league_code, "teams": 0, "games": 0, "errors": []}

    async with httpx.AsyncClient(timeout=60.0) as client:
        # Get teams
        try:
            response = await client.get(
                f"{API_SPORTS_BASE_URL}/teams",
                params={"league": league_id, "season": CURRENT_SEASON},
                headers=headers
            )
            response.raise_for_status()
            data = response.json()

            if data.get("errors"):
                result["errors"].append(f"Teams API error: {data['errors']}")
                return result

            teams_data = data.get("response", [])

            # Filter out all-star teams
            teams_data = [
                t for t in teams_data
                if t.get("national") is False
                and "Division" not in t.get("name", "")
                and "All Star" not in t.get("name", "")
            ]

            for team_data in teams_data:
                team_api_id = str(team_data["id"])
                team_name = team_data["name"]
                abbrev = generate_abbrev(team_name)

                existing = db.query(Team).filter(
                    Team.league == league_code,
                    Team.team_id == team_api_id
                ).first()

                if existing:
                    existing.name = team_name
                    existing.abbrev = abbrev
                    existing.logo_url = team_data.get("logo")
                    existing.name_ru = names_ru.get(team_name)
                else:
                    team = Team(
                        league=league_code,
                        team_id=team_api_id,
                        abbrev=abbrev,
                        name=team_name,
                        name_ru=names_ru.get(team_name),
                        logo_url=team_data.get("logo")
                    )
                    db.add(team)
                    result["teams"] += 1

            db.commit()

        except Exception as e:
            result["errors"].append(f"Teams sync error: {str(e)}")
            return result

        # Get games
        try:
            response = await client.get(
                f"{API_SPORTS_BASE_URL}/games",
                params={"league": league_id, "season": CURRENT_SEASON},
                headers=headers
            )
            response.raise_for_status()
            data = response.json()

            if data.get("errors"):
                result["errors"].append(f"Games API error: {data['errors']}")
                return result

            games_data = data.get("response", [])

            for game_data in games_data:
                game_api_id = str(game_data["id"])
                game_id = f"{league_code.lower()}_{game_api_id}"

                existing = db.query(Game).filter(Game.game_id == game_id).first()

                home_team_api_id = str(game_data.get("teams", {}).get("home", {}).get("id"))
                away_team_api_id = str(game_data.get("teams", {}).get("away", {}).get("id"))

                home_team = db.query(Team).filter(
                    Team.league == league_code,
                    Team.team_id == home_team_api_id
                ).first()
                away_team = db.query(Team).filter(
                    Team.league == league_code,
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

                scores = game_data.get("scores", {})
                home_score = scores.get("home")
                away_score = scores.get("away")

                status = game_data.get("status", {}).get("short", "")
                is_finished = status == "FT"

                season = f"{CURRENT_SEASON}{CURRENT_SEASON + 1}"

                if existing:
                    existing.home_score = home_score
                    existing.away_score = away_score
                    existing.is_finished = is_finished
                else:
                    game = Game(
                        league=league_code,
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
                    result["games"] += 1

            db.commit()

        except Exception as e:
            result["errors"].append(f"Games sync error: {str(e)}")

    # Log update
    update = DataUpdate(update_type=f"{league_code.lower()}_sync")
    db.add(update)
    db.commit()

    return result


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Sync all API-Sports leagues"""
        if not API_SPORTS_KEY:
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "API_SPORTS_KEY not configured"}).encode())
            return

        try:
            import asyncio
            db = SessionLocal()

            try:
                results = {}
                for league_code, league_config in LEAGUES.items():
                    results[league_code] = asyncio.run(sync_league(db, league_code, league_config))

                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": True,
                    "results": results,
                    "timestamp": datetime.now().isoformat()
                }).encode())

            finally:
                db.close()

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
