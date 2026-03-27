"""
Pure PDF report generation for farm health summaries.

Generates a printable PDF suitable for FIRA/Financiera Rural loan applications.
All text in Spanish. No I/O — takes data dicts in, returns PDF bytes out.
"""

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
