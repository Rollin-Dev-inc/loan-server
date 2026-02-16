from datetime import date
from enum import Enum

from pydantic import BaseModel


class DashboardPeriod(str, Enum):
    ONE_MONTH = "1m"
    THREE_MONTHS = "3m"
    SIX_MONTHS = "6m"
    ONE_YEAR = "1y"
    THREE_YEARS = "3y"
    FIVE_YEARS = "5y"


class DashboardBorrowedItemRead(BaseModel):
    item_id: int
    item_code: str
    item_name: str
    total_loans: int
    total_revenue: float
    last_borrowed_at: date


class DashboardSummaryRead(BaseModel):
    period: DashboardPeriod
    period_start: date
    period_end: date
    total_revenue: float
    total_loans: int
    unique_items_borrowed: int
    items_ever_borrowed: int
    borrowed_items: list[DashboardBorrowedItemRead]
