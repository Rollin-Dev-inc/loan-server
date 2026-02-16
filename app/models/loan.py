from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Loan(Base):
    __tablename__ = "loans"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    borrower_name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), nullable=False, index=True)
    item_code: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)
    borrowed_at: Mapped[date] = mapped_column(Date, nullable=False)
    due_at: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    price_to_pay: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    is_returned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    returned_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    item = relationship("Item", back_populates="loans")

    @property
    def is_overdue(self) -> bool:
        return (not self.is_returned) and self.due_at <= date.today()
