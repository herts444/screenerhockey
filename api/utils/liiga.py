"""Finnish Liiga API client - stateless version"""
import httpx
from datetime import datetime, timedelta, timezone
from typing import List
from .stats import GameResult, StatsCalculator


LIIGA_TEAM_NAMES_RU = {
    "HIFK": "ХИФК Хельсинки", "K-ESPOO": "К-Эспоо", "KALPA": "КалПа Куопио",
    "HPK": "ХПК Хямеэнлинна", "ILVES": "Ильвес Тампере", "JYP": "ЮП Ювяскюля",
    "JUKURIT": "Юкурит Миккели", "LUKKO": "Лукко Раума", "PELICANS": "Пеликанс Лахти",
    "SAIPA": "СайПа Лаппеэнранта", "SPORT": "Спорт Вааса", "TAPPARA": "Таппара Тампере",
    "TPS": "ТПС Турку", "ASSAT": "Ассат Пори", "KARPAT": "Кярпят Оулу",
    "KOOKOO": "Кукоо Коувола", "ÄSSÄT": "Ассат Пори", "KÄRPÄT": "Кярпят Оулу",
}


class LiigaService:
    BASE_URL = "https://liiga.fi/api/v2"
    CURRENT_SEASON = 2026

    @classmethod
    async def get_all_games(cls, season: int = None) -> List[dict]:
        season = season or cls.CURRENT_SEASON
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            url = f"{cls.BASE_URL}/games?tournament=runkosarja&season={season}"
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    @classmethod
    async def get_teams(cls) -> List[dict]:
        games = await cls.get_all_games()
        teams = {}

        for game in games:
            for team_data in [game.get("homeTeam", {}), game.get("awayTeam", {})]:
                team_id = team_data.get("teamId", "")
                if team_id and team_id not in teams:
                    abbrev = team_id.split(":")[-1].upper() if ":" in team_id else team_id
                    teams[team_id] = {
                        "abbrev": abbrev,
                        "name": team_data.get("teamName", ""),
                        "name_ru": LIIGA_TEAM_NAMES_RU.get(abbrev),
                        "logo_url": team_data.get("logos", {}).get("darkBg", ""),
                        "team_id": team_id
                    }

        return list(teams.values())

    @classmethod
    async def get_schedule(cls, days: int = 7) -> List[dict]:
        games = await cls.get_all_games()

        now_utc = datetime.now(timezone.utc)
        start = datetime(now_utc.year, now_utc.month, now_utc.day)
        end = start + timedelta(days=days + 1)

        result = []
        seen_ids = set()

        for game in games:
            game_id = game.get("id")
            if game_id in seen_ids or game.get("ended", False):
                continue

            game_start = game.get("start", "")
            if not game_start:
                continue

            try:
                game_date = datetime.fromisoformat(game_start.replace("Z", "+00:00"))
                game_date_naive = game_date.replace(tzinfo=None)
                if not (start <= game_date_naive < end):
                    continue
            except:
                continue

            seen_ids.add(game_id)

            home_data = game.get("homeTeam", {})
            away_data = game.get("awayTeam", {})
            home_id = home_data.get("teamId", "")
            away_id = away_data.get("teamId", "")
            home_abbrev = home_id.split(":")[-1].upper() if ":" in home_id else home_id
            away_abbrev = away_id.split(":")[-1].upper() if ":" in away_id else away_id

            result.append({
                "game_id": f"liiga_{game_id}",
                "date": game_date.strftime("%d.%m.%Y %H:%M"),
                "date_iso": game_date.isoformat(),
                "home_team": {
                    "abbrev": home_abbrev,
                    "name": home_data.get("teamName", home_abbrev),
                    "name_ru": LIIGA_TEAM_NAMES_RU.get(home_abbrev),
                    "logo_url": home_data.get("logos", {}).get("darkBg", "")
                },
                "away_team": {
                    "abbrev": away_abbrev,
                    "name": away_data.get("teamName", away_abbrev),
                    "name_ru": LIIGA_TEAM_NAMES_RU.get(away_abbrev),
                    "logo_url": away_data.get("logos", {}).get("darkBg", "")
                },
                "venue": game.get("iceRink", {}).get("name", "")
            })

        return sorted(result, key=lambda g: g.get("date_iso", ""))

    @classmethod
    async def get_team_stats(cls, team_abbrev: str, last_n: int = 0) -> dict:
        games = await cls.get_all_games()

        # Find team_id
        team_id = None
        team_info = None
        for game in games:
            for team_data in [game.get("homeTeam", {}), game.get("awayTeam", {})]:
                tid = team_data.get("teamId", "")
                abbrev = tid.split(":")[-1].upper() if ":" in tid else tid
                if abbrev == team_abbrev:
                    team_id = tid
                    team_info = {
                        "abbrev": abbrev,
                        "name": team_data.get("teamName", ""),
                        "name_ru": LIIGA_TEAM_NAMES_RU.get(abbrev),
                        "logo_url": team_data.get("logos", {}).get("darkBg", "")
                    }
                    break
            if team_id:
                break

        if not team_id:
            return {}

        # Filter finished games for this team
        finished = [g for g in games if g.get("ended", False)]
        team_games = [g for g in finished if
                      g.get("homeTeam", {}).get("teamId") == team_id or
                      g.get("awayTeam", {}).get("teamId") == team_id]

        home_matches, away_matches = [], []

        for game in team_games:
            home_data = game.get("homeTeam", {})
            away_data = game.get("awayTeam", {})
            is_home = home_data.get("teamId") == team_id

            home_score = home_data.get("goals", 0) or 0
            away_score = away_data.get("goals", 0) or 0

            if is_home:
                team_score, opp_score = home_score, away_score
                opp_id = away_data.get("teamId", "")
                opp_name = away_data.get("teamName", "")
            else:
                team_score, opp_score = away_score, home_score
                opp_id = home_data.get("teamId", "")
                opp_name = home_data.get("teamName", "")

            opp_abbrev = opp_id.split(":")[-1].upper() if ":" in opp_id else opp_id

            game_date_str = game.get("start", "")
            try:
                game_date = datetime.fromisoformat(game_date_str.replace("Z", "+00:00")).replace(tzinfo=None)
            except:
                continue

            result = GameResult(
                game_id=str(game.get("id")),
                date=game_date,
                opponent=LIIGA_TEAM_NAMES_RU.get(opp_abbrev, opp_name),
                opponent_abbrev=opp_abbrev,
                is_home=is_home,
                team_score=team_score,
                opponent_score=opp_score,
                total_goals=team_score + opp_score
            )

            if is_home:
                home_matches.append(result)
            else:
                away_matches.append(result)

        home_matches.sort(key=lambda x: x.date, reverse=True)
        away_matches.sort(key=lambda x: x.date, reverse=True)

        if last_n > 0:
            home_matches = home_matches[:last_n]
            away_matches = away_matches[:last_n]

        stats = StatsCalculator.get_full_team_stats(home_matches, away_matches)

        return {
            "team": team_info,
            "stats": stats
        }
