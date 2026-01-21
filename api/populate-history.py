"""API endpoint to populate prediction history with real NHL matches"""
from http.server import BaseHTTPRequestHandler
import json
import httpx
import os
import sys
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

TYPICAL_ODDS = {
    "home_it_over": {
        2.5: {"over": 1.95, "under": 1.85},
        3.5: {"over": 2.45, "under": 1.55},
    },
    "away_it_over": {
        2.5: {"over": 2.10, "under": 1.75},
        3.5: {"over": 2.85, "under": 1.42},
    },
    "match_total": {
        5.5: {"over": 1.92, "under": 1.88},
        6.5: {"over": 2.30, "under": 1.62},
    }
}

MIN_VALUE = 50
MIN_ODDS = 1.80

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


async def fetch_team_schedule(team_abbrev: str):
    """Fetch team schedule from NHL API"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        url = f"https://api-web.nhle.com/v1/club-schedule-season/{team_abbrev}/20242025"
        resp = await client.get(url)
        return resp.json()


async def fetch_all_teams():
    """Fetch all NHL teams"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        url = "https://api-web.nhle.com/v1/standings/now"
        resp = await client.get(url)
        data = resp.json()
        teams = []
        for team_data in data.get("standings", []):
            teams.append({
                "abbrev": team_data.get("teamAbbrev", {}).get("default"),
                "name": team_data.get("teamName", {}).get("default"),
                "logo": team_data.get("teamLogo")
            })
        return teams


def calculate_stats(games, team_abbrev, before_date, is_home):
    """Calculate stats for team before a specific date"""
    filtered = []
    for g in games:
        if g.get("gameState") not in ["OFF", "FINAL"]:
            continue
        game_date_str = g.get("gameDate")
        try:
            game_date = datetime.strptime(game_date_str, "%Y-%m-%d")
        except:
            continue
        if game_date >= before_date:
            continue

        home_abbrev = g.get("homeTeam", {}).get("abbrev")
        is_home_game = home_abbrev == team_abbrev

        if is_home and not is_home_game:
            continue
        if not is_home and is_home_game:
            continue

        if is_home_game:
            team_score = g.get("homeTeam", {}).get("score", 0) or 0
            opp_score = g.get("awayTeam", {}).get("score", 0) or 0
        else:
            team_score = g.get("awayTeam", {}).get("score", 0) or 0
            opp_score = g.get("homeTeam", {}).get("score", 0) or 0

        filtered.append({
            "team_score": team_score,
            "opp_score": opp_score,
            "total": team_score + opp_score
        })

    return filtered


def get_individual_totals(matches):
    if not matches:
        return {}
    stats = {}
    for threshold in [2, 3, 4]:
        count = sum(1 for m in matches if m["team_score"] >= threshold)
        stats[f"{threshold}+"] = {"percentage": (count / len(matches)) * 100 if matches else 0}
    return stats


def get_match_totals(matches):
    if not matches:
        return {}
    stats = {}
    for threshold in [5, 6, 7]:
        count = sum(1 for m in matches if m["total"] >= threshold)
        stats[f"{threshold}+"] = {"percentage": (count / len(matches)) * 100 if matches else 0}
    return stats


