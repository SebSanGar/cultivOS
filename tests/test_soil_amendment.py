"""Tests for soil amendment calculator — pure computation + API endpoint + frontend page."""

import pytest
from fastapi.testclient import TestClient

from cultivos.app import create_app
from cultivos.db.session import get_db
from cultivos.services.intelligence.soil_amendment import calculate_soil_amendments


# ── Pure function tests ──────────────────────────────────────────────────

class TestCalculateSoilAmendments:
    """Pure function: soil values in → amendment prescriptions out."""

    def test_low_ph_recommends_lime(self):
        """Acidic soil (pH 4.5, target 6.5) should recommend cal agricola."""
        result = calculate_soil_amendments(
            current_ph=4.5, target_ph=6.5,
            current_om_pct=3.0, target_om_pct=3.0,
            current_n_ppm=40, target_n_ppm=40,
            current_p_ppm=20, target_p_ppm=20,
            current_k_ppm=150, target_k_ppm=150,
        )
        amendments = {a["name"] for a in result["amendments"]}
        assert "Cal agricola" in amendments
        lime = next(a for a in result["amendments"] if a["name"] == "Cal agricola")
        assert lime["kg_per_ha"] > 0
        assert lime["reason_es"] != ""

    def test_high_ph_recommends_sulfur(self):
        """Alkaline soil (pH 8.5, target 6.5) should recommend azufre."""
        result = calculate_soil_amendments(
            current_ph=8.5, target_ph=6.5,
            current_om_pct=3.0, target_om_pct=3.0,
            current_n_ppm=40, target_n_ppm=40,
            current_p_ppm=20, target_p_ppm=20,
            current_k_ppm=150, target_k_ppm=150,
        )
        amendments = {a["name"] for a in result["amendments"]}
        assert "Azufre elemental" in amendments
        sulfur = next(a for a in result["amendments"] if a["name"] == "Azufre elemental")
        assert sulfur["kg_per_ha"] > 0

    def test_low_om_recommends_compost(self):
        """Low organic matter (1%, target 4%) should recommend composta."""
        result = calculate_soil_amendments(
            current_ph=6.5, target_ph=6.5,
            current_om_pct=1.0, target_om_pct=4.0,
            current_n_ppm=40, target_n_ppm=40,
            current_p_ppm=20, target_p_ppm=20,
            current_k_ppm=150, target_k_ppm=150,
        )
        amendments = {a["name"] for a in result["amendments"]}
        assert "Composta madura" in amendments
        compost = next(a for a in result["amendments"] if a["name"] == "Composta madura")
        assert compost["kg_per_ha"] > 0

    def test_low_nitrogen_recommends_organic_n(self):
        """Low nitrogen (10 ppm, target 40 ppm) should recommend organic N source."""
        result = calculate_soil_amendments(
            current_ph=6.5, target_ph=6.5,
            current_om_pct=3.0, target_om_pct=3.0,
            current_n_ppm=10, target_n_ppm=40,
            current_p_ppm=20, target_p_ppm=20,
            current_k_ppm=150, target_k_ppm=150,
        )
        amendments = {a["name"] for a in result["amendments"]}
        assert "Harina de sangre" in amendments or "Composta madura" in amendments

    def test_low_phosphorus_recommends_bone_meal(self):
        """Low phosphorus (5 ppm, target 25 ppm) should recommend harina de hueso."""
        result = calculate_soil_amendments(
            current_ph=6.5, target_ph=6.5,
            current_om_pct=3.0, target_om_pct=3.0,
            current_n_ppm=40, target_n_ppm=40,
            current_p_ppm=5, target_p_ppm=25,
            current_k_ppm=150, target_k_ppm=150,
        )
        amendments = {a["name"] for a in result["amendments"]}
        assert "Harina de hueso" in amendments

    def test_low_potassium_recommends_wood_ash(self):
        """Low potassium (50 ppm, target 200 ppm) should recommend ceniza de madera."""
        result = calculate_soil_amendments(
            current_ph=6.5, target_ph=6.5,
            current_om_pct=3.0, target_om_pct=3.0,
            current_n_ppm=40, target_n_ppm=40,
            current_p_ppm=20, target_p_ppm=20,
            current_k_ppm=50, target_k_ppm=200,
        )
        amendments = {a["name"] for a in result["amendments"]}
        assert "Ceniza de madera" in amendments

    def test_all_at_target_returns_empty(self):
        """When all values meet target, no amendments needed."""
        result = calculate_soil_amendments(
            current_ph=6.5, target_ph=6.5,
            current_om_pct=4.0, target_om_pct=4.0,
            current_n_ppm=40, target_n_ppm=40,
            current_p_ppm=25, target_p_ppm=25,
            current_k_ppm=200, target_k_ppm=200,
        )
        assert len(result["amendments"]) == 0
        assert result["summary_es"] != ""

    def test_multiple_deficiencies(self):
        """Multiple problems should return multiple amendments."""
        result = calculate_soil_amendments(
            current_ph=4.5, target_ph=6.5,
            current_om_pct=1.0, target_om_pct=4.0,
            current_n_ppm=10, target_n_ppm=40,
            current_p_ppm=5, target_p_ppm=25,
            current_k_ppm=50, target_k_ppm=200,
        )
        assert len(result["amendments"]) >= 3

    def test_result_structure(self):
        """Result has required keys."""
        result = calculate_soil_amendments(
            current_ph=5.0, target_ph=6.5,
            current_om_pct=2.0, target_om_pct=4.0,
            current_n_ppm=20, target_n_ppm=40,
            current_p_ppm=10, target_p_ppm=25,
            current_k_ppm=100, target_k_ppm=200,
        )
        assert "amendments" in result
        assert "summary_es" in result
        assert "total_cost_mxn_per_ha" in result
        for a in result["amendments"]:
            assert "name" in a
            assert "kg_per_ha" in a
            assert "reason_es" in a
            assert "cost_mxn_per_ha" in a
            assert "organic" in a


