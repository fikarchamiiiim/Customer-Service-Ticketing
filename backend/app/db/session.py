import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

logger = logging.getLogger(__name__)

engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
)

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    """Dependency FastAPI: satu sesi per request."""
    async with SessionLocal() as session:
        yield session


async def check_db() -> tuple[bool, str | None]:
    """Cek koneksi ke Postgres. Dipakai endpoint /health."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True, None
    except Exception as exc:  # noqa: BLE001 - kita memang ingin semua error tertangkap
        logger.warning("db health check failed: %s", exc)
        return False, str(exc)
