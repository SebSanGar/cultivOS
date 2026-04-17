"""D4: Soil health trend sparklines on farm dashboard.

Verifies that frontend/app.js fetches /soil-trajectory per field and that
the renderer emits an inline sparkline SVG for both pH and organic matter
next to the existing soil grid.
"""

import re


class TestSoilTrajectoryFetch:
    """app.js must call the soil-trajectory endpoint when loading fields."""

    def test_soil_trajectory_endpoint_called(self):
        with open("frontend/app.js") as f:
            js = f.read()
        assert "soil-trajectory" in js, "app.js must fetch /soil-trajectory per field"

    def test_soil_trajectory_cached_per_field(self):
        with open("frontend/app.js") as f:
            js = f.read()
        assert "soilTrajectoryByField" in js, (
            "app.js must store soil trajectory results keyed by field id"
        )


class TestSparklineRendering:
    """Soil sparkline SVG must appear in rendered field markup."""

    def test_soil_sparkline_builder_exists(self):
        with open("frontend/app.js") as f:
            js = f.read()
        assert re.search(r"function\s+buildSoilSparkline", js), (
            "app.js must define buildSoilSparkline(series, trend)"
        )

    def test_soil_sparkline_rendered_in_field_card(self):
        with open("frontend/app.js") as f:
            js = f.read()
        assert "buildSoilSparkline" in js and "soil-sparkline" in js, (
            "Soil sparkline must be inlined into field rendering"
        )

    def test_sparkline_uses_trend_colour_class(self):
        with open("frontend/app.js") as f:
            js = f.read()
        assert "sparkline-improving" in js or "soil-sparkline-improving" in js


class TestSparklineCSS:
    """Minimal styling hook for the soil sparkline element."""

    def test_soil_sparkline_css_hook_present(self):
        with open("frontend/styles.css") as f:
            css = f.read()
        assert ".soil-sparkline" in css, "styles.css must style .soil-sparkline"


class TestSoilTrajectoryAPI:
    """API endpoint behind the sparkline returns the expected shape."""

    def test_soil_trajectory_endpoint_returns_shape(self, client, db):
        from cultivos.db.models import Farm, Field, SoilAnalysis
        from datetime import datetime

        farm = Farm(name="Finca Spark", total_hectares=50)
        db.add(farm)
        db.commit()
        db.refresh(farm)
        field = Field(farm_id=farm.id, name="Campo", crop_type="maiz", hectares=10)
        db.add(field)
        db.commit()
        db.refresh(field)

        for month, ph, om in [
            (1, 6.0, 2.0),
            (2, 6.2, 2.2),
            (3, 6.4, 2.5),
            (4, 6.5, 2.8),
        ]:
            db.add(
                SoilAnalysis(
                    field_id=field.id,
                    ph=ph,
                    organic_matter_pct=om,
                    nitrogen_ppm=20,
                    phosphorus_ppm=15,
                    potassium_ppm=100,
                    moisture_pct=30,
                    sampled_at=datetime(2026, month, 10),
                )
            )
        db.commit()

        resp = client.get(
            f"/api/farms/{farm.id}/fields/{field.id}/soil-trajectory"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "months" in data
        assert "ph_trend" in data
        assert "organic_matter_trend" in data
        assert len(data["months"]) >= 1
        month_keys = set(data["months"][0].keys())
        assert {"month_label", "avg_ph", "avg_organic_matter_pct"}.issubset(month_keys)
