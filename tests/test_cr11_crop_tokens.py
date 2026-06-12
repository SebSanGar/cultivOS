"""
CR11 — crop tokens raw in non-farmer-journey JS renderers.
Source-inspection tests (no server). All fail before implementation.
Target: intel.js, calendario.js, irrigation.js, yield.js, regional.js, management.js
DONE-GATE: no raw crop tokens in visible renders; option VALUES stay raw (API filters).
"""
import os

FRONTEND = os.path.join(os.path.dirname(__file__), '..', 'frontend')


def _js(name: str) -> str:
    with open(os.path.join(FRONTEND, name), 'r', encoding='utf-8') as f:
        return f.read()


# ── intel.js ──────────────────────────────────────────────────────────────────

def test_intel_has_cropLabel_shim():
    assert 'function cropLabel' in _js('intel.js'), \
        'intel.js must define cropLabel() shim'


def test_intel_crop_filter_uses_cropLabel():
    assert 'cropLabel(ct)' in _js('intel.js'), \
        'intel.js loadCropTypeOptions must use cropLabel(ct) for opt.textContent'


def test_intel_no_raw_charAt_crop():
    # Old: opt.textContent = ct.charAt(0).toUpperCase() + ct.slice(1)
    assert 'ct.charAt(0)' not in _js('intel.js'), \
        'intel.js must not use charAt(0) for crop display — use cropLabel(ct)'


# ── calendario.js ─────────────────────────────────────────────────────────────

def test_calendario_has_cropLabel_shim():
    assert 'function cropLabel' in _js('calendario.js'), \
        'calendario.js must define cropLabel() shim'


def test_calendario_row_label_uses_cropLabel():
    # Old: label.textContent = crop.crop_type
    assert 'label.textContent = cropLabel(' in _js('calendario.js'), \
        'calendario.js cal-crop-label textContent must use cropLabel(crop.crop_type)'


def test_calendario_field_opt_uses_cropLabel():
    # Old: f.name + (f.crop_type ? ' (' + f.crop_type + ')' : '')
    assert 'cropLabel(f.crop_type)' in _js('calendario.js'), \
        'calendario.js field select opt.textContent must use cropLabel(f.crop_type)'


def test_calendario_detail_panel_uses_cropLabel():
    # Old: data.crop_type raw in cal-field-info innerHTML
    assert 'cropLabel(data.crop_type)' in _js('calendario.js'), \
        'calendario.js field detail panel must use cropLabel(data.crop_type)'


# ── irrigation.js ─────────────────────────────────────────────────────────────

def test_irrigation_has_cropLabel_shim():
    assert 'function cropLabel' in _js('irrigation.js'), \
        'irrigation.js must define cropLabel() shim'


def test_irrigation_field_opt_uses_cropLabel():
    # Old: opt.textContent = f.name + (f.crop_type ? " (" + f.crop_type + ")" : "")
    assert 'cropLabel(f.crop_type)' in _js('irrigation.js'), \
        'irrigation.js field select opt must use cropLabel(f.crop_type)'


def test_irrigation_stat_uses_cropLabel():
    # Old: document.getElementById("irrigation-crop").textContent = data.crop_type || "--"
    assert 'cropLabel(data.crop_type)' in _js('irrigation.js'), \
        'irrigation.js irrigation-crop stat must use cropLabel(data.crop_type)'


# ── yield.js ──────────────────────────────────────────────────────────────────

def test_yield_has_cropLabel_shim():
    assert 'function cropLabel' in _js('yield.js'), \
        'yield.js must define cropLabel() shim'


def test_yield_field_opt_uses_cropLabel():
    # Old: opt.textContent = f.name + (f.crop_type ? " (" + f.crop_type + ")" : "")
    assert 'cropLabel(f.crop_type)' in _js('yield.js'), \
        'yield.js field select opt must use cropLabel(f.crop_type)'


def test_yield_card_uses_cropLabel():
    # Old: esc(data.crop_type) in card innerHTML twice
    assert 'cropLabel(data.crop_type)' in _js('yield.js'), \
        'yield.js yield card render must use cropLabel(data.crop_type)'


# ── regional.js ───────────────────────────────────────────────────────────────

def test_regional_has_cropLabel_shim():
    assert 'function cropLabel' in _js('regional.js'), \
        'regional.js must define cropLabel() shim'


def test_regional_badge_uses_cropLabel():
    # Old: '<span class="intel-badge">' + escapeHtml(c.crop_type) + ...
    assert 'cropLabel(c.crop_type)' in _js('regional.js'), \
        'regional.js crop_distribution badge must use cropLabel(c.crop_type)'


# ── management.js ─────────────────────────────────────────────────────────────

def test_management_has_cropLabel_shim():
    assert 'function cropLabel' in _js('management.js'), \
        'management.js must define cropLabel() shim'


def test_management_table_uses_cropLabel():
    # Old: cropLabels[f.crop_type] || esc(f.crop_type || '—')
    assert 'cropLabel(f.crop_type)' in _js('management.js'), \
        'management.js field table must use cropLabel(f.crop_type)'


def test_management_no_static_dict():
    # Old static dict must be gone
    assert "maize: 'Maiz'" not in _js('management.js'), \
        "management.js static cropLabels dict must be replaced by cropLabel() shim"
