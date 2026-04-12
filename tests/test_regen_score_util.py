"""Golden tests for the shared regen_score formula util (#218)."""

from cultivos.services.intelligence.regen_score_util import compute_regen_score


def test_all_organic_high_health_returns_100():
    assert compute_regen_score(organic_pct=100.0, avg_health=100.0) == 100.0


def test_no_organic_low_health():
    # 0 * 0.6 + 20 * 0.4 = 8.0
    assert compute_regen_score(organic_pct=0.0, avg_health=20.0) == 8.0


def test_mixed_inputs():
    # 50 * 0.6 + 70 * 0.4 = 30 + 28 = 58.0
    assert compute_regen_score(organic_pct=50.0, avg_health=70.0) == 58.0


def test_zero_inputs_edge_case():
    assert compute_regen_score(organic_pct=0.0, avg_health=0.0) == 0.0
