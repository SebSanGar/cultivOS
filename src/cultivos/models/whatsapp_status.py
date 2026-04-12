"""Pydantic models for #185 — WhatsApp-ready farm status message."""

from pydantic import BaseModel


class WhatsAppStatusOut(BaseModel):
    farm_id: int
    message_es: str
    has_alerts: bool
    generated_at: str
