from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    item_code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False, index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    photo_data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    photo_content_type: Mapped[str] = mapped_column(String(100), nullable=False, default="image/jpeg")

    category = relationship("Category", back_populates="items")
    loans = relationship("Loan", back_populates="item")

    @property
    def has_photo(self) -> bool:
        return bool(self.photo_data)
