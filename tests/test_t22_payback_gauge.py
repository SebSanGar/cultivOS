"""T2.2 — Owner payback radial gauge on economic-impact page.

RED tests — must FAIL before implementation.
GREEN after: #payback-gauge-section + .payback-ring div + updatePaybackGauge() JS,
 green<6mo / amber 6-12 / red>12.
"""


class TestT22PaybackGaugeHTML:
    """economic-impact.html must contain the payback gauge block."""

    def test_payback_gauge_section_exists(self, client):
        r = client.get("/impacto-economico")
        assert r.status_code == 200
        assert 'id="payback-gauge-section"' in r.text

    def test_payback_ring_element_exists(self, client):
        r = client.get("/impacto-economico")
        assert r.status_code == 200
        assert 'id="payback-ring"' in r.text

    def test_payback_gauge_has_value_span(self, client):
        r = client.get("/impacto-economico")
        assert r.status_code == 200
        assert 'id="payback-ring-value"' in r.text

    def test_payback_gauge_has_months_label(self, client):
        r = client.get("/impacto-economico")
        assert r.status_code == 200
        # label says "months" or "mo"
        assert "months" in r.text.lower() or ">mo<" in r.text.lower()


class TestT22PaybackGaugeJS:
    """economic-impact.js must contain updatePaybackGauge function + thresholds."""

    def _js(self, client):
        r = client.get("/economic-impact.js")
        assert r.status_code == 200
        return r.text

    def test_update_payback_gauge_function_exists(self, client):
        js = self._js(client)
        assert "updatePaybackGauge" in js

    def test_green_threshold_lt_6(self, client):
        js = self._js(client)
        # green < 6 months
        assert "< 6" in js or "<6" in js

    def test_red_threshold_gt_12(self, client):
        js = self._js(client)
        # red > 12 months
        assert "> 12" in js or ">12" in js
