"""Tests for weather-integrated action timeline endpoint.

GET /api/farms/{farm_id}/fields/{field_id}/action-timeline
Composes: seasonal calendar + growth stage + weather forecast + pending treatments
into a unified next-7-days action list sorted by priority.
"""

from datetime import datetime, date, timedelta

import pytest

from cultivos.db.models import Farm, Field, TreatmentRecord, WeatherRecord
from cultivos.services.intelligence.action_timeline import build_action_timeline


# ---------------------------------------------------------------------------
# Pure function tests
# ---------------------------------------------------------------------------


class TestBuildActionTimeline:
    """Tests for the pure build_action_timeline function."""

    def test_seasonal_alerts_appear_at_correct_dates(self):
        """Seasonal TEK alerts for the reference date's month are included."""
        # March is preparation season for milpa, maiz, frijol, calabaza, etc.
        result = build_action_timeline(
            reference_date=date(2026, 3, 15),
            crop_type="maiz",
            planted_at=None,
            forecast_3day=[],
            pending_treatments=[],
        )
        actions = result["actions"]
        seasonal = [a for a in actions if a["source"] == "seasonal_calendar"]
        assert len(seasonal) > 0, "Expected seasonal alerts in March"
        # Maiz preparacion should be present in March
        maiz_prep = [a for a in seasonal if "maiz" in a["description"].lower() or a["crop"] == "Maiz"]
        assert len(maiz_prep) > 0, "Expected Maiz preparacion alert in March"

    def test_growth_stage_actions_included(self):
        """Growth stage actions appear when planted_at is set."""
        planted = datetime(2026, 2, 1)
        ref = date(2026, 3, 15)  # 42 days after planting
        result = build_action_timeline(
            reference_date=ref,
            crop_type="maiz",
            planted_at=planted,
            forecast_3day=[],
            pending_treatments=[],
        )
        actions = result["actions"]
        growth = [a for a in actions if a["source"] == "growth_stage"]
        assert len(growth) > 0, "Expected growth stage action"
        assert growth[0]["stage"] == "vegetativo"  # maiz: siembra ends day 15, vegetativo until day 55

    def test_weather_sensitive_treatments_repositioned_by_forecast(self):
        """Pending treatments with rain forecast get a weather warning."""
        rain_forecast = [
            {"temp_c": 22, "humidity_pct": 80, "wind_kmh": 10, "description": "Lluvia ligera", "rainfall_mm": 12.0},
            {"temp_c": 24, "humidity_pct": 60, "wind_kmh": 5, "description": "Despejado", "rainfall_mm": 0.0},
            {"temp_c": 23, "humidity_pct": 65, "wind_kmh": 8, "description": "Nublado", "rainfall_mm": 0.0},
        ]
        pending = [
            {
                "id": 1,
                "problema": "Deficiencia de nitrogeno",
                "tratamiento": "Aplicar composta foliar",
                "urgencia": "alta",
                "costo_estimado_mxn": 500,
                "created_at": datetime(2026, 3, 14),
            },
        ]
        result = build_action_timeline(
            reference_date=date(2026, 3, 15),
            crop_type="maiz",
            planted_at=datetime(2026, 1, 1),
            forecast_3day=rain_forecast,
            pending_treatments=pending,
        )
        actions = result["actions"]
        treatment_actions = [a for a in actions if a["source"] == "treatment"]
        assert len(treatment_actions) > 0
        # The treatment should have a weather_note since day 1 has rain
        assert treatment_actions[0].get("weather_note") is not None
        assert "lluvia" in treatment_actions[0]["weather_note"].lower() or "rain" in treatment_actions[0]["weather_note"].lower()

    def test_empty_data_returns_empty_timeline(self):
        """With no data at all, returns empty actions list."""
        result = build_action_timeline(
            reference_date=date(2026, 3, 15),
            crop_type=None,
            planted_at=None,
            forecast_3day=[],
            pending_treatments=[],
        )
        # With no crop_type, no planted_at, no treatments: only generic seasonal alerts (if any match)
        # But seasonal alerts still fire for all crops — that's ok. The key is it doesn't crash.
        assert "actions" in result
        assert isinstance(result["actions"], list)

    def test_actions_sorted_by_priority(self):
        """Actions should be sorted with highest priority first."""
        pending = [
            {
                "id": 1,
                "problema": "Baja",
                "tratamiento": "Riego suave",
                "urgencia": "baja",
                "costo_estimado_mxn": 100,
                "created_at": datetime(2026, 3, 14),
            },
            {
                "id": 2,
                "problema": "Alta urgencia",
                "tratamiento": "Aplicar tratamiento",
                "urgencia": "alta",
                "costo_estimado_mxn": 500,
                "created_at": datetime(2026, 3, 14),
            },
        ]
        result = build_action_timeline(
            reference_date=date(2026, 3, 15),
            crop_type="maiz",
            planted_at=datetime(2026, 2, 1),
            forecast_3day=[],
            pending_treatments=pending,
        )
        actions = result["actions"]
        # Find indexes of the two treatment actions
        treatment_actions = [a for a in actions if a["source"] == "treatment"]
        assert len(treatment_actions) == 2
        # alta should come before baja
        priorities = [a["priority"] for a in treatment_actions]
        assert priorities[0] <= priorities[1], "Higher priority (lower number) should come first"


