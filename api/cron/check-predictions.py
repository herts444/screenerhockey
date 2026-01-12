"""Scheduled task to automatically check prediction results"""
from http.server import BaseHTTPRequestHandler
import json
import sys
import os
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from app.models.database import SessionLocal, ValueBetPrediction, Game


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Auto-check predictions that are ready (5+ hours after match start)"""
        try:
            db = SessionLocal()
            try:
                result = self._auto_check_predictions(db)

                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
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

    def _auto_check_predictions(self, db):
        """Check predictions that are 5+ hours old and not yet checked"""
        # Get predictions that:
        # 1. Are not checked yet
        # 2. Match started 5+ hours ago
        # 3. Not older than 7 days
        now = datetime.now()
        check_threshold = now - timedelta(hours=5)
        cutoff_date = now - timedelta(days=7)

        predictions = db.query(ValueBetPrediction).filter(
            ValueBetPrediction.is_checked == False,
            ValueBetPrediction.scheduled >= cutoff_date,
            ValueBetPrediction.scheduled <= check_threshold
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
            "lost": checked_count - won_count,
            "timestamp": now.isoformat()
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
