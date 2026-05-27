"""H1 — NDVI zone shape mismatch: seed zones must match NDVIZoneOut schema.

ROOT CAUSE: seed_iteso_demo writes zones as {"zone": ..., "ndvi_mean": ...}
but NDVIZoneOut requires {classification, min_ndvi, max_ndvi, pixel_count, percentage}.
GET /api/farms/X/fields/Y/ndvi returns 500 on response validation.

Acceptance criteria:
  - GET /api/farms/{farm_id}/fields/{field_id}/ndvi returns 200 (not 500)
  - Each zone has all 5 required keys: classification, min_ndvi, max_ndvi, pixel_count, percentage
  - zone.percentage values across zones sum to 100.0 (within 1.0 tolerance)
  - zone.classification is one of: alto, moderado, bajo, estres
  - zone.pixel_count is a positive integer
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from cultivos.db.models import Base, Farm, Field


NDVI_ZONE_REQUIRED_KEYS = {"classification", "min_ndvi", "max_ndvi", "pixel_count", "percentage"}
VALID_CLASSIFICATIONS = {"alto", "moderado", "bajo", "estres"}
ITESO_FARM_NAMES = [
    "Rancho Don Manuel [DEMO]",
    "Aguacates La Joya [DEMO]",
    "Tierras Altas [DEMO]",
]


@pytest.fixture
def seeded_db():
    """In-memory DB seeded with ITESO demo data."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    from scripts.seed_demo import seed_iteso_demo
    seed_iteso_demo(session)

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def seeded_client(seeded_db):
    """TestClient with seeded in-memory DB injected."""
    import os
    os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing-only")
    from cultivos.config import get_settings
    get_settings.cache_clear()
    from cultivos.app import create_app
    from fastapi.testclient import TestClient
    from cultivos.db.session import get_db

    app = create_app()
    app.dependency_overrides[get_db] = lambda: seeded_db
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c, seeded_db
    app.dependency_overrides.clear()


def _first_iteso_field(db):
    """Return (farm_id, field_id) for the first ITESO demo farm/field."""
    farm = (
        db.query(Farm)
        .filter(Farm.name.in_(ITESO_FARM_NAMES))
        .order_by(Farm.id)
        .first()
    )
    assert farm is not None, "No ITESO demo farm found — seed failed?"
    field = (
        db.query(Field)
        .filter(Field.farm_id == farm.id)
        .order_by(Field.id)
        .first()
    )
    assert field is not None, "No field for ITESO farm — seed failed?"
    return farm.id, field.id


class TestH1NdviZoneShape:

    def test_ndvi_endpoint_returns_200(self, seeded_client):
        """GET /ndvi must return 200, not 500 caused by zone shape mismatch."""
        client, db = seeded_client
        farm_id, field_id = _first_iteso_field(db)
        resp = client.get(f"/api/farms/{farm_id}/fields/{field_id}/ndvi")
        assert resp.status_code == 200, (
            f"Expected 200, got {resp.status_code}. Body: {resp.text[:300]}"
        )

    def test_zones_are_list(self, seeded_client):
        """Each NDVIResult has a zones list."""
        client, db = seeded_client
        farm_id, field_id = _first_iteso_field(db)
        results = client.get(f"/api/farms/{farm_id}/fields/{field_id}/ndvi").json()
        assert len(results) > 0, "No NDVI results for field"
        for r in results:
            assert isinstance(r["zones"], list), "zones must be a list"
            assert len(r["zones"]) > 0, "zones must not be empty"

    def test_zone_has_all_required_keys(self, seeded_client):
        """Each zone dict has exactly the 5 NDVIZoneOut keys."""
        client, db = seeded_client
        farm_id, field_id = _first_iteso_field(db)
        results = client.get(f"/api/farms/{farm_id}/fields/{field_id}/ndvi").json()
        for r in results:
            for zone in r["zones"]:
                missing = NDVI_ZONE_REQUIRED_KEYS - set(zone.keys())
                assert not missing, (
                    f"Zone missing keys {missing}. Got keys: {set(zone.keys())}"
                )

    def test_zone_no_legacy_keys(self, seeded_client):
        """Zone must NOT have old legacy keys (zone, ndvi_mean)."""
        client, db = seeded_client
        farm_id, field_id = _first_iteso_field(db)
        results = client.get(f"/api/farms/{farm_id}/fields/{field_id}/ndvi").json()
        for r in results:
            for zone in r["zones"]:
                assert "zone" not in zone, "Legacy key 'zone' still present"
                assert "ndvi_mean" not in zone, "Legacy key 'ndvi_mean' still present"

    def test_zone_classification_valid(self, seeded_client):
        """classification must be one of: alto, moderado, bajo, estres."""
        client, db = seeded_client
        farm_id, field_id = _first_iteso_field(db)
        results = client.get(f"/api/farms/{farm_id}/fields/{field_id}/ndvi").json()
        for r in results:
            for zone in r["zones"]:
                assert zone["classification"] in VALID_CLASSIFICATIONS, (
                    f"Invalid classification: {zone['classification']!r}"
                )

    def test_zone_percentages_sum_to_100(self, seeded_client):
        """zone percentages within one NDVIResult must sum to ~100."""
        client, db = seeded_client
        farm_id, field_id = _first_iteso_field(db)
        results = client.get(f"/api/farms/{farm_id}/fields/{field_id}/ndvi").json()
        for r in results:
            total = sum(z["percentage"] for z in r["zones"])
            assert abs(total - 100.0) < 1.0, (
                f"Zone percentages sum to {total}, expected ~100"
            )

    def test_zone_pixel_count_positive(self, seeded_client):
        """pixel_count must be a positive integer."""
        client, db = seeded_client
        farm_id, field_id = _first_iteso_field(db)
        results = client.get(f"/api/farms/{farm_id}/fields/{field_id}/ndvi").json()
        for r in results:
            for zone in r["zones"]:
                assert isinstance(zone["pixel_count"], int), "pixel_count must be int"
                assert zone["pixel_count"] > 0, "pixel_count must be positive"

    def test_all_iteso_fields_ndvi_200(self, seeded_client):
        """All 9 ITESO fields return 200 from /ndvi endpoint."""
        client, db = seeded_client
        farms = (
            db.query(Farm)
            .filter(Farm.name.in_(ITESO_FARM_NAMES))
            .all()
        )
        for farm in farms:
            fields = (
                db.query(Field)
                .filter(Field.farm_id == farm.id)
                .all()
            )
            for field in fields:
                resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/ndvi")
                assert resp.status_code == 200, (
                    f"farm={farm.id} field={field.id} → {resp.status_code}: {resp.text[:200]}"
                )
