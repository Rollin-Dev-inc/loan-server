from datetime import date, datetime, timedelta

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import DBSession
from app.models import Item, Loan
from app.schema import (
    LoanCreate,
    LoanNotificationRead,
    LoanRead,
    LoanReturnConfirmation,
    LoanUpdate,
)

router = APIRouter(prefix="/loans", tags=["loans"])


def _build_due_date(borrowed_at: date, duration_days: int) -> date:
    return borrowed_at + timedelta(days=duration_days)


@router.get("/", response_model=list[LoanRead])
def list_loans(db: DBSession) -> list[Loan]:
    return db.scalars(select(Loan).order_by(Loan.id)).all()


@router.get("/notifications", response_model=list[LoanNotificationRead])
def list_loan_notifications(db: DBSession) -> list[LoanNotificationRead]:
    today = date.today()
    overdue_loans = db.scalars(
        select(Loan).where(
            Loan.is_returned.is_(False),
            Loan.due_at <= today,
        ).order_by(Loan.due_at)
    ).all()

    notifications: list[LoanNotificationRead] = []
    for loan in overdue_loans:
        days_overdue = (today - loan.due_at).days
        notifications.append(
            LoanNotificationRead(
                loan_id=loan.id,
                borrower_name=loan.borrower_name,
                item_id=loan.item_id,
                item_code=loan.item_code,
                due_at=loan.due_at,
                days_overdue=days_overdue,
                message=(
                    f"Barang dengan kode {loan.item_code} sudah jatuh tempo. "
                    "Apakah barang sudah dikembalikan?"
                ),
            )
        )
    return notifications


@router.get("/{loan_id}", response_model=LoanRead)
def get_loan(loan_id: int, db: DBSession) -> Loan:
    loan = db.get(Loan, loan_id)
    if loan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loan not found",
        )
    return loan


@router.post("/", response_model=LoanRead, status_code=status.HTTP_201_CREATED)
def create_loan(payload: LoanCreate, db: DBSession) -> Loan:
    item = db.get(Item, payload.item_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Item not found",
        )
    if payload.item_code is not None and payload.item_code != item.item_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Item code does not match selected item",
        )
    active_loan = db.scalar(
        select(Loan.id).where(
            Loan.item_id == payload.item_id,
            Loan.is_returned.is_(False),
        ).limit(1)
    )
    if active_loan is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Item is currently borrowed and has not been returned",
        )

    loan = Loan(
        borrower_name=payload.borrower_name,
        item_id=payload.item_id,
        item_code=item.item_code,
        duration_days=payload.duration_days,
        borrowed_at=payload.borrowed_at,
        due_at=_build_due_date(payload.borrowed_at, payload.duration_days),
        price_to_pay=payload.price_to_pay,
        is_returned=payload.is_returned,
        returned_at=datetime.utcnow() if payload.is_returned else None,
    )
    db.add(loan)
    db.commit()
    db.refresh(loan)
    return loan


@router.put("/{loan_id}", response_model=LoanRead)
def update_loan(loan_id: int, payload: LoanUpdate, db: DBSession) -> Loan:
    loan = db.get(Loan, loan_id)
    if loan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loan not found",
        )

    if payload.item_id is not None:
        item = db.get(Item, payload.item_id)
        if item is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Item not found",
            )
        if payload.item_code is not None and payload.item_code != item.item_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Item code does not match selected item",
            )
        active_loan = db.scalar(
            select(Loan.id).where(
                Loan.item_id == payload.item_id,
                Loan.is_returned.is_(False),
                Loan.id != loan_id,
            ).limit(1)
        )
        if active_loan is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Item is currently borrowed and has not been returned",
            )
        loan.item_id = payload.item_id
        loan.item_code = item.item_code
    elif payload.item_code is not None and payload.item_code != loan.item_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Item code does not match selected item",
        )

    if payload.borrower_name is not None:
        loan.borrower_name = payload.borrower_name

    if payload.duration_days is not None:
        loan.duration_days = payload.duration_days

    if payload.borrowed_at is not None:
        loan.borrowed_at = payload.borrowed_at

    if payload.price_to_pay is not None:
        loan.price_to_pay = payload.price_to_pay

    if payload.is_returned is not None:
        loan.is_returned = payload.is_returned
        loan.returned_at = datetime.utcnow() if payload.is_returned else None

    loan.due_at = _build_due_date(loan.borrowed_at, loan.duration_days)
    db.commit()
    db.refresh(loan)
    return loan


@router.patch("/{loan_id}/confirm-return", response_model=LoanRead)
def confirm_return(loan_id: int, payload: LoanReturnConfirmation, db: DBSession) -> Loan:
    loan = db.get(Loan, loan_id)
    if loan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loan not found",
        )

    loan.is_returned = payload.is_returned
    loan.returned_at = datetime.utcnow() if payload.is_returned else None
    db.commit()
    db.refresh(loan)
    return loan


@router.delete("/{loan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_loan(loan_id: int, db: DBSession) -> None:
    loan = db.get(Loan, loan_id)
    if loan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loan not found",
        )
    db.delete(loan)
    db.commit()
