"""Pydantic schema for cumulative savings time series endpoint."""

from typing import List, Optional
from pydantic import BaseModel


class CumulativeSavingsPoint(BaseModel):
    month: int
    cumulative_savings_mxn: int
    is_estimate: bool = True


class CumulativeSavingsOut(BaseModel):
    farm_id: int
    data_points: List[CumulativeSavingsPoint]
    breakeven_month: Optional[int] = None
    subscription_cost_mxn: Optional[int] = None
