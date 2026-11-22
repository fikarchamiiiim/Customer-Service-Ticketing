"""Test autentikasi: token, cookie, RBAC, dan perilaku dev-login."""

import httpx
import pytest

from app.config import settings
from app.main import app
from app.models.core import User
from app.models.enums import UserRole
from app.security import create_session_token, decode_session_token


# --------------------------------------------------------------------------
# Unit test murni (tanpa DB, tanpa HTTP)
# --------------------------------------------------------------------------

def test_session_token_roundtrip():
    token = create_session_token(42)
    assert decode_session_token(token) == 42


def test_session_token_rejects_garbage():
    assert decode_session_token("bukan-token") is None
    assert decode_session_token("") is None


def test_session_token_rejects_wrong_secret(monkeypatch):
    import jwt
    from datetime import datetime, timedelta, timezone

    forged = jwt.encode(
        {
            "sub": "1",
            "exp": int((datetime.now(timezone.utc) + timedelta(days=1)).timestamp()),
        },
        "secret-yang-salah",
        algorithm="HS256",
    )
    assert decode_session_token(forged) is None


def test_session_token_rejects_expired(monkeypatch):
    import jwt
    from datetime import datetime, timedelta, timezone

    expired = jwt.encode(
        {
            "sub": "1",
            "exp": int((datetime.now(timezone.utc) - timedelta(minutes=1)).timestamp()),
        },
        settings.jwt_secret,
        algorithm="HS256",
    )
    assert decode_session_token(expired) is None


# --------------------------------------------------------------------------
# Test lewat HTTP (ASGI transport -> tanpa server nyata)
# --------------------------------------------------------------------------

@pytest.fixture
def client(db_override):
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://test")


async def test_me_without_cookie_returns_401(client):
    resp = await client.get("/api/v1/me")
    assert resp.status_code == 401
    body = resp.json()
    assert body["error"]["code"] == "UNAUTHORIZED"


async def test_me_with_invalid_cookie_returns_401(client):
    client.cookies.set(settings.session_cookie_name, "token-palsu")
    resp = await client.get("/api/v1/me")
    assert resp.status_code == 401


async def test_dev_login_sets_httponly_cookie(client):
    resp = await client.post(
        "/api/v1/auth/dev-login", json={"email": "agent1@example.com"}
    )
    assert resp.status_code == 200

    body = resp.json()
    assert body["email"] == "agent1@example.com"
    assert body["role"] == "agent"
    assert "id_token" not in body and "token" not in body

    set_cookie = resp.headers["set-cookie"]
    assert "HttpOnly" in set_cookie
    assert "SameSite=lax" in set_cookie.replace("samesite", "SameSite").replace("LAX", "lax")
    assert "Path=/" in set_cookie


async def test_dev_login_then_me(client):
    await client.post("/api/v1/auth/dev-login", json={"email": "customer1@example.com"})
    resp = await client.get("/api/v1/me")
    assert resp.status_code == 200
    assert resp.json()["role"] == "customer"


async def test_role_from_allowlist_not_from_client(client):
    """Client TIDAK bisa memilih role. Role datang dari AGENT_EMAILS di server."""
    resp = await client.post(
        "/api/v1/auth/dev-login", json={"email": "bukan-agent@example.com"}
    )
    assert resp.json()["role"] == "customer"

    resp2 = await client.post("/api/v1/auth/dev-login", json={"email": "agent2@example.com"})
    assert resp2.json()["role"] == "agent"


async def test_require_role_blocks_customer(client):
    await client.post("/api/v1/auth/dev-login", json={"email": "customer1@example.com"})
    resp = await client.get("/api/v1/dev/agent-only")
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "FORBIDDEN"


async def test_require_role_allows_agent(client):
    await client.post("/api/v1/auth/dev-login", json={"email": "agent1@example.com"})
    resp = await client.get("/api/v1/dev/agent-only")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


async def test_logout_clears_cookie(client):
    await client.post("/api/v1/auth/dev-login", json={"email": "agent1@example.com"})
    assert (await client.get("/api/v1/me")).status_code == 200

    resp = await client.post("/api/v1/auth/logout")
    assert resp.status_code == 204
    client.cookies.clear()  # browser akan menghapusnya lewat Set-Cookie kedaluwarsa

    assert (await client.get("/api/v1/me")).status_code == 401


async def test_dev_login_disabled_when_dev_auth_false(client, monkeypatch):
    monkeypatch.setattr(settings, "dev_auth", False)
    resp = await client.post("/api/v1/auth/dev-login", json={"email": "agent1@example.com"})
    assert resp.status_code == 404


async def test_google_login_without_client_id_returns_500(client):
    resp = await client.post("/api/v1/auth/google", json={"id_token": "x" * 30})
    assert resp.status_code == 500
    assert resp.json()["error"]["code"] == "GOOGLE_NOT_CONFIGURED"


async def test_google_login_with_bogus_token(client, monkeypatch):
    monkeypatch.setattr(settings, "google_client_id", "test-client-id.apps.googleusercontent.com")
    resp = await client.post("/api/v1/auth/google", json={"id_token": "a" * 40})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "INVALID_GOOGLE_TOKEN"



# --------------------------------------------------------------------------
# Regresi: bug yang pernah terjadi (Step 2)
# --------------------------------------------------------------------------

async def test_dev_login_does_not_overwrite_seeded_name(client, db_override):
    """dev-login TIDAK boleh menimpa profil user yang sudah ada.

    Bug nyata: login dev sebagai agent1@example.com mengubah nama "Agent Satu"
    menjadi "agent1", karena sinkronisasi profil dipakai di semua jalur login.
    Sinkronisasi profil hanya boleh terjadi pada login Google.
    """
    from sqlalchemy import select

    from app.models.core import User
    from app.models.enums import UserRole

    # User sudah ada dengan profil lengkap (meniru kondisi setelah seed).
    db_override.add(
        User(
            email="existing@example.com",
            name="Nama Asli",
            role=UserRole.customer,
        )
    )
    await db_override.flush()

    resp = await client.post("/api/v1/auth/dev-login", json={"email": "existing@example.com"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Nama Asli"

    user = await db_override.scalar(select(User).where(User.email == "existing@example.com"))
    await db_override.refresh(user)
    assert user.name == "Nama Asli"


async def test_new_user_via_dev_login_gets_customer_role(client, db_override):
    resp = await client.post("/api/v1/auth/dev-login", json={"email": "baru@example.com"})
    assert resp.status_code == 200
    assert resp.json()["role"] == "customer"
    # UserOut tidak pernah memuat google_sub / token apa pun
    assert "google_sub" not in resp.json()
