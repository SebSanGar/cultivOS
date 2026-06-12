"""KB entity-name English variants (name_en) + backfill for pre-existing DBs.

Knowledge-base NAMES (technique, fertilizer, disease, treatment) stayed Spanish
in EN mode — only descriptions had _en columns. Seeds populate name_en on fresh
DBs; backfill_kb_english() fills NULL _en fields on DBs seeded before the
bilingual layer existed (prod path: alembic adds columns, startup backfills).
"""

import pytest
from fastapi.testclient import TestClient

from cultivos.app import create_app
from cultivos.db.seeds import (
    backfill_kb_english,
    seed_ancestral_methods,
    seed_crops,
    seed_diseases,
    seed_fertilizers,
)
from cultivos.db.session import get_db


@pytest.fixture()
def seeded_db(db):
    seed_fertilizers(db)
    seed_ancestral_methods(db)
    seed_crops(db)
    seed_diseases(db)
    return db


@pytest.fixture()
def client(seeded_db):
    application = create_app()
    application.dependency_overrides[get_db] = lambda: seeded_db
    with TestClient(application, raise_server_exceptions=False) as c:
        yield c
    application.dependency_overrides.clear()


class TestSeedsPopulateNameEn:
    def test_ancestral_methods(self, seeded_db):
        from cultivos.db.models import AncestralMethod
        rows = seeded_db.query(AncestralMethod).all()
        assert rows
        assert all(r.name_en for r in rows)

    def test_fertilizers(self, seeded_db):
        from cultivos.db.models import Fertilizer
        rows = seeded_db.query(Fertilizer).all()
        assert rows
        assert all(r.name_en for r in rows)

    def test_diseases_and_treatments(self, seeded_db):
        from cultivos.db.models import Disease
        rows = seeded_db.query(Disease).all()
        assert rows
        assert all(r.name_en for r in rows)
        for r in rows:
            assert all(tr.get("name_en") for tr in r.treatments), r.name


class TestApiServesNameEn:
    def test_ancestral_endpoint(self, client):
        data = client.get("/api/knowledge/ancestral").json()
        assert data and all(m["name_en"] for m in data)

    def test_fertilizers_endpoint(self, client):
        data = client.get("/api/knowledge/fertilizers").json()
        assert data and all(f["name_en"] for f in data)

    def test_diseases_endpoint_with_treatments(self, client):
        data = client.get("/api/knowledge/diseases").json()
        if isinstance(data, dict):  # paginated envelope
            data = data.get("data") or data.get("items")
        assert data and all(d["name_en"] for d in data)
        assert all(tr["name_en"] for d in data for tr in d["treatments"])


class TestBackfill:
    def test_fills_nulled_fields_and_is_idempotent(self, seeded_db):
        from cultivos.db.models import AncestralMethod, Disease, Fertilizer

        m = seeded_db.query(AncestralMethod).first()
        f = seeded_db.query(Fertilizer).first()
        d = seeded_db.query(Disease).first()
        m.name_en = None
        f.name_en = None
        d.name_en = None
        d.treatments = [
            {k: v for k, v in tr.items() if k != "name_en"} for tr in d.treatments
        ]
        seeded_db.commit()

        assert backfill_kb_english(seeded_db) >= 3
        seeded_db.expire_all()
        assert m.name_en and f.name_en and d.name_en
        assert all(tr.get("name_en") for tr in d.treatments)

        assert backfill_kb_english(seeded_db) == 0
