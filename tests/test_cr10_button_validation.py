"""
CR10 — Primary action buttons: English validation feedback when no farm/field selected.
Done-gate: empty-state elements show English text; economic-impact shows visible message on no-farm.
Source-inspection tests (no server).
"""

import os

FRONTEND = os.path.join(os.path.dirname(__file__), '..', 'frontend')


def _html(name: str) -> str:
    with open(os.path.join(FRONTEND, name), 'r', encoding='utf-8') as f:
        return f.read()


def _js(name: str) -> str:
    with open(os.path.join(FRONTEND, name), 'r', encoding='utf-8') as f:
        return f.read()


# --- anomalies.html ---

def test_anomalies_empty_state_english():
    html = _html('anomalies.html')
    assert 'Select a farm' in html, 'anomalies.html empty state must contain English "Select a farm"'


def test_anomalies_empty_state_no_spanish_select():
    html = _html('anomalies.html')
    assert 'Seleccione una granja y un campo para detectar anomalias' not in html, \
        'anomalies.html still has Spanish no-selection message'


# --- microbiome.html ---

def test_microbiome_empty_state_english():
    html = _html('microbiome.html')
    assert 'Select a farm' in html, 'microbiome.html empty state must contain English "Select a farm"'


def test_microbiome_empty_state_no_spanish_select():
    html = _html('microbiome.html')
    assert 'Seleccione una granja y un campo para ver los indicadores de microbioma del suelo' not in html, \
        'microbiome.html still has Spanish no-selection message'


# --- rotation.html ---

def test_rotation_empty_state_english():
    html = _html('rotation.html')
    assert 'Select a farm' in html, 'rotation.html empty state must contain English "Select a farm"'


def test_rotation_empty_state_no_spanish_select():
    html = _html('rotation.html')
    assert 'Seleccione una granja y un campo para generar el plan de rotacion de cultivos' not in html, \
        'rotation.html still has Spanish no-selection message'


# --- seasonal.html ---

def test_seasonal_empty_state_english():
    html = _html('seasonal.html')
    assert 'Select a farm' in html, 'seasonal.html empty state must contain English "Select a farm"'


def test_seasonal_empty_state_no_spanish_select():
    html = _html('seasonal.html')
    assert 'Seleccione una granja y un campo para comparar el rendimiento entre temporadas' not in html, \
        'seasonal.html still has Spanish no-selection message'


# --- soil-history.html ---

def test_soil_history_empty_state_english():
    html = _html('soil-history.html')
    assert 'Select a farm' in html, 'soil-history.html empty state must contain English "Select a farm"'


def test_soil_history_empty_state_no_spanish_select():
    html = _html('soil-history.html')
    assert 'Seleccione una granja y un campo para ver el historial de suelo' not in html, \
        'soil-history.html still has Spanish no-selection message'


# --- thermal-dashboard.html ---

def test_thermal_empty_state_english():
    html = _html('thermal-dashboard.html')
    assert 'Select a farm' in html, 'thermal-dashboard.html empty state must contain English "Select a farm"'


def test_thermal_empty_state_no_spanish_select():
    html = _html('thermal-dashboard.html')
    assert 'Seleccione una granja y un campo para ver el analisis termico' not in html, \
        'thermal-dashboard.html still has Spanish no-selection message'


# --- timeline.html ---

def test_timeline_empty_state_english():
    html = _html('timeline.html')
    assert 'Select a farm' in html, 'timeline.html empty state must contain English "Select a farm"'


def test_timeline_empty_state_no_spanish_select():
    html = _html('timeline.html')
    assert 'Seleccione una granja y un campo para ver el historial de salud' not in html, \
        'timeline.html still has Spanish no-selection message'


# --- yield.html ---

def test_yield_empty_state_english():
    html = _html('yield.html')
    assert 'Select a farm' in html, 'yield.html empty state must contain English "Select a farm"'


def test_yield_empty_state_no_spanish_select():
    html = _html('yield.html')
    assert 'Seleccione una granja y un campo para ver la prediccion de rendimiento' not in html, \
        'yield.html still has Spanish no-selection message'


# --- economic-impact.js ---

def test_economic_impact_no_farm_shows_message():
    """Done-gate: no-farm path must show a visible English message, not just silently reset."""
    js = _js('economic-impact.js')
    assert 'Select a farm' in js, \
        'economic-impact.js must show English message when no farm selected (no silent no-op)'


def test_economic_impact_nota_not_hidden_on_no_farm():
    """notaEl must not be hidden (display:none) in the no-farm early return branch."""
    js = _js('economic-impact.js')
    lines = js.splitlines()
    in_no_farm_block = False
    for i, line in enumerate(lines):
        if '!farmId' in line:
            in_no_farm_block = True
        if in_no_farm_block and 'return;' in line:
            break
        if in_no_farm_block and "notaEl.style.display = 'none'" in line:
            assert False, \
                'economic-impact.js hides notaEl in no-farm path — must show message instead'
