"""CR7 — Bilingual EN strings in Python service layer (yield, stress, fusion).

Verifies that yield_model, stress_composite, and fusion services return
English-language recommendation/note strings alongside Spanish ones.
"""

import pytest

from cultivos.services.intelligence.yield_model import predict_yield
import cultivos.services.intelligence.stress_composite as _sc_mod
from cultivos.services.intelligence.stress_composite import compute_stress_composite

_RECOMMENDATIONS = _sc_mod._RECOMMENDATIONS
_RECOMMENDATIONS_EN = getattr(_sc_mod, "_RECOMMENDATIONS_EN", {})
from cultivos.services.crop.fusion import validate_sensor_fusion


# ── yield_model ───────────────────────────────────────────────────────────────

class TestYieldModelBilingual:
    def test_high_health_returns_nota_en(self):
        result = predict_yield("aguacate", 5.0, 90.0)
        assert "nota_en" in result
        nota_en = result["nota_en"]
        assert isinstance(nota_en, str)
        assert len(nota_en) > 0

    def test_high_health_nota_en_is_english(self):
        result = predict_yield("aguacate", 5.0, 90.0)
        nota_en = result["nota_en"]
        # Must not contain Spanish accented chars or common Spanish words
        assert "Rendimiento" not in nota_en
        assert "Campo" not in nota_en
        assert "buen" not in nota_en
        # Must contain English indicator
        assert any(w in nota_en for w in ["expected", "Good", "good", "field", "Field"])

    def test_medium_health_nota_en_is_english(self):
        result = predict_yield("maiz", 10.0, 60.0)
        assert "nota_en" in result
        nota_en = result["nota_en"]
        assert "Moderado" not in nota_en
        assert "mejorar" not in nota_en
        assert any(w in nota_en for w in ["moderate", "Moderate", "yield", "health"])

    def test_low_health_nota_en_is_english(self):
        result = predict_yield("frijol", 3.0, 20.0)
        assert "nota_en" in result
        nota_en = result["nota_en"]
        assert "estres" not in nota_en.lower()
        assert "atencion" not in nota_en
        assert any(w in nota_en for w in ["stress", "urgent", "reduced", "Reduced"])

    def test_nota_es_still_present(self):
        result = predict_yield("aguacate", 5.0, 90.0)
        assert "nota" in result
        assert "Rendimiento" in result["nota"] or "Campo" in result["nota"]


# ── stress_composite ──────────────────────────────────────────────────────────

class TestStressCompositeEN:
    def test_recommendations_en_dict_exists(self):
        assert "_RECOMMENDATIONS_EN" in dir(__import__(
            "cultivos.services.intelligence.stress_composite",
            fromlist=["_RECOMMENDATIONS_EN"]
        ))

    def test_recommendations_en_has_all_levels(self):
        levels = {"none", "low", "moderate", "high", "critical"}
        assert set(_RECOMMENDATIONS_EN.keys()) == levels

    def test_recommendations_en_values_are_english(self):
        for level, text in _RECOMMENDATIONS_EN.items():
            assert isinstance(text, str)
            assert len(text) > 0
            # No Spanish-only words
            assert "optimas" not in text
            assert "estres" not in text.lower()
            assert "detectado" not in text
            assert "requerida" not in text

    def test_compute_stress_composite_returns_recommendation_en(self, db):
        from cultivos.db.models import Farm, Field
        farm = Farm(name="Test Farm CR7", municipality="Zapopan", total_hectares=10.0)
        db.add(farm)
        db.flush()
        field = Field(farm_id=farm.id, name="Test Field", crop_type="maiz", hectares=5.0)
        db.add(field)
        db.flush()

        result = compute_stress_composite(field, db)
        assert "recommendation_en" in result
        assert isinstance(result["recommendation_en"], str)
        assert len(result["recommendation_en"]) > 0

    def test_recommendation_en_matches_level(self, db):
        from cultivos.db.models import Farm, Field
        farm = Farm(name="Test Farm CR7b", municipality="Zapopan", total_hectares=10.0)
        db.add(farm)
        db.flush()
        field = Field(farm_id=farm.id, name="Test Field b", crop_type="maiz", hectares=5.0)
        db.add(field)
        db.flush()

        result = compute_stress_composite(field, db)
        level = result["stress_level"]
        assert result["recommendation_en"] == _RECOMMENDATIONS_EN[level]

    def test_recommendation_es_still_present(self, db):
        from cultivos.db.models import Farm, Field
        farm = Farm(name="Test Farm CR7c", municipality="Zapopan", total_hectares=10.0)
        db.add(farm)
        db.flush()
        field = Field(farm_id=farm.id, name="Test Field c", crop_type="maiz", hectares=5.0)
        db.add(field)
        db.flush()

        result = compute_stress_composite(field, db)
        assert "recommendation_es" in result


# ── fusion ────────────────────────────────────────────────────────────────────

