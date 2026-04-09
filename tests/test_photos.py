"""Tests for crop photo upload and analysis endpoints."""

import io
import pytest
from PIL import Image


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_image(width: int = 100, height: int = 100, color: tuple = (34, 139, 34)) -> bytes:
    """Create a test image with the given color, return JPEG bytes."""
    img = Image.new("RGB", (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def _seed_farm_field(db):
    """Seed a farm + field and return (farm_id, field_id)."""
    from cultivos.db.models import Farm, Field
    farm = Farm(name="Test Farm", owner_name="Tester", state="Jalisco", total_hectares=10)
    db.add(farm)
    db.flush()
    field = Field(name="Parcela A", farm_id=farm.id, crop_type="maiz", hectares=5)
    db.add(field)
    db.commit()
    return farm.id, field.id


# ---------------------------------------------------------------------------
# Pure service tests
# ---------------------------------------------------------------------------

class TestAnalyzeCropPhoto:
    """Tests for the pure analyze_crop_photo function."""

    def test_healthy_vegetation_image(self):
        from cultivos.services.crop.photo_analysis import analyze_crop_photo
        img_bytes = _make_image(color=(30, 180, 30))
        result = analyze_crop_photo(img_bytes)
        assert result["classification"] == "healthy_vegetation"
        assert result["green_ratio"] > 0.3
        assert isinstance(result["dominant_colors"], list)
        assert len(result["dominant_colors"]) >= 1
        assert isinstance(result["avg_brightness"], float)

    def test_brown_soil_image(self):
        from cultivos.services.crop.photo_analysis import analyze_crop_photo
        img_bytes = _make_image(color=(200, 180, 150))
        result = analyze_crop_photo(img_bytes)
        assert result["classification"] == "bare_soil"
        assert result["green_ratio"] < 0.2

    def test_mixed_dark_image(self):
        from cultivos.services.crop.photo_analysis import analyze_crop_photo
        img_bytes = _make_image(color=(60, 50, 50))
        result = analyze_crop_photo(img_bytes)
        assert result["classification"] == "mixed"
        assert result["avg_brightness"] < 160

    def test_invalid_bytes_raises(self):
        from cultivos.services.crop.photo_analysis import analyze_crop_photo
        with pytest.raises(ValueError, match="Cannot decode image"):
            analyze_crop_photo(b"this is not an image")

    def test_empty_bytes_raises(self):
        from cultivos.services.crop.photo_analysis import analyze_crop_photo
        with pytest.raises(ValueError, match="Cannot decode image"):
            analyze_crop_photo(b"")

    def test_png_format_works(self):
        from cultivos.services.crop.photo_analysis import analyze_crop_photo
        img = Image.new("RGB", (50, 50), (0, 200, 0))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        result = analyze_crop_photo(buf.getvalue())
        assert "classification" in result

    def test_large_image_resized(self):
        from cultivos.services.crop.photo_analysis import analyze_crop_photo
        img_bytes = _make_image(width=800, height=600, color=(30, 180, 30))
        result = analyze_crop_photo(img_bytes)
        assert result["classification"] == "healthy_vegetation"

    def test_dominant_colors_present(self):
        from cultivos.services.crop.photo_analysis import analyze_crop_photo
        img_bytes = _make_image(color=(100, 200, 50))
        result = analyze_crop_photo(img_bytes)
        total = sum(c["percentage"] for c in result["dominant_colors"])
        assert total > 50.0


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------

class TestPhotoUploadEndpoint:
    """Tests for POST /api/farms/{id}/fields/{id}/photos."""

    def test_upload_valid_photo(self, client, db):
        farm_id, field_id = _seed_farm_field(db)
        img_bytes = _make_image(color=(30, 180, 30))
        resp = client.post(
            f"/api/farms/{farm_id}/fields/{field_id}/photos",
            files={"file": ("crop.jpg", io.BytesIO(img_bytes), "image/jpeg")},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["filename"] == "crop.jpg"
        assert data["field_id"] == field_id
        assert data["analysis"] is not None
        assert data["analysis"]["classification"] == "healthy_vegetation"
        assert data["size_bytes"] == len(img_bytes)

    def test_upload_stores_metadata(self, client, db):
        from cultivos.db.models import FieldPhoto
        farm_id, field_id = _seed_farm_field(db)
        img_bytes = _make_image()
        resp = client.post(
            f"/api/farms/{farm_id}/fields/{field_id}/photos",
            files={"file": ("test.jpg", io.BytesIO(img_bytes), "image/jpeg")},
        )
        assert resp.status_code == 201
        photo = db.query(FieldPhoto).first()
        assert photo is not None
        assert photo.filename == "test.jpg"
        assert photo.field_id == field_id
        assert photo.analysis_json is not None

    def test_upload_invalid_image_returns_400(self, client, db):
        farm_id, field_id = _seed_farm_field(db)
        resp = client.post(
            f"/api/farms/{farm_id}/fields/{field_id}/photos",
            files={"file": ("bad.jpg", io.BytesIO(b"not-an-image"), "image/jpeg")},
        )
        assert resp.status_code == 400

    def test_upload_empty_file_returns_400(self, client, db):
        farm_id, field_id = _seed_farm_field(db)
        resp = client.post(
            f"/api/farms/{farm_id}/fields/{field_id}/photos",
            files={"file": ("empty.jpg", io.BytesIO(b""), "image/jpeg")},
        )
        assert resp.status_code == 400

    def test_upload_field_not_found(self, client, db):
        from cultivos.db.models import Farm
        farm = Farm(name="Test", owner_name="T", state="Jalisco", total_hectares=5)
        db.add(farm)
        db.commit()
        img_bytes = _make_image()
        resp = client.post(
            f"/api/farms/{farm.id}/fields/999/photos",
            files={"file": ("x.jpg", io.BytesIO(img_bytes), "image/jpeg")},
        )
        assert resp.status_code == 404

    def test_upload_farm_not_found(self, client, db):
        img_bytes = _make_image()
        resp = client.post(
            "/api/farms/999/fields/1/photos",
            files={"file": ("x.jpg", io.BytesIO(img_bytes), "image/jpeg")},
        )
        assert resp.status_code == 404


class TestPhotoListEndpoint:
    """Tests for GET /api/farms/{id}/fields/{id}/photos."""

    def test_list_empty(self, client, db):
        farm_id, field_id = _seed_farm_field(db)
        resp = client.get(f"/api/farms/{farm_id}/fields/{field_id}/photos")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_after_upload(self, client, db):
        farm_id, field_id = _seed_farm_field(db)
        img_bytes = _make_image()
        client.post(
            f"/api/farms/{farm_id}/fields/{field_id}/photos",
            files={"file": ("a.jpg", io.BytesIO(img_bytes), "image/jpeg")},
        )
        client.post(
            f"/api/farms/{farm_id}/fields/{field_id}/photos",
            files={"file": ("b.jpg", io.BytesIO(img_bytes), "image/jpeg")},
        )
        resp = client.get(f"/api/farms/{farm_id}/fields/{field_id}/photos")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["filename"] == "b.jpg"

    def test_list_field_not_found(self, client, db):
        from cultivos.db.models import Farm
        farm = Farm(name="Test", owner_name="T", state="Jalisco", total_hectares=5)
        db.add(farm)
        db.commit()
        resp = client.get(f"/api/farms/{farm.id}/fields/999/photos")
        assert resp.status_code == 404


class TestPhotoDeleteEndpoint:
    """Tests for DELETE /api/farms/{id}/fields/{id}/photos/{id}."""

    def test_delete_photo(self, client, db):
        from cultivos.db.models import FieldPhoto
        farm_id, field_id = _seed_farm_field(db)
        img_bytes = _make_image()
        resp = client.post(
            f"/api/farms/{farm_id}/fields/{field_id}/photos",
            files={"file": ("del.jpg", io.BytesIO(img_bytes), "image/jpeg")},
        )
        photo_id = resp.json()["id"]
        del_resp = client.delete(f"/api/farms/{farm_id}/fields/{field_id}/photos/{photo_id}")
        assert del_resp.status_code == 204
        assert db.query(FieldPhoto).filter(FieldPhoto.id == photo_id).first() is None

    def test_delete_not_found(self, client, db):
        farm_id, field_id = _seed_farm_field(db)
        resp = client.delete(f"/api/farms/{farm_id}/fields/{field_id}/photos/999")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Frontend page test
# ---------------------------------------------------------------------------

class TestFotosPage:
    """Tests for /fotos frontend page."""

    def test_page_loads(self, client):
        resp = client.get("/fotos")
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")

    def test_page_has_content(self, client):
        resp = client.get("/fotos")
        html = resp.text.lower()
        assert "fotos" in html or "foto" in html
