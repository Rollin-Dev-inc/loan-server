import argparse
import getpass

from sqlalchemy import select

from app.core.security import get_password_hash
from app.database import SessionLocal, init_db
from app.models import User


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create backend user account")
    parser.add_argument("--username", help="Username for login. If omitted, prompt will be shown.")
    parser.add_argument("--password", help="User password. If omitted, prompt will be shown.")
    parser.add_argument("--full-name", default=None, help="Optional full name")
    parser.add_argument("--inactive", action="store_true", help="Create user as inactive")
    return parser.parse_args()


def _prompt_username() -> str:
    while True:
        username = input("Username: ").strip()
        if len(username) < 3:
            print("Username must be at least 3 characters")
            continue
        return username


def _prompt_password() -> str:
    while True:
        password = getpass.getpass("Password: ")
        if len(password) < 6:
            print("Password must be at least 6 characters")
            continue
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("Password confirmation does not match")
            continue
        return password


def main() -> None:
    args = _parse_args()
    username = args.username.strip() if args.username else _prompt_username()
    if len(username) < 3:
        raise ValueError("Username must be at least 3 characters")

    if args.password:
        password = args.password
        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters")
    else:
        password = _prompt_password()

    init_db()
    with SessionLocal() as db:
        existing = db.scalar(select(User).where(User.username == username))
        if existing is not None:
            raise ValueError(f"Username '{username}' already exists")

        user = User(
            username=username,
            full_name=args.full_name,
            hashed_password=get_password_hash(password),
            is_active=not args.inactive,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"User created: id={user.id}, username={user.username}, active={user.is_active}")


if __name__ == "__main__":
    main()
