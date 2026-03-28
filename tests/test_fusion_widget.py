"""Tests for sensor fusion widget scenarios.

Verifies the fusion data shapes and edge cases the field detail
frontend widget depends on: confidence levels, contradiction details,
sensor badge counts, and assessment text for each scenario.
"""

import pytest
from cultivos.services.crop.fusion import validate_sensor_fusion


# --- Widget scenario: high confidence, no contradictions ---

def test_widget_all_sensors_healthy_high_confidence():
    """Widget shows green confidence bar when all 4 sensors agree healthy."""
    result = validate_sensor_fusion(
        ndvi={"ndvi_mean": 0.72, "ndvi_std": 0.04, "stress_pct": 8.0},
        thermal={"stress_pct": 10.0, "temp_mean": 27.0, "irrigation_deficit": False},
        soil={"ph": 6.5, "organic_matter_pct": 4.0, "nitrogen_ppm": 35,
              "phosphorus_ppm": 25, "potassium_ppm": 150, "moisture_pct": 40.0},
        weather={"temp_c": 27.0, "humidity_pct": 55, "wind_kmh": 8.0},
    )
    assert result["confidence"] >= 0.7
    assert len(result["sensors_used"]) == 4
    assert result["contradictions"] == []
    assert "buen estado" in result["assessment"]


# --- Widget scenario: low confidence with contradictions ---

def test_widget_contradiction_shows_warning_details():
    """Widget renders contradiction card with tag, sensors, and description."""
    result = validate_sensor_fusion(
        ndvi={"ndvi_mean": 0.75, "ndvi_std": 0.05, "stress_pct": 5.0},
        thermal={"stress_pct": 50.0, "temp_mean": 38.0, "irrigation_deficit": True},
    )
    assert len(result["contradictions"]) >= 1
    c = result["contradictions"][0]
    # Widget needs all three fields for rendering
    assert "tag" in c
    assert "sensors" in c and len(c["sensors"]) == 2
    assert "description" in c and len(c["description"]) > 10
    # Confidence should be reduced
    assert result["confidence"] < 0.7


# --- Widget scenario: single sensor (minimal data) ---

def test_widget_single_sensor_low_confidence():
    """Widget shows low confidence bar when only one sensor available."""
    result = validate_sensor_fusion(
        ndvi={"ndvi_mean": 0.65, "ndvi_std": 0.06, "stress_pct": 12.0},
    )
    assert len(result["sensors_used"]) == 1
    assert result["confidence"] < 0.5
    assert result["contradictions"] == []


# --- Widget scenario: no sensors at all ---

def test_widget_no_sensors_zero_confidence():
    """Widget shows empty state when no sensor data provided."""
    result = validate_sensor_fusion()
    assert result["confidence"] == 0.0
    assert result["sensors_used"] == []
    assert result["contradictions"] == []


# --- Widget scenario: multiple contradictions ---

def test_widget_multiple_contradictions_stacked():
    """Widget stacks multiple contradiction cards."""
    result = validate_sensor_fusion(
        ndvi={"ndvi_mean": 0.75, "ndvi_std": 0.05, "stress_pct": 5.0},
        thermal={"stress_pct": 55.0, "temp_mean": 38.0, "irrigation_deficit": True},
        soil={"ph": 6.5, "organic_matter_pct": 4.5, "moisture_pct": 60.0},
    )
    # ndvi_thermal_mismatch + thermal_soil_moisture_mismatch
    assert len(result["contradictions"]) >= 2
    tags = [c["tag"] for c in result["contradictions"]]
    assert "ndvi_thermal_mismatch" in tags
    assert "thermal_soil_moisture_mismatch" in tags


# --- Widget scenario: assessment text is always Spanish ---

def test_widget_assessment_always_spanish():
    """Widget assessment text is in Spanish for farmer-facing display."""
    for scenario in [
        {"ndvi": {"ndvi_mean": 0.7, "ndvi_std": 0.04, "stress_pct": 8.0}},
        {"ndvi": {"ndvi_mean": 0.3, "ndvi_std": 0.1, "stress_pct": 40.0},
         "thermal": {"stress_pct": 50.0, "temp_mean": 38.0, "irrigation_deficit": True}},
    ]:
        result = validate_sensor_fusion(**scenario)
        assert isinstance(result["assessment"], str)
        assert len(result["assessment"]) > 0
        # Should contain Spanish words
        text = result["assessment"].lower()
        assert any(w in text for w in ["sensor", "confianza", "campo", "coinciden", "inconsistencia"])


# --- Widget scenario: confidence bar percentage mapping ---

def test_widget_confidence_percentage_for_bar_width():
    """Confidence 0.0-1.0 maps to 0-100% bar width in widget."""
    result = validate_sensor_fusion(
        ndvi={"ndvi_mean": 0.72, "ndvi_std": 0.04, "stress_pct": 8.0},
        thermal={"stress_pct": 10.0, "temp_mean": 28.0, "irrigation_deficit": False},
    )
    # Confidence should be a float between 0 and 1
    assert isinstance(result["confidence"], float)
    assert 0.0 <= result["confidence"] <= 1.0
    # Two consistent sensors should give moderate-high confidence
    assert result["confidence"] >= 0.4
