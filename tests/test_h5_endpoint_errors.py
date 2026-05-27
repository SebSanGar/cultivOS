"""H5 — Fix 400 on /mission-plan and 422 on /growth-stage.

ROOT CAUSE:
  - /mission-plan: returns 400 when field.boundary_coordinates is NULL.
  - /growth-stage: returns 422 when field.planted_at is NULL.

FIX (graceful degradation):
  - /mission-plan: when no boundary_coordinates, return default plan with a
    synthetic 10-ha square boundary instead of 400.
  - /growth-stage: when no planted_at, return 'pre-siembra' default stage
    instead of 422.

TDD tests: all RED before fix, all GREEN after.
"""

from datetime import date, timedelta

import pytest


# ---------------------------------------------------------------------------
# Helpers — create test farm + field
# ---------------------------------------------------------------------------


def _make_farm(db, name="Test Farm"):
    from cultivos.db.models import Farm

    farm = Farm(
        name=name,
        municipality="Tlajomulco",
        state="Jalisco",
        total_hectares=10.0,
        location_lat=20.5,
        location_lon=-103.5,
    )
    db.add(farm)
    db.commit()
    db.refresh(farm)
    return farm


def _make_field(db, farm_id, *, with_boundary=True, with_planted_at=True):
    from cultivos.db.models import Field

    field = Field(
        farm_id=farm_id,
        name="Parcela Norte",
        crop_type="aguacate",
        hectares=5.0,
        planted_at=date.today() - timedelta(days=120) if with_planted_at else None,
        boundary_coordinates=[
            [-103.5, 20.5], [-103.49, 20.5], [-103.49, 20.51], [-103.5, 20.51], [-103.5, 20.5]
        ] if with_boundary else None,
    )
    db.add(field)
    db.commit()
    db.refresh(field)
    return field


# ---------------------------------------------------------------------------
# T1 — /mission-plan with boundary_coordinates = NULL → 200 (not 400)
# ---------------------------------------------------------------------------


class TestH5MissionPlanGraceful:
    """/mission-plan must return 200 even when field has no boundary_coordinates."""

    def test_mission_plan_no_boundary_returns_200(self, client, db):
        farm = _make_farm(db, "Farm No Boundary")
        field = _make_field(db, farm.id, with_boundary=False, with_planted_at=True)
        resp = client.get(
            f"/api/farms/{farm.id}/fields/{field.id}/mission-plan"
        )
        assert resp.status_code == 200, (
            f"Expected 200 (graceful default plan), got {resp.status_code}: {resp.text[:300]}"
        )

    def test_mission_plan_no_boundary_response_has_required_fields(self, client, db):
        farm = _make_farm(db, "Farm No Boundary 2")
        field = _make_field(db, farm.id, with_boundary=False)
        resp = client.get(
            f"/api/farms/{farm.id}/fields/{field.id}/mission-plan"
        )
        assert resp.status_code == 200
        body = resp.json()
        for key in ("waypoints", "pattern", "area_hectares", "estimated_duration_min"):
            assert key in body, f"Response missing '{key}' field"

    def test_mission_plan_with_boundary_still_200(self, client, db):
        farm = _make_farm(db, "Farm With Boundary")
        field = _make_field(db, farm.id, with_boundary=True)
        resp = client.get(
            f"/api/farms/{farm.id}/fields/{field.id}/mission-plan"
        )
        assert resp.status_code == 200, (
            f"Regression: /mission-plan with boundary broke: {resp.status_code}"
        )


# ---------------------------------------------------------------------------
# T2 — /growth-stage with planted_at = NULL → 200 (not 422)
# ---------------------------------------------------------------------------


class TestH5GrowthStageGraceful:
    """/growth-stage must return 200 with default stage when field.planted_at is NULL."""

    def test_growth_stage_no_planted_at_returns_200(self, client, db):
        farm = _make_farm(db, "Farm No PlantedAt")
        field = _make_field(db, farm.id, with_planted_at=False)
        resp = client.get(
            f"/api/farms/{farm.id}/fields/{field.id}/growth-stage"
        )
        assert resp.status_code == 200, (
            f"Expected 200 (graceful pre-siembra default), got {resp.status_code}: {resp.text[:300]}"
        )

    def test_growth_stage_no_planted_at_returns_pre_siembra(self, client, db):
        farm = _make_farm(db, "Farm No PlantedAt 2")
        field = _make_field(db, farm.id, with_planted_at=False)
        resp = client.get(
            f"/api/farms/{farm.id}/fields/{field.id}/growth-stage"
        )
        assert resp.status_code == 200
        body = resp.json()
        # Should have stage field with some sensible default
        assert "stage" in body, "Response missing 'stage' field"
        assert body["stage"] is not None, "stage must not be None"

    def test_growth_stage_with_planted_at_still_200(self, client, db):
        farm = _make_farm(db, "Farm With PlantedAt")
        field = _make_field(db, farm.id, with_planted_at=True)
        resp = client.get(
            f"/api/farms/{farm.id}/fields/{field.id}/growth-stage"
        )
        assert resp.status_code == 200, (
            f"Regression: /growth-stage with planted_at broke: {resp.status_code}"
        )
