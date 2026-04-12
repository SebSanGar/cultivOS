"""
Pure report generation for farm health summaries (PDF and CSV).

Generates printable reports suitable for FIRA/Financiera Rural loan applications.
All text in Spanish. No I/O — takes data dicts in, returns bytes out.
"""

import csv
import io
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch, cm
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
)


# -- Color palette --
_GREEN = HexColor("#2d7a3a")
_DARK = HexColor("#1a1a2e")
_GRAY = HexColor("#666666")
_LIGHT_BG = HexColor("#f0f4f0")
_WHITE = HexColor("#ffffff")
_RED = HexColor("#c0392b")
_YELLOW = HexColor("#f39c12")


def _build_styles():
    """Build Spanish-language report styles."""
    base = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle(
            "ReportTitle", parent=base["Title"],
            fontSize=22, textColor=_GREEN, spaceAfter=6,
        ),
        "subtitle": ParagraphStyle(
            "ReportSubtitle", parent=base["Normal"],
            fontSize=12, textColor=_GRAY, spaceAfter=20,
        ),
        "heading": ParagraphStyle(
            "SectionHeading", parent=base["Heading2"],
            fontSize=14, textColor=_DARK, spaceBefore=16, spaceAfter=8,
        ),
        "normal": ParagraphStyle(
            "ReportNormal", parent=base["Normal"],
            fontSize=10, textColor=_DARK, spaceAfter=4,
        ),
        "small": ParagraphStyle(
            "ReportSmall", parent=base["Normal"],
            fontSize=8, textColor=_GRAY,
        ),
    }
    return styles


def _health_label(score: float) -> str:
    if score >= 75:
        return "Bueno"
    elif score >= 50:
        return "Regular"
    elif score >= 25:
        return "Bajo"
    else:
        return "Critico"


def _trend_label(trend: str) -> str:
    labels = {
        "improving": "Mejorando",
        "stable": "Estable",
        "declining": "Declinando",
    }
    return labels.get(trend, trend)