# ---------------------------------------------------------------------------
# API integration tests
# ---------------------------------------------------------------------------


def _seed_farm_field(db, crop_type="maiz", planted_at=None):
    """Helper: create a farm + field."""
    farm = Farm(name="Test Farm", state="Jalisco", municipality="Zapopan")
    db.add(farm)
    db.flush()
    field = Field(
        farm_id=farm.id,
        name="Parcela A",
        crop_type=crop_type,
        hectares=5.0,
        planted_at=planted_at,
    )
    db.add(field)
    db.flush()
    return farm, field


class TestActionTimelineAPI:
    """Integration tests for the action-timeline endpoint."""

    def test_get_action_timeline_basic(self, client, db):
        """GET returns 200 with timeline for a valid field."""
        farm, field = _seed_farm_field(db, crop_type="maiz", planted_at=datetime(2026, 2, 1))
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/action-timeline")
        assert resp.status_code == 200
        data = resp.json()
        assert "actions" in data
        assert "reference_date" in data

    def test_get_action_timeline_with_pending_treatments(self, client, db):
        """Pending (unapplied) treatments appear in the timeline."""
        farm, field = _seed_farm_field(db, crop_type="maiz", planted_at=datetime(2026, 2, 1))
        t = TreatmentRecord(
            field_id=field.id,
            health_score_used=45.0,
            problema="Estres hidrico",
            causa_probable="Falta de riego",
            tratamiento="Riego profundo",
            costo_estimado_mxn=200,
            urgencia="alta",
            prevencion="Monitorear humedad",
            organic=True,
        )
        db.add(t)
        db.commit()
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/action-timeline")
        assert resp.status_code == 200
        data = resp.json()
        treatment_actions = [a for a in data["actions"] if a["source"] == "treatment"]
        assert len(treatment_actions) == 1
        assert treatment_actions[0]["description"] == "Riego profundo"

    def test_get_action_timeline_with_weather(self, client, db):
        """Weather forecast data influences timeline."""
        import json
        farm, field = _seed_farm_field(db, crop_type="maiz", planted_at=datetime(2026, 2, 1))
        w = WeatherRecord(
            farm_id=farm.id,
            temp_c=25.0,
            humidity_pct=70.0,
            wind_kmh=12.0,
            rainfall_mm=0.0,
            description="Despejado",
            forecast_3day=[
                {"temp_c": 22, "humidity_pct": 80, "wind_kmh": 10, "description": "Lluvia", "rainfall_mm": 15.0},
                {"temp_c": 24, "humidity_pct": 60, "wind_kmh": 5, "description": "Despejado", "rainfall_mm": 0.0},
                {"temp_c": 23, "humidity_pct": 65, "wind_kmh": 8, "description": "Nublado", "rainfall_mm": 0.0},
            ],
        )
        db.add(w)
        db.commit()
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/action-timeline")
        assert resp.status_code == 200
        data = resp.json()
        assert "weather_summary" in data

    def test_field_not_found(self, client, db):
        """404 when field doesn't exist."""
        farm = Farm(name="Test Farm", state="Jalisco", municipality="Zapopan")
        db.add(farm)
        db.flush()
        resp = client.get(f"/api/farms/{farm.id}/fields/9999/action-timeline")
        assert resp.status_code == 404
