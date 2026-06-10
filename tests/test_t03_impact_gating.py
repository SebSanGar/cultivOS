"""T0.3 — compute_farmer_impact: only emit peso when data is sufficient.

Rule: savings_state = "active" when len(health_scores)>1 AND treatments_applied>0.
Else savings_state = "insufficient_data", estimated_savings_mxn = 0.

Tests FAIL before T0.3 implementation, PASS after.
"""

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def farm_with_data(db):
    """Farm with >1 health score AND applied treatments."""
    from cultivos.db.models import Farm, Field, HealthScore, TreatmentRecord
    from datetime import datetime

    farm = Farm(name="T03 Active Farm", municipality="Guadalajara", total_hectares=10.0)
    db.add(farm)
    db.flush()
    field = Field(farm_id=farm.id, name="Norte", hectares=10.0, crop_type="maize")
    db.add(field)
    db.flush()
    db.add(HealthScore(field_id=field.id, score=60))
    db.add(HealthScore(field_id=field.id, score=75))
    db.add(TreatmentRecord(
        field_id=field.id,
        health_score_used=60,
        problema="Estres",
        causa_probable="Sequia",
        tratamiento="Riego",
        urgencia="alta",
        prevencion="Monitoreo",
        applied_at=datetime(2026, 1, 15),
    ))
    db.commit()
    return farm.id


@pytest.fixture()
def farm_one_score_no_treatments(db):
    """Farm with only 1 health score and no applied treatments."""
    from cultivos.db.models import Farm, Field, HealthScore

    farm = Farm(name="T03 New Farm", municipality="Guadalajara", total_hectares=5.0)
    db.add(farm)
    db.flush()
    field = Field(farm_id=farm.id, name="Sur", hectares=5.0, crop_type="maize")
    db.add(field)
    db.flush()
    db.add(HealthScore(field_id=field.id, score=55))
    db.commit()
    return farm.id


@pytest.fixture()
def farm_no_scores(db):
    """Farm with no health scores."""
    from cultivos.db.models import Farm, Field

    farm = Farm(name="T03 Empty Farm", municipality="Guadalajara", total_hectares=5.0)
    db.add(farm)
    db.flush()
    db.add(Field(farm_id=farm.id, name="Este", hectares=5.0, crop_type="maize"))
    db.commit()
    return farm.id


# ---------------------------------------------------------------------------
# T1 — savings_state field present in output
# ---------------------------------------------------------------------------


class TestSavingsStateField:
    def test_active_farm_has_savings_state(self, db, farm_with_data):
        from cultivos.services.intelligence.analytics import compute_farmer_impact
        result = compute_farmer_impact(db, farm_with_data)
        assert result is not None
        assert "savings_state" in result, (
            "T0.3: compute_farmer_impact must return savings_state field"
        )

    def test_new_farm_has_savings_state(self, db, farm_one_score_no_treatments):
        from cultivos.services.intelligence.analytics import compute_farmer_impact
        result = compute_farmer_impact(db, farm_one_score_no_treatments)
        assert result is not None
        assert "savings_state" in result, (
            "T0.3: compute_farmer_impact must return savings_state field even for new farms"
        )


# ---------------------------------------------------------------------------
# T2 — State values correct
# ---------------------------------------------------------------------------


class TestSavingsStateValues:
    def test_active_farm_state_is_active(self, db, farm_with_data):
        from cultivos.services.intelligence.analytics import compute_farmer_impact
        result = compute_farmer_impact(db, farm_with_data)
        assert result["savings_state"] == "active", (
            f"T0.3: farm with scores>1 and treatments>0 should be 'active', got {result['savings_state']!r}"
        )

    def test_new_farm_state_is_insufficient(self, db, farm_one_score_no_treatments):
        from cultivos.services.intelligence.analytics import compute_farmer_impact
        result = compute_farmer_impact(db, farm_one_score_no_treatments)
        assert result["savings_state"] == "insufficient_data", (
            f"T0.3: new farm (1 score, no treatments) should be 'insufficient_data', got {result['savings_state']!r}"
        )

    def test_empty_farm_state_is_insufficient(self, db, farm_no_scores):
        from cultivos.services.intelligence.analytics import compute_farmer_impact
        result = compute_farmer_impact(db, farm_no_scores)
        assert result["savings_state"] == "insufficient_data"


# ---------------------------------------------------------------------------
# T3 — Peso only emitted when active; zero when insufficient
# ---------------------------------------------------------------------------


class TestSavingsGating:
    def test_active_farm_emits_nonzero_savings(self, db, farm_with_data):
        from cultivos.services.intelligence.analytics import compute_farmer_impact
        result = compute_farmer_impact(db, farm_with_data)
        assert result["savings_state"] == "active"
        assert result["estimated_savings_mxn"] > 0, (
            "T0.3: active farm must have positive estimated_savings_mxn"
        )

    def test_insufficient_farm_emits_zero_savings(self, db, farm_one_score_no_treatments):
        from cultivos.services.intelligence.analytics import compute_farmer_impact
        result = compute_farmer_impact(db, farm_one_score_no_treatments)
        assert result["savings_state"] == "insufficient_data"
        assert result["estimated_savings_mxn"] == 0, (
            "T0.3: insufficient farm must have estimated_savings_mxn = 0"
        )

    def test_empty_farm_emits_zero_savings(self, db, farm_no_scores):
        from cultivos.services.intelligence.analytics import compute_farmer_impact
        result = compute_farmer_impact(db, farm_no_scores)
        assert result["estimated_savings_mxn"] == 0


# ---------------------------------------------------------------------------
# T4 — Forward line present for insufficient farms
# ---------------------------------------------------------------------------


class TestForwardLine:
    def test_insufficient_farm_has_forward_line(self, db, farm_one_score_no_treatments):
        from cultivos.services.intelligence.analytics import compute_farmer_impact
        result = compute_farmer_impact(db, farm_one_score_no_treatments)
        assert "savings_forward_line" in result, (
            "T0.3: insufficient_data farms must include savings_forward_line"
        )
        line = result["savings_forward_line"] or ""
        assert len(line) > 10, (
            "T0.3: savings_forward_line must be a non-trivial string"
        )

    def test_active_farm_forward_line_absent_or_none(self, db, farm_with_data):
        from cultivos.services.intelligence.analytics import compute_farmer_impact
        result = compute_farmer_impact(db, farm_with_data)
        # Either absent or None — active farm doesn't need forward line
        assert result.get("savings_forward_line") is None or "savings_forward_line" not in result


# ---------------------------------------------------------------------------
# T5 — health_observed is present
# ---------------------------------------------------------------------------


class TestHealthObservedField:
    def test_active_farm_has_health_observed(self, db, farm_with_data):
        from cultivos.services.intelligence.analytics import compute_farmer_impact
        result = compute_farmer_impact(db, farm_with_data)
        assert "health_observed" in result, (
            "T0.3: result must include health_observed (real DB data flag)"
        )
        assert result["health_observed"] is True, (
            "T0.3: health_observed must be True when health scores exist"
        )

    def test_empty_farm_health_observed_false(self, db, farm_no_scores):
        from cultivos.services.intelligence.analytics import compute_farmer_impact
        result = compute_farmer_impact(db, farm_no_scores)
        assert "health_observed" in result
        assert result["health_observed"] is False