def generate_farm_report_pdf(
    farm: dict,
    fields: list[dict],
    treatments: list[dict],
) -> bytes:
    """Generate a farm health report PDF.

    Args:
        farm: dict with keys: name, owner_name, municipality, state, total_hectares
        fields: list of dicts with keys: name, crop_type, hectares, health_score, health_trend, ndvi_mean
        treatments: list of dicts with keys: field_name, problema, tratamiento, urgencia, costo_estimado_mxn

    Returns:
        PDF file content as bytes.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
        pageCompression=0,
    )
    styles = _build_styles()
    story = []

    # -- Header --
    story.append(Paragraph("Reporte de Salud de la Granja", styles["title"]))
    story.append(Paragraph(
        f"Generado: {datetime.utcnow().strftime('%d/%m/%Y')}  |  cultivOS - Agricultura de Precision",
        styles["subtitle"],
    ))

    # -- Farm info table --
    story.append(Paragraph("Informacion General", styles["heading"]))
    farm_data = [
        ["Nombre de la Granja", farm.get("name", "—")],
        ["Propietario", farm.get("owner_name", "—") or "—"],
        ["Municipio / Estado", f"{farm.get('municipality', '—')} / {farm.get('state', '—')}"],
        ["Superficie Total", f"{farm.get('total_hectares', 0)} hectareas"],
    ]
    farm_table = Table(farm_data, colWidths=[3.5 * inch, 3.5 * inch])
    farm_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), _LIGHT_BG),
        ("TEXTCOLOR", (0, 0), (-1, -1), _DARK),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, _GRAY),
    ]))
    story.append(farm_table)
    story.append(Spacer(1, 16))

    # -- Fields / Parcelas --
    story.append(Paragraph("Parcelas", styles["heading"]))

    if not fields:
        story.append(Paragraph("Sin parcelas registradas", styles["normal"]))
    else:
        field_header = ["Parcela", "Cultivo", "Hectareas", "Salud", "Tendencia", "NDVI"]
        field_rows = [field_header]
        for f in fields:
            score = f.get("health_score")
            score_str = f"{score:.1f} ({_health_label(score)})" if score is not None else "—"
            trend = f.get("health_trend", "—")
            trend_str = _trend_label(trend) if trend != "—" else "—"
            ndvi = f.get("ndvi_mean")
            ndvi_str = f"{ndvi:.3f}" if ndvi is not None else "—"
            field_rows.append([
                f.get("name", "—"),
                f.get("crop_type", "—") or "—",
                str(f.get("hectares", "—")),
                score_str,
                trend_str,
                ndvi_str,
            ])

        field_table = Table(field_rows, colWidths=[1.6 * inch, 1 * inch, 0.9 * inch, 1.3 * inch, 1 * inch, 0.9 * inch])
        field_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), _GREEN),
            ("TEXTCOLOR", (0, 0), (-1, 0), _WHITE),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("GRID", (0, 0), (-1, -1), 0.5, _GRAY),
            ("ALIGN", (2, 0), (-1, -1), "CENTER"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [_WHITE, _LIGHT_BG]),
        ]))
        story.append(field_table)

    story.append(Spacer(1, 16))

    # -- Treatment Recommendations --
    story.append(Paragraph("Recomendaciones de Tratamiento", styles["heading"]))

    if not treatments:
        story.append(Paragraph("Sin recomendaciones activas", styles["normal"]))
    else:
        for t in treatments:
            urgency = t.get("urgencia", "—")
            story.append(Paragraph(
                f"<b>{t.get('field_name', '—')}</b> — {t.get('problema', '—')} "
                f"(Urgencia: {urgency})",
                styles["normal"],
            ))
            story.append(Paragraph(
                f"Tratamiento: {t.get('tratamiento', '—')}",
                styles["normal"],
            ))
            cost = t.get("costo_estimado_mxn", 0)
            story.append(Paragraph(
                f"Costo estimado: ${cost:,} MXN",
                styles["small"],
            ))
            story.append(Spacer(1, 8))

    # -- Footer --
    story.append(Spacer(1, 30))
    story.append(Paragraph(
        "Este reporte fue generado automaticamente por cultivOS. "
        "Los datos reflejan las mediciones mas recientes disponibles.",
        styles["small"],
    ))

    doc.build(story)
    return buf.getvalue()


# -- Portfolio Report --


def generate_portfolio_report_pdf(
    farms_summary: dict,
    farm_details: list[dict],
    carbon_summary: dict,
    economic_summary: dict,
) -> bytes:
    """Generate a multi-farm portfolio summary PDF.

    Args:
        farms_summary: dict with total_farms, total_hectares, avg_health_score, total_fields
        farm_details: list of dicts per farm with name, municipality, state, hectares,
                      avg_health, health_trend, field_count, treatment_count
        carbon_summary: dict with total_co2e_tonnes, avg_soc_tonnes_per_ha
        economic_summary: dict with total_savings_mxn, water_savings_mxn,
                          fertilizer_savings_mxn, yield_improvement_mxn

    Returns:
        PDF file content as bytes.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
        pageCompression=0,
    )
    styles = _build_styles()
    story = []

    # -- Title --
    story.append(Paragraph("Reporte de Portafolio", styles["title"]))
    story.append(Paragraph(
        f"Generado: {datetime.utcnow().strftime('%d/%m/%Y')}  |  cultivOS - Agricultura de Precision",
        styles["subtitle"],
    ))

    # -- Executive Summary --
    story.append(Paragraph("Resumen Ejecutivo", styles["heading"]))

    total_farms = farms_summary.get("total_farms", 0)

    if total_farms == 0:
        story.append(Paragraph("Sin granjas registradas en el portafolio.", styles["normal"]))
    else:
        summary_data = [
            ["Total de Granjas", str(total_farms)],
            ["Total de Parcelas", str(farms_summary.get("total_fields", 0))],
            ["Superficie Total", f"{farms_summary.get('total_hectares', 0):.1f} hectareas"],
            ["Salud Promedio", f"{farms_summary.get('avg_health_score', 0):.1f} ({_health_label(farms_summary.get('avg_health_score', 0))})"],
        ]
        summary_table = Table(summary_data, colWidths=[3.5 * inch, 3.5 * inch])
        summary_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), _LIGHT_BG),
            ("TEXTCOLOR", (0, 0), (-1, -1), _DARK),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("GRID", (0, 0), (-1, -1), 0.5, _GRAY),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 16))

        # -- Per-farm health scores --
        story.append(Paragraph("Salud por Granja", styles["heading"]))

        farm_header = ["Granja", "Municipio", "Hectareas", "Parcelas", "Salud", "Tendencia", "Tratamientos"]
        farm_rows = [farm_header]
        for fd in farm_details:
            score = fd.get("avg_health", 0)
            score_str = f"{score:.1f}" if score else "—"
            trend = fd.get("health_trend", "—")
            trend_str = _trend_label(trend) if trend and trend != "—" else "—"
            farm_rows.append([
                fd.get("name", "—"),
                fd.get("municipality", "—") or "—",
                f"{fd.get('hectares', 0):.0f}",
                str(fd.get("field_count", 0)),
                score_str,
                trend_str,
                str(fd.get("treatment_count", 0)),
            ])

        farm_table = Table(farm_rows, colWidths=[1.4 * inch, 1.1 * inch, 0.8 * inch, 0.7 * inch, 0.9 * inch, 0.9 * inch, 1.0 * inch])
        farm_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), _GREEN),
            ("TEXTCOLOR", (0, 0), (-1, 0), _WHITE),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("GRID", (0, 0), (-1, -1), 0.5, _GRAY),
            ("ALIGN", (2, 0), (-1, -1), "CENTER"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [_WHITE, _LIGHT_BG]),
        ]))
        story.append(farm_table)
        story.append(Spacer(1, 16))

        # -- Treatments aggregate --
        story.append(Paragraph("Tratamientos Aplicados", styles["heading"]))
        total_treatments = sum(fd.get("treatment_count", 0) for fd in farm_details)
        story.append(Paragraph(
            f"Total de tratamientos aplicados en el portafolio: <b>{total_treatments}</b>",
            styles["normal"],
        ))
        story.append(Spacer(1, 16))

        # -- Carbon sequestration --
        story.append(Paragraph("Carbono Secuestrado", styles["heading"]))
        co2e = carbon_summary.get("total_co2e_tonnes", 0)
        avg_soc = carbon_summary.get("avg_soc_tonnes_per_ha", 0)
        carbon_data = [
            ["CO<sub>2</sub>e Total Secuestrado", f"{co2e:,.1f} toneladas"],
            ["SOC Promedio por Hectarea", f"{avg_soc:,.1f} ton/ha"],
        ]
        carbon_table = Table(carbon_data, colWidths=[3.5 * inch, 3.5 * inch])
        carbon_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), _LIGHT_BG),
            ("TEXTCOLOR", (0, 0), (-1, -1), _DARK),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("GRID", (0, 0), (-1, -1), 0.5, _GRAY),
        ]))
        story.append(carbon_table)
        story.append(Spacer(1, 16))

        # -- Economic impact --
        story.append(Paragraph("Impacto Economico Estimado", styles["heading"]))
        eco = economic_summary
        econ_data = [
            ["Ahorro en Agua", f"${eco.get('water_savings_mxn', 0):,} MXN"],
            ["Ahorro en Fertilizante", f"${eco.get('fertilizer_savings_mxn', 0):,} MXN"],
            ["Mejora en Rendimiento", f"${eco.get('yield_improvement_mxn', 0):,} MXN"],
            ["Ahorro Total Anual", f"${eco.get('total_savings_mxn', 0):,} MXN"],
        ]
        econ_table = Table(econ_data, colWidths=[3.5 * inch, 3.5 * inch])
        econ_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), _LIGHT_BG),
            ("TEXTCOLOR", (0, 0), (-1, -1), _DARK),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("GRID", (0, 0), (-1, -1), 0.5, _GRAY),
            ("BACKGROUND", (-1, -1), (-1, -1), _GREEN),
            ("TEXTCOLOR", (-1, -1), (-1, -1), _WHITE),
            ("FONTSIZE", (-1, -1), (-1, -1), 12),
        ]))
        story.append(econ_table)

    # -- Footer --
    story.append(Spacer(1, 30))
    story.append(Paragraph(
        "Este reporte fue generado automaticamente por cultivOS. "
        "Los datos reflejan las mediciones mas recientes disponibles.",
        styles["small"],
    ))

    doc.build(story)
    return buf.getvalue()


