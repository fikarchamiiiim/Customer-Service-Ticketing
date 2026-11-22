"""Session token: satu-satunya hal yang disimpan di cookie.

Sengaja SEDERHANA: JWT berisi user id + exp, ditandatangani HS256.
Tidak ada refresh token, tidak ada token di localStorage.
"""

from datetime import datetime, timedelta, timezone

import jwt

from app.config import settings

ALGORITHM = "HS256"
SESSION_DAYS = 7


def create_session_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=SESSION_DAYS)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_session_token(token: str) -> int | None:
    """Kembalikan user_id, atau None kalau token tidak valid/kadaluarsa.

    Kenapa None dan bukan raise: pemanggilnya berbeda-beda (route -> 401,
    WebSocket -> close 4401). Yang memutuskan apa yang dilakukan adalah pemanggil.
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None
    sub = payload.get("sub")
    try:
        return int(sub)
    except (TypeError, ValueError):
        return None
