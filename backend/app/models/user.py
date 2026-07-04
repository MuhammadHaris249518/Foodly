from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from ..core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    location = Column(String, nullable=True)
    # 'user' | 'admin'. Never settable from the public register endpoint —
    # only changed via direct DB access or scripts/promote_admin.py.
    role = Column(String, default="user", nullable=False, server_default="user")
    created_at = Column(DateTime(timezone=True), server_default=func.now())