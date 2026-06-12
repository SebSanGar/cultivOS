"""
CR5g — Wire 8 pages into i18n: page titles, subtitles, stat labels, table headers.
Source-inspection tests (no server). Pages: escalaciones-alertas, flights, fotos,
frescura-sensores, historial-alertas, historial-enfermedades, hitos-regenerativos, indice-estres.
"""

import os

FRONTEND = os.path.join(os.path.dirname(__file__), '..', 'frontend')
I18N_JS = os.path.join(FRONTEND, 'i18n.js')


def _html(name: str) -> str:
    with open(os.path.join(FRONTEND, name), 'r', encoding='utf-8') as f:
        return f.read()


def _i18n() -> str:
    with open(I18N_JS, 'r', encoding='utf-8') as f:
        return f.read()


def _has_attr(html: str, key: str) -> bool:
    return f'data-i18n="{key}"' in html or f"data-i18n='{key}'" in html


def _has_key_en(content: str, key: str) -> bool:
    en_idx = content.find("en: {")
    if en_idx == -1:
        en_idx = content.find('en:{')
    if en_idx == -1:
        return False
    en_block = content[en_idx:]
    return f"'{key}'" in en_block or f'"{key}"' in en_block


def _has_key_es(content: str, key: str) -> bool:
    es_idx = content.find("es: {")
    if es_idx == -1:
        es_idx = content.find('es:{')
    if es_idx == -1:
        return False
    en_idx = content.find("en: {")
    es_block = content[es_idx:en_idx] if en_idx != -1 else content[es_idx:]
    return f"'{key}'" in es_block or f'"{key}"' in es_block


# ── escalaciones-alertas.html ─────────────────────────────────────────────────

def test_escalaciones_title_has_data_i18n():
    html = _html('escalaciones-alertas.html')
    assert _has_attr(html, 'escalacionesAlertas.title'), \
        "escalaciones-alertas.html: <h1> missing data-i18n='escalacionesAlertas.title'"


def test_escalaciones_kpi_total_has_data_i18n():
    html = _html('escalaciones-alertas.html')
    assert _has_attr(html, 'escalacionesAlertas.kpiTotal'), \
        "escalaciones-alertas.html: 'Total Escalaciones' KPI missing data-i18n"


def test_escalaciones_kpi_critical_has_data_i18n():
    html = _html('escalaciones-alertas.html')
    assert _has_attr(html, 'escalacionesAlertas.kpiCritical'), \
        "escalaciones-alertas.html: 'Alertas Criticas' KPI missing data-i18n"


def test_escalaciones_th_alert_type_has_data_i18n():
    html = _html('escalaciones-alertas.html')
    assert _has_attr(html, 'escalacionesAlertas.thAlertType'), \
        "escalaciones-alertas.html: 'Tipo de Alerta' th missing data-i18n"


def test_escalaciones_th_severity_has_data_i18n():
    html = _html('escalaciones-alertas.html')
    assert _has_attr(html, 'escalacionesAlertas.thSeverity'), \
        "escalaciones-alertas.html: 'Severidad' th missing data-i18n"


def test_escalaciones_th_days_pending_has_data_i18n():
    html = _html('escalaciones-alertas.html')
    assert _has_attr(html, 'escalacionesAlertas.thDaysPending'), \
        "escalaciones-alertas.html: 'Dias Pendientes' th missing data-i18n"


def test_escalaciones_th_action_has_data_i18n():
    html = _html('escalaciones-alertas.html')
    assert _has_attr(html, 'escalacionesAlertas.thAction'), \
        "escalaciones-alertas.html: 'Accion Recomendada' th missing data-i18n"


def test_escalaciones_keys_in_i18n_en():
    i18n = _i18n()
    for key in (
        'escalacionesAlertas.title',
        'escalacionesAlertas.kpiTotal',
        'escalacionesAlertas.kpiCritical',
        'escalacionesAlertas.thAlertType',
        'escalacionesAlertas.thSeverity',
        'escalacionesAlertas.thDaysPending',
        'escalacionesAlertas.thAction',
    ):
        assert _has_key_en(i18n, key), f"i18n.js en block missing key '{key}'"


