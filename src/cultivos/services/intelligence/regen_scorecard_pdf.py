"""Regen scorecard PDF export service — generates a printable PDF using reportlab.

Wraps compute_farm_regen_scorecard_csv() to produce a formatted PDF with:
- Farm name and export date
- Per-field table: organic %, SOC, synthetic inputs avoided, biodiversity score, regen score
- Overall readiness percentage
"""

import io
from datetime import date

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from sqlalchemy.orm import Session

from cultivos.db.models import Farm
from cultivos.services.intelligence.regen_scorecard import compute_farm_regen_scorecard_csv


def generate_regen_scorecard_pdf(farm_id: int, db: Session) -> bytes | None:
    """Generate PDF bytes for the farm's regenerative scorecard.

    Returns None if farm not found (signals 404 to caller).
    Returns b'%PDF...' bytes on success — empty farm produces a PDF with zero rows.
    """
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if farm is None:
        return None

    rows = compute_farm_regen_scorecard_csv(farm_id, db) or []

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    story = []

    # Title
    story.append(Paragraph(f"Scorecard Regenerativo — {farm.name}", styles["Title"]))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(f"Fecha: {date.today().isoformat()}", styles["Normal"]))
    story.append(Spacer(1, 0.5 * cm))

    # Summary: overall readiness
    if rows:
        overall_pct = round(
            sum(r.get("regen_score", 0) or 0 for r in rows) / len(rows), 1
        )
    else:
        overall_pct = 0.0
    story.append(
        Paragraph(f"Porcentaje de preparacion regenerativa general: <b>{overall_pct}%</b>", styles["Normal"])
    )
    story.append(Spacer(1, 0.5 * cm))

    # Table header
    header = [
        "Campo",
        "Cultivo",
        "ha",
        "Trat. organico %",
        "SOC %",
        "Entradas sinteticas evitadas",
        "Biodiversidad",
        "Score",
    ]

    table_data = [header]
    for r in rows:
        table_data.append([
            str(r.get("field_name", "")),
            str(r.get("crop_type", "")),
            str(r.get("hectares", 0)),
            f"{r.get('organic_treatments_pct', 0):.1f}",
            str(r.get("soc_pct", "—")),
            str(r.get("synthetic_inputs_avoided", 0)),
            f"{r.get('biodiversity_score', 0):.0f}",
            f"{r.get('regen_score', 0):.1f}",
        ])

    if not rows:
        table_data.append(["(sin campos)", "", "", "", "", "", "", ""])

    col_widths = [3.5 * cm, 2 * cm, 1.2 * cm, 2.8 * cm, 1.5 * cm, 3.5 * cm, 2 * cm, 1.5 * cm]
    tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2d5016")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4eb")]),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cccccc")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 0.5 * cm))
    story.append(
        Paragraph(
            "cultivOS — Plataforma de Inteligencia Agricola Regenerativa",
            styles["Normal"],
        )
    )

    doc.build(story)
    return buf.getvalue()
