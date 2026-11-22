"""Dependency bersama: sesi DB, user aktif, dan pengecekan role."""

from collections.abc import Callable, Coroutine
from typing import Any

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db
from app.models.core import User
from app.models.enums import UserRole
from app.security import decode_session_token


def unauthorized(message: str = "Belum login") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"code": "UNAUTHORIZED", "message": message},
    )


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Baca cookie sesi -> decode -> ambil user.

    Cookie dibaca lewat 'request.cookies' (bukan header Authorization) karena:
      - browser mengirimnya otomatis, termasuk saat handshake WebSocket
      - JavaScript tidak bisa membacanya (httpOnly) -> aman dari XSS
    """
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        raise unauthorized()

    user_id = decode_session_token(token)
    if user_id is None:
        raise unauthorized("Sesi tidak valid atau kadaluarsa")

    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise unauthorized("Akun tidak ditemukan atau nonaktif")

    return user


def require_role(*roles: UserRole) -> Callable[..., Coroutine[Any, Any, User]]:
    """Dependency factory: hanya role tertentu yang boleh lewat.

    Dipakai seperti:  Depends(require_role(UserRole.agent, UserRole.admin))
    """

    async def _guard(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "FORBIDDEN",
                    "message": f"Butuh role: {', '.join(r.value for r in roles)}",
                },
            )
        return user

    return _guard
