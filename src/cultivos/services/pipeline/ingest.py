"""Bulk data ingestion services — CSV import for soil analysis records."""

import csv
import io
from datetime import datetime
from typing import Any

from pydantic import ValidationError

from cultivos.models.soil import SoilAnalysisCreate


REQUIRED_COLUMNS = {"sampled_at"}

VALID_COLUMNS = {
    "ph", "organic_matter_pct", "nitrogen_ppm", "phosphorus_ppm",
    "potassium_ppm", "texture", "moisture_pct", "electrical_conductivity",
    "depth_cm", "notes", "recommendations", "sampled_at",
}


def parse_soil_csv(file_bytes: bytes) -> dict[str, Any]:
    """Parse a CSV file into validated SoilAnalysisCreate objects.

    Returns dict with:
        - records: list of SoilAnalysisCreate (valid rows)
        - errors: list of {"row": int, "detail": str} (invalid rows)
        - missing_columns: list of str if required columns absent (caller should 422)
    """
    text = file_bytes.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))

    if reader.fieldnames is None:
        return {"records": [], "errors": [], "missing_columns": ["sampled_at"]}

    headers = set(reader.fieldnames)

    missing = REQUIRED_COLUMNS - headers
    if missing:
        return {"records": [], "errors": [], "missing_columns": sorted(missing)}

    usable_columns = headers & VALID_COLUMNS

    records: list[SoilAnalysisCreate] = []
    errors: list[dict[str, Any]] = []

    for row_num, row in enumerate(reader, start=2):  # row 1 = header
        row_data = {}
        for col in usable_columns:
            val = row.get(col, "").strip()
            if val == "":
                continue
            if col == "sampled_at":
                row_data[col] = val
            elif col in ("texture", "notes", "recommendations"):
                row_data[col] = val
            else:
                try:
                    row_data[col] = float(val)
                except ValueError:
                    errors.append({"row": row_num, "detail": f"Invalid number for {col}: {val}"})
                    continue

        if "sampled_at" not in row_data:
            errors.append({"row": row_num, "detail": "Missing sampled_at value"})
            continue

        try:
            record = SoilAnalysisCreate(**row_data)
            records.append(record)
        except ValidationError as e:
            errors.append({"row": row_num, "detail": str(e.errors()[0]["msg"])})

    return {"records": records, "errors": errors, "missing_columns": []}
