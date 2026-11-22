import logging

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.core import User
from app.models.enums import UserRole

logger = logging.getLogger(__name__)


class AuthError(Exception):
    """Error autentikasi yang aman ditampilkan ke client."""

    def __init__(self, code: str, message: str, status: int = 401):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


def verify_google_token(raw_token: str) -> dict:
    """Verifikasi ID token Google.

    verify_oauth2_token() sudah mengecek:
      - tanda tangan Google
      - audience == client_id kita
      - exp / iat
    Kita tinggal menambah pengecekan email_verified.
    """
    if not settings.google_client_id:
        raise AuthError(
            "GOOGLE_NOT_CONFIGURED",
            "GOOGLE_CLIENT_ID belum diisi di .env",
            status=500,
        )

    try:
        claims = google_id_token.verify_oauth2_token(
            raw_token,
            google_requests.Request(),
            settings.google_client_id,
        )
    except ValueError as exc:
        logger.warning("google token ditolak: %s", exc)
        raise AuthError("INVALID_GOOGLE_TOKEN", "ID token Google tidak valid") from exc

    if not claims.get("email_verified", False):
        raise AuthError("EMAIL_NOT_VERIFIED", "Email Google belum terverifikasi")

    if not claims.get("email"):
        raise AuthError("EMAIL_MISSING", "Google tidak mengirimkan email")

    return claims


async def get_or_create_user(
    db: AsyncSession,
    *,
    email: str,
    name: str,
    avatar_url: str | None = None,
    google_sub: str | None = None,
    sync_profile: bool = True,
) -> User:
    """Cari user berdasarkan google_sub, lalu email. Buat baru kalau belum ada.

    Role awal ditentukan oleh ALLOWLIST email (AGENT_EMAILS di .env), BUKAN oleh
    apa pun yang dikirim client. Client tidak pernah boleh memilih role sendiri.
    """
    email = email.strip().lower()

    user = None
    if google_sub:
        user = await db.scalar(select(User).where(User.google_sub == google_sub))
    if user is None:
        user = await db.scalar(select(User).where(User.email == email))

    if user is not None:
        if not sync_profile:
            # dev-login: jangan sentuh profil. Nama seed ("Agent Satu") harus bertahan.
            return user
        # Sinkronkan profil ringan, dan simpan google_sub saat login Google pertama.
        if google_sub and user.google_sub is None:
            user.google_sub = google_sub
        if user.name != name:
            user.name = name
        if avatar_url and user.avatar_url != avatar_url:
            user.avatar_url = avatar_url
        return user

    role = UserRole.agent if email in settings.agent_email_set else UserRole.customer
    user = User(
        email=email,
        name=name,
        avatar_url=avatar_url,
        role=role,
        google_sub=google_sub,
    )
    db.add(user)
    await db.flush()
    logger.info("user baru: %s (role=%s)", user.email, user.role.value)
    return user
