"""Detailed system health endpoint — operational status for grant reviewers."""

import glob
import sys
import time

import fastapi
from fastapi import APIRouter, Depends, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from cultivos.auth import get_current_user
from cultivos.db.models import (
    Farm, Field, SoilAnalysis, NDVIResult, ThermalResult,
    TreatmentRecord, Alert, FlightLog, WeatherRecord,
)
from cultivos.db.session import get_db

router = APIRouter(prefix="/api/system", tags=["system"], dependencies=[Depends(get_current_user)])

_start_time = time.monotonic()


def _count_tests() -> int:
    """Count test functions across all test files."""
    import os
    test_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "tests")
    test_dir = os.path.normpath(test_dir)
    count = 0
    for filepath in glob.glob(os.path.join(test_dir, "test_*.py")):
        with open(filepath, "r") as f:
            for line in f:
                stripped = line.strip()
                if stripped.startswith("def test_"):
                    count += 1
    return count


@router.get("/health-detailed")
def health_detailed(request: Request, db: Session = Depends(get_db)):
    """Comprehensive system status: versions, DB counts, timestamps, endpoint and test counts."""
    # Database record counts
    database = {
        "farms": db.query(func.count(Farm.id)).scalar() or 0,
        "fields": db.query(func.count(Field.id)).scalar() or 0,
        "soil_analyses": db.query(func.count(SoilAnalysis.id)).scalar() or 0,
        "ndvi_results": db.query(func.count(NDVIResult.id)).scalar() or 0,
        "thermal_results": db.query(func.count(ThermalResult.id)).scalar() or 0,
        "treatments": db.query(func.count(TreatmentRecord.id)).scalar() or 0,
        "alerts": db.query(func.count(Alert.id)).scalar() or 0,
        "flight_logs": db.query(func.count(FlightLog.id)).scalar() or 0,
        "weather_records": db.query(func.count(WeatherRecord.id)).scalar() or 0,
    }

    # Latest data timestamps
    def _latest_ts(model, col):
        val = db.query(func.max(col)).scalar()
        return val.isoformat() if val else None

    latest_data = {
        "soil": _latest_ts(SoilAnalysis, SoilAnalysis.sampled_at),
        "ndvi": _latest_ts(NDVIResult, NDVIResult.analyzed_at),
        "thermal": _latest_ts(ThermalResult, ThermalResult.analyzed_at),
        "weather": _latest_ts(WeatherRecord, WeatherRecord.recorded_at),
    }

    # Count registered API endpoints
    endpoint_count = len(request.app.routes)

    # Count test functions
    test_count = _count_tests()

    return {
        "status": "operational",
        "api_version": "0.1.0",
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "fastapi_version": fastapi.__version__,
        "uptime_seconds": round(time.monotonic() - _start_time, 1),
        "database": database,
        "latest_data": latest_data,
        "endpoint_count": endpoint_count,
        "test_count": test_count,
    }
