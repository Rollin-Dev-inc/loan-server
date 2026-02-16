from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DBSession
from app.core.security import create_access_token, verify_password
from app.models import User
from app.schema import LoginRequest, TokenRead, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenRead)
def login(payload: LoginRequest, db: DBSession) -> TokenRead:
    user = db.scalar(select(User).where(User.username == payload.username))
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive",
        )

    return TokenRead(access_token=create_access_token(subject=user.username))


@router.get("/me", response_model=UserRead)
def get_me(current_user: CurrentUser) -> User:
    return current_user
