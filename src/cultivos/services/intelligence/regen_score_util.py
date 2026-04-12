"""Shared regenerative-score formula — single source of truth (#218).

The FODECIJAL headline metric. Three intelligence services
(regen_trajectory, farm_regen_milestones, coop_monthly_progress)
all compose monthly health + organic-treatment percentages into
the same score; routing the formula through this util prevents
weight drift between endpoints that grant reviewers compare.
"""


def compute_regen_score(organic_pct: float, avg_health: float) -> float:
    return organic_pct * 0.6 + avg_health * 0.4
