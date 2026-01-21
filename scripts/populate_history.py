"""
Script to populate prediction history with real NHL matches from January 19, 2025
"""
import asyncio
import httpx
import os
import sys
from datetime import datetime

# Database URL
DATABASE_URL = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set")
    sys.exit(1)

print(f"Connecting to database...")

from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# Models
class Team(Base):
    __tablename__ = "teams"
    id = Column(Integer, primary_key=True)
    league = Column(String(50))
    abbrev = Column(String(10))
    name = Column(String(100))
    name_ru = Column(String(100))
    logo_url = Column(String(500))

class Game(Base):
    __tablename__ = "games"
    id = Column(Integer, primary_key=True)
    league = Column(String(50))
    game_id = Column(String(100), unique=True)
    date = Column(DateTime)
    home_team_id = Column(Integer, ForeignKey("teams.id"))
    away_team_id = Column(Integer, ForeignKey("teams.id"))
    home_score = Column(Integer)
    away_score = Column(Integer)
    is_finished = Column(Boolean, default=False)
    season = Column(String(20))
    home_team = relationship("Team", foreign_keys=[home_team_id])
    away_team = relationship("Team", foreign_keys=[away_team_id])

class ValueBetPrediction(Base):
    __tablename__ = "value_bet_predictions"
    id = Column(Integer, primary_key=True)
    event_id = Column(String(100))
    league = Column(String(50))
    scheduled = Column(DateTime)
    home_team = Column(String(100))
    home_abbrev = Column(String(10))
    away_team = Column(String(100))
    away_abbrev = Column(String(10))
    bet_type = Column(String(50))
    bet_label = Column(String(100))
    line = Column(Float)
    odds = Column(Float)
    probability = Column(Float)
    fair_odds = Column(Float)
    value_percentage = Column(Float)
    is_checked = Column(Boolean, default=False)
    is_won = Column(Boolean)
    actual_result = Column(String(20))
    checked_at = Column(DateTime)

# Create tables
Base.metadata.create_all(engine)
print("Tables created.")

TEAM_NAMES_RU = {
    "ANA": "Анахайм Дакс", "BOS": "Бостон Брюинз", "BUF": "Баффало Сейбрз",
    "CGY": "Калгари Флэймз", "CAR": "Каролина Харрикейнз", "CHI": "Чикаго Блэкхокс",
    "COL": "Колорадо Эвеланш", "CBJ": "Коламбус Блю Джекетс", "DAL": "Даллас Старз",
    "DET": "Детройт Ред Уингз", "EDM": "Эдмонтон Ойлерз", "FLA": "Флорида Пантерз",
    "LAK": "Лос-Анджелес Кингз", "MIN": "Миннесота Уайлд", "MTL": "Монреаль Канадиенс",
    "NSH": "Нэшвилл Предаторз", "NJD": "Нью-Джерси Девилз", "NYI": "Нью-Йорк Айлендерс",
    "NYR": "Нью-Йорк Рейнджерс", "OTT": "Оттава Сенаторз", "PHI": "Филадельфия Флайерз",
    "PIT": "Питтсбург Пингвинз", "SJS": "Сан-Хосе Шаркс", "SEA": "Сиэтл Кракен",
    "STL": "Сент-Луис Блюз", "TBL": "Тампа-Бэй Лайтнинг", "TOR": "Торонто Мейпл Лифс",
    "UTA": "Юта Хоккей Клаб", "VAN": "Ванкувер Кэнакс", "VGK": "Вегас Голден Найтс",
    "WSH": "Вашингтон Кэпиталз", "WPG": "Виннипег Джетс"
}

TYPICAL_ODDS = {
    2.5: {"over": 1.95, "under": 1.85},
    3.5: {"over": 2.45, "under": 1.55},
}

MIN_VALUE = 50
MIN_ODDS = 1.80


async def fetch_team_schedule(client, team_abbrev: str):
    url = f"https://api-web.nhle.com/v1/club-schedule-season/{team_abbrev}/20242025"
    resp = await client.get(url)
    return resp.json()


