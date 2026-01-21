"""API endpoints for value bet predictions tracking"""
from http.server import BaseHTTPRequestHandler
import json
import sys
import os
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.models.database import SessionLocal, ValueBetPrediction, Game, init_db

# Initialize database tables on cold start
try:
    init_db()
except Exception as e:
    print(f"DB init error (may be ok if tables exist): {e}")


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Save predictions"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            predictions = data.get('predictions', [])

            db = SessionLocal()
            try:
                saved_count = 0
                for pred in predictions:
                    # Check if prediction already exists
                    existing = db.query(ValueBetPrediction).filter(
                        ValueBetPrediction.event_id == pred['eventId'],
                        ValueBetPrediction.bet_type == pred['betType'],
                        ValueBetPrediction.line == pred['line']
                    ).first()

                    if existing:
                        continue  # Skip duplicates

                    # Create new prediction
                    prediction = ValueBetPrediction(
                        event_id=pred['eventId'],
                        league=pred['league'],
                        scheduled=datetime.fromtimestamp(pred['scheduled'] / 1000) if pred.get('scheduled') else None,
                        home_team=pred['homeTeam'],
                        home_abbrev=pred['homeAbbrev'],
                        away_team=pred['awayTeam'],
                        away_abbrev=pred['awayAbbrev'],
                        bet_type=pred['betType'],
                        bet_label=pred['betLabel'],
                        line=pred['line'],
                        odds=pred['odds'],
                        probability=pred['probability'],
                        fair_odds=pred['fairOdds'],
                        value_percentage=pred['value']
                    )
                    db.add(prediction)
                    saved_count += 1

                db.commit()

                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": True,
                    "saved": saved_count,
                    "skipped": len(predictions) - saved_count
                }).encode())

            finally:
                db.close()

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def do_GET(self):
        """Get prediction history or check results"""
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        action = params.get('action', ['history'])[0]

        try:
            db = SessionLocal()
            try:
                if action == 'check':
                    # Check and update prediction results
                    result = self._check_predictions(db)
                else:
                    # Get history
                    date_str = params.get('date', [None])[0]
                    result = self._get_history(db, date_str)

                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())

            finally:
                db.close()

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def _get_history(self, db, date_str=None):
        """Get prediction history for a specific date"""
        if date_str:
            target_date = datetime.strptime(date_str, '%Y-%m-%d')
            start_date = target_date
            end_date = target_date + timedelta(days=1)
        else:
            # Default to yesterday
            yesterday = datetime.now() - timedelta(days=1)
            start_date = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=1)

        predictions = db.query(ValueBetPrediction).filter(
            ValueBetPrediction.scheduled >= start_date,
            ValueBetPrediction.scheduled < end_date
        ).order_by(ValueBetPrediction.scheduled).all()

        return {
            "date": start_date.strftime('%Y-%m-%d'),
            "predictions": [self._format_prediction(p) for p in predictions]
        }

    def _check_predictions(self, db):
        """Check prediction results against finished games"""
        # Get unchecked predictions from last 7 days
        cutoff_date = datetime.now() - timedelta(days=7)
        predictions = db.query(ValueBetPrediction).filter(
            ValueBetPrediction.is_checked == False,
            ValueBetPrediction.scheduled >= cutoff_date,
            ValueBetPrediction.scheduled < datetime.now()
        ).all()

        checked_count = 0
        won_count = 0

        for pred in predictions:
            # Find corresponding game
            game = db.query(Game).filter(
                Game.league == pred.league,
                Game.date >= pred.scheduled - timedelta(hours=2),
                Game.date <= pred.scheduled + timedelta(hours=2)
            ).filter(
                ((Game.home_team.has(abbrev=pred.home_abbrev)) &
                 (Game.away_team.has(abbrev=pred.away_abbrev)))
            ).first()

            if not game or not game.is_finished or game.home_score is None:
                continue

            # Check bet result
            is_won = self._check_bet_result(pred, game)

            if is_won is not None:
                pred.is_checked = True
                pred.is_won = is_won
                pred.actual_result = f"{game.home_score}-{game.away_score}"
                pred.checked_at = datetime.now()
                checked_count += 1
                if is_won:
                    won_count += 1

        db.commit()

        return {
            "success": True,
            "checked": checked_count,
            "won": won_count,
            "lost": checked_count - won_count
        }

    def _check_bet_result(self, pred, game):
        """Check if prediction was correct based on game result"""
        bet_type = pred.bet_type
        line = pred.line
        home_score = game.home_score
        away_score = game.away_score
        total_score = home_score + away_score

        if 'home-it-over' in bet_type:
            return home_score > line
        elif 'home-it-under' in bet_type:
            return home_score < line
        elif 'away-it-over' in bet_type:
            return away_score > line
        elif 'away-it-under' in bet_type:
            return away_score < line
        elif 'match-total-over' in bet_type:
            return total_score > line
        elif 'match-total-under' in bet_type:
            return total_score < line

        return None

    def _format_prediction(self, pred):
        """Format prediction for API response"""
        return {
            "id": pred.id,
            "eventId": pred.event_id,
            "league": pred.league,
            "scheduled": int(pred.scheduled.timestamp() * 1000) if pred.scheduled else None,
            "homeTeam": pred.home_team,
            "homeAbbrev": pred.home_abbrev,
            "awayTeam": pred.away_team,
            "awayAbbrev": pred.away_abbrev,
            "betType": pred.bet_type,
            "betLabel": pred.bet_label,
            "line": pred.line,
            "odds": pred.odds,
            "probability": pred.probability,
            "fairOdds": pred.fair_odds,
            "value": pred.value_percentage,
            "isChecked": pred.is_checked,
            "isWon": pred.is_won,
            "actualResult": pred.actual_result
        }

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
