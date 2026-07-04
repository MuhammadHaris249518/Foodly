"""
Promote a user to admin. Run manually — never exposed via API,
since an API endpoint for self/other-promotion is itself a privilege
escalation risk.

Usage:
    python scripts/promote_admin.py someone@example.com
"""
import sys
import os
import argparse

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from app.core.database import SessionLocal
from app.models.user import User


def promote(email: str) -> None:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"No user found with email: {email}")
            return
        if user.role == "admin":
            print(f"{email} is already an admin.")
            return
        user.role = "admin"
        db.add(user)
        db.commit()
        print(f"{email} promoted to admin.")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Promote a user to admin role.")
    parser.add_argument("email", help="Email of the user to promote")
    args = parser.parse_args()
    promote(args.email)