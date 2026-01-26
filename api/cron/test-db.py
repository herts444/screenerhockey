"""Test database connection"""
from http.server import BaseHTTPRequestHandler
import json
import os
import sys

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        result = {"step": "start"}

        try:
            # Step 1: Check env vars
            result["step"] = "env_check"
            result["has_database_url"] = bool(os.environ.get("DATABASE_URL"))
            result["has_postgres_url"] = bool(os.environ.get("POSTGRES_URL"))
            result["has_api_key"] = bool(os.environ.get("API_SPORTS_KEY"))

            # Step 2: Try to add backend to path
            result["step"] = "path_setup"
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

            # Step 3: Try to import database
            result["step"] = "import_database"
            from app.models.database import SessionLocal, Team, Game
            result["import_success"] = True

            # Step 4: Try to connect
            result["step"] = "connect"
            db = SessionLocal()

            # Step 5: Try a simple query
            result["step"] = "query"
            teams_count = db.query(Team).count()
            games_count = db.query(Game).count()

            result["teams_count"] = teams_count
            result["games_count"] = games_count
            result["success"] = True

            db.close()

        except Exception as e:
            result["error"] = str(e)
            result["error_type"] = type(e).__name__

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(result, indent=2).encode())
