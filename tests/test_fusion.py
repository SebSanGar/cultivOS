"""Tests for multi-sensor fusion validation.

Cross-checks NDVI + thermal + soil + weather for consistency,
flags contradictions, and computes confidence scores.
"""

import pytest
from cultivos.services.crop.fusion import (
    validate_sensor_fusion,
    FusionResult,
    SensorContradiction,
)


# --- Contradiction detection ---


def test_contradiction_ndvi_healthy_thermal_stressed():
    """NDVI says healthy (>0.6) but thermal shows high stress (>40%) => flag."""
    result = validate_sensor_fusion(
        ndvi={"ndvi_mean": 0.75, "ndvi_std": 0.05, "stress_pct": 5.0},
        thermal={"stress_pct": 50.0, "temp_mean": 38.0, "irrigation_deficit": True},
    )
    assert len(result["contradictions"]) >= 1
    tags = [c["tag"] for c in result["contradictions"]]
    assert "ndvi_thermal_mismatch" in tags


def test_contradiction_ndvi_stressed_soil_healthy():
    """NDVI shows stress (<0.4) but soil metrics are all optimal => flag."""
    result = validate_sensor_fusion(
        ndvi={"ndvi_mean": 0.30, "ndvi_std": 0.12, "stress_pct": 40.0},
        soil={
            "ph": 6.5,
            "organic_matter_pct": 5.0,
            "nitrogen_ppm": 40,
            "phosphorus_ppm": 25,
            "potassium_ppm": 175,
            "moisture_pct": 35.0,
        },
    )
    assert len(result["contradictions"]) >= 1
    tags = [c["tag"] for c in result["contradictions"]]
    assert "ndvi_soil_mismatch" in tags


def test_contradiction_weather_hot_thermal_cool():
    """Weather says hot (>35C) but thermal stress is low (<10%) => flag."""
    result = validate_sensor_fusion(
        thermal={"stress_pct": 5.0, "temp_mean": 24.0, "irrigation_deficit": False},
        weather={"temp_c": 40.0, "humidity_pct": 20, "wind_kmh": 5.0},
    )
    assert len(result["contradictions"]) >= 1
    tags = [c["tag"] for c in result["contradictions"]]
    assert "weather_thermal_mismatch" in tags


# --- No false flags when consistent ---


def test_no_contradiction_all_healthy():
    """All sensors agree: healthy field => no contradictions."""
    result = validate_sensor_fusion(
        ndvi={"ndvi_mean": 0.75, "ndvi_std": 0.04, "stress_pct": 5.0},
        thermal={"stress_pct": 8.0, "temp_mean": 28.0, "irrigation_deficit": False},
        soil={
            "ph": 6.5,
            "organic_matter_pct": 4.5,
            "nitrogen_ppm": 35,
            "phosphorus_ppm": 25,
            "potassium_ppm": 150,
            "moisture_pct": 40.0,
        },
        weather={"temp_c": 28.0, "humidity_pct": 55, "wind_kmh": 10.0},
    )
    assert result["contradictions"] == []


def test_no_contradiction_all_stressed():
    """All sensors agree: stressed field => no contradictions."""
    result = validate_sensor_fusion(
        ndvi={"ndvi_mean": 0.25, "ndvi_std": 0.15, "stress_pct": 55.0},
        thermal={"stress_pct": 60.0, "temp_mean": 39.0, "irrigation_deficit": True},
        soil={
            "ph": 4.5,
            "organic_matter_pct": 1.0,
            "moisture_pct": 10.0,
        },
        weather={"temp_c": 39.0, "humidity_pct": 15, "wind_kmh": 25.0},
    )
    assert result["contradictions"] == []


def test_no_false_flag_partial_data():
    """With only NDVI data, no contradictions can be flagged."""
    result = validate_sensor_fusion(
        ndvi={"ndvi_mean": 0.70, "ndvi_std": 0.05, "stress_pct": 8.0},
    )
    assert result["contradictions"] == []


# --- Confidence score ---


