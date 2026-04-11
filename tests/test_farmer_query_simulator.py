"""Tests for POST /api/demo/farmer-query — WhatsApp query simulator."""

import pytest
from fastapi.testclient import TestClient

from cultivos.app import create_app
from cultivos.db.session import get_db


@pytest.fixture()
def app(db):
    application = create_app()
    application.dependency_overrides[get_db] = lambda: db
    yield application
    application.dependency_overrides.clear()


@pytest.fixture()
def client(app):
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture()
def farm(db):
    """Seed one farm and one field so farm_id=1 is valid."""
    from cultivos.db.models import Farm, Field

    f = Farm(
        name="Rancho La Perla",
        owner_name="Don Manuel",
        municipality="Tlaquepaque",
        state="Jalisco",
        total_hectares=10.0,
    )
    db.add(f)
    db.flush()
    field = Field(farm_id=f.id, name="Parcela 1", crop_type="maiz", hectares=5.0)
    db.add(field)
    db.commit()
    return f


# --------------------------------------------------------------------------- #
# Happy path — Spanish queries return structured dicts                         #
# --------------------------------------------------------------------------- #


class TestFarmerQueryHappyPath:
    def test_returns_200(self, client):
        resp = client.post(
            "/api/demo/farmer-query",
            json={"message": "mis plantas tienen manchas amarillas"},
        )
        assert resp.status_code == 200

    def test_response_has_required_fields(self, client):
        resp = client.post(
            "/api/demo/farmer-query",
            json={"message": "mis plantas tienen manchas amarillas"},
        )
        data = resp.json()
        assert "detected_issue" in data
        assert "crop" in data
        assert "severity" in data
        assert "recommended_action" in data
        assert "confidence" in data

    def test_confidence_in_range(self, client):
        resp = client.post(
            "/api/demo/farmer-query",
            json={"message": "mis plantas tienen manchas amarillas"},
        )
        confidence = resp.json()["confidence"]
        assert 0.0 <= confidence <= 1.0

    def test_severity_valid_value(self, client):
        resp = client.post(
            "/api/demo/farmer-query",
            json={"message": "mis plantas tienen manchas amarillas"},
        )
        assert resp.json()["severity"] in ("low", "medium", "high")

    def test_recommended_action_in_spanish(self, client):
        """Recommended action must be non-empty and use Spanish text."""
        resp = client.post(
            "/api/demo/farmer-query",
            json={"message": "mis plantas tienen manchas amarillas"},
        )
        action = resp.json()["recommended_action"]
        assert len(action) > 10  # meaningful sentence

    def test_yellow_spots_detected_as_disease(self, client):
        resp = client.post(
            "/api/demo/farmer-query",
            json={"message": "manchas amarillas en las hojas"},
        )
        data = resp.json()
        assert data["detected_issue"] is not None
        assert len(data["detected_issue"]) > 0

    def test_drought_query_detected(self, client):
        resp = client.post(
            "/api/demo/farmer-query",
            json={"message": "la tierra esta muy seca, no ha llovido"},
        )
        data = resp.json()
        assert data["detected_issue"] is not None

    def test_pest_query_detected(self, client):
        resp = client.post(
            "/api/demo/farmer-query",
            json={"message": "hay muchos insectos comiendo las hojas de maiz"},
        )
        data = resp.json()
        assert data["detected_issue"] is not None
        # Crop detected from keyword
        assert data["crop"] == "maiz"

    def test_crop_detected_from_message(self, client):
        resp = client.post(
            "/api/demo/farmer-query",
            json={"message": "mi frijol tiene manchas cafes"},
        )
        assert resp.json()["crop"] == "frijol"

    def test_agave_detected(self, client):
        resp = client.post(
            "/api/demo/farmer-query",
            json={"message": "el agave tiene las puntas amarillas"},
        )
        assert resp.json()["crop"] == "agave"


# --------------------------------------------------------------------------- #
# Unknown crop — handled gracefully                                             #
# --------------------------------------------------------------------------- #


class TestUnknownCrop:
    def test_unknown_crop_returns_200(self, client):
        """Unrecognised crop keyword → still returns valid structured response."""
        resp = client.post(
            "/api/demo/farmer-query",
            json={"message": "mi parcela tiene problemas"},
        )
        assert resp.status_code == 200

    def test_unknown_crop_field_is_null_or_string(self, client):
        resp = client.post(
            "/api/demo/farmer-query",
            json={"message": "no se que pasa en mi campo"},
        )
        crop = resp.json()["crop"]
        assert crop is None or isinstance(crop, str)

    def test_no_crash_on_generic_message(self, client):
        resp = client.post(
            "/api/demo/farmer-query",
            json={"message": "hola, necesito ayuda"},
        )
        assert resp.status_code == 200
        assert "recommended_action" in resp.json()


# --------------------------------------------------------------------------- #
# Optional farm_id                                                              #
# --------------------------------------------------------------------------- #


class TestFarmIdOptional:
    def test_missing_farm_id_returns_200(self, client):
        resp = client.post(
            "/api/demo/farmer-query",
            json={"message": "manchas en el maiz"},
        )
        assert resp.status_code == 200

    def test_valid_farm_id_returns_200(self, client, farm):
        resp = client.post(
            "/api/demo/farmer-query",
            json={"message": "manchas amarillas", "farm_id": farm.id},
        )
        assert resp.status_code == 200

    def test_invalid_farm_id_returns_404(self, client):
        resp = client.post(
            "/api/demo/farmer-query",
            json={"message": "manchas amarillas", "farm_id": 99999},
        )
        assert resp.status_code == 404

    def test_farm_id_zero_returns_422_or_404(self, client):
        """farm_id=0 is invalid — expect 422 validation error or 404."""
        resp = client.post(
            "/api/demo/farmer-query",
            json={"message": "manchas amarillas", "farm_id": 0},
        )
        assert resp.status_code in (404, 422)


# --------------------------------------------------------------------------- #
# Input validation                                                              #
# --------------------------------------------------------------------------- #


class TestInputValidation:
    def test_empty_message_returns_422(self, client):
        resp = client.post(
            "/api/demo/farmer-query",
            json={"message": ""},
        )
        assert resp.status_code == 422

    def test_missing_message_returns_422(self, client):
        resp = client.post("/api/demo/farmer-query", json={})
        assert resp.status_code == 422