async def fetch_all_teams(client):
    # Use hardcoded list of NHL teams
    teams = [
        {"abbrev": "ANA", "name": "Anaheim Ducks"},
        {"abbrev": "BOS", "name": "Boston Bruins"},
        {"abbrev": "BUF", "name": "Buffalo Sabres"},
        {"abbrev": "CGY", "name": "Calgary Flames"},
        {"abbrev": "CAR", "name": "Carolina Hurricanes"},
        {"abbrev": "CHI", "name": "Chicago Blackhawks"},
        {"abbrev": "COL", "name": "Colorado Avalanche"},
        {"abbrev": "CBJ", "name": "Columbus Blue Jackets"},
        {"abbrev": "DAL", "name": "Dallas Stars"},
        {"abbrev": "DET", "name": "Detroit Red Wings"},
        {"abbrev": "EDM", "name": "Edmonton Oilers"},
        {"abbrev": "FLA", "name": "Florida Panthers"},
        {"abbrev": "LAK", "name": "Los Angeles Kings"},
        {"abbrev": "MIN", "name": "Minnesota Wild"},
        {"abbrev": "MTL", "name": "Montreal Canadiens"},
        {"abbrev": "NSH", "name": "Nashville Predators"},
        {"abbrev": "NJD", "name": "New Jersey Devils"},
        {"abbrev": "NYI", "name": "New York Islanders"},
        {"abbrev": "NYR", "name": "New York Rangers"},
        {"abbrev": "OTT", "name": "Ottawa Senators"},
        {"abbrev": "PHI", "name": "Philadelphia Flyers"},
        {"abbrev": "PIT", "name": "Pittsburgh Penguins"},
        {"abbrev": "SJS", "name": "San Jose Sharks"},
        {"abbrev": "SEA", "name": "Seattle Kraken"},
        {"abbrev": "STL", "name": "St. Louis Blues"},
        {"abbrev": "TBL", "name": "Tampa Bay Lightning"},
        {"abbrev": "TOR", "name": "Toronto Maple Leafs"},
        {"abbrev": "UTA", "name": "Utah Hockey Club"},
        {"abbrev": "VAN", "name": "Vancouver Canucks"},
        {"abbrev": "VGK", "name": "Vegas Golden Knights"},
        {"abbrev": "WSH", "name": "Washington Capitals"},
        {"abbrev": "WPG", "name": "Winnipeg Jets"},
    ]
    return teams


def calculate_home_stats(games, team_abbrev, before_date):
    """Calculate home stats for team before date"""
    results = []
    for g in games:
        if g.get("gameState") not in ["OFF", "FINAL"]:
            continue
        try:
            game_date = datetime.strptime(g.get("gameDate", ""), "%Y-%m-%d")
        except:
            continue
        if game_date >= before_date:
            continue

        home_abbrev = g.get("homeTeam", {}).get("abbrev")
        if home_abbrev != team_abbrev:
            continue

        home_score = g.get("homeTeam", {}).get("score", 0) or 0
        away_score = g.get("awayTeam", {}).get("score", 0) or 0
        results.append({"team_score": home_score, "total": home_score + away_score})

    return results


def calculate_away_stats(games, team_abbrev, before_date):
    """Calculate away stats for team before date"""
    results = []
    for g in games:
        if g.get("gameState") not in ["OFF", "FINAL"]:
            continue
        try:
            game_date = datetime.strptime(g.get("gameDate", ""), "%Y-%m-%d")
        except:
            continue
        if game_date >= before_date:
            continue

        away_abbrev = g.get("awayTeam", {}).get("abbrev")
        if away_abbrev != team_abbrev:
            continue

        away_score = g.get("awayTeam", {}).get("score", 0) or 0
        home_score = g.get("homeTeam", {}).get("score", 0) or 0
        results.append({"team_score": away_score, "total": home_score + away_score})

    return results


def generate_prediction(game_date, home_abbrev, away_abbrev, home_stats, away_stats, event_id):
    """Generate best value bet"""
    predictions = []
    home_name = TEAM_NAMES_RU.get(home_abbrev, home_abbrev)
    away_name = TEAM_NAMES_RU.get(away_abbrev, away_abbrev)

    for line, odds in TYPICAL_ODDS.items():
        threshold = int(line + 0.5)

        # Home team individual over
        if home_stats:
            count = sum(1 for m in home_stats if m["team_score"] >= threshold)
            prob = count / len(home_stats)
            if prob > 0 and odds["over"] >= MIN_ODDS:
                fair = 1 / prob
                value = ((odds["over"] - fair) / fair) * 100
                if value >= MIN_VALUE:
                    predictions.append({
                        "bet_type": "home-it-over",
                        "bet_label": f"ИТБ {home_name}",
                        "line": line,
                        "odds": odds["over"],
                        "probability": prob,
                        "fair_odds": fair,
                        "value": value
                    })

        # Away team individual over
        if away_stats:
            count = sum(1 for m in away_stats if m["team_score"] >= threshold)
            prob = count / len(away_stats)
            if prob > 0 and odds["over"] >= MIN_ODDS:
                fair = 1 / prob
                value = ((odds["over"] - fair) / fair) * 100
                if value >= MIN_VALUE:
                    predictions.append({
                        "bet_type": "away-it-over",
                        "bet_label": f"ИТБ {away_name}",
                        "line": line,
                        "odds": odds["over"],
                        "probability": prob,
                        "fair_odds": fair,
                        "value": value
                    })

    if predictions:
        predictions.sort(key=lambda x: x["value"], reverse=True)
        best = predictions[0]
        return {
            "event_id": event_id,
            "scheduled": game_date,
            "home_team": home_name,
            "home_abbrev": home_abbrev,
            "away_team": away_name,
            "away_abbrev": away_abbrev,
            **best
        }
    return None


