"""Tests for #207 Farm ancestral method adoption log."""

from datetime import datetime, timedelta

import pytest

from cultivos.db.models import AncestralMethod, Farm, Field


@pytest.fixture
def farm_with_fields(db):
    farm = Farm(name="Finca Test", state="Jalisco", total_hectares=10.0)
    db.add(farm)
    db.commit()
    db.refresh(farm)
    f1 = Field(farm_id=farm.id, name="Parcela Norte", crop_type="maiz", hectares=3.0)
    f2 = Field(farm_id=farm.id, name="Parcela Sur", crop_type="frijol", hectares=4.0)
    db.add_all([f1, f2])
    db.commit()
    db.refresh(f1)
    db.refresh(f2)
    return farm, f1, f2


@pytest.fixture
def ancestral_method(db):
    m = AncestralMethod(
        name="Milpa tradicional",
        description_es="Policultivo maiz-frijol-calabaza",
        region="Jalisco",
        practice_type="intercropping",
        crops=["maiz", "frijol", "calabaza"],
        benefits_es="Mejora fertilidad del suelo",
        problems=["erosion"],
        applicable_months=[5, 6, 7],
        timing_rationale="Inicio temporal de lluvias",
        ecological_benefit=5,
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


def test_tek_adoption_post_basic(client, db, farm_with_fields, ancestral_method):
    farm, f1, f2 = farm_with_fields
    resp = client.post(
        f"/api/farms/{farm.id}/tek-adoptions",
        json={
            "method_name": "Milpa tradicional",
            "adopted_at": datetime.utcnow().isoformat(),
            "fields_applied": [f1.id, f2.id],
            "farmer_notes_es": "Sembrado con calendario lunar",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["method_name"] == "Milpa tradicional"
    assert body["fields_count"] == 2
    assert body["farmer_notes_es"] == "Sembrado con calendario lunar"
    assert body["ecological_benefit"] == 5


def test_tek_adoption_post_invalid_method(client, db, farm_with_fields, ancestral_method):
    farm, f1, _ = farm_with_fields
    resp = client.post(
        f"/api/farms/{farm.id}/tek-adoptions",
        json={
            "method_name": "Metodo inexistente",
            "adopted_at": datetime.utcnow().isoformat(),
            "fields_applied": [f1.id],
            "farmer_notes_es": "",
        },
    )
    assert resp.status_code == 404
    body = resp.json()
    msg = (body.get("error", {}).get("message") or body.get("detail") or "").lower()
    assert "method" in msg or "not found" in msg


def test_tek_adoption_get_empty(client, db, farm_with_fields):
    farm, _, _ = farm_with_fields
    resp = client.get(f"/api/farms/{farm.id}/tek-adoptions")
    assert resp.status_code == 200
    body = resp.json()
    assert body["farm_id"] == farm.id
    assert body["adoption_count"] == 0
    assert body["adoptions"] == []
    assert body["most_recent_adoption_at"] is None


def test_tek_adoption_get_sorted(client, db, farm_with_fields, ancestral_method):
    farm, f1, f2 = farm_with_fields
    older = (datetime.utcnow() - timedelta(days=10)).isoformat()
    newer = datetime.utcnow().isoformat()

    r1 = client.post(
        f"/api/farms/{farm.id}/tek-adoptions",
        json={
            "method_name": "Milpa tradicional",
            "adopted_at": older,
            "fields_applied": [f1.id],
            "farmer_notes_es": "primera",
        },
    )
    assert r1.status_code == 201
    r2 = client.post(
        f"/api/farms/{farm.id}/tek-adoptions",
        json={
            "method_name": "Milpa tradicional",
            "adopted_at": newer,
            "fields_applied": [f2.id],
            "farmer_notes_es": "segunda",
        },
    )
    assert r2.status_code == 201

    resp = client.get(f"/api/farms/{farm.id}/tek-adoptions")
    assert resp.status_code == 200
    body = resp.json()
    assert body["adoption_count"] == 2
    # newest first
    assert body["adoptions"][0]["farmer_notes_es"] == "segunda"
    assert body["adoptions"][1]["farmer_notes_es"] == "primera"
    assert body["most_recent_adoption_at"] is not None


def test_tek_adoption_404_farm(client, db, ancestral_method):
    resp = client.get("/api/farms/99999/tek-adoptions")
    assert resp.status_code == 404


def test_tek_adoption_post_404_field(client, db, farm_with_fields, ancestral_method):
    farm, f1, _ = farm_with_fields
    resp = client.post(
        f"/api/farms/{farm.id}/tek-adoptions",
        json={
            "method_name": "Milpa tradicional",
            "adopted_at": datetime.utcnow().isoformat(),
            "fields_applied": [f1.id, 99999],
            "farmer_notes_es": "",
        },
    )
    assert resp.status_code == 404
    body = resp.json()
    msg = (body.get("error", {}).get("message") or body.get("detail") or "").lower()
    assert "field" in msg or "not found" in msg
