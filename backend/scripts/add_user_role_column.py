"""
Additive migration: adds `role` column to `users` for the admin-auth redesign.
Safe to re-run (IF NOT EXISTS). Does not touch existing data.
"""
import sys
import os
from sqlalchemy import text

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from app.core.database import engine


def add_role_column() -> None:
    with engine.connect() as conn:
        conn.execute(text(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR NOT NULL DEFAULT 'user';"
        ))
        conn.commit()
    print("Migration complete: users.role column ensured (default 'user').")


if __name__ == "__main__":
    add_role_column()