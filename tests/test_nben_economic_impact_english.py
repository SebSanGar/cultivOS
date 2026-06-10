"""NB-EN — Economic Impact page English coverage.

Asserts economic-impact.html has English default strings and no key Spanish
UI labels. JS error messages must also be English.
"""

import re
from pathlib import Path

HTML = Path("frontend/economic-impact.html").read_text()
JS = Path("frontend/economic-impact.js").read_text()


# ── HTML English presence ────────────────────────────────────────────────────

def test_page_h1_is_english():
    assert "Economic Impact" in HTML

def test_page_subtitle_is_english():
    assert "Estimated savings" in HTML

def test_farm_select_placeholder_is_english():
    assert "Select a farm" in HTML

def test_refresh_button_is_english():
    assert "Refresh" in HTML

def test_stat_label_total_savings_is_english():
    assert "Total savings" in HTML

def test_stat_label_hectares_is_english():
    assert "Hectares" in HTML

def test_stat_label_water_is_english():
    # The label in the stats strip
    assert "Water" in HTML

def test_stat_label_fertilizer_is_english():
    assert "Fertilizer" in HTML

def test_stat_label_yield_is_english():
    assert "Yield" in HTML

def test_card_titles_are_english():
    assert "Water savings" in HTML
    assert "Organic fertilizer" in HTML

def test_footer_is_english():
    assert "Precision agriculture" in HTML or "precision agriculture" in HTML

def test_reference_section_is_english():
    # Footer reference blob should be in English
    assert "Reference:" in HTML or "Jalisco, Mexico" in HTML or "typical" in HTML


# ── HTML Spanish absence (key banlist) ───────────────────────────────────────

def test_no_spanish_ahorro_total():
    assert "Ahorro total" not in HTML

def test_no_spanish_hectareas_label():
    # "Hectareas" as a stat label should be gone; data values may remain
    # We check for the <label> context specifically
    assert "Hectareas</div>" not in HTML

def test_no_spanish_ahorro_en_agua_label():
    assert "Ahorro en agua</div>" not in HTML

def test_no_spanish_rendimiento_label():
    # As a standalone stat label
    assert "Rendimiento</div>" not in HTML

def test_no_spanish_seleccione():
    assert "Seleccione una granja" not in HTML

def test_no_spanish_actualizar_button():
    # "Actualizar" as button text (not in a comment)
    assert ">Actualizar<" not in HTML

def test_no_spanish_impacto_economico_h1():
    # Page h1 should be English; "Impacto Economico" may only appear in nav link
    assert "<h1" in HTML
    h1_match = re.search(r"<h1[^>]*>(.*?)</h1>", HTML, re.DOTALL)
    assert h1_match, "No h1 found"
    assert "Impacto" not in h1_match.group(1)

def test_no_spanish_agricultura_footer():
    assert "Agricultura de precision para Jalisco" not in HTML

def test_no_spanish_transformando_footer():
    assert "Transformando la agricultura" not in HTML

def test_no_spanish_referencia():
    assert "Referencia:" not in HTML


# ── JS English presence ───────────────────────────────────────────────────────

def test_js_error_message_is_english():
    assert "Could not" in JS or "Failed to" in JS or "Unable to" in JS

def test_js_no_spanish_error():
    assert "No se pudo obtener" not in JS
