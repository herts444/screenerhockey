"""NHL API client - stateless version"""
import httpx
from datetime import datetime, timedelta
from typing import List, Optional
from .stats import GameResult, StatsCalculator


TEAM_NAMES_RU = {
    "ANA": "Анахайм Дакс", "ARI": "Аризона Койотс", "BOS": "Бостон Брюинз",
    "BUF": "Баффало Сейбрз", "CGY": "Калгари Флэймз", "CAR": "Каролина Харрикейнз",
    "CHI": "Чикаго Блэкхокс", "COL": "Колорадо Эвеланш", "CBJ": "Коламбус Блю Джекетс",
    "DAL": "Даллас Старз", "DET": "Детройт Ред Уингз", "EDM": "Эдмонтон Ойлерз",
    "FLA": "Флорида Пантерз", "LAK": "Лос-Анджелес Кингз", "MIN": "Миннесота Уайлд",
    "MTL": "Монреаль Канадиенс", "NSH": "Нэшвилл Предаторз", "NJD": "Нью-Джерси Девилз",
    "NYI": "Нью-Йорк Айлендерс", "NYR": "Нью-Йорк Рейнджерс", "OTT": "Оттава Сенаторз",
    "PHI": "Филадельфия Флайерз", "PIT": "Питтсбург Пингвинз", "SJS": "Сан-Хосе Шаркс",
    "SEA": "Сиэтл Кракен", "STL": "Сент-Луис Блюз", "TBL": "Тампа-Бэй Лайтнинг",
    "TOR": "Торонто Мейпл Лифс", "UTA": "Юта Хоккей Клаб", "VAN": "Ванкувер Кэнакс",
    "VGK": "Вегас Голден Найтс", "WSH": "Вашингтон Кэпиталз", "WPG": "Виннипег Джетс"
}


class NHLService:
    BASE_URL = "https://api-web.nhle.com/v1"

    @classmethod
    async def get_teams(cls) -> List[dict]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{cls.BASE_URL}/standings/now")
            response.raise_for_status()
            standings = response.json()

        teams = []
        for team_data in standings.get("standings", []):
            abbrev = team_data.get("teamAbbrev", {}).get("default")
            teams.append({
                "abbrev": abbrev,
                "name": team_data.get("teamName", {}).get("default"),
                "name_ru": TEAM_NAMES_RU.get(abbrev),
                "logo_url": team_data.get("teamLogo")
            })
        return teams

    @classmethod
    async def get_schedule(cls, days: int = 7) -> List[dict]:
        games = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            for i in range(days):
                date = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
                try:
                    response = await client.get(f"{cls.BASE_URL}/schedule/{date}")
                    response.raise_for_status()
                    schedule = response.json()

                    for day in schedule.get("gameWeek", []):
                        if day.get("date") == date:
                            for game in day.get("games", []):
                                game_date_str = game.get("startTimeUTC", "")
                                try:
                                    game_date = datetime.fromisoformat(game_date_str.replace("Z", "+00:00"))
                                except:
                                    game_date = None

                                home = game.get("homeTeam", {})
                                away = game.get("awayTeam", {})
                                home_abbrev = home.get("abbrev")
                                away_abbrev = away.get("abbrev")

                                games.append({
                                    "game_id": game.get("id"),
                                    "date": game_date.strftime("%d.%m.%Y %H:%M") if game_date else "",
                                    "date_iso": game_date.isoformat() if game_date else "",
                                    "home_team": {
                                        "abbrev": home_abbrev,
                                        "name": home.get("placeName", {}).get("default", home_abbrev),
                                        "name_ru": TEAM_NAMES_RU.get(home_abbrev, home_abbrev),
                                        "logo_url": home.get("logo")
                                    },
                                    "away_team": {
                                        "abbrev": away_abbrev,
                                        "name": away.get("placeName", {}).get("default", away_abbrev),
                                        "name_ru": TEAM_NAMES_RU.get(away_abbrev, away_abbrev),
                                        "logo_url": away.get("logo")
                                    },
                                    "venue": game.get("venue", {}).get("default", "")
                                })
                except Exception as e:
                    print(f"Error fetching NHL schedule for {date}: {e}")
        return games

    @classmethod
    async def get_team_stats(cls, team_abbrev: str, last_n: int = 0, season: str = "20242025") -> dict:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{cls.BASE_URL}/club-schedule-season/{team_abbrev}/{season}")
            response.raise_for_status()
            schedule = response.json()

        games = schedule.get("games", [])
        finished = [g for g in games if g.get("gameState") in ["OFF", "FINAL"]]

        # Build game results
        home_matches, away_matches = [], []

        for game in finished:
            home_abbrev = game.get("homeTeam", {}).get("abbrev")
            away_abbrev = game.get("awayTeam", {}).get("abbrev")
            is_home = home_abbrev == team_abbrev

            home_score = game.get("homeTeam", {}).get("score", 0) or 0
            away_score = game.get("awayTeam", {}).get("score", 0) or 0

            if is_home:
                team_score, opp_score = home_score, away_score
                opp_abbrev = away_abbrev
            else:
                team_score, opp_score = away_score, home_score
                opp_abbrev = home_abbrev

            game_date_str = game.get("gameDate")
            try:
                game_date = datetime.strptime(game_date_str, "%Y-%m-%d")
            except:
                continue

            result = GameResult(
                game_id=str(game.get("id")),
                date=game_date,
                opponent=TEAM_NAMES_RU.get(opp_abbrev, opp_abbrev),
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

        # Sort by date desc and apply limit
        home_matches.sort(key=lambda x: x.date, reverse=True)
        away_matches.sort(key=lambda x: x.date, reverse=True)

        if last_n > 0:
            home_matches = home_matches[:last_n]
            away_matches = away_matches[:last_n]

        stats = StatsCalculator.get_full_team_stats(home_matches, away_matches)

        return {
            "team": {
                "abbrev": team_abbrev,
                "name": team_abbrev,
                "name_ru": TEAM_NAMES_RU.get(team_abbrev, team_abbrev),
                "logo_url": None
            },
            "stats": stats
        }
