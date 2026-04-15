"""Tests for #226 — 6 new Jalisco agronomist tips (16 → 22)."""

from cultivos.db.seeds import AGRONOMIST_TIP_SEEDS, seed_agronomist_tips
from cultivos.db.models import AgronomistTip


def test_seed_count_at_least_22():
    """AGRONOMIST_TIP_SEEDS has at least 22 entries after extension."""
    assert len(AGRONOMIST_TIP_SEEDS) >= 22


def test_temporal_planting_tip_exists():
    """A tip covering temporal planting windows for maiz exists."""
    matches = [t for t in AGRONOMIST_TIP_SEEDS if t.crop == "maiz" and "temporal" in t.tip_text_es.lower()]
    assert len(matches) >= 1


def test_nopal_drought_tip_exists():
    """A tip for nopal secas drought survival exists."""
    matches = [t for t in AGRONOMIST_TIP_SEEDS if t.crop == "nopal" and t.problem == "drought"]
    assert len(matches) >= 1


def test_nopal_maiz_intercropping_tip_exists():
    """A tip about nopal-maiz intercropping exists."""
    matches = [t for t in AGRONOMIST_TIP_SEEDS if "nopal" in t.tip_text_es.lower() and "maiz" in t.tip_text_es.lower()]
    assert len(matches) >= 1


def test_frost_mitigation_tip_exists():
    """A tip for river-valley frost mitigation (aguacate) exists."""
    matches = [t for t in AGRONOMIST_TIP_SEEDS if t.crop == "aguacate" and "helada" in t.tip_text_es.lower()]
    assert len(matches) >= 1


def test_coffee_shade_tip_exists():
    """A tip about coffee-under-shade microclimate exists."""
    matches = [t for t in AGRONOMIST_TIP_SEEDS if t.crop == "cafe" and "sombra" in t.tip_text_es.lower()]
    assert len(matches) >= 1


def test_no_none_fields_in_new_tips():
    """All tips have non-None crop, problem, tip_text_es, source, region, season."""
    for tip in AGRONOMIST_TIP_SEEDS:
        assert tip.crop is not None, f"None crop in: {tip.tip_text_es[:40]}"
        assert tip.problem is not None, f"None problem in: {tip.tip_text_es[:40]}"
        assert tip.tip_text_es is not None
        assert tip.source is not None, f"None source in: {tip.tip_text_es[:40]}"
        assert tip.region is not None, f"None region in: {tip.tip_text_es[:40]}"
        assert tip.season is not None, f"None season in: {tip.tip_text_es[:40]}"


def test_seed_function_inserts_all(db):
    """seed_agronomist_tips inserts all entries into DB."""
    count = seed_agronomist_tips(db)
    assert count >= 22
    assert db.query(AgronomistTip).count() >= 22
