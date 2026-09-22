import argparse
import sys

from app.db import SessionLocal
from app.domain.user import User
from app.orchestration.daily_digest import (
    send_daily_digest_all,
    send_daily_digest_for_user,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Send daily digest email of new bookmarks")
    parser.add_argument("--email", help="Target a single user by email (default: all users)", default=None)
    args = parser.parse_args()

    db = SessionLocal()
    try:
        if args.email:
            user = db.query(User).filter(User.email == args.email.strip()).first()
            if not user:
                print(f"Error: user with email '{args.email}' not found.", file=sys.stderr)
                sys.exit(1)
            count = send_daily_digest_for_user(db, user)
            print(f"Sent digest to {user.email}: {count} bookmarks included.")
        else:
            results = send_daily_digest_all(db)
            total = sum(results.values())
            print(f"Daily digest completed. Processed {len(results)} users, delivered {total} bookmarks in total.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
