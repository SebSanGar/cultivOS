"""Tests for GET /api/fields — global fields endpoint for crop type filters."""

from cultivos.db.models import Farm, Field


class TestGlobalFieldsEndpoint:
    def test_returns_all_fields_across_farms(self, client, db):
        farm1 = Farm(name="Farm A", owner_name="Owner A", state="Jalisco")
        farm2 = Farm(name="Farm B", owner_name="Owner B", state="Ontario")
        db.add_all([farm1, farm2])
        db.flush()
        db.add_all([
            Field(name="Field 1", farm_id=farm1.id, crop_type="maiz", hectares=10),
            Field(name="Field 2", farm_id=farm1.id, crop_type="agave", hectares=5),
            Field(name="Field 3", farm_id=farm2.id, crop_type="trigo", hectares=8),
        ])
        db.commit()

        resp = client.get("/api/fields")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3
        crop_types = {f["crop_type"] for f in data}
        assert crop_types == {"maiz", "agave", "trigo"}

    def test_empty_database_returns_empty_list(self, client, db):
        resp = client.get("/api/fields")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_crop_type_filter(self, client, db):
        farm = Farm(name="Farm", owner_name="Owner")
        db.add(farm)
        db.flush()
        db.add_all([
            Field(name="F1", farm_id=farm.id, crop_type="maiz", hectares=10),
            Field(name="F2", farm_id=farm.id, crop_type="agave", hectares=5),
        ])
        db.commit()

        resp = client.get("/api/fields?crop_type=maiz")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["crop_type"] == "maiz"

    def test_fields_include_farm_id(self, client, db):
        farm = Farm(name="Farm", owner_name="Owner")
        db.add(farm)
        db.flush()
        db.add(Field(name="F1", farm_id=farm.id, crop_type="maiz", hectares=10))
        db.commit()

        resp = client.get("/api/fields")
        data = resp.json()
        assert data[0]["farm_id"] == farm.id
