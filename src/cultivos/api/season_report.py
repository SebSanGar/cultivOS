"""Season Report Card PDF endpoint for owner economic-impact view.

GET /api/farms/{farm_id}/season-report-pdf — generates a season summary
PDF suitable for bank renewal, cooperative, or FODECIJAL grant documentation.
"""

import io
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import func
from sqlalchemy.orm import Session

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from cultivos.db.models import Farm, Field, HealthScore, TreatmentRecord
from cultivos.db.session import get_db
from cultivos.services.intelligence.economics import calculate_farm_savings
from cultivos.services.intelligence.assumptions import get_value as _a

router = APIRouter(tags=["economics"])

_GREEN = HexColor("#2d6a2d")
_DARK = HexColor("#1a1a2e")
_GRAY = HexColor("#555555")
_LIGHT_BG = HexColor("#f0f4f0")
_WHITE = HexColor("#ffffff")

_TIER_RATES = {
    "basic": _a("tier_rate_basic_mxn_ha"),
    "standard": _a("tier_rate_standard_mxn_ha"),
}


def _build_pdf(
    farm_name: str,
    municipality: str,
    hectares: float,
    avg_health: float,
    treatment_count: int,
    total_savings_mxn: int,
    total_savings_low_mxn: int,
    subscription_cost_mxn: Optional[int],
    net_savings_mxn: Optional[int],
    roi_multiple: Optional[float],
    generated_at: str,
) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, topMargin=0.75 * inch, bottomMargin=0.75 * inch)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("T", parent=styles["Title"], fontSize=20, textColor=_GREEN, spaceAfter=4)
    sub_style = ParagraphStyle("S", parent=styles["Normal"], fontSize=11, textColor=_GRAY, spaceAfter=12)
    section_style = ParagraphStyle("Sec", parent=styles["Heading2"], fontSize=13, textColor=_DARK, spaceBefore=14, spaceAfter=4)
    body_style = ParagraphStyle("B", parent=styles["Normal"], fontSize=10, textColor=_DARK)
    disclaimer_style = ParagraphStyle("D", parent=styles["Normal"], fontSize=8, textColor=_GRAY, spaceAfter=4)

    story = []

    story.append(Paragraph("cultivOS — Season Report Card", title_style))
    story.append(Paragraph(f"Prepared: {generated_at} · Estimate — not a guaranteed result", sub_style))
    story.append(Spacer(1, 0.1 * inch))

    # Farm summary table
    story.append(Paragraph("Farm Summary", section_style))
    farm_data = [
        ["Farm", farm_name],
        ["Municipality", municipality],
        ["Hectares under management", f"{hectares:.1f} ha"],
        ["Average field health score", f"{avg_health:.0f} / 100"],
        ["Treatments applied this season", str(treatment_count)],
    ]
    farm_table = Table(farm_data, colWidths=[2.4 * inch, 3.6 * inch])
    farm_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), _LIGHT_BG),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (-1, -1), _DARK),
        ("GRID", (0, 0), (-1, -1), 0.5, _GRAY),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [_WHITE, _LIGHT_BG]),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(farm_table)
    story.append(Spacer(1, 0.15 * inch))

    # Economic impact table
    story.append(Paragraph("Estimated Economic Impact", section_style))
    impact_data = [
        ["Metric", "Value", "Notes"],
        ["Estimated savings (conservative)", f"~ ${total_savings_low_mxn:,}", "Low estimate (0.6×)"],
        ["Estimated savings (projected)", f"~ ${total_savings_mxn:,}", "Model assumption"],
        ["Annual subscription cost", f"${subscription_cost_mxn:,}" if subscription_cost_mxn else "—", "Based on tier"],
        ["Net savings (est.)", f"~ ${net_savings_mxn:,}" if net_savings_mxn else "—", "Savings minus subscription"],
        ["Return on investment", f"{roi_multiple}×" if roi_multiple else "—", "Projected gross return"],
    ]
    impact_table = Table(impact_data, colWidths=[2.2 * inch, 1.8 * inch, 2.0 * inch])
    impact_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), _GREEN),
        ("TEXTCOLOR", (0, 0), (-1, 0), _WHITE),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 1), (-1, -1), _DARK),
        ("GRID", (0, 0), (-1, -1), 0.5, _GRAY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [_WHITE, _LIGHT_BG]),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(impact_table)
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("Important disclaimer", section_style))
    story.append(Paragraph(
        "All figures are model estimates based on literature averages (MDPI Agronomy 2025/2026, "
        "SARE 2021, CONAGUA 2018). They are NOT measured results for this specific farm. "
        "Actual savings depend on crop type, weather, soil conditions, and management practices. "
        "Do not use these estimates as a basis for financial commitments without independent verification.",
        disclaimer_style,
    ))
    story.append(Paragraph(
        "Generated by cultivOS · agriculture intelligence platform · cultivosagro.com",
        disclaimer_style,
    ))

    doc.build(story)
    return buf.getvalue()


@router.get("/api/farms/{farm_id}/season-report-pdf")
def get_season_report_pdf(
    farm_id: int,
    db: Session = Depends(get_db),
):
    """Generate a season report card PDF for the given farm."""
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")

    fields = db.query(Field).filter(Field.farm_id == farm_id).all()
    total_hectares = sum(f.hectares or 0 for f in fields)
    field_ids = [f.id for f in fields]

    health_scores = []
    for fid in field_ids:
        latest = (
            db.query(HealthScore)
            .filter(HealthScore.field_id == fid)
            .order_by(HealthScore.scored_at.desc())
            .first()
        )
        if latest:
            health_scores.append(float(latest.score))

    avg_health = sum(health_scores) / len(health_scores) if health_scores else 0.0

    treatment_count = (
        db.query(func.count(TreatmentRecord.id))
        .filter(TreatmentRecord.field_id.in_(field_ids))
        .scalar()
    ) or 0

    result = calculate_farm_savings(
        health_score=avg_health or 50.0,
        hectares=total_hectares or 0.0,
        treatment_count=treatment_count,
        irrigation_efficiency=None,
    )
    total = result["total_savings_mxn"]
    low = round(total * 0.6)

    tier = getattr(farm, "tier", None)
    subscription_cost_mxn: Optional[int] = None
    if tier and tier in _TIER_RATES and total_hectares > 0:
        subscription_cost_mxn = round(total_hectares * _TIER_RATES[tier])

    net_savings: Optional[int] = None
    roi_multiple: Optional[float] = None
    has_real_data = len(health_scores) >= 1 and treatment_count >= 1
    if subscription_cost_mxn and has_real_data and subscription_cost_mxn > 0:
        net_savings = total - subscription_cost_mxn
        roi_multiple = round(total / subscription_cost_mxn, 1)

    generated_at = datetime.utcnow().strftime("%Y-%m-%d")
    pdf_bytes = _build_pdf(
        farm_name=farm.name,
        municipality=getattr(farm, "municipality", "") or "",
        hectares=total_hectares,
        avg_health=avg_health,
        treatment_count=treatment_count,
        total_savings_mxn=total,
        total_savings_low_mxn=low,
        subscription_cost_mxn=subscription_cost_mxn,
        net_savings_mxn=net_savings,
        roi_multiple=roi_multiple,
        generated_at=generated_at,
    )

    safe_name = farm.name.replace(" ", "_").replace("/", "-")[:30]
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="season_report_{safe_name}_{generated_at}.pdf"',
        },
    )
