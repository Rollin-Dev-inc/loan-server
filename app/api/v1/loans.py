from datetime import date, datetime, timedelta

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DBSession
from app.models import Item, Loan
from app.schema import (
    LoanCreate,
    LoanNotificationRead,
    LoanRead,
    LoanReturnConfirmation,
    LoanUpdate,
)
from app.services.audit_service import record_audit

router = APIRouter(prefix="/loans", tags=["loans"])


def _build_due_date(borrowed_at: date, duration_days: int) -> date:
    return borrowed_at + timedelta(days=duration_days)


@router.get("/", response_model=list[LoanRead])
def list_loans(
    db: DBSession, 
    current_user: CurrentUser,
    borrower_name: str | None = None,
    item_code: str | None = None,
    status: str | None = None,  # active, returned, overdue
    start_date: date | None = None,
    end_date: date | None = None
) -> list[Loan]:
    query = select(Loan)
    if borrower_name:
        query = query.where(Loan.borrower_name.ilike(f"%{borrower_name}%"))
    if item_code:
        query = query.where(Loan.item_code.ilike(f"%{item_code}%"))
    if start_date:
        query = query.where(Loan.borrowed_at >= start_date)
    if end_date:
        query = query.where(Loan.borrowed_at <= end_date)
        
    if status == "active":
        query = query.where(Loan.is_returned.is_(False))
    elif status == "returned":
        query = query.where(Loan.is_returned.is_(True))
    elif status == "overdue":
        query = query.where(Loan.is_returned.is_(False), Loan.due_at <= date.today())

    return db.scalars(query.order_by(Loan.id)).all()


@router.get("/notifications", response_model=list[LoanNotificationRead])
def list_loan_notifications(db: DBSession, current_user: CurrentUser) -> list[LoanNotificationRead]:
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
def get_loan(loan_id: int, db: DBSession, current_user: CurrentUser) -> Loan:
    loan = db.get(Loan, loan_id)
    if loan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loan not found",
        )
    return loan


@router.post("/", response_model=LoanRead, status_code=status.HTTP_201_CREATED)
def create_loan(payload: LoanCreate, db: DBSession, current_user: CurrentUser) -> Loan:
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
    if not payload.is_returned:
        if item.stock <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Item is currently out of stock",
            )
        item.stock -= 1

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
    db.flush()
    record_audit(db, current_user.id, current_user.username, "CREATE", "LOAN", loan.id, f"Borrower: {loan.borrower_name}")
    db.commit()
    db.refresh(loan)
    return loan


@router.put("/{loan_id}", response_model=LoanRead)
def update_loan(loan_id: int, payload: LoanUpdate, db: DBSession, current_user: CurrentUser) -> Loan:
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
        # If changing items and the loan is currently active, adjust stocks
        if loan.item_id != payload.item_id and not loan.is_returned:
            old_item = db.get(Item, loan.item_id)
            if item.stock <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="The new selected item is out of stock",
                )
            if old_item:
                old_item.stock += 1
            item.stock -= 1

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

    if payload.is_returned is not None and loan.is_returned != payload.is_returned:
        item_ref = db.get(Item, loan.item_id)
        if payload.is_returned:
            # It was active, now returned
            if item_ref:
                item_ref.stock += 1
        else:
            # It was returned, now active again
            if item_ref:
                if item_ref.stock <= 0:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Cannot reactivate loan. Item is currently out of stock",
                    )
                item_ref.stock -= 1

        loan.is_returned = payload.is_returned
        loan.returned_at = datetime.utcnow() if payload.is_returned else None

    loan.due_at = _build_due_date(loan.borrowed_at, loan.duration_days)
    record_audit(db, current_user.id, current_user.username, "UPDATE", "LOAN", loan.id, f"Updated loan {loan.id}")
    db.commit()
    db.refresh(loan)
    return loan


@router.patch("/{loan_id}/confirm-return", response_model=LoanRead)
def confirm_return(loan_id: int, payload: LoanReturnConfirmation, db: DBSession, current_user: CurrentUser) -> Loan:
    loan = db.get(Loan, loan_id)
    if loan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loan not found",
        )

    if loan.is_returned != payload.is_returned:
        item = db.get(Item, loan.item_id)
        if payload.is_returned:
            # The item is being returned, restore stock
            if item:
                item.stock += 1
        else:
            # The item is un-returned (borrowed again), deduct stock
            if item:
                if item.stock <= 0:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Cannot cancel return. Item is currently out of stock",
                    )
                item.stock -= 1

    loan.is_returned = payload.is_returned
    loan.returned_at = datetime.utcnow() if payload.is_returned else None
    record_audit(db, current_user.id, current_user.username, "UPDATE_RETURN_STATUS", "LOAN", loan.id, f"Status: {payload.is_returned}")
    db.commit()
    db.refresh(loan)
    return loan


@router.delete("/{loan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_loan(loan_id: int, db: DBSession, current_user: CurrentUser) -> None:
    loan = db.get(Loan, loan_id)
    if loan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loan not found",
        )
        
    if not loan.is_returned:
        item = db.get(Item, loan.item_id)
        if item:
            item.stock += 1

    record_audit(db, current_user.id, current_user.username, "DELETE", "LOAN", loan.id, f"Deleted loan {loan.id}")
    db.delete(loan)
    db.commit()
