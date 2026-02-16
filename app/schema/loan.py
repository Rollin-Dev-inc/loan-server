from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LoanBase(BaseModel):
    borrower_name: str = Field(min_length=1, max_length=120)
    item_id: int
    item_code: str | None = Field(default=None, min_length=3, max_length=40)
    duration_days: int = Field(ge=1)
    borrowed_at: date
    price_to_pay: float = Field(ge=0)

    @field_validator("item_code")
    @classmethod
    def normalize_item_code(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return value.strip().upper()


class LoanCreate(LoanBase):
    is_returned: bool = False


class LoanUpdate(BaseModel):
    borrower_name: str | None = Field(default=None, min_length=1, max_length=120)
    item_id: int | None = None
    item_code: str | None = Field(default=None, min_length=3, max_length=40)
    duration_days: int | None = Field(default=None, ge=1)
    borrowed_at: date | None = None
    price_to_pay: float | None = Field(default=None, ge=0)
    is_returned: bool | None = None

    @field_validator("item_code")
    @classmethod
    def normalize_update_item_code(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return value.strip().upper()


class LoanReturnConfirmation(BaseModel):
    is_returned: bool


class LoanRead(BaseModel):
    id: int
    borrower_name: str
    item_id: int
    item_code: str
    duration_days: int
    borrowed_at: date
    due_at: date
    price_to_pay: float
    is_returned: bool
    returned_at: datetime | None
    is_overdue: bool

    model_config = ConfigDict(from_attributes=True)


class LoanNotificationRead(BaseModel):
    loan_id: int
    borrower_name: str
    item_id: int
    item_code: str
    due_at: date
    days_overdue: int
    message: str
