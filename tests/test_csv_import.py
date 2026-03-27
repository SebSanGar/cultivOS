"""Tests for bulk soil data CSV import."""

import io
import pytest


@pytest.fixture
def farm_and_field(client, admin_headers):
    """Create a farm + field and return (farm_id, field_id)."""
    farm = client.post("/api/farms", json={"name": "Rancho CSV"}, headers=admin_headers)
    farm_id = farm.json()["id"]
    field = client.post(f"/api/farms/{farm_id}/fields", json={
        "name": "Parcela Import", "crop_type": "maiz", "hectares": 10,
    })
    field_id = field.json()["id"]
    return farm_id, field_id


def _make_csv(rows: list[str]) -> bytes:
    """Build a CSV file from header + rows."""
    return "\n".join(rows).encode("utf-8")


# ── test_csv_import_valid ────────────────────────────────────────────

class TestCSVImportValid:
    def test_csv_import_valid(self, client, farm_and_field, admin_headers):
        """POST with valid CSV creates N soil records."""
        farm_id, field_id = farm_and_field
        csv_data = _make_csv([
            "ph,organic_matter_pct,sampled_at",
            "6.5,3.2,2026-01-15T10:00:00",
            "7.0,2.8,2026-02-20T10:00:00",
            "5.8,4.1,2026-03-10T10:00:00",
        ])
        resp = client.post(
            f"/api/farms/{farm_id}/fields/{field_id}/soil/import-csv",
            files={"file": ("soil.csv", io.BytesIO(csv_data), "text/csv")},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["imported"] == 3
        assert data["skipped"] == 0
        assert len(data["errors"]) == 0

        # Verify records exist in DB
        list_resp = client.get(f"/api/farms/{farm_id}/fields/{field_id}/soil")
        assert len(list_resp.json()) == 3


# ── test_csv_validation_errors ───────────────────────────────────────

class TestCSVValidationErrors:
    def test_csv_validation_errors(self, client, farm_and_field, admin_headers):
        """Invalid pH returns row-level errors."""
        farm_id, field_id = farm_and_field
        csv_data = _make_csv([
            "ph,organic_matter_pct,sampled_at",
            "6.5,3.2,2026-01-15T10:00:00",
            "15.0,2.8,2026-02-20T10:00:00",  # pH > 14 = invalid
            "-1.0,4.1,2026-03-10T10:00:00",  # pH < 0 = invalid
        ])
        resp = client.post(
            f"/api/farms/{farm_id}/fields/{field_id}/soil/import-csv",
            files={"file": ("soil.csv", io.BytesIO(csv_data), "text/csv")},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["imported"] == 1
        assert len(data["errors"]) == 2
        # Errors should reference row numbers
        assert data["errors"][0]["row"] == 3  # 1-indexed, header=1
        assert data["errors"][1]["row"] == 4


# ── test_csv_columns ─────────────────────────────────────────────────

class TestCSVColumns:
    def test_csv_columns_minimum(self, client, farm_and_field, admin_headers):
        """Accepts minimum columns (ph, organic_matter_pct, sampled_at) + optional extras."""
        farm_id, field_id = farm_and_field
        csv_data = _make_csv([
            "ph,organic_matter_pct,sampled_at",
            "6.5,3.2,2026-01-15T10:00:00",
        ])
        resp = client.post(
            f"/api/farms/{farm_id}/fields/{field_id}/soil/import-csv",
            files={"file": ("soil.csv", io.BytesIO(csv_data), "text/csv")},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["imported"] == 1

    def test_csv_columns_with_extras(self, client, farm_and_field, admin_headers):
        """Extra columns like nitrogen_ppm and texture are imported."""
        farm_id, field_id = farm_and_field
        csv_data = _make_csv([
            "ph,organic_matter_pct,sampled_at,nitrogen_ppm,texture",
            "6.5,3.2,2026-01-15T10:00:00,45.0,loam",
        ])
        resp = client.post(
            f"/api/farms/{farm_id}/fields/{field_id}/soil/import-csv",
            files={"file": ("soil.csv", io.BytesIO(csv_data), "text/csv")},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["imported"] == 1

        # Verify extra columns were stored
        list_resp = client.get(f"/api/farms/{farm_id}/fields/{field_id}/soil")
        record = list_resp.json()[0]
        assert record["nitrogen_ppm"] == 45.0
        assert record["texture"] == "loam"

    def test_csv_missing_required_column(self, client, farm_and_field, admin_headers):
        """CSV missing sampled_at column returns 422."""
        farm_id, field_id = farm_and_field
        csv_data = _make_csv([
            "ph,organic_matter_pct",
            "6.5,3.2",
        ])
        resp = client.post(
            f"/api/farms/{farm_id}/fields/{field_id}/soil/import-csv",
            files={"file": ("soil.csv", io.BytesIO(csv_data), "text/csv")},
            headers=admin_headers,
        )
        assert resp.status_code == 422


# ── test_duplicate_date_skip ─────────────────────────────────────────

class TestDuplicateDateSkip:
    def test_duplicate_date_skip(self, client, farm_and_field, admin_headers):
        """Same sampled_at date as existing record → skipped with warning."""
        farm_id, field_id = farm_and_field

        # First: create an existing soil record
        client.post(
            f"/api/farms/{farm_id}/fields/{field_id}/soil",
            json={"ph": 6.5, "organic_matter_pct": 3.2, "sampled_at": "2026-01-15T10:00:00"},
        )

        # Now import CSV with same date + a new date
        csv_data = _make_csv([
            "ph,organic_matter_pct,sampled_at",
            "7.0,2.8,2026-01-15T10:00:00",  # duplicate → skip
            "5.8,4.1,2026-02-20T10:00:00",  # new → import
        ])
        resp = client.post(
            f"/api/farms/{farm_id}/fields/{field_id}/soil/import-csv",
            files={"file": ("soil.csv", io.BytesIO(csv_data), "text/csv")},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["imported"] == 1
        assert data["skipped"] == 1

        # Total records = 1 original + 1 imported = 2
        list_resp = client.get(f"/api/farms/{farm_id}/fields/{field_id}/soil")
        assert len(list_resp.json()) == 2