# ── API endpoint tests ───────────────────────────────────────────────────

@pytest.fixture
def client(db):
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app, raise_server_exceptions=False)


class TestSoilAmendmentEndpoint:
    """POST /api/intel/soil-amendment."""

    def test_calculate_amendments(self, client):
        resp = client.post("/api/intel/soil-amendment", json={
            "current_ph": 5.0,
            "target_ph": 6.5,
            "current_om_pct": 2.0,
            "target_om_pct": 4.0,
            "current_n_ppm": 20,
            "target_n_ppm": 40,
            "current_p_ppm": 10,
            "target_p_ppm": 25,
            "current_k_ppm": 100,
            "target_k_ppm": 200,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "amendments" in data
        assert "total_cost_mxn_per_ha" in data
        assert len(data["amendments"]) > 0

    def test_no_amendments_needed(self, client):
        resp = client.post("/api/intel/soil-amendment", json={
            "current_ph": 6.5,
            "target_ph": 6.5,
            "current_om_pct": 4.0,
            "target_om_pct": 4.0,
            "current_n_ppm": 40,
            "target_n_ppm": 40,
            "current_p_ppm": 25,
            "target_p_ppm": 25,
            "current_k_ppm": 200,
            "target_k_ppm": 200,
        })
        assert resp.status_code == 200
        assert len(resp.json()["amendments"]) == 0

    def test_missing_required_fields(self, client):
        resp = client.post("/api/intel/soil-amendment", json={})
        assert resp.status_code == 422

    def test_invalid_ph_range(self, client):
        resp = client.post("/api/intel/soil-amendment", json={
            "current_ph": 15.0,  # invalid
            "target_ph": 6.5,
            "current_om_pct": 3.0,
            "target_om_pct": 3.0,
            "current_n_ppm": 40,
            "target_n_ppm": 40,
            "current_p_ppm": 20,
            "target_p_ppm": 20,
            "current_k_ppm": 150,
            "target_k_ppm": 150,
        })
        assert resp.status_code == 422

    def test_defaults_for_optional_targets(self, client):
        """If target values are omitted, use agronomic defaults."""
        resp = client.post("/api/intel/soil-amendment", json={
            "current_ph": 4.5,
            "current_om_pct": 1.0,
            "current_n_ppm": 10,
            "current_p_ppm": 5,
            "current_k_ppm": 50,
        })
        assert resp.status_code == 200
        assert len(resp.json()["amendments"]) > 0


# ── Frontend page tests ──────────────────────────────────────────────────

class TestCalculadoraSueloPage:
    """Frontend page at /calculadora-suelo."""

    def test_page_loads(self, client):
        resp = client.get("/calculadora-suelo")
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")

    def test_page_has_title(self, client):
        html = client.get("/calculadora-suelo").text
        assert "Calculadora" in html

    def test_page_has_form_inputs(self, client):
        html = client.get("/calculadora-suelo").text
        assert "currentPh" in html or "current_ph" in html or "pH" in html

    def test_page_has_results_container(self, client):
        html = client.get("/calculadora-suelo").text
        assert "results" in html.lower() or "resultados" in html.lower()
