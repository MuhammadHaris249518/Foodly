"""
Rate limiting key strategy: prefer authenticated user identity over IP.

Why: pure IP-based limiting is bypassed by shared IPs undercounting distinct
users (false positives on campus/office WiFi) and is trivially evaded by
switching networks while logged in. Keying on the JWT `sub` claim when present
gives accurate per-user limits; anonymous requests (e.g. pre-login) fall back
to IP, which is the only identity available for them.
"""
from fastapi import Request
from jose import jwt, JWTError
from slowapi import Limiter
from slowapi.util import get_remote_address
from ..core.config import settings


def get_rate_limit_key(request: Request) -> str:
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[len("Bearer "):]
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            sub = payload.get("sub")
            if sub:
                return f"user:{sub}"
        except JWTError:
            pass  # invalid/expired token falls through to IP-based key
    return f"ip:{get_remote_address(request)}"


# Global default (100/min) applies to any route without an explicit @limiter.limit(...)
limiter = Limiter(key_func=get_rate_limit_key, default_limits=["100/minute"])