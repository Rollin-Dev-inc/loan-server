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
    photo_data: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    photo_content_type: Mapped[str | None] = mapped_column(String(100), nullable=True, default="image/jpeg")

    category = relationship("Category", back_populates="items")
    loans = relationship("Loan", back_populates="item")
    additional_photos = relationship("ItemPhoto", back_populates="item", cascade="all, delete-orphan")

    @property
    def has_photo(self) -> bool:
        return bool(self.photo_data) or bool(self.photo_url)
