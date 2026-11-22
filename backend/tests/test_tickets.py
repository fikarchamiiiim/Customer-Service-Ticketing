"""Test tiket: state machine, RBAC scoping, internal note, pagination."""

import httpx
import pytest

from app.models.core import User
from app.models.enums import TicketStatus
from app.services.tickets import ALLOWED, can_transition


FIRST_MSG = "Deskripsi pertama"


async def _new_client(db_override):
    """Client HTTP terpisah = user terpisah (cookie terpisah)."""
    from app.main import app

    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://test")


async def _login(client, email: str) -> dict:
    resp = await client.post("/api/v1/auth/dev-login", json={"email": email})
    assert resp.status_code == 200, resp.text
    return resp.json()


async def _create_ticket(client, subject="Printer macet", priority="normal") -> dict:
    resp = await client.post(
        "/api/v1/tickets",
        json={"subject": subject, "description": FIRST_MSG, "priority": priority},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


# ==========================================================================
# State machine (fungsi murni, tanpa DB, tanpa HTTP)
# ==========================================================================

@pytest.mark.parametrize(
    "src,dst,expected",
    [
        (TicketStatus.open, TicketStatus.in_progress, True),
        (TicketStatus.open, TicketStatus.closed, True),
        (TicketStatus.open, TicketStatus.resolved, False),
        (TicketStatus.in_progress, TicketStatus.resolved, True),
        (TicketStatus.in_progress, TicketStatus.closed, True),
        (TicketStatus.resolved, TicketStatus.closed, True),
        (TicketStatus.resolved, TicketStatus.in_progress, True),   # reopen
        (TicketStatus.closed, TicketStatus.in_progress, False),
        (TicketStatus.closed, TicketStatus.open, False),
        (TicketStatus.open, TicketStatus.open, True),              # no-op
    ],
)
def test_state_machine(src, dst, expected):
    assert can_transition(src, dst) is expected


def test_every_status_is_covered():
    """Kalau ada status baru ditambahkan, test ini gagal -> paksa update ALLOWED."""
    assert set(ALLOWED) == set(TicketStatus)


# ==========================================================================
# Create & read
# ==========================================================================

async def test_create_ticket(client, db_override):
    await _login(client, "customer1@example.com")
    ticket = await _create_ticket(client)

    assert ticket["ticket_no"].startswith("TKT-")
    assert ticket["ticket_no"] == f"TKT-{int(ticket['ticket_no'][4:]):06d}"
    assert ticket["status"] == "open"
    assert ticket["priority"] == "normal"
    assert ticket["customer"]["email"] == "customer1@example.com"
    assert ticket["assignee"] is None
    assert ticket["message_count"] == 1


async def test_description_becomes_first_message(client, db_override):
    await _login(client, "customer1@example.com")
    ticket = await _create_ticket(client)

    resp = await client.get(f"/api/v1/tickets/{ticket['id']}/messages")
    messages = resp.json()["items"]
    assert len(messages) == 1
    assert messages[0]["body"] == FIRST_MSG
    assert messages[0]["is_internal"] is False


async def test_validation_rejects_short_subject(client, db_override):
    await _login(client, "customer1@example.com")
    resp = await client.post(
        "/api/v1/tickets", json={"subject": "ab", "description": "x"}
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


# ==========================================================================
# RBAC scoping
# ==========================================================================

async def test_other_customer_gets_404_not_403(client, db_override):
    """404, bukan 403: keberadaan tiket orang lain tidak boleh bocor."""
    await _login(client, "customer1@example.com")
    ticket = await _create_ticket(client)

    other = await _new_client(db_override)
    async with other:
        await _login(other, "customer2@example.com")
        resp = await other.get(f"/api/v1/tickets/{ticket['id']}")
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "NOT_FOUND"


async def test_agent_can_read_any_ticket(client, db_override):
    await _login(client, "customer1@example.com")
    ticket = await _create_ticket(client)

    agent = await _new_client(db_override)
    async with agent:
        await _login(agent, "agent1@example.com")
        resp = await agent.get(f"/api/v1/tickets/{ticket['id']}")
        assert resp.status_code == 200
        assert resp.json()["ticket_no"] == ticket["ticket_no"]


async def test_customer_list_only_own_tickets(client, db_override):
    await _login(client, "customer1@example.com")
    await _create_ticket(client, subject="Tiket saya")

    other = await _new_client(db_override)
    async with other:
        await _login(other, "customer2@example.com")
        await _create_ticket(other, subject="Tiket orang lain")

        resp = await other.get("/api/v1/tickets")
        items = resp.json()["items"]
        assert len(items) == 1
        assert items[0]["subject"] == "Tiket orang lain"


async def test_customer_cannot_use_scope_all(client, db_override):
    await _login(client, "customer1@example.com")
    resp = await client.get("/api/v1/tickets?scope=all")
    assert resp.status_code == 403


async def test_agent_can_filter_unassigned(client, db_override):
    await _login(client, "customer1@example.com")
    await _create_ticket(client)

    agent = await _new_client(db_override)
    async with agent:
        await _login(agent, "agent1@example.com")
        resp = await agent.get("/api/v1/tickets?scope=all&assignee=unassigned")
        assert resp.status_code == 200
        assert all(t["assignee"] is None for t in resp.json()["items"])


# ==========================================================================
# Update / state machine lewat HTTP
# ==========================================================================

async def test_illegal_transition_returns_422(client, db_override):
    await _login(client, "customer1@example.com")
    ticket = await _create_ticket(client)

    agent = await _new_client(db_override)
    async with agent:
        await _login(agent, "agent1@example.com")
        resp = await agent.patch(
            f"/api/v1/tickets/{ticket['id']}", json={"status": "resolved"}
        )
        assert resp.status_code == 422
        body = resp.json()
        assert body["error"]["code"] == "ILLEGAL_TRANSITION"
        assert sorted(body["error"]["details"]["allowed"]) == ["closed", "in_progress"]


async def test_agent_full_lifecycle(client, db_override):
    await _login(client, "customer1@example.com")
    ticket = await _create_ticket(client)

    agent = await _new_client(db_override)
    async with agent:
        me = await _login(agent, "agent1@example.com")

        r = await agent.patch(
            f"/api/v1/tickets/{ticket['id']}",
            json={"status": "in_progress", "assignee_id": me["id"]},
        )
        assert r.status_code == 200
        assert r.json()["status"] == "in_progress"
        assert r.json()["assignee"]["email"] == "agent1@example.com"

        r = await agent.patch(f"/api/v1/tickets/{ticket['id']}", json={"status": "resolved"})
        assert r.json()["status"] == "resolved"

        r = await agent.patch(f"/api/v1/tickets/{ticket['id']}", json={"status": "closed"})
        assert r.json()["status"] == "closed"


async def test_customer_can_close_own_ticket(client, db_override):
    await _login(client, "customer1@example.com")
    ticket = await _create_ticket(client)

    resp = await client.patch(f"/api/v1/tickets/{ticket['id']}", json={"status": "closed"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "closed"


async def test_customer_cannot_set_in_progress(client, db_override):
    await _login(client, "customer1@example.com")
    ticket = await _create_ticket(client)

    resp = await client.patch(
        f"/api/v1/tickets/{ticket['id']}", json={"status": "in_progress"}
    )
    assert resp.status_code == 403


async def test_customer_cannot_change_priority_or_assign(client, db_override):
    await _login(client, "customer1@example.com")
    ticket = await _create_ticket(client)

    r1 = await client.patch(f"/api/v1/tickets/{ticket['id']}", json={"priority": "high"})
    assert r1.status_code == 403

    r2 = await client.patch(f"/api/v1/tickets/{ticket['id']}", json={"assignee_id": 1})
    assert r2.status_code == 403


async def test_assign_to_non_agent_is_422(client, db_override):
    await _login(client, "customer1@example.com")
    ticket = await _create_ticket(client)

    agent = await _new_client(db_override)
    async with agent:
        await _login(agent, "agent1@example.com")

        # id customer ada di response tiket (relasi customer sudah di-eager-load)
        cust_id = ticket["customer"]["id"]
        resp = await agent.patch(
            f"/api/v1/tickets/{ticket['id']}", json={"assignee_id": cust_id}
        )
        assert resp.status_code == 422
        assert resp.json()["error"]["code"] == "INVALID_ASSIGNEE"


# ==========================================================================
# Pesan & internal note
# ==========================================================================

async def test_customer_cannot_write_internal_note(client, db_override):
    await _login(client, "customer1@example.com")
    ticket = await _create_ticket(client)

    resp = await client.post(
        f"/api/v1/tickets/{ticket['id']}/messages",
        json={"body": "rahasia", "is_internal": True},
    )
    assert resp.status_code == 403


async def test_internal_note_hidden_from_customer(client, db_override):
    await _login(client, "customer1@example.com")
    ticket = await _create_ticket(client)

    agent = await _new_client(db_override)
    async with agent:
        await _login(agent, "agent1@example.com")
        r = await agent.post(
            f"/api/v1/tickets/{ticket['id']}/messages",
            json={"body": "catatan internal", "is_internal": True},
        )
        assert r.status_code == 201

        # agent melihat 2 pesan (deskripsi + internal)
        r = await agent.get(f"/api/v1/tickets/{ticket['id']}/messages")
        assert len(r.json()["items"]) == 2

    # customer hanya melihat 1 (deskripsi)
    r = await client.get(f"/api/v1/tickets/{ticket['id']}/messages")
    items = r.json()["items"]
    assert len(items) == 1
    assert all(m["is_internal"] is False for m in items)


async def test_customer_cannot_post_to_others_ticket(client, db_override):
    await _login(client, "customer1@example.com")
    ticket = await _create_ticket(client)

    other = await _new_client(db_override)
    async with other:
        await _login(other, "customer2@example.com")
        resp = await other.post(
            f"/api/v1/tickets/{ticket['id']}/messages", json={"body": "menyusup"}
        )
        assert resp.status_code == 404


async def test_message_on_closed_ticket_is_409(client, db_override):
    await _login(client, "customer1@example.com")
    ticket = await _create_ticket(client)
    await client.patch(f"/api/v1/tickets/{ticket['id']}", json={"status": "closed"})

    resp = await client.post(
        f"/api/v1/tickets/{ticket['id']}/messages", json={"body": "halo?"}
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "TICKET_CLOSED"


async def test_customer_reply_reopens_resolved_ticket(client, db_override):
    await _login(client, "customer1@example.com")
    ticket = await _create_ticket(client)

    agent = await _new_client(db_override)
    async with agent:
        await _login(agent, "agent1@example.com")
        await agent.patch(f"/api/v1/tickets/{ticket['id']}", json={"status": "in_progress"})
        await agent.patch(f"/api/v1/tickets/{ticket['id']}", json={"status": "resolved"})

    await client.post(f"/api/v1/tickets/{ticket['id']}/messages", json={"body": "masih error"})

    resp = await client.get(f"/api/v1/tickets/{ticket['id']}")
    assert resp.json()["status"] == "in_progress"


async def test_internal_note_does_not_reopen_ticket(client, db_override):
    await _login(client, "customer1@example.com")
    ticket = await _create_ticket(client)

    agent = await _new_client(db_override)
    async with agent:
        await _login(agent, "agent1@example.com")
        await agent.patch(f"/api/v1/tickets/{ticket['id']}", json={"status": "in_progress"})
        await agent.patch(f"/api/v1/tickets/{ticket['id']}", json={"status": "resolved"})
        await agent.post(
            f"/api/v1/tickets/{ticket['id']}/messages",
            json={"body": "catatan", "is_internal": True},
        )

    resp = await client.get(f"/api/v1/tickets/{ticket['id']}")
    assert resp.json()["status"] == "resolved"


# ==========================================================================
# Pagination
# ==========================================================================

async def test_message_pagination_is_chronological(client, db_override):
    await _login(client, "customer1@example.com")
    ticket = await _create_ticket(client)

    for i in range(5):
        r = await client.post(
            f"/api/v1/tickets/{ticket['id']}/messages", json={"body": f"pesan {i}"}
        )
        assert r.status_code == 201

    page1 = (
        await client.get(f"/api/v1/tickets/{ticket['id']}/messages?limit=3")
    ).json()
    assert len(page1["items"]) == 3
    assert page1["next_cursor"] is not None
    # 6 pesan total (deskripsi + pesan 0..4).
    # Halaman pertama = 3 TERBARU, tapi tetap ditampilkan kronologis (lama -> baru).
    assert [m["body"] for m in page1["items"]] == ["pesan 2", "pesan 3", "pesan 4"]

    page2 = (
        await client.get(
            f"/api/v1/tickets/{ticket['id']}/messages?limit=3&before_id={page1['next_cursor']}"
        )
    ).json()
    assert [m["body"] for m in page2["items"]] == [FIRST_MSG, "pesan 0", "pesan 1"]
    assert page2["next_cursor"] is None


async def test_ticket_pagination(client, db_override):
    await _login(client, "customer1@example.com")
    for i in range(5):
        await _create_ticket(client, subject=f"Tiket {i}")

    page1 = (await client.get("/api/v1/tickets?limit=2")).json()
    assert len(page1["items"]) == 2
    assert page1["next_cursor"] is not None

    page2 = (
        await client.get(f"/api/v1/tickets?limit=2&cursor={page1['next_cursor']}")
    ).json()
    assert len(page2["items"]) == 2
    ids1 = {t["id"] for t in page1["items"]}
    ids2 = {t["id"] for t in page2["items"]}
    assert ids1.isdisjoint(ids2)
