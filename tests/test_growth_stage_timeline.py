"""Tests for growth stage timeline visualization — all stages with day ranges."""

from datetime import datetime, timedelta

import pytest


class TestAllStagesService:
    """Test the pure phenology service returns all stages info."""

    def test_get_all_stages_returns_five_stages(self):
        """All crops have exactly 5 growth stages."""
        from cultivos.services.crop.phenology import get_all_stages_info
        stages = get_all_stages_info("maiz")
        assert len(stages) == 5
        names = [s["name"] for s in stages]
        assert names == ["siembra", "vegetativo", "floracion", "fructificacion", "cosecha"]

    def test_all_stages_have_required_fields(self):
        """Each stage dict has name, name_es, start_day, end_day, water_multiplier, nutrient_focus."""
        from cultivos.services.crop.phenology import get_all_stages_info
        stages = get_all_stages_info("frijol")
        for stage in stages:
            assert "name" in stage
            assert "name_es" in stage
            assert "start_day" in stage
            assert "end_day" in stage
            assert "water_multiplier" in stage
            assert "nutrient_focus" in stage

    def test_stage_days_are_contiguous(self):
        """Stage end_day of stage N == start_day of stage N+1."""
        from cultivos.services.crop.phenology import get_all_stages_info
        stages = get_all_stages_info("chile")
        for i in range(1, len(stages)):
            assert stages[i]["start_day"] == stages[i - 1]["end_day"]

    def test_first_stage_starts_at_zero(self):
        """First stage starts at day 0."""
        from cultivos.services.crop.phenology import get_all_stages_info
        stages = get_all_stages_info("maiz")
        assert stages[0]["start_day"] == 0

    def test_unknown_crop_uses_defaults(self):
        """Unknown crop type still returns 5 valid stages."""
        from cultivos.services.crop.phenology import get_all_stages_info
        stages = get_all_stages_info("unknown_crop")
        assert len(stages) == 5
        assert stages[-1]["end_day"] > 0


class TestGrowthStageAPIAllStages:
    """Test that the API response includes all_stages."""

    def test_response_includes_all_stages(self, client, db, admin_headers):
        """Growth stage endpoint includes all_stages array."""
        from cultivos.db.models import Farm, Field
        farm = Farm(name="Timeline Farm")
        db.add(farm)
        db.commit()
        planted = datetime.utcnow() - timedelta(days=30)
        field = Field(farm_id=farm.id, name="Parcela T", crop_type="maiz", planted_at=planted)
        db.add(field)
        db.commit()

        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/growth-stage")
        assert resp.status_code == 200
        data = resp.json()
        assert "all_stages" in data
        assert len(data["all_stages"]) == 5

    def test_all_stages_marks_current(self, client, db, admin_headers):
        """The current stage in all_stages has is_current=True."""
        from cultivos.db.models import Farm, Field
        farm = Farm(name="Current Farm")
        db.add(farm)
        db.commit()
        planted = datetime.utcnow() - timedelta(days=30)
        field = Field(farm_id=farm.id, name="Parcela C", crop_type="maiz", planted_at=planted)
        db.add(field)
        db.commit()

        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/growth-stage")
        data = resp.json()
        current_stages = [s for s in data["all_stages"] if s["is_current"]]
        assert len(current_stages) == 1
        assert current_stages[0]["name"] == data["stage"]


class TestTimelineFrontend:
    """Test that frontend files contain timeline rendering code."""

    def test_field_js_has_timeline_classes(self, client):
        """field.js contains timeline-related CSS class references."""
        resp = client.get("/field.js")
        assert resp.status_code == 200
        assert "growth-timeline" in resp.text

    def test_field_html_has_growth_section(self, client):
        """field.html has the growth stage section."""
        resp = client.get("/campo")
        assert resp.status_code == 200
        assert 'id="growth-content"' in resp.text
