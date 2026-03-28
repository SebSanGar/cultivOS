"""Tests for seasonal TEK calendar widget — API data contract for the frontend."""

from datetime import date

import pytest

from cultivos.db.models import Farm
from cultivos.services.intelligence.seasonal_calendar import (
    generate_seasonal_alerts,
    _classify_current_season,
)


class TestCalendarWidgetDataContract:
    """Verify API returns data in the shape the frontend calendar widget expects."""

    def test_endpoint_returns_season_and_alerts(self, client, db, admin_headers):
        """Response has season, reference_date, and alerts list for calendar rendering."""
        farm = Farm(name="Rancho Calendario", state="Jalisco")
        db.add(farm)
        db.commit()
        db.refresh(farm)

        resp = client.get(
            f"/api/farms/{farm.id}/seasonal-alerts?reference_date=2026-03-15",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["season"] == "secas"
        assert data["reference_date"] == "2026-03-15"
        assert len(data["alerts"]) > 0
        # Each alert has fields the widget needs for rendering
        for alert in data["alerts"]:
            assert "crop" in alert
            assert "alert_type" in alert
            assert "message" in alert
            assert "month_range" in alert

    def test_alert_types_map_to_calendar_colors(self):
        """All alert_type values are one of the 4 types the widget color-codes."""
        valid_types = {"preparacion", "siembra", "cosecha", "mantenimiento"}
        # Test across multiple months to cover all alert types
        for month in range(1, 13):
            alerts = generate_seasonal_alerts(reference_date=date(2026, month, 15))
            for alert in alerts:
                assert alert["alert_type"] in valid_types, (
                    f"Unknown alert_type '{alert['alert_type']}' for {alert['crop']} in month {month}"
                )

    def test_empty_calendar_for_mid_season(self):
        """Some months may have fewer alerts — widget must handle gracefully."""
        # August should have only a few alerts (agave, sorgo)
        alerts = generate_seasonal_alerts(reference_date=date(2026, 8, 15))
        # Should still be a valid list, even if short
        assert isinstance(alerts, list)
        # At least some crops are active in August (agave planting, sorgo)
        crops = [a["crop"] for a in alerts]
        assert "Agave" in crops or "Sorgo" in crops

    def test_season_classification_covers_all_months(self):
        """Every month maps to either temporal or secas."""
        for month in range(1, 13):
            season = _classify_current_season(month)
            assert season in ("temporal", "secas")

    def test_calendar_groups_by_alert_type(self):
        """March alerts should include multiple types for grouped display."""
        alerts = generate_seasonal_alerts(reference_date=date(2026, 3, 15))
        types_present = {a["alert_type"] for a in alerts}
        # March should have both prep and harvest (garbanzo harvest is Mar-Apr)
        assert "preparacion" in types_present
        assert "cosecha" in types_present

    def test_no_data_farm_still_returns_200(self, client, db, admin_headers):
        """Widget handles farm with no crop-specific data — uses default calendar."""
        farm = Farm(name="Rancho Vacio", state="Jalisco")
        db.add(farm)
        db.commit()
        db.refresh(farm)

        # Use a month with alerts to verify calendar is global, not farm-specific
        resp = client.get(
            f"/api/farms/{farm.id}/seasonal-alerts?reference_date=2026-06-15",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        # Calendar alerts are phenology-based, not farm-data-dependent
        assert len(data["alerts"]) > 0