def test_escalaciones_keys_in_i18n_es():
    i18n = _i18n()
    for key in (
        'escalacionesAlertas.title',
        'escalacionesAlertas.kpiTotal',
        'escalacionesAlertas.kpiCritical',
        'escalacionesAlertas.thAlertType',
        'escalacionesAlertas.thSeverity',
        'escalacionesAlertas.thDaysPending',
        'escalacionesAlertas.thAction',
    ):
        assert _has_key_es(i18n, key), f"i18n.js es block missing key '{key}'"


# ── flights.html ──────────────────────────────────────────────────────────────

def test_flights_title_has_data_i18n():
    html = _html('flights.html')
    assert _has_attr(html, 'flights.title'), \
        "flights.html: <h1> missing data-i18n='flights.title'"


def test_flights_subtitle_has_data_i18n():
    html = _html('flights.html')
    assert _has_attr(html, 'flights.subtitle'), \
        "flights.html: subtitle missing data-i18n='flights.subtitle'"


def test_flights_stat_total_has_data_i18n():
    html = _html('flights.html')
    assert _has_attr(html, 'flights.statTotal'), \
        "flights.html: 'Total flights' stat label missing data-i18n"


def test_flights_stat_hours_has_data_i18n():
    html = _html('flights.html')
    assert _has_attr(html, 'flights.statHours'), \
        "flights.html: 'Flight hours' stat label missing data-i18n"


def test_flights_stat_hectares_has_data_i18n():
    html = _html('flights.html')
    assert _has_attr(html, 'flights.statHectares'), \
        "flights.html: 'Hectares covered' stat label missing data-i18n"


def test_flights_keys_in_i18n_en():
    i18n = _i18n()
    for key in (
        'flights.title', 'flights.subtitle',
        'flights.statTotal', 'flights.statHours', 'flights.statHectares',
        'flights.statImages', 'flights.statDrones',
    ):
        assert _has_key_en(i18n, key), f"i18n.js en block missing key '{key}'"


def test_flights_keys_in_i18n_es():
    i18n = _i18n()
    for key in (
        'flights.title', 'flights.subtitle',
        'flights.statTotal', 'flights.statHours', 'flights.statHectares',
        'flights.statImages', 'flights.statDrones',
    ):
        assert _has_key_es(i18n, key), f"i18n.js es block missing key '{key}'"


# ── fotos.html ────────────────────────────────────────────────────────────────

def test_fotos_title_has_data_i18n():
    html = _html('fotos.html')
    assert _has_attr(html, 'fotos.title'), \
        "fotos.html: <h1> missing data-i18n='fotos.title'"


def test_fotos_subtitle_has_data_i18n():
    html = _html('fotos.html')
    assert _has_attr(html, 'fotos.subtitle'), \
        "fotos.html: subtitle missing data-i18n='fotos.subtitle'"


def test_fotos_stat_photos_has_data_i18n():
    html = _html('fotos.html')
    assert _has_attr(html, 'fotos.statPhotos'), \
        "fotos.html: 'Fotos' stat missing data-i18n"


def test_fotos_stat_healthy_has_data_i18n():
    html = _html('fotos.html')
    assert _has_attr(html, 'fotos.statHealthy'), \
        "fotos.html: 'Vegetacion Sana' stat missing data-i18n"


def test_fotos_stat_stressed_has_data_i18n():
    html = _html('fotos.html')
    assert _has_attr(html, 'fotos.statStressed'), \
        "fotos.html: 'Estresada' stat missing data-i18n"


def test_fotos_keys_in_i18n_en():
    i18n = _i18n()
    for key in (
        'fotos.title', 'fotos.subtitle',
        'fotos.statPhotos', 'fotos.statHealthy', 'fotos.statStressed', 'fotos.statGreenRatio',
    ):
        assert _has_key_en(i18n, key), f"i18n.js en block missing key '{key}'"


