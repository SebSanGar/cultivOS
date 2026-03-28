"""Seasonal comparison — side-by-side metrics for temporal vs secas seasons."""

from datetime import datetime


def _classify_season(month: int) -> str:
    """Temporal (Jun-Oct) or secas (Nov-May)."""
    if 6 <= month <= 10:
        return "temporal"
    return "secas"


def _empty_season() -> dict:
    return {
        "avg_health_score": None,
        "avg_ndvi": None,
        "treatment_count": 0,
        "data_points": 0,
    }


def compute_seasonal_comparison(
    health_records: list[dict],
    treatments: list[dict],
    year: int | None = None,
) -> dict:
    """Compute per-season aggregates from health records and treatments.

    Parameters
    ----------
    health_records : list of dicts with keys score, ndvi_mean, scored_at
    treatments : list of dicts with key created_at
    year : optional int — if provided, only include records from that year

    Returns
    -------
    dict with keys "temporal", "secas" (each with avg_health_score, avg_ndvi,
    treatment_count, data_points), and "available_years" (sorted desc).
    """
    # Collect all years from health records
    all_years = sorted(
        {rec["scored_at"].year for rec in health_records if rec.get("scored_at")},
        reverse=True,
    )

    # Filter by year if specified
    if year is not None:
        health_records = [r for r in health_records if r["scored_at"].year == year]
        treatments = [t for t in treatments if t["created_at"].year == year]

    seasons = {
        "temporal": {"scores": [], "ndvis": [], "treatment_count": 0},
        "secas": {"scores": [], "ndvis": [], "treatment_count": 0},
    }

    for rec in health_records:
        season = _classify_season(rec["scored_at"].month)
        seasons[season]["scores"].append(rec["score"])
        if rec.get("ndvi_mean") is not None:
            seasons[season]["ndvis"].append(rec["ndvi_mean"])

    for tr in treatments:
        season = _classify_season(tr["created_at"].month)
        seasons[season]["treatment_count"] += 1

    result = {}
    for key in ("temporal", "secas"):
        s = seasons[key]
        if s["scores"]:
            result[key] = {
                "avg_health_score": round(sum(s["scores"]) / len(s["scores"]), 2),
                "avg_ndvi": round(sum(s["ndvis"]) / len(s["ndvis"]), 4) if s["ndvis"] else None,
                "treatment_count": s["treatment_count"],
                "data_points": len(s["scores"]),
            }
        else:
            result[key] = _empty_season()
            result[key]["treatment_count"] = s["treatment_count"]

    result["available_years"] = all_years

    return result
