"""Tests for Ontario/Canada adaptation — seed data + seasonal calendar."""

from datetime import date

import pytest

from cultivos.db.seeds import (
    ANCESTRAL_METHOD_SEEDS,
    CROP_TYPE_SEEDS,
    DISEASE_SEEDS,
    FERTILIZER_SEEDS,
)
from cultivos.services.intelligence.seasonal_calendar import (
    _classify_current_season,
    generate_seasonal_alerts,
)


# ── Seed data tests ──────────────────────────────────────────────


class TestOntarioCrops:
    """Verify Ontario crop seed data exists and is well-formed."""

    EXPECTED_ONTARIO_CROPS = [
        "Corn (Field)", "Soybean", "Winter Wheat", "Apple", "Grape",
        "Greenhouse Tomato",
    ]

    def test_ontario_crops_exist(self):
        ontario_crops = [
            c.name for c in CROP_TYPE_SEEDS if "Ontario" in (c.regions or [])
        ]
        for expected in self.EXPECTED_ONTARIO_CROPS:
            assert expected in ontario_crops, f"Missing Ontario crop: {expected}"

    def test_ontario_crops_have_required_fields(self):
        ontario = [c for c in CROP_TYPE_SEEDS if "Ontario" in (c.regions or [])]
        for crop in ontario:
            assert crop.family, f"{crop.name} missing family"
            assert crop.growing_season, f"{crop.name} missing growing_season"
            assert crop.description_es, f"{crop.name} missing description_es"
            assert crop.days_to_harvest > 0, f"{crop.name} invalid days_to_harvest"

    def test_no_duplicate_crop_names(self):
        names = [c.name for c in CROP_TYPE_SEEDS]
        assert len(names) == len(set(names)), f"Duplicate crop names: {[n for n in names if names.count(n) > 1]}"


class TestOntarioDiseases:
    """Verify Ontario disease seed data exists and has organic treatments."""

    EXPECTED_ONTARIO_DISEASES = [
        "Corn rootworm", "Soybean aphid", "Apple scab",
        "Powdery mildew (grape)", "Late blight (Ontario)",
        "Downy mildew (grape)",
    ]

    def test_ontario_diseases_exist(self):
        ontario_diseases = [
            d.name for d in DISEASE_SEEDS if d.region == "Ontario"
        ]
        for expected in self.EXPECTED_ONTARIO_DISEASES:
            assert expected in ontario_diseases, f"Missing Ontario disease: {expected}"

    def test_all_ontario_diseases_have_organic_treatments(self):
        ontario = [d for d in DISEASE_SEEDS if d.region == "Ontario"]
        for disease in ontario:
            assert disease.treatments, f"{disease.name} has no treatments"
            for treatment in disease.treatments:
                assert treatment.get("organic") is True, (
                    f"{disease.name}: treatment '{treatment['name']}' not marked organic"
                )

    def test_ontario_diseases_have_symptoms(self):
        ontario = [d for d in DISEASE_SEEDS if d.region == "Ontario"]
        for disease in ontario:
            assert disease.symptoms, f"{disease.name} has no symptoms"
            assert len(disease.symptoms) >= 2, f"{disease.name} needs at least 2 symptoms"

    def test_no_duplicate_disease_names(self):
        names = [d.name for d in DISEASE_SEEDS]
        assert len(names) == len(set(names)), f"Duplicate disease names: {[n for n in names if names.count(n) > 1]}"


class TestOntarioAncestralMethods:
    """Verify Ontario ancestral/traditional method seed data."""

    EXPECTED_METHODS = [
        "Cover cropping (Ontario)", "Rotacion maiz-soya-trigo",
        "Companion planting (Ontario)", "Windbreaks (cortinas rompevientos)",
    ]

    def test_ontario_methods_exist(self):
        ontario_methods = [
            m.name for m in ANCESTRAL_METHOD_SEEDS if m.region == "Ontario"
        ]
        for expected in self.EXPECTED_METHODS:
            assert expected in ontario_methods, f"Missing Ontario method: {expected}"

    def test_ontario_methods_have_scientific_basis(self):
        ontario = [m for m in ANCESTRAL_METHOD_SEEDS if m.region == "Ontario"]
        for method in ontario:
            assert method.scientific_basis, f"{method.name} missing scientific_basis"
            assert len(method.scientific_basis) > 50, f"{method.name} scientific_basis too short"


class TestOntarioFertilizers:
    """Verify Ontario fertilizer seed data."""

    def test_ontario_fertilizers_exist(self):
        ontario_ferts = [
            f.name for f in FERTILIZER_SEEDS
            if any(c in (f.suitable_crops or []) for c in ["corn", "soybean", "wheat"])
        ]
        assert len(ontario_ferts) >= 3, f"Need at least 3 Ontario-suitable fertilizers, got {len(ontario_ferts)}"

    def test_fertilizers_have_valid_costs(self):
        for fert in FERTILIZER_SEEDS:
            assert fert.cost_per_ha_mxn > 0, f"{fert.name} has invalid cost"