def test_fotos_keys_in_i18n_es():
    i18n = _i18n()
    for key in (
        'fotos.title', 'fotos.subtitle',
        'fotos.statPhotos', 'fotos.statHealthy', 'fotos.statStressed', 'fotos.statGreenRatio',
    ):
        assert _has_key_es(i18n, key), f"i18n.js es block missing key '{key}'"


# ── frescura-sensores.html ────────────────────────────────────────────────────

def test_frescura_title_has_data_i18n():
    html = _html('frescura-sensores.html')
    assert _has_attr(html, 'frescuraSensores.title'), \
        "frescura-sensores.html: <h1> missing data-i18n='frescuraSensores.title'"


def test_frescura_subtitle_has_data_i18n():
    html = _html('frescura-sensores.html')
    assert _has_attr(html, 'frescuraSensores.subtitle'), \
        "frescura-sensores.html: subtitle missing data-i18n='frescuraSensores.subtitle'"


def test_frescura_kpi_stale_has_data_i18n():
    html = _html('frescura-sensores.html')
    assert _has_attr(html, 'frescuraSensores.kpiStale'), \
        "frescura-sensores.html: 'Sensores desactualizados' KPI missing data-i18n"


def test_frescura_th_stale_has_data_i18n():
    html = _html('frescura-sensores.html')
    assert _has_attr(html, 'frescuraSensores.thStale'), \
        "frescura-sensores.html: 'Desactualizados' th missing data-i18n"


def test_frescura_lbl_crop_in_i18n():
    i18n = _i18n()
    assert _has_key_en(i18n, 'lbl.crop'), "i18n.js en block missing key 'lbl.crop'"
    assert _has_key_es(i18n, 'lbl.crop'), "i18n.js es block missing key 'lbl.crop'"


def test_frescura_keys_in_i18n_en():
    i18n = _i18n()
    for key in (
        'frescuraSensores.title', 'frescuraSensores.subtitle',
        'frescuraSensores.kpiStale', 'frescuraSensores.thStale',
        'frescuraSensores.thSoil', 'frescuraSensores.thHealth', 'frescuraSensores.thWeather',
    ):
        assert _has_key_en(i18n, key), f"i18n.js en block missing key '{key}'"


def test_frescura_keys_in_i18n_es():
    i18n = _i18n()
    for key in (
        'frescuraSensores.title', 'frescuraSensores.subtitle',
        'frescuraSensores.kpiStale', 'frescuraSensores.thStale',
        'frescuraSensores.thSoil', 'frescuraSensores.thHealth', 'frescuraSensores.thWeather',
    ):
        assert _has_key_es(i18n, key), f"i18n.js es block missing key '{key}'"


# ── historial-alertas.html ────────────────────────────────────────────────────

def test_historialAlertas_title_has_data_i18n():
    html = _html('historial-alertas.html')
    assert _has_attr(html, 'historialAlertas.title'), \
        "historial-alertas.html: <h1> missing data-i18n='historialAlertas.title'"


def test_historialAlertas_subtitle_has_data_i18n():
    html = _html('historial-alertas.html')
    assert _has_attr(html, 'historialAlertas.subtitle'), \
        "historial-alertas.html: subtitle missing data-i18n='historialAlertas.subtitle'"


def test_historialAlertas_stat_total_has_data_i18n():
    html = _html('historial-alertas.html')
    assert _has_attr(html, 'historialAlertas.statTotal'), \
        "historial-alertas.html: 'Total Alertas' stat missing data-i18n"


def test_historialAlertas_stat_critical_has_data_i18n():
    html = _html('historial-alertas.html')
    assert _has_attr(html, 'historialAlertas.statCritical'), \
        "historial-alertas.html: 'Criticas' stat missing data-i18n"


