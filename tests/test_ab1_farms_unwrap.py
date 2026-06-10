"""AB1 — farms-response unwrap: 13 JS files must use resp.data pattern, not data.farms/farms.farms."""
import re
import subprocess


BROKEN_PATTERNS = [
    r"\.farms\.forEach",
    r"data\.farms",
    r"farms\.farms",
]

FILES = [
    "frontend/alert-config.js",
    "frontend/actions.js",
    "frontend/alertas-estacionales.js",
    "frontend/clima.js",
    "frontend/comparar.js",
    "frontend/reportes.js",
    "frontend/exportar.js",
    "frontend/flights.js",
    "frontend/recommendations.js",
    "frontend/soil-history.js",
    "frontend/thermal-dashboard.js",
    "frontend/timeline.js",
    "frontend/resumen.js",
]

# Pattern all fixed files must use: unwrap resp.data or resp.items
CORRECT_UNWRAP_RE = re.compile(r"resp\.(data|items)|data\.(data|items)")


def _read(path):
    with open(path) as f:
        return f.read()


class TestAB1NoFarmsWrapper:
    """No file in the list should use the broken .farms access on the wrapper response."""

    def test_no_data_farms_pattern(self):
        result = subprocess.run(
            ["rg", r"\.farms\.forEach|data\.farms|farms\.farms", "frontend/"],
            capture_output=True,
            text=True,
        )
        # rg exit code 1 = no matches (success); 0 = matches found (fail)
        assert result.returncode == 1, (
            f"Broken farms pattern still present:\n{result.stdout}"
        )


class TestAB1CorrectUnwrap:
    """Each of the 13 files must use the correct resp.data/resp.items unwrap."""

    def test_alert_config_unwrap(self):
        js = _read("frontend/alert-config.js")
        assert CORRECT_UNWRAP_RE.search(js), "alert-config.js: missing resp.data unwrap"

    def test_actions_unwrap(self):
        js = _read("frontend/actions.js")
        assert CORRECT_UNWRAP_RE.search(js), "actions.js: missing resp.data unwrap"

    def test_alertas_estacionales_unwrap(self):
        js = _read("frontend/alertas-estacionales.js")
        assert CORRECT_UNWRAP_RE.search(js), "alertas-estacionales.js: missing resp.data unwrap"

    def test_clima_unwrap(self):
        js = _read("frontend/clima.js")
        assert CORRECT_UNWRAP_RE.search(js), "clima.js: missing resp.data unwrap"

    def test_comparar_unwrap(self):
        js = _read("frontend/comparar.js")
        assert CORRECT_UNWRAP_RE.search(js), "comparar.js: missing resp.data unwrap"

    def test_reportes_unwrap(self):
        js = _read("frontend/reportes.js")
        assert CORRECT_UNWRAP_RE.search(js), "reportes.js: missing resp.data unwrap"

    def test_exportar_unwrap(self):
        js = _read("frontend/exportar.js")
        assert CORRECT_UNWRAP_RE.search(js), "exportar.js: missing resp.data unwrap"

    def test_flights_unwrap(self):
        js = _read("frontend/flights.js")
        assert CORRECT_UNWRAP_RE.search(js), "flights.js: missing resp.data unwrap"

    def test_recommendations_unwrap(self):
        js = _read("frontend/recommendations.js")
        assert CORRECT_UNWRAP_RE.search(js), "recommendations.js: missing resp.data unwrap"

    def test_soil_history_unwrap(self):
        js = _read("frontend/soil-history.js")
        assert CORRECT_UNWRAP_RE.search(js), "soil-history.js: missing resp.data unwrap"

    def test_thermal_dashboard_unwrap(self):
        js = _read("frontend/thermal-dashboard.js")
        assert CORRECT_UNWRAP_RE.search(js), "thermal-dashboard.js: missing resp.data unwrap"

    def test_timeline_unwrap(self):
        js = _read("frontend/timeline.js")
        assert CORRECT_UNWRAP_RE.search(js), "timeline.js: missing resp.data unwrap"

    def test_resumen_unwrap(self):
        js = _read("frontend/resumen.js")
        assert CORRECT_UNWRAP_RE.search(js), "resumen.js: missing resp.data unwrap"


class TestAB1FarmsSelectPopulated:
    """Pages that expose a farm-select must serve the <select> element."""

    PAGES_WITH_SELECT = {
        "/alertas-config": "alert-farm-select",
        "/acciones": "actions-farm-select",
        "/alertas-estacionales": "seasonal-farm-select",
        "/clima": "clima-farm-select",
        "/comparar": "comp-farm-1",
        "/reportes": "reportes-farm-select",
        "/exportar": "exportar-farm-select",
        "/recomendaciones": "recs-farm-select",
        "/suelo": "soil-farm-select",
        "/termica": "thermal-farm-select",
        "/historial": "tl-farm-select",
    }

    def test_pages_serve_200(self, client):
        for route in self.PAGES_WITH_SELECT:
            resp = client.get(route)
            assert resp.status_code == 200, f"{route} returned {resp.status_code}"

    def test_select_elements_present(self, client):
        for route, select_id in self.PAGES_WITH_SELECT.items():
            resp = client.get(route)
            assert select_id in resp.text, f"{route}: missing #{select_id}"
