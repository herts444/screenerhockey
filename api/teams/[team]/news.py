"""GET /api/teams/[team]/news - Get team news from cache"""
from http.server import BaseHTTPRequestHandler
import json
import re
from urllib.parse import urlparse, parse_qs
from pathlib import Path


def load_news_cache():
    """Load news from cache file"""
    import os

    # Try multiple possible paths for Vercel compatibility
    possible_paths = [
        Path(__file__).parent.parent.parent.parent / "data" / "news_cache.json",
        Path("/var/task/data/news_cache.json"),
        Path(os.getcwd()) / "data" / "news_cache.json",
    ]

    for cache_file in possible_paths:
        try:
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            continue

    return {"teams": {}, "error": "Cache file not found"}


def get_team_news(team_abbrev: str, limit: int = 5) -> dict:
    """Get news for a team from cache"""
    cache = load_news_cache()
    team_data = cache.get("teams", {}).get(team_abbrev.upper())

    if not team_data:
        return {"error": f"Team {team_abbrev} not found"}

    articles = team_data.get("articles", [])[:limit]

    return {
        "team": team_abbrev.upper(),
        "team_name": team_data.get("team_name", ""),
        "articles": articles,
        "updated_at": team_data.get("updated_at", ""),
    }


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        match = re.search(r'/api/teams/([^/]+)/news', self.path)
        if not match:
            self.send_response(400)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Invalid path"}).encode())
            return

        team_abbrev = match.group(1).upper()
        limit = int(params.get("limit", ["5"])[0])

        result = get_team_news(team_abbrev, limit)

        if "error" in result:
            self.send_response(404)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
            return

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "s-maxage=300, stale-while-revalidate")
        self.end_headers()
        self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