def test_historialAlertas_analytics_h2_has_data_i18n():
    html = _html('historial-alertas.html')
    assert _has_attr(html, 'historialAlertas.analyticsH2'), \
        "historial-alertas.html: 'Analiticas de Entrega' h2 missing data-i18n"


def test_historialAlertas_stat_delivery_rate_has_data_i18n():
    html = _html('historial-alertas.html')
    assert _has_attr(html, 'historialAlertas.statDeliveryRate'), \
        "historial-alertas.html: 'Tasa de Entrega' stat missing data-i18n"


def test_historialAlertas_keys_in_i18n_en():
    i18n = _i18n()
    for key in (
        'historialAlertas.title', 'historialAlertas.subtitle',
        'historialAlertas.statTotal', 'historialAlertas.statCritical',
        'historialAlertas.statPending', 'historialAlertas.statFarms',
        'historialAlertas.analyticsH2',
        'historialAlertas.statDeliveryRate', 'historialAlertas.statSms',
        'historialAlertas.statSystem', 'historialAlertas.statFarmsReached',
    ):
        assert _has_key_en(i18n, key), f"i18n.js en block missing key '{key}'"


def test_historialAlertas_keys_in_i18n_es():
    i18n = _i18n()
    for key in (
        'historialAlertas.title', 'historialAlertas.subtitle',
        'historialAlertas.statTotal', 'historialAlertas.statCritical',
        'historialAlertas.statPending', 'historialAlertas.statFarms',
        'historialAlertas.analyticsH2',
        'historialAlertas.statDeliveryRate', 'historialAlertas.statSms',
        'historialAlertas.statSystem', 'historialAlertas.statFarmsReached',
    ):
        assert _has_key_es(i18n, key), f"i18n.js es block missing key '{key}'"


# ── historial-enfermedades.html ───────────────────────────────────────────────

def test_historialEnfermedades_title_has_data_i18n():
    html = _html('historial-enfermedades.html')
    assert _has_attr(html, 'historialEnfermedades.title'), \
        "historial-enfermedades.html: <h1> missing data-i18n='historialEnfermedades.title'"


def test_historialEnfermedades_subtitle_has_data_i18n():
    html = _html('historial-enfermedades.html')
    assert _has_attr(html, 'historialEnfermedades.subtitle'), \
        "historial-enfermedades.html: subtitle missing data-i18n='historialEnfermedades.subtitle'"


def test_historialEnfermedades_kpi_months_has_data_i18n():
    html = _html('historial-enfermedades.html')
    assert _has_attr(html, 'historialEnfermedades.kpiMonths'), \
        "historial-enfermedades.html: 'Meses sin enfermedad' KPI missing data-i18n"


def test_historialEnfermedades_kpi_top_disease_has_data_i18n():
    html = _html('historial-enfermedades.html')
    assert _has_attr(html, 'historialEnfermedades.kpiTopDisease'), \
        "historial-enfermedades.html: 'Enfermedad más común' KPI missing data-i18n"


def test_historialEnfermedades_kpi_recurrence_has_data_i18n():
    html = _html('historial-enfermedades.html')
    assert _has_attr(html, 'historialEnfermedades.kpiRecurrence'), \
        "historial-enfermedades.html: 'Recurrencia detectada' KPI missing data-i18n"


def test_historialEnfermedades_h3_recurrent_has_data_i18n():
    html = _html('historial-enfermedades.html')
    assert _has_attr(html, 'historialEnfermedades.recurrentH3'), \
        "historial-enfermedades.html: 'Enfermedades Recurrentes' h3 missing data-i18n"


def test_historialEnfermedades_keys_in_i18n_en():
    i18n = _i18n()
    for key in (
        'historialEnfermedades.title', 'historialEnfermedades.subtitle',
        'historialEnfermedades.kpiMonths', 'historialEnfermedades.kpiTopDisease',
        'historialEnfermedades.kpiRecurrence', 'historialEnfermedades.recurrentH3',
    ):
        assert _has_key_en(i18n, key), f"i18n.js en block missing key '{key}'"


