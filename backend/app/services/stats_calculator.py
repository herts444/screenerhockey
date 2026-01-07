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


@dataclass
class StatsResult:
    total_matches: int
    matches_count: int
    percentage: float
    weighted_percentage: float
    matches: List[GameResult]


class StatsCalculator:
    """Calculator for team statistics with weighted probability"""

    # Individual total thresholds
    INDIVIDUAL_THRESHOLDS = [2, 3, 4, 5, 6]

    # Total match goals thresholds
    TOTAL_THRESHOLDS = [5, 6, 7, 8]

    @staticmethod
    def calculate_weight(index: int, total: int, decay_factor: float = 0.1) -> float:
        """
        Calculate weight for a match based on recency
        More recent matches have higher weight
        Uses exponential decay: weight = e^(-decay * position_from_end)
        """
        position_from_end = total - index - 1
        return math.exp(-decay_factor * position_from_end)

    @staticmethod
    def calculate_weighted_percentage(
        matches: List[GameResult],
        condition_func,
        decay_factor: float = 0.1
    ) -> Tuple[float, float]:
        """
        Calculate both simple and weighted percentage for matches meeting condition

        Returns: (simple_percentage, weighted_percentage)
        """
        if not matches:
            return 0.0, 0.0

        total = len(matches)
        matches_meeting_condition = 0
        weighted_sum = 0.0
        total_weight = 0.0

        # Sort matches by date (oldest first for correct weighting)
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
    def calculate_individual_total_stats(
        cls,
        matches: List[GameResult],
        threshold: int
    ) -> StatsResult:
        """
        Calculate stats for individual total (team goals >= threshold)
        """
        condition = lambda m: m.team_score >= threshold
        matching_matches = [m for m in matches if condition(m)]
        simple_pct, weighted_pct = cls.calculate_weighted_percentage(matches, condition)

        return StatsResult(
            total_matches=len(matches),
            matches_count=len(matching_matches),
            percentage=simple_pct,
            weighted_percentage=weighted_pct,
            matches=matching_matches
        )

    @classmethod
    def calculate_total_goals_stats(
        cls,
        matches: List[GameResult],
        threshold: int
    ) -> StatsResult:
        """
        Calculate stats for total match goals (team + opponent >= threshold)
        """
        condition = lambda m: m.total_goals >= threshold
        matching_matches = [m for m in matches if condition(m)]
        simple_pct, weighted_pct = cls.calculate_weighted_percentage(matches, condition)

        return StatsResult(
            total_matches=len(matches),
            matches_count=len(matching_matches),
            percentage=simple_pct,
            weighted_percentage=weighted_pct,
            matches=matching_matches
        )

    @classmethod
    def get_full_team_stats(
        cls,
        home_matches: List[GameResult],
        away_matches: List[GameResult]
    ) -> Dict:
        """
        Get complete stats for a team split by home/away
        """
        stats = {
            "home": {
                "total_matches": len(home_matches),
                "individual_totals": {},
                "match_totals": {}
            },
            "away": {
                "total_matches": len(away_matches),
                "individual_totals": {},
                "match_totals": {}
            }
        }

        # Calculate individual totals (team goals)
        for threshold in cls.INDIVIDUAL_THRESHOLDS:
            home_stats = cls.calculate_individual_total_stats(home_matches, threshold)
            away_stats = cls.calculate_individual_total_stats(away_matches, threshold)

            stats["home"]["individual_totals"][f"{threshold}+"] = {
                "count": home_stats.matches_count,
                "percentage": home_stats.percentage,
                "weighted_percentage": home_stats.weighted_percentage,
                "matches": [
                    {
                        "date": m.date.strftime("%d.%m.%Y"),
                        "opponent": m.opponent,
                        "opponent_abbrev": m.opponent_abbrev,
                        "score": f"{m.team_score}:{m.opponent_score}"
                    }
                    for m in home_stats.matches
                ]
            }

            stats["away"]["individual_totals"][f"{threshold}+"] = {
                "count": away_stats.matches_count,
                "percentage": away_stats.percentage,
                "weighted_percentage": away_stats.weighted_percentage,
                "matches": [
                    {
                        "date": m.date.strftime("%d.%m.%Y"),
                        "opponent": m.opponent,
                        "opponent_abbrev": m.opponent_abbrev,
                        "score": f"{m.team_score}:{m.opponent_score}"
                    }
                    for m in away_stats.matches
                ]
            }

        # Calculate match totals (team + opponent goals)
        for threshold in cls.TOTAL_THRESHOLDS:
            home_stats = cls.calculate_total_goals_stats(home_matches, threshold)
            away_stats = cls.calculate_total_goals_stats(away_matches, threshold)

            stats["home"]["match_totals"][f"{threshold}+"] = {
                "count": home_stats.matches_count,
                "percentage": home_stats.percentage,
                "weighted_percentage": home_stats.weighted_percentage,
                "matches": [
                    {
                        "date": m.date.strftime("%d.%m.%Y"),
                        "opponent": m.opponent,
                        "opponent_abbrev": m.opponent_abbrev,
                        "score": f"{m.team_score}:{m.opponent_score}",
                        "total": m.total_goals
                    }
                    for m in home_stats.matches
                ]
            }

            stats["away"]["match_totals"][f"{threshold}+"] = {
                "count": away_stats.matches_count,
                "percentage": away_stats.percentage,
                "weighted_percentage": away_stats.weighted_percentage,
                "matches": [
                    {
                        "date": m.date.strftime("%d.%m.%Y"),
                        "opponent": m.opponent,
                        "opponent_abbrev": m.opponent_abbrev,
                        "score": f"{m.team_score}:{m.opponent_score}",
                        "total": m.total_goals
                    }
                    for m in away_stats.matches
                ]
            }

        return stats
