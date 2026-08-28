import argparse
import getpass

from app.db import SessionLocal
from app.domain.user import User, hash_password


def create_user(email: str, password: str) -> None:
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing is not None:
            raise SystemExit(f"User already exists: {email}")
        user = User(email=email, password_hash=hash_password(password))
        db.add(user)
        db.commit()
        print(f"Created user {email}")
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a cozy-bookmarks user")
    parser.add_argument("--email", required=True)
    args = parser.parse_args()

    password = getpass.getpass("Password: ")
    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        raise SystemExit("Passwords do not match")

    create_user(args.email, password)


if __name__ == "__main__":
    main()