def test_historialEnfermedades_keys_in_i18n_es():
    i18n = _i18n()
    for key in (
        'historialEnfermedades.title', 'historialEnfermedades.subtitle',
        'historialEnfermedades.kpiMonths', 'historialEnfermedades.kpiTopDisease',
        'historialEnfermedades.kpiRecurrence', 'historialEnfermedades.recurrentH3',
    ):
        assert _has_key_es(i18n, key), f"i18n.js es block missing key '{key}'"


# ── hitos-regenerativos.html ──────────────────────────────────────────────────

def test_hitosReg_title_has_data_i18n():
    html = _html('hitos-regenerativos.html')
    assert _has_attr(html, 'hitosReg.title'), \
        "hitos-regenerativos.html: <h1> missing data-i18n='hitosReg.title'"


def test_hitosReg_subtitle_has_data_i18n():
    html = _html('hitos-regenerativos.html')
    assert _has_attr(html, 'hitosReg.subtitle'), \
        "hitos-regenerativos.html: subtitle missing data-i18n='hitosReg.subtitle'"


def test_hitosReg_keys_in_i18n_en():
    i18n = _i18n()
    for key in ('hitosReg.title', 'hitosReg.subtitle'):
        assert _has_key_en(i18n, key), f"i18n.js en block missing key '{key}'"


def test_hitosReg_keys_in_i18n_es():
    i18n = _i18n()
    for key in ('hitosReg.title', 'hitosReg.subtitle'):
        assert _has_key_es(i18n, key), f"i18n.js es block missing key '{key}'"


# ── indice-estres.html ────────────────────────────────────────────────────────

def test_indiceEstres_title_has_data_i18n():
    html = _html('indice-estres.html')
    assert _has_attr(html, 'indiceEstres.title'), \
        "indice-estres.html: <h1> missing data-i18n='indiceEstres.title'"


def test_indiceEstres_subtitle_has_data_i18n():
    html = _html('indice-estres.html')
    assert _has_attr(html, 'indiceEstres.subtitle'), \
        "indice-estres.html: subtitle missing data-i18n='indiceEstres.subtitle'"


def test_indiceEstres_label_estres_has_data_i18n():
    html = _html('indice-estres.html')
    assert _has_attr(html, 'indiceEstres.labelEstres'), \
        "indice-estres.html: 'Estrés' ring label missing data-i18n"


def test_indiceEstres_label_water_has_data_i18n():
    html = _html('indice-estres.html')
    assert _has_attr(html, 'indiceEstres.labelWater'), \
        "indice-estres.html: 'Agua (40%)' gauge label missing data-i18n"


def test_indiceEstres_label_disease_has_data_i18n():
    html = _html('indice-estres.html')
    assert _has_attr(html, 'indiceEstres.labelDisease'), \
        "indice-estres.html: 'Enfermedad (35%)' gauge label missing data-i18n"


def test_indiceEstres_label_thermal_has_data_i18n():
    html = _html('indice-estres.html')
    assert _has_attr(html, 'indiceEstres.labelThermal'), \
        "indice-estres.html: 'Térmico (25%)' gauge label missing data-i18n"


def test_indiceEstres_keys_in_i18n_en():
    i18n = _i18n()
    for key in (
        'indiceEstres.title', 'indiceEstres.subtitle',
        'indiceEstres.labelEstres', 'indiceEstres.labelWater',
        'indiceEstres.labelDisease', 'indiceEstres.labelThermal',
    ):
        assert _has_key_en(i18n, key), f"i18n.js en block missing key '{key}'"


def test_indiceEstres_keys_in_i18n_es():
    i18n = _i18n()
    for key in (
        'indiceEstres.title', 'indiceEstres.subtitle',
        'indiceEstres.labelEstres', 'indiceEstres.labelWater',
        'indiceEstres.labelDisease', 'indiceEstres.labelThermal',
    ):
        assert _has_key_es(i18n, key), f"i18n.js es block missing key '{key}'"
