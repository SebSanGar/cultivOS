"""Tests for the knowledge discovery page at /conocimiento."""

import pytest
from fastapi.testclient import TestClient

from cultivos.app import create_app
from cultivos.db.models import AncestralMethod, CropType, Disease, Fertilizer
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
def admin_headers(client, db):
    """Register admin user and return auth headers."""
    from cultivos.db.models import User
    from cultivos.auth import hash_password

    if not db.query(User).filter(User.username == "testadmin").first():
        db.add(User(username="testadmin", hashed_password=hash_password("secret123"), role="admin"))
        db.commit()
    resp = client.post("/api/auth/login", json={
        "username": "testadmin", "password": "secret123"
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _seed_knowledge_data(db):
    """Seed fertilizers, diseases, ancestral methods, and crop types."""
    f = Fertilizer(
        name="Composta orgánica",
        description_es="Abono orgánico rico en nutrientes",
        application_method="Incorporar al suelo antes de siembra",
        cost_per_ha_mxn=1500,
        nutrient_profile="N-P-K equilibrado",
        suitable_crops=["maiz", "frijol"],
    )
    db.add(f)

    d = Disease(
        name="Roya del maíz",
        description_es="Hongo que produce pústulas anaranjadas en hojas",
        symptoms=["manchas anaranjadas", "defoliación"],
        affected_crops=["maiz"],
        treatments=[{"name": "Extracto de neem", "description_es": "Aplicar cada 7 dias", "organic": True}],
        region="Jalisco",
        severity="media",
    )
    db.add(d)

    a = AncestralMethod(
        name="Milpa tradicional",
        description_es="Policultivo de maíz, frijol y calabaza",
        region="Mesoamérica",
        practice_type="intercropping",
        crops=["maiz", "frijol", "calabaza"],
        benefits_es="Fijación de nitrógeno, retención de humedad, control de plagas",
        scientific_basis="El frijol fija nitrógeno atmosférico a través de rizobios",
    )
    db.add(a)

    c = CropType(
        name="Maíz",
        family="Poaceae",
        growing_season="temporal",
        water_needs="media",
        regions=["jalisco", "michoacan"],
        companions=["frijol", "calabaza"],
        days_to_harvest=120,
        optimal_temp_min=18.0,
        optimal_temp_max=30.0,
        description_es="Cereal base de la agricultura mexicana",
    )
    db.add(c)
    db.commit()


# ---------- HTML page structure tests ----------

class TestConocimientoPageLoads:
    def test_page_returns_200(self, client):
        resp = client.get("/conocimiento")
        assert resp.status_code == 200

    def test_page_is_html(self, client):
        resp = client.get("/conocimiento")
        assert "text/html" in resp.headers.get("content-type", "")

    def test_page_has_title(self, client):
        resp = client.get("/conocimiento")
        assert "Conocimiento" in resp.text or "conocimiento" in resp.text

    def test_page_has_search_input(self, client):
        resp = client.get("/conocimiento")
        assert 'id="search-input"' in resp.text

    def test_page_has_category_filter(self, client):
        resp = client.get("/conocimiento")
        assert 'id="category-filter"' in resp.text

    def test_page_has_cards_container(self, client):
        resp = client.get("/conocimiento")
        assert 'id="knowledge-cards"' in resp.text

    def test_page_has_stats_strip(self, client):
        resp = client.get("/conocimiento")
        assert "stats-strip" in resp.text

    def test_page_has_navigation(self, client):
        resp = client.get("/conocimiento")
        assert "intel-nav" in resp.text

    def test_page_has_spanish_labels(self, client):
        resp = client.get("/conocimiento")
        html = resp.text
        assert "Buscar" in html
        assert "categorias" in html.lower() or "categor" in html.lower()

    def test_page_loads_js(self, client):
        resp = client.get("/conocimiento")
        assert "knowledge.js" in resp.text


# ---------- API integration tests ----------

class TestKnowledgeAPIs:
    def test_fertilizers_endpoint(self, client, db, admin_headers):
        _seed_knowledge_data(db)
        resp = client.get("/api/knowledge/fertilizers", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert data[0]["name"] == "Composta orgánica"
        assert data[0]["description_es"] is not None

    def test_diseases_endpoint(self, client, db, admin_headers):
        _seed_knowledge_data(db)
        resp = client.get("/api/knowledge/diseases", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert data[0]["name"] == "Roya del maíz"
        assert "symptoms" in data[0]

    def test_ancestral_endpoint(self, client, db, admin_headers):
        _seed_knowledge_data(db)
        resp = client.get("/api/knowledge/ancestral", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert data[0]["name"] == "Milpa tradicional"
        assert "scientific_basis" in data[0]

    def test_crops_endpoint(self, client, db, admin_headers):
        _seed_knowledge_data(db)
        resp = client.get("/api/knowledge/crops", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert data[0]["name"] == "Maíz"

    def test_fertilizers_filter_by_crop(self, client, db, admin_headers):
        _seed_knowledge_data(db)
        resp = client.get("/api/knowledge/fertilizers?crop=maiz", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1

    def test_diseases_filter_by_crop(self, client, db, admin_headers):
        _seed_knowledge_data(db)
        resp = client.get("/api/knowledge/diseases?crop=maiz", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1


# ---------- Card rendering structure tests ----------

class TestKnowledgeCardData:
    def test_fertilizer_has_required_fields(self, client, db, admin_headers):
        _seed_knowledge_data(db)
        resp = client.get("/api/knowledge/fertilizers", headers=admin_headers)
        item = resp.json()[0]
        assert "name" in item
        assert "description_es" in item
        assert "application_method" in item
        assert "cost_per_ha_mxn" in item
        assert "suitable_crops" in item

    def test_disease_has_required_fields(self, client, db, admin_headers):
        _seed_knowledge_data(db)
        resp = client.get("/api/knowledge/diseases", headers=admin_headers)
        item = resp.json()[0]
        assert "name" in item
        assert "description_es" in item
        assert "symptoms" in item
        assert "treatments" in item
        assert "severity" in item

    def test_ancestral_has_required_fields(self, client, db, admin_headers):
        _seed_knowledge_data(db)
        resp = client.get("/api/knowledge/ancestral", headers=admin_headers)
        item = resp.json()[0]
        assert "name" in item
        assert "description_es" in item
        assert "scientific_basis" in item
        assert "practice_type" in item
        assert "benefits_es" in item

    def test_crop_has_required_fields(self, client, db, admin_headers):
        _seed_knowledge_data(db)
        resp = client.get("/api/knowledge/crops", headers=admin_headers)
        item = resp.json()[0]
        assert "name" in item
        assert "description_es" in item
        assert "growing_season" in item
        assert "water_needs" in item
        assert "regions" in item
