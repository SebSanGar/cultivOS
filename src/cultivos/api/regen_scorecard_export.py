"""Regenerative scorecard CSV export endpoint."""

import csv
import io
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from cultivos.db.session import get_db
from cultivos.services.intelligence.regen_scorecard import compute_farm_regen_scorecard_csv

router = APIRouter(tags=["intelligence"])

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