def check_result(pred, home_score, away_score):
    bet_type = pred["bet_type"]
    line = pred["line"]

    if 'home-it-over' in bet_type:
        return home_score > line
    elif 'away-it-over' in bet_type:
        return away_score > line
    return None


async def main():
    db = SessionLocal()

    async with httpx.AsyncClient(timeout=30.0) as client:
        print("Fetching NHL teams...")
        teams_data = await fetch_all_teams(client)
        print(f"Found {len(teams_data)} teams")

        # Sync teams to DB
        for t in teams_data:
            existing = db.query(Team).filter(Team.league == "NHL", Team.abbrev == t["abbrev"]).first()
            if not existing:
                team = Team(
                    league="NHL", abbrev=t["abbrev"], name=t["name"],
                    name_ru=TEAM_NAMES_RU.get(t["abbrev"]), logo_url=t.get("logo")
                )
                db.add(team)
        db.commit()

        # Fetch schedules
        print("Fetching team schedules...")
        team_schedules = {}
        for t in teams_data:
            try:
                schedule = await fetch_team_schedule(client, t["abbrev"])
                team_schedules[t["abbrev"]] = schedule.get("games", [])
                print(f"  {t['abbrev']}: {len(team_schedules[t['abbrev']])} games")
            except Exception as e:
                print(f"  {t['abbrev']}: error - {e}")

        # Process games from Jan 19
        print("\nProcessing games from Jan 19, 2025...")
        start_date = datetime(2025, 1, 19)
        end_date = datetime.now()

        processed = set()
        added = 0
        won = 0
        lost = 0

        for abbrev, games in team_schedules.items():
            for g in games:
                if g.get("gameState") not in ["OFF", "FINAL"]:
                    continue

                game_id = str(g.get("id"))
                if game_id in processed:
                    continue

                try:
                    game_date = datetime.strptime(g.get("gameDate", ""), "%Y-%m-%d")
                except:
                    continue

                if game_date < start_date or game_date > end_date:
                    continue

                processed.add(game_id)

                home_abbrev = g.get("homeTeam", {}).get("abbrev")
                away_abbrev = g.get("awayTeam", {}).get("abbrev")
                home_score = g.get("homeTeam", {}).get("score", 0) or 0
                away_score = g.get("awayTeam", {}).get("score", 0) or 0

                # Get stats before this game
                home_games = team_schedules.get(home_abbrev, [])
                away_games = team_schedules.get(away_abbrev, [])

                home_stats = calculate_home_stats(home_games, home_abbrev, game_date)
                away_stats = calculate_away_stats(away_games, away_abbrev, game_date)

                if len(home_stats) < 5 or len(away_stats) < 5:
                    continue

                pred = generate_prediction(game_date, home_abbrev, away_abbrev, home_stats, away_stats, f"nhl_{game_id}")

                if not pred:
                    continue

                # Check if exists
                existing = db.query(ValueBetPrediction).filter(
                    ValueBetPrediction.event_id == pred["event_id"]
                ).first()

                if existing:
                    continue

                is_won = check_result(pred, home_score, away_score)

                db_pred = ValueBetPrediction(
                    event_id=pred["event_id"],
                    league="NHL",
                    scheduled=pred["scheduled"],
                    home_team=pred["home_team"],
                    home_abbrev=pred["home_abbrev"],
                    away_team=pred["away_team"],
                    away_abbrev=pred["away_abbrev"],
                    bet_type=pred["bet_type"],
                    bet_label=pred["bet_label"],
                    line=pred["line"],
                    odds=pred["odds"],
                    probability=pred["probability"],
                    fair_odds=pred["fair_odds"],
                    value_percentage=pred["value"],
                    is_checked=True,
                    is_won=is_won,
                    actual_result=f"{home_score}-{away_score}",
                    checked_at=datetime.now()
                )
                db.add(db_pred)
                added += 1

                status = "WON" if is_won else "LOST"
                if is_won:
                    won += 1
                else:
                    lost += 1

                print(f"  {game_date.strftime('%m/%d')} {home_abbrev} vs {away_abbrev}: {pred['bet_label']} ({pred['line']}) - {status}")

        db.commit()

        print(f"\n=== SUMMARY ===")
        print(f"Total predictions: {added}")
        print(f"Won: {won}")
        print(f"Lost: {lost}")
        if added > 0:
            print(f"Win rate: {(won / added * 100):.1f}%")

    db.close()


if __name__ == "__main__":
    asyncio.run(main())
