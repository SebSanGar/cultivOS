"""Regenerative scorecard CSV and PDF export endpoints."""

import csv
import io
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session

from cultivos.auth import get_current_user
from cultivos.db.session import get_db
from cultivos.services.intelligence.regen_scorecard import compute_farm_regen_scorecard_csv
from cultivos.services.intelligence.regen_scorecard_pdf import generate_regen_scorecard_pdf

router = APIRouter(tags=["intelligence"], dependencies=[Depends(get_current_user)])

_CSV_HEADERS = [
    "field_id", "field_name", "crop_type", "hectares",
    "regen_score", "organic_treatments_pct", "soc_pct",
    "synthetic_inputs_avoided", "biodiversity_score", "date_from", "date_to",
]


@router.get("/api/farms/{farm_id}/regen-scorecard/export.csv")
def export_regen_scorecard(
    farm_id: int,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db),
):
    """Export regenerative scorecard as CSV for a farm.

    One row per field with: regen score, organic treatment %, soil organic carbon,
    synthetic inputs avoided, biodiversity score. Filterable by date range.
    FODECIJAL: downloadable evidence for certification bodies and grant reviewers.
    """
    rows = compute_farm_regen_scorecard_csv(farm_id, db, date_from, date_to)
    if rows is None:
        raise HTTPException(status_code=404, detail="Farm not found")

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=_CSV_HEADERS)
    writer.writeheader()
    writer.writerows(rows)
    output.seek(0)

    filename = f"regen_scorecard_farm_{farm_id}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/api/farms/{farm_id}/regen-scorecard/export.pdf")
def export_regen_scorecard_pdf(
    farm_id: int,
    db: Session = Depends(get_db),
):
    """Export regenerative scorecard as PDF for a farm.

    Returns a formatted PDF with per-field metrics and overall readiness %.
    FODECIJAL: printable audit evidence for certification bodies and grant reviewers.
    """
    pdf_bytes = generate_regen_scorecard_pdf(farm_id, db)
    if pdf_bytes is None:
        raise HTTPException(status_code=404, detail="Farm not found")

    filename = f"regen_scorecard_farm_{farm_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
