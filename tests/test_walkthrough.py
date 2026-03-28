"""Tests for FODECIJAL demo walkthrough page and demo farms API."""

import pytest
from cultivos.db.models import Farm, Field
from datetime import datetime


class TestDemoFarmsAPI:
    """Tests for GET /api/demo/farms — returns only [DEMO] farms with fields."""

    def _seed_demo_farms(self, db):
        """Seed demo + non-demo farms."""
        demo_farm = Farm(
            name="Rancho Azul [DEMO]",
            owner_name="Carlos Hernandez",
            location_lat=20.8833,
            location_lon=-103.8333,
            total_hectares=45,
            municipality="Tequila",
            state="Jalisco",
        )
        regular_farm = Farm(
            name="Finca Real",
            owner_name="Juan Perez",
            total_hectares=20,
        )
        db.add_all([demo_farm, regular_farm])
        db.flush()
        # Add fields to demo farm
        f1 = Field(farm_id=demo_farm.id, name="Agave Norte", crop_type="agave", hectares=20)
        f2 = Field(farm_id=demo_farm.id, name="Maiz Sur", crop_type="maiz", hectares=15)
        # Add field to regular farm
        f3 = Field(farm_id=regular_farm.id, name="Parcela A", crop_type="frijol", hectares=10)
        db.add_all([f1, f2, f3])
        db.commit()
        return demo_farm, regular_farm

    def test_demo_farms_returns_only_demo(self, client, db):
        """Only farms with [DEMO] in name are returned."""
        demo, regular = self._seed_demo_farms(db)
        resp = client.get("/api/demo/farms")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert "[DEMO]" in data[0]["name"]
        assert data[0]["id"] == demo.id

    def test_demo_farms_include_fields(self, client, db):
        """Each demo farm includes its fields list."""
        self._seed_demo_farms(db)
        resp = client.get("/api/demo/farms")
        data = resp.json()
        assert "fields" in data[0]
        assert len(data[0]["fields"]) == 2

    def test_demo_farms_empty_when_no_demo(self, client, db):
        """Returns empty list when no demo farms exist."""
        regular = Farm(name="Finca Normal", total_hectares=10)
        db.add(regular)
        db.commit()
        resp = client.get("/api/demo/farms")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_demo_farms_fields_have_crop_type(self, client, db):
        """Fields include crop_type for display in walkthrough."""
        self._seed_demo_farms(db)
        resp = client.get("/api/demo/farms")
        fields = resp.json()[0]["fields"]
        assert all("crop_type" in f for f in fields)
        assert fields[0]["crop_type"] == "agave"


class TestWalkthroughRoute:
    """Tests for /recorrido serving the walkthrough HTML page."""

    def test_walkthrough_route_serves_html(self, client):
        """GET /recorrido returns 200 with HTML content."""
        resp = client.get("/recorrido")
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")

    def test_walkthrough_has_four_sections(self, client):
        """Page contains all 4 guided sections."""
        resp = client.get("/recorrido")
        html = resp.text
        assert "Datos del Campo" in html
        assert "Salud" in html
        assert "Recomendaciones" in html
        assert "Impacto Regenerativo" in html

    def test_walkthrough_has_progress_indicator(self, client):
        """Page has a progress/step indicator."""
        resp = client.get("/recorrido")
        html = resp.text
        assert "step-indicator" in html or "progress" in html

    def test_walkthrough_has_navigation(self, client):
        """Page has next/prev navigation controls."""
        resp = client.get("/recorrido")
        html = resp.text
        assert "Siguiente" in html or "next" in html.lower()
