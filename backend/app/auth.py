from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
import time
from typing import Callable, Deque, Dict, Optional

import bcrypt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import User

bearer_scheme = HTTPBearer(auto_error=False)


class AppError(HTTPException):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(
            status_code=status_code,
            detail={"code": code, "message": message},
        )


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )
    except Exception:
        return False


def hash_password(plain_password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")


def create_access_token(user_id: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except jwt.ExpiredSignatureError as exc:
        raise AppError(
            status.HTTP_401_UNAUTHORIZED,
            "TOKEN_EXPIRED",
            "Authentication token has expired.",
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise AppError(
            status.HTTP_401_UNAUTHORIZED,
            "INVALID_TOKEN",
            "Invalid authentication token.",
        ) from exc


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None or not credentials.credentials:
        raise AppError(
            status.HTTP_401_UNAUTHORIZED,
            "NOT_AUTHENTICATED",
            "Missing Bearer authentication token.",
        )
    payload = decode_access_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise AppError(status.HTTP_401_UNAUTHORIZED, "INVALID_TOKEN", "Missing token subject.")

    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if user is None:
        raise AppError(status.HTTP_401_UNAUTHORIZED, "USER_NOT_FOUND", "User no longer exists.")
    return user


def require_roles(*allowed_roles: str) -> Callable:
    async def _role_guard(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise AppError(
                status.HTTP_403_FORBIDDEN,
                "FORBIDDEN_ROLE",
                f"Role '{current_user.role}' is not permitted for this operation.",
            )
        return current_user

    return _role_guard


def resolve_target_user_id(
    current_user: User,
    requested_user_id: Optional[str],
    allow_flight_surgeon: bool = True,
) -> str:
    """
    Central IDOR guard:
    - ASTRONAUT may only access their own user_id.
    - CMO (and FLIGHT_SURGEON when allow_flight_surgeon=True) may access any crew user_id.
    """
    if requested_user_id is None or requested_user_id == current_user.id:
        return current_user.id

    allowed_elevated = {"CMO", "FLIGHT_SURGEON"} if allow_flight_surgeon else {"CMO"}
    if current_user.role not in allowed_elevated:
        raise AppError(
            status.HTTP_403_FORBIDDEN,
            "FORBIDDEN_OWNERSHIP",
            "Astronauts may only access or mutate their own medical records.",
        )
    return requested_user_id


class SlidingWindowRateLimiter:
    def __init__(self, max_requests: int, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)

    def check(self, key: str) -> None:
        now = time.monotonic()
        bucket = self._hits[key]
        while bucket and (now - bucket[0]) > self.window_seconds:
            bucket.popleft()
        if len(bucket) >= self.max_requests:
            raise AppError(
                status.HTTP_429_TOO_MANY_REQUESTS,
                "RATE_LIMIT_EXCEEDED",
                "Too many requests. Please wait before retrying.",
            )
        bucket.append(now)


login_rate_limiter = SlidingWindowRateLimiter(max_requests=10, window_seconds=60)
consultation_rate_limiter = SlidingWindowRateLimiter(max_requests=6, window_seconds=60)
