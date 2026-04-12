"""Tests for GET /api/farms/{farm_id}/regen-milestones."""

from datetime import datetime, timedelta
import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def farm(db):
    from cultivos.db.models import Farm
    f = Farm(name="Rancho Milestones", state="Jalisco", total_hectares=10.0)
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


@pytest.fixture
def field(db, farm):
    from cultivos.db.models import Field
    f = Field(farm_id=farm.id, name="Parcela M", crop_type="maiz", hectares=5.0)
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


def _make_treatment(db, field_id, *, organic=True, tratamiento="Aplicación",
                     created_at=None):
    from cultivos.db.models import TreatmentRecord
    t = TreatmentRecord(
        field_id=field_id,
        health_score_used=70.0,
        problema="Baja fertilidad",
        causa_probable="Suelo",
        tratamiento=tratamiento,
        costo_estimado_mxn=100,
        urgencia="baja",
        prevencion="N/A",
        organic=organic,
    )
    if created_at is not None:
        t.created_at = created_at
    db.add(t)
    db.commit()
    return t


def _make_tek_adoption(db, farm_id, method_name, adopted_at):
    from cultivos.db.models import TEKAdoption
    a = TEKAdoption(
        farm_id=farm_id,
        method_name=method_name,
        adopted_at=adopted_at,
        fields_applied=[],
    )
    db.add(a)
    db.commit()
    return a


def _make_carbon_baseline(db, field_id, recorded_at):
    from cultivos.db.models import CarbonBaseline
    c = CarbonBaseline(
        field_id=field_id,
        soc_percent=1.5,
        measurement_date=recorded_at.strftime("%Y-%m-%d"),
        lab_method="dry_combustion",
        recorded_at=recorded_at,
    )
    db.add(c)
    db.commit()
    return c


def _make_health(db, field_id, score, scored_at):
    from cultivos.db.models import HealthScore
    h = HealthScore(
        field_id=field_id,
        score=score,
        sources=["ndvi"],
        breakdown={},
        scored_at=scored_at,
    )
    db.add(h)
    db.commit()
    return h


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_unknown_farm_returns_404(client):
    res = client.get("/api/farms/9999/regen-milestones")
    assert res.status_code == 404


def test_none_achieved_new_farm(client, db, farm):
    """New farm with zero activity — all milestones unachieved, progress 0."""
    res = client.get(f"/api/farms/{farm.id}/regen-milestones")
    assert res.status_code == 200
    data = res.json()
    assert data["farm_id"] == farm.id
    assert data["milestones_achieved_count"] == 0
    assert len(data["milestones"]) == 7
    for m in data["milestones"]:
        assert m["achieved"] is False
        assert m["achieved_at"] is None
    assert data["next_milestone_es"]  # non-empty
    assert data["progress_to_next_pct"] == 0.0


def test_basic_three_achieved(client, db, farm, field):
    """Organic treatment + compost + carbon baseline → 3/8 milestones."""
    now = datetime.utcnow()
    _make_treatment(db, field.id, organic=True, tratamiento="Aplicación foliar",
                    created_at=now - timedelta(days=90))
    _make_treatment(db, field.id, organic=True, tratamiento="Composta de cocina",
                    created_at=now - timedelta(days=60))
    _make_carbon_baseline(db, field.id, now - timedelta(days=30))

    res = client.get(f"/api/farms/{farm.id}/regen-milestones")
    assert res.status_code == 200
    data = res.json()

    by_name = {m["name"]: m for m in data["milestones"]}
    assert by_name["first_organic_treatment"]["achieved"] is True
    assert by_name["first_organic_treatment"]["achieved_at"] is not None
    assert by_name["first_compost_application"]["achieved"] is True
    assert by_name["first_carbon_baseline"]["achieved"] is True
    assert by_name["first_cover_crop"]["achieved"] is False
    assert data["milestones_achieved_count"] == 3


def test_cover_crop_from_tek_adoption(client, db, farm, field):
    """TEKAdoption with cover-crop keyword satisfies first_cover_crop."""
    _make_tek_adoption(db, farm.id, "Cobertura vegetal invierno",
                       datetime.utcnow() - timedelta(days=10))
    res = client.get(f"/api/farms/{farm.id}/regen-milestones")
    data = res.json()
    by_name = {m["name"]: m for m in data["milestones"]}
    assert by_name["first_cover_crop"]["achieved"] is True


def test_score_threshold_60_and_80(client, db, farm, field):
    """One month of 100% organic treatments + avg_health 100 → regen_score 100 → 60 + 80 thresholds achieved."""
    now = datetime.utcnow()
    # Put everything in the same month via scored_at and created_at in current month
    month_day = now.replace(day=15)
    _make_treatment(db, field.id, organic=True, tratamiento="Aplicación",
                    created_at=month_day)
    _make_health(db, field.id, 100.0, month_day)
    # regen_score = 100*0.6 + 100*0.4 = 100 ≥ 80

    res = client.get(f"/api/farms/{farm.id}/regen-milestones")
    data = res.json()
    by_name = {m["name"]: m for m in data["milestones"]}
    assert by_name["reached_regen_score_60"]["achieved"] is True
    assert by_name["reached_regen_score_80"]["achieved"] is True
    # 6-month maintenance not yet — only 1 month of data
    assert by_name["maintained_regen_score_70_for_6_months"]["achieved"] is False


def test_next_milestone_suggested(client, db, farm, field):
    """Next milestone points to the first unachieved one with progress percentage."""
    # Achieve only first_organic_treatment
    _make_treatment(db, field.id, organic=True, tratamiento="Aplicación",
                    created_at=datetime.utcnow() - timedelta(days=5))
    res = client.get(f"/api/farms/{farm.id}/regen-milestones")
    data = res.json()
    assert data["milestones_achieved_count"] == 1
    assert data["next_milestone_es"]  # non-empty Spanish hint
    # progress_to_next_pct reflects 1/8 toward next
    assert 0.0 <= data["progress_to_next_pct"] <= 100.0


def test_response_has_required_fields(client, db, farm):
    res = client.get(f"/api/farms/{farm.id}/regen-milestones")
    data = res.json()
    required = {
        "farm_id", "milestones", "milestones_achieved_count",
        "next_milestone_es", "progress_to_next_pct",
    }
    assert required.issubset(data.keys())
    for m in data["milestones"]:
        assert {"name", "achieved", "achieved_at", "description_es"}.issubset(m.keys())
