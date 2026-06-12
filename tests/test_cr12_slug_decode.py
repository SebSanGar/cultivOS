"""
CR12 — raw underscore slugs shown to users.
Source-inspection tests (no server). All fail before implementation.

Targets:
  /conocimiento — practice_type badges: water_management, soil_management,
                  biological_control, knowledge_system, intercropping shown raw.
  /campo        — risk badge shows 'Risksin_riesgo' (levelLabel misses sin_riesgo slug).

Fix:
  knowledge.js  — add practiceTypeLabel() helper + use it in renderAncestral badge.
  field.js      — add sin_riesgo to levelLabel keyMap (ONLY this slug line).
  i18n.js       — add know.practice* keys (ES+EN) + field.levelNoRisk (ES+EN).

DONE-GATE: /conocimiento badges readable; /campo risk badge decodes sin_riesgo.
"""
import os

FRONTEND = os.path.join(os.path.dirname(__file__), '..', 'frontend')


def _read(name: str) -> str:
    with open(os.path.join(FRONTEND, name), 'r', encoding='utf-8') as f:
        return f.read()


# ── i18n.js — practice type keys ─────────────────────────────────────────────

def test_i18n_es_has_practiceWaterMgmt():
    src = _read('i18n.js')
    assert '"know.practiceWaterMgmt"' in src, \
        'i18n.js ES dict must have know.practiceWaterMgmt'


def test_i18n_es_has_practiceSoilMgmt():
    src = _read('i18n.js')
    assert '"know.practiceSoilMgmt"' in src, \
        'i18n.js ES dict must have know.practiceSoilMgmt'


def test_i18n_es_has_practiceBioControl():
    src = _read('i18n.js')
    assert '"know.practiceBioControl"' in src, \
        'i18n.js ES dict must have know.practiceBioControl'


def test_i18n_es_has_practiceKnowledgeSys():
    src = _read('i18n.js')
    assert '"know.practiceKnowledgeSys"' in src, \
        'i18n.js ES dict must have know.practiceKnowledgeSys'


def test_i18n_es_has_practiceIntercropping():
    src = _read('i18n.js')
    assert '"know.practiceIntercropping"' in src, \
        'i18n.js ES dict must have know.practiceIntercropping'


def test_i18n_en_practice_keys_are_english():
    src = _read('i18n.js')
    assert '"Water management"' in src, \
        'i18n.js EN dict must have English label for water_management'
    assert '"Soil management"' in src, \
        'i18n.js EN dict must have English label for soil_management'
    assert '"Biological control"' in src, \
        'i18n.js EN dict must have English label for biological_control'
    assert '"Knowledge system"' in src, \
        'i18n.js EN dict must have English label for knowledge_system'
    assert '"Intercropping"' in src, \
        'i18n.js EN dict must have English label for intercropping'


# ── i18n.js — field.levelNoRisk ──────────────────────────────────────────────

def test_i18n_has_fieldLevelNoRisk_key():
    src = _read('i18n.js')
    assert '"field.levelNoRisk"' in src, \
        'i18n.js must have field.levelNoRisk key in both ES and EN'


def test_i18n_en_fieldLevelNoRisk_value():
    src = _read('i18n.js')
    assert '"No risk detected"' in src, \
        'i18n.js EN dict field.levelNoRisk must map to "No risk detected"'


# ── knowledge.js — practiceTypeLabel helper ───────────────────────────────────

def test_knowledge_js_has_practiceTypeLabel():
    src = _read('knowledge.js')
    assert 'function practiceTypeLabel' in src, \
        'knowledge.js must define practiceTypeLabel() helper'


def test_knowledge_js_badge_uses_practiceTypeLabel():
    src = _read('knowledge.js')
    assert 'practiceTypeLabel(m.practice_type)' in src, \
        'knowledge.js renderAncestral badge must call practiceTypeLabel(m.practice_type)'


def test_knowledge_js_badge_no_raw_practice_type():
    src = _read('knowledge.js')
    # Old pattern: ${m.practice_type} directly in template literal
    assert '>${m.practice_type}<' not in src, \
        'knowledge.js must not render m.practice_type raw in badge innerHTML'


def test_knowledge_js_practiceTypeLabel_covers_water_management():
    src = _read('knowledge.js')
    assert 'water_management' in src, \
        'practiceTypeLabel must handle water_management slug'


def test_knowledge_js_practiceTypeLabel_covers_biological_control():
    src = _read('knowledge.js')
    assert 'biological_control' in src, \
        'practiceTypeLabel must handle biological_control slug'


# ── field.js — levelLabel sin_riesgo ─────────────────────────────────────────

def test_field_js_levelLabel_has_sin_riesgo():
    src = _read('field.js')
    assert 'sin_riesgo' in src, \
        'field.js levelLabel keyMap must include sin_riesgo slug'


def test_field_js_levelLabel_sin_riesgo_maps_to_i18n_key():
    src = _read('field.js')
    assert 'field.levelNoRisk' in src, \
        "field.js must map sin_riesgo slug to 'field.levelNoRisk' i18n key"
