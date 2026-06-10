"""T2.7 — Confidence badge per figure (Estimado/Medido/Confirmado) on economic-impact page.

RED tests — must FAIL before implementation.
GREEN after:
  - EconomicImpactOut.confidence_label field (Estimado/Medido/Confirmado)
  - API derives it: low→Estimado, medium→Medido, high→Confirmado
  - High confidence tier: >=6 health scores + >=6 treatments
  - Frontend: #econ-confidence-badge-total + #econ-confidence-badge-hero
  - JS: updateConfidenceBadges() function
  - CSS: .estimate-badge--confirmed variant
"""
import pytest

from cultivos.db.models import Farm, Field, HealthScore, TreatmentRecord


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def farm_no_data(client, db):
    """Farm with field but zero health scores — low confidence → Estimado."""
    farm = Farm(name="T27 No Data Farm", municipality="Guadalajara", tier="standard")
    db.add(farm)
    db.flush()
    field = Field(farm_id=farm.id, name="Field A", hectares=10.0)
    db.add(field)
    db.commit()
    return farm


@pytest.fixture
def farm_medium(client, db):
    """3 health scores + 3 treatments — medium confidence → Medido."""
    farm = Farm(name="T27 Medium Farm", municipality="Guadalajara", tier="standard")
    db.add(farm)
    db.flush()
    field = Field(farm_id=farm.id, name="Field A", hectares=20.0)
    db.add(field)
    db.flush()
    for score_val in [60, 65, 70]:
        db.add(HealthScore(field_id=field.id, score=score_val))
    for _ in range(3):
        db.add(TreatmentRecord(
            field_id=field.id, health_score_used=65, problema="test",
            causa_probable="test", tratamiento="Composta", urgencia="media",
            prevencion="rotacion", organic=True, costo_estimado_mxn=500,
        ))
    db.commit()
    return farm


@pytest.fixture
def farm_high(client, db):
    """6 health scores + 6 treatments — high confidence → Confirmado."""
    farm = Farm(name="T27 High Farm", municipality="Guadalajara", tier="standard")
    db.add(farm)
    db.flush()
    field = Field(farm_id=farm.id, name="Field A", hectares=20.0)
    db.add(field)
    db.flush()
    for score_val in [60, 65, 70, 75, 80, 85]:
        db.add(HealthScore(field_id=field.id, score=score_val))
    for _ in range(6):
        db.add(TreatmentRecord(
            field_id=field.id, health_score_used=72, problema="test",
            causa_probable="test", tratamiento="Composta", urgencia="media",
            prevencion="rotacion", organic=True, costo_estimado_mxn=500,
        ))
    db.commit()
    return farm


# ---------------------------------------------------------------------------
# API — confidence_label field presence
# ---------------------------------------------------------------------------

class TestT27ConfidenceLabelField:
    """economic-impact endpoint must return confidence_label field."""

    def test_confidence_label_present_in_response(self, client, farm_no_data):
        r = client.get(f"/api/farms/{farm_no_data.id}/economic-impact")
        assert r.status_code == 200
        assert "confidence_label" in r.json()

    def test_confidence_label_is_string(self, client, farm_no_data):
        r = client.get(f"/api/farms/{farm_no_data.id}/economic-impact")
        assert r.status_code == 200
        assert isinstance(r.json()["confidence_label"], str)

    def test_confidence_label_only_valid_values(self, client, farm_no_data):
        r = client.get(f"/api/farms/{farm_no_data.id}/economic-impact")
        assert r.status_code == 200
        assert r.json()["confidence_label"] in {"Estimado", "Medido", "Confirmado"}


# ---------------------------------------------------------------------------
# API — mapping: low→Estimado, medium→Medido, high→Confirmado
# ---------------------------------------------------------------------------

