"""Tests for #217 — 8 extended Jalisco landrace crop varieties."""

from cultivos.db.models import CropVariety
from cultivos.db.seeds import CROP_VARIETY_SEEDS, seed_crop_varieties


EXPECTED_NEW_VARIETY_NAMES = {
    "Maíz Cónico Norteño",
    "Maíz Tabloncillo",
    "Frijol Garbancillo",
    "Frijol Mayocoba",
    "Chile Manzano",
    "Chile de Árbol Yahualica",
    "Tomate Riñón",
    "Calabaza Pipiana",
}


def test_eight_new_varieties_present_in_seed_list():
    seed_names = {v.name for v in CROP_VARIETY_SEEDS}
    missing = EXPECTED_NEW_VARIETY_NAMES - seed_names
    assert not missing, f"Missing extended varieties in CROP_VARIETY_SEEDS: {missing}"


def test_total_seed_count_at_least_24():
    # 16 original + 8 new = 24 minimum
    assert len(CROP_VARIETY_SEEDS) >= 24


def test_extended_varieties_schema_complete():
    new_entries = [v for v in CROP_VARIETY_SEEDS if v.name in EXPECTED_NEW_VARIETY_NAMES]
    assert len(new_entries) == 8
    for v in new_entries:
        assert isinstance(v.crop_name, str) and v.crop_name
        assert isinstance(v.name, str) and v.name
        assert isinstance(v.region, str) and v.region
        assert isinstance(v.altitude_m, int) and v.altitude_m > 0
        assert isinstance(v.water_mm, int) and v.water_mm > 0
        assert isinstance(v.diseases, list) and len(v.diseases) >= 1
        assert isinstance(v.adaptation_notes, str) and len(v.adaptation_notes) > 20


def test_extended_varieties_cover_expected_crops():
    new_entries = [v for v in CROP_VARIETY_SEEDS if v.name in EXPECTED_NEW_VARIETY_NAMES]
    crops = {v.crop_name for v in new_entries}
    # Must cover: maiz, frijol, chile, tomate, calabaza
    assert {"maiz", "frijol", "chile", "tomate", "calabaza"}.issubset(crops)


def test_altitude_m_within_jalisco_range():
    new_entries = [v for v in CROP_VARIETY_SEEDS if v.name in EXPECTED_NEW_VARIETY_NAMES]
    for v in new_entries:
        # Jalisco cultivable range: ~200m (costa) to ~2500m (sierra)
        assert 100 <= v.altitude_m <= 2600, f"{v.name} altitude {v.altitude_m} out of range"


def test_seed_crop_varieties_inserts_all_rows(db):
    count = seed_crop_varieties(db)
    assert count == len(CROP_VARIETY_SEEDS)
    db_count = db.query(CropVariety).count()
    assert db_count == len(CROP_VARIETY_SEEDS)
    for expected in EXPECTED_NEW_VARIETY_NAMES:
        row = db.query(CropVariety).filter_by(name=expected).one_or_none()
        assert row is not None, f"{expected} not persisted"


def test_variety_names_are_unique():
    names = [v.name for v in CROP_VARIETY_SEEDS]
    assert len(names) == len(set(names)), "Duplicate CropVariety names"