class TestFusionEN:
    def test_all_healthy_returns_assessment_en(self):
        result = validate_sensor_fusion(
            ndvi={"ndvi_mean": 0.75, "ndvi_std": 0.05, "stress_pct": 5.0},
            thermal={"stress_pct": 10.0, "temp_mean": 28.0, "irrigation_deficit": False},
        )
        assert "assessment_en" in result
        assert isinstance(result["assessment_en"], str)
        assert len(result["assessment_en"]) > 0

    def test_all_healthy_assessment_en_is_english(self):
        result = validate_sensor_fusion(
            ndvi={"ndvi_mean": 0.75, "ndvi_std": 0.05, "stress_pct": 5.0},
            thermal={"stress_pct": 10.0, "temp_mean": 28.0, "irrigation_deficit": False},
        )
        assessment_en = result["assessment_en"]
        assert "sensores" not in assessment_en
        assert "coinciden" not in assessment_en
        assert "campo" not in assessment_en.lower()
        assert any(w in assessment_en for w in ["sensor", "Sensor", "field", "Field", "good", "All", "all"])

    def test_stressed_assessment_en_is_english(self):
        result = validate_sensor_fusion(
            ndvi={"ndvi_mean": 0.25, "ndvi_std": 0.15, "stress_pct": 60.0},
            thermal={"stress_pct": 55.0, "temp_mean": 38.0, "irrigation_deficit": True},
        )
        assert "assessment_en" in result
        en = result["assessment_en"]
        assert "recomienda" not in en
        assert "inmediata" not in en
        assert any(w in en for w in ["stress", "action", "immediate", "Action", "Stress"])

    def test_contradictions_assessment_en_is_english(self):
        result = validate_sensor_fusion(
            ndvi={"ndvi_mean": 0.75, "ndvi_std": 0.05, "stress_pct": 5.0},
            thermal={"stress_pct": 55.0, "temp_mean": 38.0, "irrigation_deficit": True},
        )
        # NDVI healthy + thermal stressed → contradiction
        assert len(result["contradictions"]) > 0
        en = result["assessment_en"]
        assert "inconsistencia" not in en
        assert any(w in en for w in ["inconsisten", "contradiction", "discrepan", "mismatch"])

    def test_assessment_es_still_present(self):
        result = validate_sensor_fusion(
            ndvi={"ndvi_mean": 0.75, "ndvi_std": 0.05, "stress_pct": 5.0},
        )
        assert "assessment" in result
        assert isinstance(result["assessment"], str)

    def test_no_sensors_returns_assessment_en(self):
        result = validate_sensor_fusion()
        assert "assessment_en" in result
        assert isinstance(result["assessment_en"], str)


# ── API endpoints ─────────────────────────────────────────────────────────────

@pytest.fixture
def seeded_farm_field(db):
    from cultivos.db.models import Farm, Field
    farm = Farm(name="CR7 Farm", municipality="Zapopan", total_hectares=20.0)
    db.add(farm)
    db.flush()
    field = Field(farm_id=farm.id, name="CR7 Field", crop_type="maiz", hectares=5.0)
    db.add(field)
    db.flush()
    db.commit()
    return farm, field


class TestYieldAPIEN:
    def test_yield_endpoint_returns_nota_en(self, client, seeded_farm_field):
        farm, field = seeded_farm_field
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/yield")
        assert resp.status_code == 200
        data = resp.json()
        assert "nota_en" in data
        assert isinstance(data["nota_en"], str)
        assert len(data["nota_en"]) > 0

    def test_yield_endpoint_nota_en_is_english(self, client, seeded_farm_field):
        farm, field = seeded_farm_field
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/yield")
        data = resp.json()
        nota_en = data["nota_en"]
        assert "Rendimiento" not in nota_en
        assert "estres" not in nota_en.lower()


class TestFusionAPIEN:
    def test_fusion_post_returns_assessment_en(self, client):
        payload = {
            "ndvi": {"ndvi_mean": 0.7, "ndvi_std": 0.05, "stress_pct": 10.0},
            "thermal": {"stress_pct": 15.0, "temp_mean": 28.0, "irrigation_deficit": False},
        }
        resp = client.post("/api/analysis/fusion", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "assessment_en" in data
        assert isinstance(data["assessment_en"], str)
        assert len(data["assessment_en"]) > 0

    def test_fusion_assessment_en_is_english(self, client):
        payload = {
            "ndvi": {"ndvi_mean": 0.7, "ndvi_std": 0.05, "stress_pct": 10.0},
        }
        resp = client.post("/api/analysis/fusion", json=payload)
        data = resp.json()
        assert "sensores" not in data["assessment_en"]
        assert "campo" not in data["assessment_en"].lower()


class TestStressIndexAPIEN:
    def test_stress_index_endpoint_returns_recommendation_en(self, client, seeded_farm_field):
        farm, field = seeded_farm_field
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/stress-index")
        assert resp.status_code == 200
        data = resp.json()
        assert "recommendation_en" in data
        assert isinstance(data["recommendation_en"], str)
        assert len(data["recommendation_en"]) > 0
