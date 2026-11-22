from fastapi import APIRouter

from app.config import settings
from app.db.session import check_db

router = APIRouter(tags=["system"])


@router.get("/health")
async def health():
    db_ok, db_error = await check_db()
    return {
        "status": "ok" if db_ok else "degraded",
        "db": "ok" if db_ok else "down",
        "db_error": db_error,
        "version": settings.app_version,
    }