# -- FODECIJAL Grant Narrative Report --


def generate_fodecijal_report_pdf(
    platform_stats: dict,
    cerebro_summary: dict,
    pipeline_status: list[dict],
    carbon_summary: dict,
    farm_details: list[dict],
    cooperative_stats: list[dict] | None = None,
) -> bytes:
    """Generate a FODECIJAL grant narrative PDF showing TRL 4-5 maturity.

    Args:
        platform_stats: dict with api_endpoints, frontend_pages, passing_tests,
                        route_files, total_farms, total_fields, total_hectares
        cerebro_summary: dict with health_scoring_sources, treatment_methods,
                         ancestral_methods, supported_crops, organic_only
        pipeline_status: list of dicts with name, status, records
        carbon_summary: dict with total_co2e_tonnes, avg_soc_tonnes_per_ha
        farm_details: list of dicts with name, municipality, state, hectares,
                      field_count, avg_health, treatment_count
        cooperative_stats: optional list of dicts with name, state, farm_count,
                           total_hectares, avg_health, total_co2e_tonnes

    Returns:
        PDF file content as bytes.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
        pageCompression=0,
    )
    styles = _build_styles()
    story = []

    # -- Title page --
    story.append(Spacer(1, 60))
    story.append(Paragraph(
        "cultivOS — Reporte Tecnico FODECIJAL",
        styles["title"],
    ))
    story.append(Paragraph(
        "Plataforma de Inteligencia Agricola con Precision por Drones",
        styles["subtitle"],
    ))
    story.append(Spacer(1, 20))
    story.append(Paragraph(
        f"Generado: {datetime.utcnow().strftime('%d/%m/%Y')}",
        styles["normal"],
    ))
    story.append(Paragraph(
        "Nivel de Madurez Tecnologica: TRL 4 → TRL 5",
        styles["normal"],
    ))
    story.append(Spacer(1, 30))
    story.append(Paragraph(
        "Este documento presenta el estado actual de la plataforma cultivOS, "
        "desarrollada para transformar la agricultura de precision en Jalisco. "
        "El sistema integra imagenes de drones (NDVI, termal), analisis de suelo, "
        "conocimiento ancestral y recomendaciones de tratamientos organicos para "
        "apoyar a agricultores de pequena y mediana escala.",
        styles["normal"],
    ))

    story.append(PageBreak())

    # -- Section 1: Plataforma --
    story.append(Paragraph("1. Resumen de la Plataforma", styles["heading"]))

    ps = platform_stats
    platform_data = [
        ["Endpoints API funcionales", str(ps.get("api_endpoints", 0))],
        ["Paginas de interfaz", str(ps.get("frontend_pages", 0))],
        ["Pruebas automatizadas", str(ps.get("passing_tests", 0))],
        ["Archivos de rutas", str(ps.get("route_files", 0))],
        ["Granjas registradas", str(ps.get("total_farms", 0))],
        ["Parcelas registradas", str(ps.get("total_fields", 0))],
        ["Superficie total", f"{ps.get('total_hectares', 0):.1f} hectareas"],
    ]
    platform_table = Table(platform_data, colWidths=[3.5 * inch, 3.5 * inch])
    platform_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), _LIGHT_BG),
        ("TEXTCOLOR", (0, 0), (-1, -1), _DARK),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, _GRAY),
    ]))
    story.append(platform_table)
    story.append(Spacer(1, 16))

    # -- Section 2: Cerebro Intelligence --
    story.append(Paragraph("2. Motor de Inteligencia Cerebro", styles["heading"]))

    cs = cerebro_summary
    sources = cs.get("health_scoring_sources", [])
    cerebro_data = [
        ["Fuentes de datos para scoring", ", ".join(sources) if sources else "—"],
        ["Metodos de tratamiento", str(cs.get("treatment_methods", 0))],
        ["Metodos ancestrales documentados", str(cs.get("ancestral_methods", 0))],
        ["Tipos de cultivo soportados", str(cs.get("supported_crops", 0))],
        ["Solo organico", "Si" if cs.get("organic_only") else "No"],
    ]
    cerebro_table = Table(cerebro_data, colWidths=[3.5 * inch, 3.5 * inch])
    cerebro_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), _LIGHT_BG),
        ("TEXTCOLOR", (0, 0), (-1, -1), _DARK),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, _GRAY),
    ]))
    story.append(cerebro_table)
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "El motor Cerebro combina multiples fuentes de datos — imagenes NDVI y "
        "termales de drones, analisis de suelo, datos meteorologicos — para generar "
        "una puntuacion de salud 0-100 por parcela. Todas las recomendaciones de "
        "tratamiento son 100% organicas, priorizando metodos regenerativos y "
        "conocimiento ancestral (sistema milpa, fertilizantes naturales).",
        styles["normal"],
    ))
    story.append(Spacer(1, 16))

    # -- Section 3: Pipelines de Datos --
    story.append(Paragraph("3. Pipelines de Datos", styles["heading"]))

    if pipeline_status:
        pipe_header = ["Pipeline", "Estado", "Registros"]
        pipe_rows = [pipe_header]
        for p in pipeline_status:
            status_label = "Operativo" if p.get("status") == "operational" else "Planificado"
            pipe_rows.append([
                p.get("name", "—"),
                status_label,
                str(p.get("records", 0)),
            ])

        pipe_table = Table(pipe_rows, colWidths=[3.0 * inch, 2.0 * inch, 2.0 * inch])
        pipe_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), _GREEN),
            ("TEXTCOLOR", (0, 0), (-1, 0), _WHITE),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("GRID", (0, 0), (-1, -1), 0.5, _GRAY),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [_WHITE, _LIGHT_BG]),
        ]))
        story.append(pipe_table)
    else:
        story.append(Paragraph("Sin pipelines configurados.", styles["normal"]))

    story.append(Spacer(1, 16))

    # -- Section 4: Carbono --
    story.append(Paragraph("4. Captura de Carbono", styles["heading"]))

    co2e = carbon_summary.get("total_co2e_tonnes", 0)
    avg_soc = carbon_summary.get("avg_soc_tonnes_per_ha", 0)
    carbon_data = [
        ["CO2e Total Estimado", f"{co2e:,.1f} toneladas"],
        ["SOC Promedio por Hectarea", f"{avg_soc:,.2f} ton/ha"],
    ]
    carbon_table = Table(carbon_data, colWidths=[3.5 * inch, 3.5 * inch])
    carbon_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), _LIGHT_BG),
        ("TEXTCOLOR", (0, 0), (-1, -1), _DARK),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, _GRAY),
    ]))
    story.append(carbon_table)
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "La plataforma monitorea el carbono organico del suelo (SOC) y proyecta "
        "secuestro de CO2 equivalente usando el factor de conversion molecular "
        "(3.67 CO2/C). Las practicas regenerativas recomendadas — cobertura vegetal, "
        "labranza minima, rotacion con leguminosas — incrementan el SOC de manera "
        "medible entre temporadas.",
        styles["normal"],
    ))
    story.append(Spacer(1, 16))

    # -- Section 5: Portafolio de Granjas --
    story.append(Paragraph("5. Portafolio de Granjas", styles["heading"]))

    if farm_details:
        farm_header = ["Granja", "Municipio", "Hectareas", "Parcelas", "Salud", "Tratamientos"]
        farm_rows = [farm_header]
        for fd in farm_details:
            score = fd.get("avg_health", 0)
            score_str = f"{score:.1f}" if score else "—"
            farm_rows.append([
                fd.get("name", "—"),
                fd.get("municipality", "—") or "—",
                f"{fd.get('hectares', 0):.0f}",
                str(fd.get("field_count", 0)),
                score_str,
                str(fd.get("treatment_count", 0)),
            ])

        farm_table = Table(farm_rows, colWidths=[1.6 * inch, 1.2 * inch, 0.9 * inch, 0.9 * inch, 0.9 * inch, 1.2 * inch])
        farm_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), _GREEN),
            ("TEXTCOLOR", (0, 0), (-1, 0), _WHITE),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("GRID", (0, 0), (-1, -1), 0.5, _GRAY),
            ("ALIGN", (2, 0), (-1, -1), "CENTER"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [_WHITE, _LIGHT_BG]),
        ]))
        story.append(farm_table)
    else:
        story.append(Paragraph("Sin granjas registradas en el portafolio.", styles["normal"]))

    # -- Section 6: Cooperativas --
    coops = cooperative_stats or []
    if coops:
        story.append(Spacer(1, 16))
        story.append(Paragraph("6. Impacto Colectivo — Cooperativas", styles["heading"]))

        total_coop_farms = sum(c.get("farm_count", 0) for c in coops)
        total_coop_hectares = sum(c.get("total_hectares", 0) for c in coops)
        total_coop_co2e = sum(c.get("total_co2e_tonnes", 0) for c in coops)

        coop_summary_data = [
            ["Cooperativas activas", str(len(coops))],
            ["Granjas miembro", str(total_coop_farms)],
            ["Superficie colectiva", f"{total_coop_hectares:,.1f} hectareas"],
            ["CO2e colectivo", f"{total_coop_co2e:,.1f} toneladas"],
        ]
        coop_summary_table = Table(coop_summary_data, colWidths=[3.5 * inch, 3.5 * inch])
        coop_summary_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), _LIGHT_BG),
            ("TEXTCOLOR", (0, 0), (-1, -1), _DARK),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("GRID", (0, 0), (-1, -1), 0.5, _GRAY),
        ]))
        story.append(coop_summary_table)
        story.append(Spacer(1, 12))

        coop_header = ["Cooperativa", "Estado", "Granjas", "Hectareas", "Salud", "CO2e (ton)"]
        coop_rows = [coop_header]
        for c in coops:
            health = c.get("avg_health", 0)
            health_str = f"{health:.1f}" if health else "—"
            coop_rows.append([
                c.get("name", "—"),
                c.get("state", "—"),
                str(c.get("farm_count", 0)),
                f"{c.get('total_hectares', 0):,.0f}",
                health_str,
                f"{c.get('total_co2e_tonnes', 0):,.1f}",
            ])

        coop_table = Table(coop_rows, colWidths=[1.8 * inch, 0.9 * inch, 0.7 * inch, 0.9 * inch, 0.8 * inch, 1.0 * inch])
        coop_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), _GREEN),
            ("TEXTCOLOR", (0, 0), (-1, 0), _WHITE),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("GRID", (0, 0), (-1, -1), 0.5, _GRAY),
            ("ALIGN", (2, 0), (-1, -1), "CENTER"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [_WHITE, _LIGHT_BG]),
        ]))
        story.append(coop_table)
        story.append(Spacer(1, 8))
        story.append(Paragraph(
            "Las cooperativas representan el modelo colectivo de agricultura "
            "regenerativa que FODECIJAL busca impulsar. El impacto agregado "
            "demuestra que la organizacion cooperativa multiplica los beneficios "
            "ambientales y economicos de la agricultura de precision.",
            styles["normal"],
        ))

    # -- Footer --
    story.append(Spacer(1, 30))
    story.append(Paragraph(
        "Este reporte fue generado automaticamente por cultivOS. "
        "Los datos reflejan las mediciones mas recientes disponibles. "
        "cultivOS es una plataforma de inteligencia agricola desarrollada "
        "para agricultores de pequena y mediana escala en Jalisco, Mexico.",
        styles["small"],
    ))

    doc.build(story)
    return buf.getvalue()


# -- CSV Export --

_CSV_HEADERS = [
    "Parcela",
    "Cultivo",
    "Hectareas",
    "Salud",
    "Tendencia",
    "NDVI Promedio",
    "pH Suelo",
    "Materia Organica %",
    "Tratamientos",
    "Ultimo Tratamiento",
]


def generate_farm_export_csv(fields: list[dict]) -> str:
    """Generate a CSV export of farm field data with Spanish headers.

    Args:
        fields: list of dicts with keys: name, crop_type, hectares,
                health_score, health_trend, ndvi_mean, soil_ph,
                soil_organic_matter_pct

    Returns:
        CSV content as a string.
    """
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(_CSV_HEADERS)

    for f in fields:
        score = f.get("health_score")
        score_str = f"{score:.1f}" if score is not None else ""
        trend_map = {
            "improving": "Mejorando",
            "stable": "Estable",
            "declining": "Declinando",
        }
        trend = f.get("health_trend", "")
        trend_str = trend_map.get(trend, trend) if trend else ""
        ndvi = f.get("ndvi_mean")
        ndvi_str = f"{ndvi:.3f}" if ndvi is not None else ""
        ph = f.get("soil_ph")
        ph_str = f"{ph:.1f}" if ph is not None else ""
        om = f.get("soil_organic_matter_pct")
        om_str = f"{om:.1f}" if om is not None else ""

        treatment_count = f.get("treatment_count", 0) or 0
        last_date = f.get("last_treatment_date")
        last_date_str = last_date.strftime("%Y-%m-%d") if last_date else ""

        writer.writerow([
            f.get("name", ""),
            f.get("crop_type", "") or "",
            f.get("hectares", ""),
            score_str,
            trend_str,
            ndvi_str,
            ph_str,
            om_str,
            treatment_count,
            last_date_str,
        ])

    return buf.getvalue()
