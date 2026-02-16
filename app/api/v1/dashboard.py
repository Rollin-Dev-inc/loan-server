from calendar import monthrange
from datetime import date

from fastapi import APIRouter
from sqlalchemy import desc, func, select

from app.api.deps import DBSession
from app.models import Item, Loan
from app.schema import DashboardBorrowedItemRead, DashboardPeriod, DashboardSummaryRead

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

PERIOD_TO_MONTHS = {
    DashboardPeriod.ONE_MONTH: 1,
    DashboardPeriod.THREE_MONTHS: 3,
    DashboardPeriod.SIX_MONTHS: 6,
    DashboardPeriod.ONE_YEAR: 12,
    DashboardPeriod.THREE_YEARS: 36,
    DashboardPeriod.FIVE_YEARS: 60,
}


def _subtract_months(reference: date, months: int) -> date:
    month = reference.month - months
    year = reference.year
    while month <= 0:
        month += 12
        year -= 1
    day = min(reference.day, monthrange(year, month)[1])
    return date(year, month, day)


@router.get("/", response_model=DashboardSummaryRead)
def get_dashboard_summary(
    db: DBSession,
    period: DashboardPeriod = DashboardPeriod.ONE_MONTH,
) -> DashboardSummaryRead:
    today = date.today()
    period_start = _subtract_months(today, PERIOD_TO_MONTHS[period])

    filter_conditions = (
        Loan.borrowed_at >= period_start,
        Loan.borrowed_at <= today,
    )

    total_revenue = db.scalar(
        select(func.coalesce(func.sum(Loan.price_to_pay), 0.0)).where(*filter_conditions)
    )
    total_loans = db.scalar(select(func.count(Loan.id)).where(*filter_conditions))
    unique_items_borrowed = db.scalar(
        select(func.count(func.distinct(Loan.item_id))).where(*filter_conditions)
    )
    items_ever_borrowed = db.scalar(select(func.count(func.distinct(Loan.item_id))))

    borrowed_item_rows = db.execute(
        select(
            Loan.item_id.label("item_id"),
            Loan.item_code.label("item_code"),
            Item.name.label("item_name"),
            func.count(Loan.id).label("total_loans"),
            func.coalesce(func.sum(Loan.price_to_pay), 0.0).label("total_revenue"),
            func.max(Loan.borrowed_at).label("last_borrowed_at"),
        )
        .join(Item, Item.id == Loan.item_id)
        .where(*filter_conditions)
        .group_by(Loan.item_id, Loan.item_code, Item.name)
        .order_by(desc("total_loans"), desc("total_revenue"), Loan.item_id)
    ).all()

    borrowed_items = [
        DashboardBorrowedItemRead(
            item_id=row.item_id,
            item_code=row.item_code,
            item_name=row.item_name,
            total_loans=row.total_loans,
            total_revenue=float(row.total_revenue or 0.0),
            last_borrowed_at=row.last_borrowed_at,
        )
        for row in borrowed_item_rows
    ]

    return DashboardSummaryRead(
        period=period,
        period_start=period_start,
        period_end=today,
        total_revenue=float(total_revenue or 0.0),
        total_loans=int(total_loans or 0),
        unique_items_borrowed=int(unique_items_borrowed or 0),
        items_ever_borrowed=int(items_ever_borrowed or 0),
        borrowed_items=borrowed_items,
    )