class TestT27ConfidenceLabelMapping:
    """Correct label assigned based on data availability."""

    def test_low_confidence_gives_estimado(self, client, farm_no_data):
        r = client.get(f"/api/farms/{farm_no_data.id}/economic-impact")
        assert r.status_code == 200
        data = r.json()
        assert data["confidence"] == "low"
        assert data["confidence_label"] == "Estimado"

    def test_medium_confidence_gives_medido(self, client, farm_medium):
        r = client.get(f"/api/farms/{farm_medium.id}/economic-impact")
        assert r.status_code == 200
        data = r.json()
        assert data["confidence"] == "medium"
        assert data["confidence_label"] == "Medido"

    def test_high_confidence_gives_confirmado(self, client, farm_high):
        r = client.get(f"/api/farms/{farm_high.id}/economic-impact")
        assert r.status_code == 200
        data = r.json()
        assert data["confidence"] == "high"
        assert data["confidence_label"] == "Confirmado"

    def test_no_fields_farm_gives_estimado(self, client, db):
        """Farm with no fields at all → Estimado."""
        farm = Farm(name="T27 Empty Farm", municipality="Guadalajara", tier="standard")
        db.add(farm)
        db.commit()
        r = client.get(f"/api/farms/{farm.id}/economic-impact")
        assert r.status_code == 200
        assert r.json()["confidence_label"] == "Estimado"


# ---------------------------------------------------------------------------
# API — high confidence tier threshold
# ---------------------------------------------------------------------------

class TestT27HighConfidenceThreshold:
    """>=6 health scores AND >=6 treatments must produce confidence==high."""

    def test_high_confidence_requires_6_scores(self, client, farm_high):
        r = client.get(f"/api/farms/{farm_high.id}/economic-impact")
        assert r.status_code == 200
        assert r.json()["confidence"] == "high"

    def test_five_scores_not_high(self, client, db):
        """5 scores + 5 treatments still only medium (below threshold)."""
        farm = Farm(name="T27 Five Farm", municipality="Guadalajara", tier="standard")
        db.add(farm)
        db.flush()
        field = Field(farm_id=farm.id, name="F", hectares=10.0)
        db.add(field)
        db.flush()
        for s in [60, 65, 70, 75, 80]:
            db.add(HealthScore(field_id=field.id, score=s))
        for _ in range(5):
            db.add(TreatmentRecord(
                field_id=field.id, health_score_used=70, problema="test",
                causa_probable="test", tratamiento="Composta", urgencia="media",
                prevencion="rotacion", organic=True, costo_estimado_mxn=500,
            ))
        db.commit()
        data = client.get(f"/api/farms/{farm.id}/economic-impact").json()
        assert data["confidence"] == "medium"


# ---------------------------------------------------------------------------
# Frontend HTML — confidence badge elements per figure
# ---------------------------------------------------------------------------

class TestT27FrontendHTML:
    """economic-impact.html must have per-figure confidence badge elements."""

    def test_confidence_badge_total_exists(self, client):
        r = client.get("/impacto-economico")
        assert r.status_code == 200
        assert 'id="econ-confidence-badge-total"' in r.text

    def test_confidence_badge_hero_exists(self, client):
        r = client.get("/impacto-economico")
        assert r.status_code == 200
        assert 'id="econ-confidence-badge-hero"' in r.text

    def test_confidence_badges_have_estimate_badge_class(self, client):
        r = client.get("/impacto-economico")
        assert r.status_code == 200
        assert "estimate-badge" in r.text


# ---------------------------------------------------------------------------
# Frontend JS — updateConfidenceBadges function
# ---------------------------------------------------------------------------

class TestT27FrontendJS:
    """economic-impact.js must contain updateConfidenceBadges function."""

    def _js(self, client):
        r = client.get("/economic-impact.js")
        assert r.status_code == 200
        return r.text

    def test_update_confidence_badges_function_exists(self, client):
        assert "updateConfidenceBadges" in self._js(client)

    def test_js_reads_confidence_label_from_data(self, client):
        js = self._js(client)
        assert "confidence_label" in js


# ---------------------------------------------------------------------------
# CSS — badge modifier variants
# ---------------------------------------------------------------------------

class TestT27CSS:
    """styles.css must have badge modifier for each confidence level."""

    def _css(self, client):
        r = client.get("/styles.css")
        assert r.status_code == 200
        return r.text

    def test_css_has_confirmed_variant(self, client):
        assert "estimate-badge--confirmed" in self._css(client)

    def test_css_has_measured_variant(self, client):
        # already exists from T2.1 area — verify still present
        assert "estimate-badge--measured" in self._css(client)
