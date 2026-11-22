from fastapi import APIRouter, Depends

from app.config import settings
from app.deps import require_role
from app.models.core import User
from app.models.enums import UserRole

router = APIRouter(tags=["dev"])


@router.get("/dev/config")
async def dev_config():
    """Info publik untuk FE: apakah dev-login tersedia, dan apakah Google aktif.

    Tidak membocorkan rahasia apa pun — hanya dua boolean.
    """
    return {
        "dev_auth": settings.dev_auth,
        "google_enabled": bool(settings.google_client_id),
        "session_cookie": settings.session_cookie_name,
    }


@router.get("/dev/agent-only")
async def agent_only(user: User = Depends(require_role(UserRole.agent, UserRole.admin))):
    """Contoh endpoint yang butuh role agent — dipakai untuk menguji require_role."""
    return {"ok": True, "user": user.email, "role": user.role.value}
