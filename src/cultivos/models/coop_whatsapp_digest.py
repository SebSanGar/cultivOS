"""Pydantic models for #202 — cooperative WhatsApp digest aggregate."""

from typing import List

from pydantic import BaseModel


class AttentionFarmEntry(BaseModel):
    farm_id: int
    farm_name: str
    critical_count: int
    high_count: int
    message_es: str


class CoopWhatsAppDigestOut(BaseModel):
    cooperative_id: int
    generated_at: str
    total_farms: int
    total_critical_alerts: int
    total_high_alerts: int
    farms_with_alerts: int
    top_attention_farms: List[AttentionFarmEntry]
    digest_message_es: str
