"""Hash de contraseñas (Argon2) y tokens JWT."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from app.core.config import get_strict_settings

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    try:
        return _hasher.verify(hashed, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def create_token(user_id: int, token_type: str) -> str:
    s = get_strict_settings()
    now = datetime.now(timezone.utc)
    delta = (
        timedelta(minutes=s.access_token_minutes)
        if token_type == "access"
        else timedelta(days=s.refresh_token_days)
    )
    payload = {"sub": str(user_id), "type": token_type, "iat": now, "exp": now + delta, "jti": uuid.uuid4().hex}
    return jwt.encode(payload, s.jwt_secret, algorithm="HS256")


def decode_token(token: str, expected_type: str) -> int | None:
    """Devuelve el id de usuario o None si el token es inválido/expirado/de otro tipo."""
    s = get_strict_settings()
    try:
        data = jwt.decode(token, s.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None
    if data.get("type") != expected_type:
        return None
    try:
        return int(data["sub"])
    except (KeyError, ValueError):
        return None
