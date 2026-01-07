"""Stats calculator for hockey data - stateless version"""
from typing import List, Dict, Tuple
from dataclasses import dataclass
from datetime import datetime
import math


@dataclass
class GameResult:
    game_id: str
    date: datetime
    opponent: str
    opponent_abbrev: str
    is_home: bool
    team_score: int
    opponent_score: int
    total_goals: int


class StatsCalculator:
    """Calculator for team statistics with weighted probability"""

    INDIVIDUAL_THRESHOLDS = [2, 3, 4, 5, 6]
    TOTAL_THRESHOLDS = [5, 6, 7, 8]

    @staticmethod
    def calculate_weight(index: int, total: int, decay_factor: float = 0.1) -> float:
        position_from_end = total - index - 1
        return math.exp(-decay_factor * position_from_end)

    @staticmethod
    def calculate_weighted_percentage(
        matches: List[GameResult],
        condition_func,
        decay_factor: float = 0.1
    ) -> Tuple[float, float]:
        if not matches:
            return 0.0, 0.0

        total = len(matches)
        matches_meeting_condition = 0
        weighted_sum = 0.0
        total_weight = 0.0

        sorted_matches = sorted(matches, key=lambda m: m.date)

        for i, match in enumerate(sorted_matches):
            weight = StatsCalculator.calculate_weight(i, total, decay_factor)
            total_weight += weight

            if condition_func(match):
                matches_meeting_condition += 1
                weighted_sum += weight

        simple_pct = (matches_meeting_condition / total) * 100 if total > 0 else 0
        weighted_pct = (weighted_sum / total_weight) * 100 if total_weight > 0 else 0

        return round(simple_pct, 1), round(weighted_pct, 1)

    @classmethod
    def get_full_team_stats(cls, home_matches: List[GameResult], away_matches: List[GameResult]) -> Dict:
        stats = {
            "home": {"total_matches": len(home_matches), "individual_totals": {}, "match_totals": {}},
            "away": {"total_matches": len(away_matches), "individual_totals": {}, "match_totals": {}}
        }

        # Individual totals
        for threshold in cls.INDIVIDUAL_THRESHOLDS:
            for location, matches in [("home", home_matches), ("away", away_matches)]:
                condition = lambda m, t=threshold: m.team_score >= t
                matching = [m for m in matches if condition(m)]
                simple_pct, weighted_pct = cls.calculate_weighted_percentage(matches, condition)

                stats[location]["individual_totals"][f"{threshold}+"] = {
                    "count": len(matching),
                    "percentage": simple_pct,
                    "weighted_percentage": weighted_pct,
                    "matches": [
                        {
                            "date": m.date.strftime("%d.%m.%Y"),
                            "opponent": m.opponent,
                            "opponent_abbrev": m.opponent_abbrev,
                            "score": f"{m.team_score}:{m.opponent_score}"
                        }
                        for m in matching
                    ]
                }

        # Match totals
        for threshold in cls.TOTAL_THRESHOLDS:
            for location, matches in [("home", home_matches), ("away", away_matches)]:
                condition = lambda m, t=threshold: m.total_goals >= t
                matching = [m for m in matches if condition(m)]
                simple_pct, weighted_pct = cls.calculate_weighted_percentage(matches, condition)

                stats[location]["match_totals"][f"{threshold}+"] = {
                    "count": len(matching),
                    "percentage": simple_pct,
                    "weighted_percentage": weighted_pct,
                    "matches": [
                        {
                            "date": m.date.strftime("%d.%m.%Y"),
                            "opponent": m.opponent,
                            "opponent_abbrev": m.opponent_abbrev,
                            "score": f"{m.team_score}:{m.opponent_score}",
                            "total": m.total_goals
                        }
                        for m in matching
                    ]
                }

        return stats
