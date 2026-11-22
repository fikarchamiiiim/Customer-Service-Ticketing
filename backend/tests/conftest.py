"""Fixture test.

Strategi:
  1. Database TERPISAH (ticketing_test) — tidak pernah menyentuh data dev.
  2. Skema dibuat lewat ALEMBIC (bukan create_all) — supaya migrasi ikut teruji.
  3. Tiap test dibungkus transaksi yang DI-ROLLBACK — test tidak saling mengotori.

Catatan scope: semua fixture ber-scope "function" supaya event loop-nya selalu
sama dengan test. Persiapan database yang mahal dijalankan sekali lewat flag
modul _prepared.
"""

import asyncio
import os
import subprocess
from pathlib import Path

import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.db.session import get_db

TEST_DB = "ticketing_test"
BACKEND_DIR = Path(__file__).resolve().parent.parent

BASE_URL = settings.database_url.rsplit("/", 1)[0]
TEST_URL = f"{BASE_URL}/{TEST_DB}"
ADMIN_URL = f"{BASE_URL}/postgres"

_prepared = False


def _run_alembic(*args: str) -> None:
    """Jalankan alembic di subprocess dengan DATABASE_URL menunjuk ke DB test."""
    env = {**os.environ, "DATABASE_URL": TEST_URL}
    subprocess.run(
        [str(BACKEND_DIR / ".venv" / "bin" / "alembic"), *args],
        cwd=BACKEND_DIR,
        env=env,
        check=True,
        capture_output=True,
    )


async def _prepare_database() -> None:
    """Buat database test kosong + jalankan semua migrasi. Sekali per sesi pytest."""
    admin = create_async_engine(ADMIN_URL, isolation_level="AUTOCOMMIT")
    async with admin.connect() as conn:
        exists = await conn.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": TEST_DB}
        )
        if exists:
            await conn.execute(text(f'DROP DATABASE "{TEST_DB}" WITH (FORCE)'))
        await conn.execute(text(f'CREATE DATABASE "{TEST_DB}"'))
    await admin.dispose()

    await asyncio.to_thread(_run_alembic, "upgrade", "head")


class _DbHandle:
    """Sesi + data seed yang siap dipakai test."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.agent_email = "agent1@example.com"
        self.customer_email = "customer1@example.com"


@pytest_asyncio.fixture
async def db() -> AsyncSession:
    """Sesi yang selalu di-rollback di akhir test."""
    global _prepared
    if not _prepared:
        await _prepare_database()
        _prepared = True

    engine = create_async_engine(TEST_URL)
    connection = await engine.connect()
    transaction = await connection.begin()

    maker = async_sessionmaker(bind=connection, class_=AsyncSession, expire_on_commit=False)
    session = maker()

    try:
        yield session
    finally:
        await session.close()
        await transaction.rollback()
        await connection.close()
        await engine.dispose()


@pytest_asyncio.fixture
async def db_override(db):
    """Timpa dependency get_db supaya HTTP test memakai transaksi yang sama.

    Dengan begitu data yang dibuat lewat request API langsung terlihat oleh test,
    dan semuanya tetap di-rollback di akhir.
    """
    from app.main import app

    async def _get_db_override():
        yield db

    app.dependency_overrides[get_db] = _get_db_override
    try:
        yield db
    finally:
        app.dependency_overrides.pop(get_db, None)



@pytest_asyncio.fixture
async def client(db_override):
    """HTTP client yang memakai sesi DB test (semua perubahan di-rollback)."""
    import httpx

    from app.main import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def login(client):
    """Helper: login via dev-login dan kembalikan user JSON-nya.

    Cookie disimpan DI CLIENT, jadi client yang sama mewakili satu user.
    Untuk dua user sekaligus, buat dua client (lihat fixture client2).
    """

    async def _login(email: str) -> dict:
        resp = await client.post("/api/v1/auth/dev-login", json={"email": email})
        assert resp.status_code == 200, resp.text
        return resp.json()

    return _login