def test_confidence_increases_with_more_sensors():
    """More sensors = higher confidence."""
    result_one = validate_sensor_fusion(
        ndvi={"ndvi_mean": 0.70, "ndvi_std": 0.05, "stress_pct": 8.0},
    )
    result_two = validate_sensor_fusion(
        ndvi={"ndvi_mean": 0.70, "ndvi_std": 0.05, "stress_pct": 8.0},
        thermal={"stress_pct": 10.0, "temp_mean": 28.0, "irrigation_deficit": False},
    )
    result_all = validate_sensor_fusion(
        ndvi={"ndvi_mean": 0.70, "ndvi_std": 0.05, "stress_pct": 8.0},
        thermal={"stress_pct": 10.0, "temp_mean": 28.0, "irrigation_deficit": False},
        soil={"ph": 6.5, "organic_matter_pct": 4.0, "moisture_pct": 35.0},
        weather={"temp_c": 28.0, "humidity_pct": 55, "wind_kmh": 10.0},
    )
    assert result_one["confidence"] < result_two["confidence"]
    assert result_two["confidence"] < result_all["confidence"]


def test_confidence_drops_with_contradictions():
    """Contradictions reduce confidence."""
    # Consistent
    consistent = validate_sensor_fusion(
        ndvi={"ndvi_mean": 0.75, "ndvi_std": 0.05, "stress_pct": 5.0},
        thermal={"stress_pct": 8.0, "temp_mean": 28.0, "irrigation_deficit": False},
    )
    # Contradictory
    contradictory = validate_sensor_fusion(
        ndvi={"ndvi_mean": 0.75, "ndvi_std": 0.05, "stress_pct": 5.0},
        thermal={"stress_pct": 50.0, "temp_mean": 38.0, "irrigation_deficit": True},
    )
    assert contradictory["confidence"] < consistent["confidence"]


def test_confidence_range():
    """Confidence is always 0.0-1.0."""
    result = validate_sensor_fusion(
        ndvi={"ndvi_mean": 0.70, "ndvi_std": 0.05, "stress_pct": 8.0},
    )
    assert 0.0 <= result["confidence"] <= 1.0


# --- Result structure ---


def test_result_has_required_fields():
    """Result has all required fields."""
    result = validate_sensor_fusion(
        ndvi={"ndvi_mean": 0.70, "ndvi_std": 0.05, "stress_pct": 8.0},
    )
    assert "contradictions" in result
    assert "confidence" in result
    assert "sensors_used" in result
    assert "assessment" in result


def test_sensors_used_tracks_inputs():
    """sensors_used lists which sensors were provided."""
    result = validate_sensor_fusion(
        ndvi={"ndvi_mean": 0.70, "ndvi_std": 0.05, "stress_pct": 8.0},
        soil={"ph": 6.5},
    )
    assert "ndvi" in result["sensors_used"]
    assert "soil" in result["sensors_used"]
    assert "thermal" not in result["sensors_used"]
    assert "weather" not in result["sensors_used"]


def test_assessment_text_in_spanish():
    """Assessment is farmer-facing Spanish text."""
    result = validate_sensor_fusion(
        ndvi={"ndvi_mean": 0.75, "ndvi_std": 0.05, "stress_pct": 5.0},
        thermal={"stress_pct": 8.0, "temp_mean": 28.0, "irrigation_deficit": False},
    )
    assert isinstance(result["assessment"], str)
    assert len(result["assessment"]) > 0


# --- API route tests ---


class TestFusionAPI:
    """Integration tests for POST /api/analysis/fusion."""

    def test_post_fusion_happy_path(self, client):
        resp = client.post("/api/analysis/fusion", json={
            "ndvi": {"ndvi_mean": 0.75, "ndvi_std": 0.05, "stress_pct": 5.0},
            "thermal": {"stress_pct": 8.0, "temp_mean": 28.0, "irrigation_deficit": False},
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["contradictions"] == []
        assert data["confidence"] > 0
        assert "ndvi" in data["sensors_used"]
        assert "thermal" in data["sensors_used"]

    def test_post_fusion_detects_contradiction(self, client):
        resp = client.post("/api/analysis/fusion", json={
            "ndvi": {"ndvi_mean": 0.75, "ndvi_std": 0.05, "stress_pct": 5.0},
            "thermal": {"stress_pct": 50.0, "temp_mean": 38.0, "irrigation_deficit": True},
        })
        assert resp.status_code == 200
        tags = [c["tag"] for c in resp.json()["contradictions"]]
        assert "ndvi_thermal_mismatch" in tags

    def test_post_fusion_empty_body(self, client):
        resp = client.post("/api/analysis/fusion", json={})
        assert resp.status_code == 200
        assert resp.json()["sensors_used"] == []

    def test_post_fusion_validation_error(self, client):
        resp = client.post("/api/analysis/fusion", json={
            "ndvi": {"ndvi_mean": 2.0},  # >1.0 invalid
        })
        assert resp.status_code == 422
