"""GET /api/teams - Get all teams for a league"""
from http.server import BaseHTTPRequestHandler
import json
import asyncio
from urllib.parse import urlparse, parse_qs


def get_service(league: str):
    from utils.nhl import NHLService
    from utils.ahl import AHLService
    from utils.liiga import LiigaService

    services = {
        "NHL": NHLService,
        "AHL": AHLService,
        "LIIGA": LiigaService
    }
    return services.get(league.upper())


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Parse query params
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        league = params.get("league", ["NHL"])[0].upper()

        service = get_service(league)
        if not service:
            self.send_response(400)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Invalid league"}).encode())
            return

        try:
            teams = asyncio.run(service.get_teams())
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "s-maxage=3600, stale-while-revalidate")
            self.end_headers()
            self.wfile.write(json.dumps(teams).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
