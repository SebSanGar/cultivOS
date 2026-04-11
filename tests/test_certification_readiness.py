"""Tests for GET /api/farms/{farm_id}/certification-readiness."""

from datetime import datetime, timedelta
import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def farm(db):
    from cultivos.db.models import Farm
    f = Farm(name="Rancho Certif", state="Jalisco", total_hectares=10.0)
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


@pytest.fixture
def field(db, farm):
    from cultivos.db.models import Field
    f = Field(farm_id=farm.id, name="Parcela A", crop_type="maiz", hectares=5.0)
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


def _make_treatment(db, field_id, *, organic=True, tratamiento="Composta organica"):
    from cultivos.db.models import TreatmentRecord
    t = TreatmentRecord(
        field_id=field_id,
        health_score_used=70.0,
        problema="Baja fertilidad",
        causa_probable="Suelo degradado",
        tratamiento=tratamiento,
        costo_estimado_mxn=500,
        urgencia="media",
        prevencion="Aplicar anualmente",
        organic=organic,
    )
    db.add(t)
    db.commit()
    return t


def _make_soil(db, field_id, organic_matter_pct, days_ago=0):
    from cultivos.db.models import SoilAnalysis
    s = SoilAnalysis(
        field_id=field_id,
        organic_matter_pct=organic_matter_pct,
        sampled_at=datetime.utcnow() - timedelta(days=days_ago),
        ph=6.5,
    )
    db.add(s)
    db.commit()
    return s


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_unknown_farm_returns_404(client):
    res = client.get("/api/farms/9999/certification-readiness")
    assert res.status_code == 404


def test_empty_farm_returns_zeros(client, db, farm):
    """Farm with no fields/treatments/soil: all checks False, 0%."""
    res = client.get(f"/api/farms/{farm.id}/certification-readiness")
    assert res.status_code == 200
    data = res.json()
    assert data["synthetic_inputs_free"] is True   # no synthetic inputs → qualifies
    assert data["treatment_organic_only"] is True   # no treatments → qualifies
    assert data["soc_trend_positive"] is False      # no soil data
    assert data["cover_crop_days_gte_90"] is False  # no cover crop records
    assert data["overall_pct"] == 50.0              # 2/4 checks pass


def test_all_organic_positive_soc_is_100_pct(client, db, farm, field):
    """All-organic treatments + rising SOC = 100%."""
    _make_treatment(db, field.id, organic=True, tratamiento="cobertura vegetal organica")
    _make_treatment(db, field.id, organic=True, tratamiento="Abono verde cobertura vegetal")
    _make_treatment(db, field.id, organic=True, tratamiento="Cubierta vegetal invierno")
    _make_soil(db, field.id, organic_matter_pct=1.5, days_ago=60)
    _make_soil(db, field.id, organic_matter_pct=2.0, days_ago=30)
    _make_soil(db, field.id, organic_matter_pct=2.5, days_ago=0)

    res = client.get(f"/api/farms/{farm.id}/certification-readiness")
    assert res.status_code == 200
    data = res.json()
    assert data["synthetic_inputs_free"] is True
    assert data["treatment_organic_only"] is True
    assert data["soc_trend_positive"] is True
    assert data["cover_crop_days_gte_90"] is True
    assert data["overall_pct"] == 100.0


def test_synthetic_treatment_fails_organic_check(client, db, farm, field):
    """One synthetic treatment makes synthetic_inputs_free and treatment_organic_only False."""
    _make_treatment(db, field.id, organic=True)
    _make_treatment(db, field.id, organic=False, tratamiento="Herbicida quimico")
    _make_soil(db, field.id, organic_matter_pct=1.5, days_ago=30)
    _make_soil(db, field.id, organic_matter_pct=2.0, days_ago=0)

    res = client.get(f"/api/farms/{farm.id}/certification-readiness")
    assert res.status_code == 200
    data = res.json()
    assert data["synthetic_inputs_free"] is False
    assert data["treatment_organic_only"] is False
    assert data["soc_trend_positive"] is True  # SOC still rising
    assert data["overall_pct"] == 25.0         # 1/4 checks pass (SOC only)


def test_negative_soc_trend_fails_soc_check(client, db, farm, field):
    """Declining SOC → soc_trend_positive = False."""
    _make_treatment(db, field.id, organic=True)
    _make_soil(db, field.id, organic_matter_pct=3.0, days_ago=60)
    _make_soil(db, field.id, organic_matter_pct=2.5, days_ago=30)
    _make_soil(db, field.id, organic_matter_pct=2.0, days_ago=0)

    res = client.get(f"/api/farms/{farm.id}/certification-readiness")
    assert res.status_code == 200
    data = res.json()
    assert data["soc_trend_positive"] is False
    assert data["synthetic_inputs_free"] is True


def test_only_one_soil_record_fails_soc_check(client, db, farm, field):
    """Single soil sample = cannot compute trend → False."""
    _make_soil(db, field.id, organic_matter_pct=2.5, days_ago=0)

    res = client.get(f"/api/farms/{farm.id}/certification-readiness")
    data = res.json()
    assert data["soc_trend_positive"] is False


def test_cover_crop_keyword_counts(client, db, farm, field):
    """3 cover crop treatments counts as >= 90 days."""
    for _ in range(3):
        _make_treatment(db, field.id, organic=True, tratamiento="cobertura vegetal organica")

    res = client.get(f"/api/farms/{farm.id}/certification-readiness")
    data = res.json()
    assert data["cover_crop_days_gte_90"] is True


def test_cover_crop_below_90_days(client, db, farm, field):
    """2 cover crop treatments = 60 days → False."""
    _make_treatment(db, field.id, organic=True, tratamiento="cobertura organica")
    _make_treatment(db, field.id, organic=True, tratamiento="abono verde")

    res = client.get(f"/api/farms/{farm.id}/certification-readiness")
    data = res.json()
    assert data["cover_crop_days_gte_90"] is False


def test_overall_pct_is_correct_fraction(client, db, farm, field):
    """Farm with 3/4 checks passing → 75%."""
    _make_treatment(db, field.id, organic=True, tratamiento="cubierta vegetal")
    _make_treatment(db, field.id, organic=True, tratamiento="cubierta organica")
    _make_treatment(db, field.id, organic=True, tratamiento="cobertura de invierno")
    _make_soil(db, field.id, organic_matter_pct=1.0, days_ago=60)
    _make_soil(db, field.id, organic_matter_pct=2.0, days_ago=0)
    # No synthetic inputs, positive SOC, cover crop OK, treatment organic OK → 100%
    res = client.get(f"/api/farms/{farm.id}/certification-readiness")
    data = res.json()
    assert data["overall_pct"] == 100.0  # all 4 pass


def test_response_has_required_fields(client, db, farm):
    """Response schema includes all expected fields."""
    res = client.get(f"/api/farms/{farm.id}/certification-readiness")
    data = res.json()
    required_fields = {
        "synthetic_inputs_free", "treatment_organic_only",
        "soc_trend_positive", "cover_crop_days_gte_90", "overall_pct"
    }
    assert required_fields.issubset(data.keys())