# ── Seasonal calendar tests ──────────────────────────────────────


class TestOntarioSeasonClassification:
    """Verify Ontario season classification logic."""

    def test_january_is_winter(self):
        assert _classify_current_season(1, "ontario") == "winter"

    def test_march_is_spring_prep(self):
        assert _classify_current_season(3, "ontario") == "spring_prep"

    def test_april_is_spring_prep(self):
        assert _classify_current_season(4, "ontario") == "spring_prep"

    def test_may_is_growing(self):
        assert _classify_current_season(5, "ontario") == "growing"

    def test_july_is_growing(self):
        assert _classify_current_season(7, "ontario") == "growing"

    def test_october_is_fall_harvest(self):
        assert _classify_current_season(10, "ontario") == "fall_harvest"

    def test_december_is_winter(self):
        assert _classify_current_season(12, "ontario") == "winter"

    def test_default_region_is_jalisco(self):
        assert _classify_current_season(7) == "temporal"
        assert _classify_current_season(1) == "secas"


class TestOntarioSeasonalAlerts:
    """Verify Ontario seasonal calendar alerts."""

    def test_april_returns_prep_alerts(self):
        alerts = generate_seasonal_alerts(date(2026, 4, 15), region="ontario")
        crops = [a["crop"] for a in alerts]
        assert "Corn (Field)" in crops
        assert "Soybean" in crops

    def test_may_returns_planting_alerts(self):
        alerts = generate_seasonal_alerts(date(2026, 5, 15), region="ontario")
        planting = [a for a in alerts if a["alert_type"] == "siembra"]
        crops = [a["crop"] for a in planting]
        assert "Corn (Field)" in crops
        assert "Soybean" in crops

    def test_october_returns_harvest_alerts(self):
        alerts = generate_seasonal_alerts(date(2026, 10, 5), region="ontario")
        harvest = [a for a in alerts if a["alert_type"] == "cosecha"]
        crops = [a["crop"] for a in harvest]
        assert "Corn (Field)" in crops
        assert "Apple" in crops

    def test_september_returns_winter_wheat_planting(self):
        alerts = generate_seasonal_alerts(date(2026, 9, 25), region="ontario")
        wheat_planting = [
            a for a in alerts
            if a["crop"] == "Winter Wheat" and a["alert_type"] == "siembra"
        ]
        assert len(wheat_planting) == 1

    def test_may_returns_frost_warning(self):
        alerts = generate_seasonal_alerts(date(2026, 5, 10), region="ontario")
        frost = [a for a in alerts if a["alert_type"] == "frost_warning"]
        assert len(frost) >= 1

    def test_october_returns_frost_warning(self):
        alerts = generate_seasonal_alerts(date(2026, 10, 1), region="ontario")
        frost = [a for a in alerts if a["alert_type"] == "frost_warning"]
        assert len(frost) >= 1

    def test_ontario_never_returns_milpa(self):
        """Ontario calendar should never include Milpa (Mesoamerican system)."""
        for month in range(1, 13):
            alerts = generate_seasonal_alerts(date(2026, month, 15), region="ontario")
            milpa = [a for a in alerts if a["crop"] == "Milpa"]
            assert len(milpa) == 0, f"Month {month} returned Milpa alerts for Ontario"

    def test_default_region_returns_jalisco(self):
        """No region param should return Jalisco calendar (backward compat)."""
        alerts = generate_seasonal_alerts(date(2026, 3, 15))
        crops = [a["crop"] for a in alerts]
        assert "Milpa" in crops
        assert "Maiz" in crops

    def test_greenhouse_tomato_year_round(self):
        """Greenhouse Tomato should have alerts in every month."""
        for month in range(1, 13):
            alerts = generate_seasonal_alerts(date(2026, month, 15), region="ontario")
            tomato = [a for a in alerts if a["crop"] == "Greenhouse Tomato"]
            assert len(tomato) >= 1, f"Month {month}: no Greenhouse Tomato alert"

    def test_august_returns_cover_crop_window(self):
        alerts = generate_seasonal_alerts(date(2026, 8, 20), region="ontario")
        cover = [a for a in alerts if a["crop"] == "Cover Crop"]
        assert len(cover) >= 1

    def test_july_returns_wheat_harvest(self):
        alerts = generate_seasonal_alerts(date(2026, 7, 15), region="ontario")
        wheat_harvest = [
            a for a in alerts
            if a["crop"] == "Winter Wheat" and a["alert_type"] == "cosecha"
        ]
        assert len(wheat_harvest) == 1
