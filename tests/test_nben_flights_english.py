"""NB-EN — Drone Flight Log page (flights.html / flights.js) English coverage."""

import re
from pathlib import Path

HTML = Path("frontend/flights.html").read_text()
JS = Path("frontend/flights.js").read_text()


# ── HTML title / header ──────────────────────────────────────────────────────

def test_page_title_is_english():
    assert "Flight Log" in HTML or "Drone Flight" in HTML


def test_page_h1_is_english():
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", HTML, re.DOTALL)
    assert h1, "No h1 found"
    assert "Flight" in h1.group(1)


def test_subtitle_is_english():
    assert "mission" in HTML.lower() or "drone" in HTML.lower()


# ── HTML filter dropdowns ─────────────────────────────────────────────────────

def test_filter_all_drones_is_english():
    assert "All drones" in HTML


def test_filter_all_missions_is_english():
    assert "All missions" in HTML


def test_filter_health_scan_is_english():
    assert "Health scan" in HTML or "Health Scan" in HTML


def test_filter_thermal_check_is_english():
    assert "Thermal check" in HTML or "Thermal Check" in HTML


def test_filter_spray_is_english():
    assert "Spray" in HTML


def test_refresh_button_is_english():
    assert "Refresh" in HTML or "Update" in HTML


# ── HTML stats strip ─────────────────────────────────────────────────────────

def test_stat_total_flights_is_english():
    assert "Total flights" in HTML or "total flights" in HTML.lower()


def test_stat_flight_hours_is_english():
    assert "Flight hours" in HTML or "flight hours" in HTML.lower()


def test_stat_hectares_covered_is_english():
    assert "covered" in HTML.lower() or "Covered" in HTML


def test_stat_images_captured_is_english():
    assert "captured" in HTML.lower() or "Images" in HTML


def test_stat_active_drones_is_english():
    assert "Active drones" in HTML or "active drones" in HTML.lower()


# ── HTML table headers ────────────────────────────────────────────────────────

def test_table_header_date_is_english():
    assert ">Date<" in HTML


def test_table_header_farm_is_english():
    assert ">Farm<" in HTML


def test_table_header_field_is_english():
    assert ">Field<" in HTML


def test_table_header_drone_is_english():
    assert ">Drone<" in HTML


def test_table_header_mission_is_english():
    assert ">Mission<" in HTML


def test_table_header_duration_is_english():
    assert ">Duration<" in HTML


def test_table_header_altitude_is_english():
    assert ">Altitude<" in HTML


def test_table_header_coverage_is_english():
    assert ">Coverage<" in HTML


def test_table_header_images_is_english():
    assert ">Images<" in HTML


def test_table_header_status_is_english():
    assert ">Status<" in HTML


# ── HTML nav / footer ─────────────────────────────────────────────────────────

def test_nav_logout_is_english():
    assert ">Sign out<" in HTML or ">Logout<" in HTML or ">Log out<" in HTML


def test_nav_flights_tab_is_english():
    assert ">Flights<" in HTML


def test_footer_is_english():
    assert "Precision" in HTML or "precision" in HTML or "agriculture" in HTML.lower()


# ── HTML Spanish absence ──────────────────────────────────────────────────────

def test_no_spanish_registro_de_vuelos_h1():
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", HTML, re.DOTALL)
    assert h1
    assert "Registro de Vuelos" not in h1.group(1)


def test_no_spanish_todos_los_drones():
    assert "Todos los drones" not in HTML


def test_no_spanish_todas_las_misiones():
    assert "Todas las misiones" not in HTML


def test_no_spanish_escaneo_de_salud():
    assert "Escaneo de salud" not in HTML


def test_no_spanish_vuelos_totales_stat():
    assert "Vuelos totales" not in HTML


def test_no_spanish_granjas_nav():
    assert ">Granjas<" not in HTML


def test_no_spanish_salir():
    assert ">Salir<" not in HTML


def test_no_spanish_fecha_header():
    assert ">Fecha<" not in HTML


def test_no_spanish_granja_header():
    assert ">Granja<" not in HTML


def test_no_spanish_mision_header():
    assert ">Mision<" not in HTML


# ── JS English presence ───────────────────────────────────────────────────────

def test_js_mission_labels_health_scan_is_english():
    assert "Health scan" in JS or "Health Scan" in JS


def test_js_mission_labels_thermal_check_is_english():
    assert "Thermal check" in JS or "Thermal Check" in JS


def test_js_mission_labels_spray_is_english():
    assert "'Spray'" in JS or '"Spray"' in JS


def test_js_status_labels_pending_is_english():
    assert "'Pending'" in JS or '"Pending"' in JS


def test_js_status_labels_processing_is_english():
    assert "'Processing'" in JS or '"Processing"' in JS


def test_js_status_labels_complete_is_english():
    assert "'Complete'" in JS or '"Complete"' in JS


def test_js_status_labels_failed_is_english():
    assert "'Failed'" in JS or '"Failed"' in JS


def test_js_loading_is_english():
    assert "Loading" in JS


def test_js_no_farms_message_is_english():
    assert "No farms" in JS or "no farms" in JS


def test_js_no_flights_message_is_english():
    assert "No flights" in JS or "no flights" in JS


# ── JS Spanish absence ────────────────────────────────────────────────────────

def test_js_no_escaneo_de_salud():
    assert "'Escaneo de salud'" not in JS and '"Escaneo de salud"' not in JS


def test_js_no_pendiente():
    assert "'Pendiente'" not in JS and '"Pendiente"' not in JS


def test_js_no_procesando():
    assert "'Procesando'" not in JS and '"Procesando"' not in JS


def test_js_no_completo():
    assert "'Completo'" not in JS and '"Completo"' not in JS


def test_js_no_fallido():
    assert "'Fallido'" not in JS and '"Fallido"' not in JS


def test_js_no_cargando_vuelos():
    assert "Cargando vuelos" not in JS


def test_js_no_sin_granjas():
    assert "Sin granjas" not in JS


def test_js_no_sin_vuelos():
    assert "Sin vuelos" not in JS