def generate_prediction(game_date, home_abbrev, away_abbrev, home_name, away_name,
                        home_it_stats, away_it_stats, home_total_stats, event_id):
    """Generate best value bet prediction for a game"""
    predictions = []

    # Home team individual totals
    for line, odds_data in TYPICAL_ODDS["home_it_over"].items():
        threshold = f"{int(line + 0.5)}+"
        if threshold in home_it_stats:
            prob_over = home_it_stats[threshold]["percentage"] / 100
            if prob_over > 0 and odds_data["over"] >= MIN_ODDS:
                fair_odds = 1 / prob_over
                value = ((odds_data["over"] - fair_odds) / fair_odds) * 100
                if value >= MIN_VALUE:
                    predictions.append({
                        "bet_type": "home-it-over", "bet_label": f"ИТБ {home_name}",
                        "line": line, "odds": odds_data["over"], "probability": prob_over,
                        "fair_odds": fair_odds, "value": value
                    })

    # Away team individual totals
    for line, odds_data in TYPICAL_ODDS["away_it_over"].items():
        threshold = f"{int(line + 0.5)}+"
        if threshold in away_it_stats:
            prob_over = away_it_stats[threshold]["percentage"] / 100
            if prob_over > 0 and odds_data["over"] >= MIN_ODDS:
                fair_odds = 1 / prob_over
                value = ((odds_data["over"] - fair_odds) / fair_odds) * 100
                if value >= MIN_VALUE:
                    predictions.append({
                        "bet_type": "away-it-over", "bet_label": f"ИТБ {away_name}",
                        "line": line, "odds": odds_data["over"], "probability": prob_over,
                        "fair_odds": fair_odds, "value": value
                    })

    # Match totals
    for line, odds_data in TYPICAL_ODDS["match_total"].items():
        threshold = f"{int(line + 0.5)}+"
        if threshold in home_total_stats:
            prob_over = home_total_stats[threshold]["percentage"] / 100
            if prob_over > 0 and odds_data["over"] >= MIN_ODDS:
                fair_odds = 1 / prob_over
                value = ((odds_data["over"] - fair_odds) / fair_odds) * 100
                if value >= MIN_VALUE:
                    predictions.append({
                        "bet_type": "match-total-over", "bet_label": "ТБ",
                        "line": line, "odds": odds_data["over"], "probability": prob_over,
                        "fair_odds": fair_odds, "value": value
                    })

    if predictions:
        predictions.sort(key=lambda x: x["value"], reverse=True)
        best = predictions[0]
        return {
            "event_id": event_id,
            "league": "NHL",
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
    total = home_score + away_score

    if 'home-it-over' in bet_type:
        return home_score > line
    elif 'away-it-over' in bet_type:
        return away_score > line
    elif 'match-total-over' in bet_type:
        return total > line
    return None


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        import asyncio

        try:
            from app.models.database import init_db, SessionLocal, ValueBetPrediction, Team

            init_db()
            db = SessionLocal()

            async def run():
                # Fetch all teams
                teams_data = await fetch_all_teams()
                team_schedules = {}

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

                # Fetch schedules for first 10 teams (to stay within timeout)
                for t in teams_data[:15]:
                    try:
                        schedule = await fetch_team_schedule(t["abbrev"])
                        team_schedules[t["abbrev"]] = schedule.get("games", [])
                    except Exception as e:
                        print(f"Error fetching {t['abbrev']}: {e}")

                # Process games from Jan 19
                start_date = datetime(2025, 1, 19)
                end_date = datetime.now()

                processed_games = set()
                predictions_added = 0
                won = 0
                lost = 0

                for abbrev, games in team_schedules.items():
                    for g in games:
                        if g.get("gameState") not in ["OFF", "FINAL"]:
                            continue

                        game_id = str(g.get("id"))
                        if game_id in processed_games:
                            continue

                        game_date_str = g.get("gameDate")
                        try:
                            game_date = datetime.strptime(game_date_str, "%Y-%m-%d")
                        except:
                            continue

                        if game_date < start_date or game_date > end_date:
                            continue

                        processed_games.add(game_id)

                        home_abbrev = g.get("homeTeam", {}).get("abbrev")
                        away_abbrev = g.get("awayTeam", {}).get("abbrev")
                        home_score = g.get("homeTeam", {}).get("score", 0) or 0
                        away_score = g.get("awayTeam", {}).get("score", 0) or 0

                        home_name = TEAM_NAMES_RU.get(home_abbrev, home_abbrev)
                        away_name = TEAM_NAMES_RU.get(away_abbrev, away_abbrev)

                        # Get stats
                        home_games = team_schedules.get(home_abbrev, [])
                        away_games = team_schedules.get(away_abbrev, [])

                        home_matches = calculate_stats(home_games, home_abbrev, game_date, True)
                        away_matches = calculate_stats(away_games, away_abbrev, game_date, False)

                        if len(home_matches) < 5 or len(away_matches) < 5:
                            continue

                        home_it_stats = get_individual_totals(home_matches)
                        away_it_stats = get_individual_totals(away_matches)
                        home_total_stats = get_match_totals(home_matches)

                        pred = generate_prediction(
                            game_date, home_abbrev, away_abbrev, home_name, away_name,
                            home_it_stats, away_it_stats, home_total_stats, f"nhl_{game_id}"
                        )

                        if not pred:
                            continue

                        # Check if exists
                        existing = db.query(ValueBetPrediction).filter(
                            ValueBetPrediction.event_id == pred["event_id"],
                            ValueBetPrediction.bet_type == pred["bet_type"],
                            ValueBetPrediction.line == pred["line"]
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
                        predictions_added += 1
                        if is_won:
                            won += 1
                        else:
                            lost += 1

                db.commit()
                return {
                    "success": True,
                    "predictions_added": predictions_added,
                    "won": won,
                    "lost": lost,
                    "win_rate": f"{(won / predictions_added * 100):.1f}%" if predictions_added > 0 else "0%"
                }

            result = asyncio.run(run())
            db.close()

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())

        except Exception as e:
            import traceback
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e), "trace": traceback.format_exc()}).encode())
