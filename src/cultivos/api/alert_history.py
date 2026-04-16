"""Cross-farm alert history timeline — combines Alert (SMS) and AlertLog (system) records."""

from datetime import date, datetime, time
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from cultivos.auth import get_current_user
from cultivos.db.models import Alert, AlertLog
from cultivos.db.session import get_db
from cultivos.models.alert import AlertAnalyticsOut

router = APIRouter(
    prefix="/api/alerts",
    tags=["alert-history"],
    dependencies=[Depends(get_current_user)]
)


def _alert_to_dict(a: Alert) -> dict:
    return {
        "id": f"sms-{a.id}",
        "farm_id": a.farm_id,
        "field_id": a.field_id,
        "alert_type": a.alert_type,
        "message": a.message,
        "severity": _type_to_severity(a.alert_type),
        "source": "sms",
        "status": a.status,
        "acknowledged": None,
        "created_at": a.created_at.isoformat(),
    }


def _log_to_dict(log: AlertLog) -> dict:
    return {
        "id": f"sys-{log.id}",
        "farm_id": log.farm_id,
        "field_id": log.field_id,
        "alert_type": log.alert_type,
        "message": log.message,
        "severity": log.severity,
        "source": "system",
        "status": None,
        "acknowledged": log.acknowledged,
        "created_at": log.created_at.isoformat(),
    }


def _type_to_severity(alert_type: str) -> str:
    """Map SMS alert types to severity levels."""
    critical_types = {"anomaly_health_drop", "anomaly_ndvi_drop", "low_health"}
    warning_types = {"irrigation"}
    if alert_type in critical_types:
        return "critical"
    if alert_type in warning_types:
        return "warning"
    return "info"


@router.get("/analytics", response_model=AlertAnalyticsOut)
def get_alert_analytics(
    farm_id: int | None = Query(None),
    db: Session = Depends(get_db),
) -> AlertAnalyticsOut:
    """Aggregate alert delivery metrics and farmer engagement KPIs."""
    # Query Alert (SMS) records
    q_alerts = db.query(Alert)
    if farm_id is not None:
        q_alerts = q_alerts.filter(Alert.farm_id == farm_id)
    sms_alerts = q_alerts.all()

    # Query AlertLog (system) records
    q_logs = db.query(AlertLog)
    if farm_id is not None:
        q_logs = q_logs.filter(AlertLog.farm_id == farm_id)
    sys_logs = q_logs.all()

    # Counts by type (unified across both sources)
    by_type: dict[str, int] = {}
    for a in sms_alerts:
        by_type[a.alert_type] = by_type.get(a.alert_type, 0) + 1
    for log in sys_logs:
        by_type[log.alert_type] = by_type.get(log.alert_type, 0) + 1

    # Counts by severity (compute for SMS, read from system logs)
    by_severity: dict[str, int] = {}
    for a in sms_alerts:
        sev = _type_to_severity(a.alert_type)
        by_severity[sev] = by_severity.get(sev, 0) + 1
    for log in sys_logs:
        by_severity[log.severity] = by_severity.get(log.severity, 0) + 1

    # Counts by SMS status (only SMS alerts have status)
    by_status: dict[str, int] = {}
    for a in sms_alerts:
        by_status[a.status] = by_status.get(a.status, 0) + 1

    # Delivery rate: sent / total SMS * 100
    total_sms = len(sms_alerts)
    sent_count = by_status.get("sent", 0)
    delivery_rate = (sent_count / total_sms * 100) if total_sms > 0 else 0.0

    # Reach: unique farms and fields across all alerts
    all_farm_ids = {a.farm_id for a in sms_alerts} | {log.farm_id for log in sys_logs}
    all_field_ids = set()
    for a in sms_alerts:
        if a.field_id is not None:
            all_field_ids.add(a.field_id)
    for log in sys_logs:
        if log.field_id is not None:
            all_field_ids.add(log.field_id)

    return AlertAnalyticsOut(
        total_alerts=total_sms + len(sys_logs),
        total_sms=total_sms,
        total_system=len(sys_logs),
        delivery_rate=round(delivery_rate, 1),
        by_type=by_type,
        by_severity=by_severity,
        by_status=by_status,
        farms_reached=len(all_farm_ids),
        fields_reached=len(all_field_ids),
    )


@router.get("/history")
def get_alert_history(
    farm_id: int | None = Query(None),
    alert_type: str | None = Query(None),
    severity: str | None = Query(None),
    start_date: Optional[date] = Query(None, description="Filter alerts on or after this date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="Filter alerts on or before this date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Return combined alert history from Alert + AlertLog tables, newest first."""
    start_dt = datetime.combine(start_date, time.min) if start_date is not None else None
    end_dt = datetime.combine(end_date, time.max) if end_date is not None else None

    # Query Alert (SMS) records
    q_alerts = db.query(Alert)
    if farm_id is not None:
        q_alerts = q_alerts.filter(Alert.farm_id == farm_id)
    if alert_type is not None:
        q_alerts = q_alerts.filter(Alert.alert_type == alert_type)
    if start_dt is not None:
        q_alerts = q_alerts.filter(Alert.created_at >= start_dt)
    if end_dt is not None:
        q_alerts = q_alerts.filter(Alert.created_at <= end_dt)
    alerts = q_alerts.all()

    # Query AlertLog (system) records
    q_logs = db.query(AlertLog)
    if farm_id is not None:
        q_logs = q_logs.filter(AlertLog.farm_id == farm_id)
    if alert_type is not None:
        q_logs = q_logs.filter(AlertLog.alert_type == alert_type)
    if severity is not None:
        q_logs = q_logs.filter(AlertLog.severity == severity)
    if start_dt is not None:
        q_logs = q_logs.filter(AlertLog.created_at >= start_dt)
    if end_dt is not None:
        q_logs = q_logs.filter(AlertLog.created_at <= end_dt)
    logs = q_logs.all()

    # Convert to unified dicts
    results = [_alert_to_dict(a) for a in alerts]
    results += [_log_to_dict(log) for log in logs]

    # Apply severity filter to SMS alerts (computed, not stored)
    if severity is not None:
        results = [r for r in results if r["severity"] == severity]

    # Sort newest first
    results.sort(key=lambda x: x["created_at"], reverse=True)
    return results
