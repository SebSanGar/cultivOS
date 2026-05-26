"""F4 — farmer_voice.py TDD tests.

translate_to_farmer(signal: dict) -> str

Covers 12 signal types. Each test verifies:
1. Output is a non-empty Spanish string
2. Output contains no technical jargon (NDVI, ROI, KPI, threshold,
   optimization, anomaly, dashboard, metricas, celsius, pct)
"""

import re
import pytest

from cultivos.services.intelligence.farmer_voice import translate_to_farmer

# ---------------------------------------------------------------------------
# Jargon-leak guard — applied to every output
# ---------------------------------------------------------------------------
_JARGON = re.compile(
    r"\b(ndvi|roi|kpi|threshold|optimization|anomaly|dashboard|metricas|celsius|pct)\b",
    re.IGNORECASE,
)


def _no_jargon(text: str) -> bool:
    """Return True if text contains no forbidden jargon."""
    return _JARGON.search(text) is None


def _is_spanish(text: str) -> bool:
    """Rough heuristic: contains at least one common Spanish word."""
    markers = re.compile(
        r"\b(tu|la|el|en|de|que|una|los|las|hay|muy|no|si|su|se|es|por)\b",
        re.IGNORECASE,
    )
    return bool(markers.search(text))


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def _check(signal: dict) -> str:
    result = translate_to_farmer(signal)
    assert isinstance(result, str), "output must be str"
    assert len(result) > 5, "output too short"
    assert _no_jargon(result), f"jargon found in: {result!r}"
    assert _is_spanish(result), f"output doesn't look Spanish: {result!r}"
    return result


# ---------------------------------------------------------------------------
# 12 signal types
# ---------------------------------------------------------------------------

class TestLowNdvi:
    def test_returns_spanish_string(self):
        out = _check({"type": "low_ndvi", "value": 0.32})
        # Should mention water/thirst — low NDVI = water stress in avocado
        assert any(w in out.lower() for w in ("sed", "agua", "seco", "humedad")), out

    def test_very_low_ndvi(self):
        _check({"type": "low_ndvi", "value": 0.10})

    def test_no_jargon(self):
        out = translate_to_farmer({"type": "low_ndvi", "value": 0.25})
        assert _no_jargon(out), out


class TestHighThermal:
    def test_returns_spanish_string(self):
        out = _check({"type": "high_thermal", "celsius": 38})
        assert any(w in out.lower() for w in ("calor", "caliente", "temperatura", "seca")), out

    def test_extreme_heat(self):
        _check({"type": "high_thermal", "celsius": 45})

    def test_no_jargon(self):
        out = translate_to_farmer({"type": "high_thermal", "celsius": 39})
        assert _no_jargon(out), out


class TestLowHealth:
    def test_returns_spanish_string(self):
        out = _check({"type": "low_health", "score": 28})
        assert any(w in out.lower() for w in ("atencion", "bien", "mal", "salud", "cuidado")), out

    def test_moderate_low_health(self):
        _check({"type": "low_health", "score": 45})

    def test_no_jargon(self):
        out = translate_to_farmer({"type": "low_health", "score": 30})
        assert _no_jargon(out), out


class TestIrrigation:
    def test_returns_spanish_string(self):
        out = _check({"type": "irrigation"})
        assert any(w in out.lower() for w in ("agua", "riego", "riega", "regar")), out

    def test_no_jargon(self):
        out = translate_to_farmer({"type": "irrigation"})
        assert _no_jargon(out), out


class TestAnomalyHealthDrop:
    def test_returns_spanish_string(self):
        out = _check({"type": "anomaly_health_drop", "drop_pct": 15})
        assert any(w in out.lower() for w in ("bajo", "perdio", "perdiendo", "cambio", "rapido", "baja")), out

    def test_no_jargon(self):
        out = translate_to_farmer({"type": "anomaly_health_drop", "drop_pct": 20})
        assert _no_jargon(out), out


class TestAnomalyNdviDrop:
    def test_returns_spanish_string(self):
        out = _check({"type": "anomaly_ndvi_drop", "drop_pct": 12})
        assert any(w in out.lower() for w in ("plantas", "fuerza", "debil", "perdiendo", "vigor")), out

    def test_no_jargon(self):
        out = translate_to_farmer({"type": "anomaly_ndvi_drop"})
        assert _no_jargon(out), out


class TestWaterStressSevere:
    def test_returns_spanish_string(self):
        out = _check({"type": "water_stress_severe"})
        assert any(w in out.lower() for w in ("seco", "urgente", "hoy", "agua", "inmediato")), out

    def test_no_jargon(self):
        out = translate_to_farmer({"type": "water_stress_severe"})
        assert _no_jargon(out), out


class TestWaterStressModerate:
    def test_returns_spanish_string(self):
        out = _check({"type": "water_stress_moderate"})
        assert any(w in out.lower() for w in ("pronto", "agua", "riego", "humedad", "revisar")), out

    def test_no_jargon(self):
        out = translate_to_farmer({"type": "water_stress_moderate"})
        assert _no_jargon(out), out


class TestDiseaseRiskHigh:
    def test_returns_spanish_string(self):
        out = _check({"type": "disease_risk_high"})
        assert any(w in out.lower() for w in ("plaga", "enfermedad", "hongo", "revision", "revisa")), out

    def test_no_jargon(self):
        out = translate_to_farmer({"type": "disease_risk_high"})
        assert _no_jargon(out), out


class TestDiseaseRiskMedium:
    def test_returns_spanish_string(self):
        out = _check({"type": "disease_risk_medium"})
        assert any(w in out.lower() for w in ("vigila", "cuida", "atencion", "plaga", "enfermedad")), out

    def test_no_jargon(self):
        out = translate_to_farmer({"type": "disease_risk_medium"})
        assert _no_jargon(out), out


class TestFrost:
    def test_returns_spanish_string(self):
        out = _check({"type": "frost"})
        assert any(w in out.lower() for w in ("helada", "frio", "fría", "protege", "noche")), out

    def test_no_jargon(self):
        out = translate_to_farmer({"type": "frost"})
        assert _no_jargon(out), out


class TestHeavyRain:
    def test_returns_spanish_string(self):
        out = _check({"type": "heavy_rain", "rainfall_mm": 60})
        assert any(w in out.lower() for w in ("lluvia", "agua", "inundacion", "encharcamiento", "encharca")), out

    def test_no_jargon(self):
        out = translate_to_farmer({"type": "heavy_rain"})
        assert _no_jargon(out), out


# ---------------------------------------------------------------------------
# Unknown type — graceful fallback, no exception
# ---------------------------------------------------------------------------

class TestUnknownType:
    def test_returns_fallback_string(self):
        out = translate_to_farmer({"type": "totally_unknown_signal"})
        assert isinstance(out, str)
        assert len(out) > 0

    def test_missing_type_key(self):
        out = translate_to_farmer({})
        assert isinstance(out, str)
        assert len(out) > 0
