import logging

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db
from app.deps import get_current_user, unauthorized
from app.models.core import User
from app.schemas.auth import DevLoginIn, GoogleLoginIn, UserOut
from app.security import SESSION_DAYS, create_session_token
from app.services.auth import AuthError, get_or_create_user, verify_google_token

logger = logging.getLogger(__name__)
router = APIRouter(tags=["auth"])


def set_session_cookie(response: Response, user_id: int) -> None:
    """Set cookie sesi.

    HttpOnly     : JavaScript tidak bisa membaca -> aman dari XSS
    SameSite=Lax : terkirim saat navigasi biasa, dan saat handshake WebSocket
    Path=/       : berlaku untuk seluruh aplikasi
    Secure       : hanya kalau https (dev pakai http, jadi dimatikan lewat .env)
    """
    response.set_cookie(
        key=settings.session_cookie_name,
        value=create_session_token(user_id),
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        max_age=SESSION_DAYS * 24 * 3600,
        path="/",
    )


@router.post("/auth/google", response_model=UserOut)
async def login_google(
    payload: GoogleLoginIn,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        claims = verify_google_token(payload.id_token)
    except AuthError as exc:
        raise HTTPException(
            status_code=exc.status,
            detail={"code": exc.code, "message": exc.message},
        ) from exc

    user = await get_or_create_user(
        db,
        email=claims["email"],
        name=claims.get("name") or claims["email"].split("@")[0],
        avatar_url=claims.get("picture"),
        google_sub=claims.get("sub"),
    )
    await db.commit()
    await db.refresh(user)

    set_session_cookie(response, user.id)
    logger.info("login google: %s", user.email)
    return user


@router.post("/auth/dev-login", response_model=UserOut)
async def login_dev(
    payload: DevLoginIn,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Login tanpa Google. HANYA aktif kalau DEV_AUTH=true.

    Kalau DEV_AUTH=false, endpoint ini menjawab 404 — seolah tidak ada.
    Ini jaring pengaman supaya setup Google Console tidak memblokir belajar.
    """
    if not settings.dev_auth:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Not Found"})

    email = str(payload.email).lower()
    user = await get_or_create_user(
        db, email=email, name=email.split("@")[0], sync_profile=False
    )
    await db.commit()
    await db.refresh(user)

    set_session_cookie(response, user.id)
    logger.info("login dev: %s", user.email)
    return user


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    user: User = Depends(get_current_user),
) -> Response:
    response.delete_cookie(
        key=settings.session_cookie_name,
        path="/",
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
    )
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
