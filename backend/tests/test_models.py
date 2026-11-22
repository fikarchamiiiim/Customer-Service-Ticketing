"""Test lapisan data: model, enum, sequence, constraint."""

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from app.models.core import User
from app.models.enums import TicketStatus, UserRole
from app.models.ticket import Ticket
from app.services.ticket_no import next_ticket_no


async def test_insert_user_and_read_back(db):
    user = User(email="uji@example.com", name="Uji", role=UserRole.customer)
    db.add(user)
    await db.flush()

    found = await db.scalar(select(User).where(User.email == "uji@example.com"))
    assert found is not None
    assert found.id == user.id
    # SQLAlchemy mengembalikan ENUM PYTHON, bukan string mentah
    assert found.role is UserRole.customer
    assert found.is_active is True
    # timestamps diisi oleh Postgres (server_default), bukan Python
    assert found.created_at is not None


async def test_email_unique(db):
    db.add(User(email="dobel@example.com", name="A", role=UserRole.customer))
    await db.flush()

    # SAVEPOINT: error-nya bisa dibatalkan tanpa mematikan transaksi test
    with pytest.raises(IntegrityError):
        async with db.begin_nested():
            db.add(User(email="dobel@example.com", name="B", role=UserRole.customer))
            await db.flush()

    # transaksi luar masih hidup, data sebelumnya masih ada
    assert await db.scalar(select(User.id).where(User.email == "dobel@example.com"))


async def test_ticket_no_format_and_increment(db):
    customer = User(email="c@example.com", name="C", role=UserRole.customer)
    db.add(customer)
    await db.flush()

    no1 = await next_ticket_no(db)
    no2 = await next_ticket_no(db)

    assert no1.startswith("TKT-")
    assert len(no1) == len("TKT-000001")
    assert int(no2[4:]) == int(no1[4:]) + 1


async def test_ticket_defaults_from_database(db):
    customer = User(email="c2@example.com", name="C2", role=UserRole.customer)
    db.add(customer)
    await db.flush()

    ticket = Ticket(
        ticket_no=await next_ticket_no(db),
        subject="Subjek uji",
        description="Deskripsi uji",
        customer_id=customer.id,
    )
    db.add(ticket)
    await db.flush()
    await db.refresh(ticket)

    # server_default di DB yang mengisi, bukan Python
    assert ticket.status == TicketStatus.open
    assert ticket.priority.value == "normal"
    assert ticket.assignee_id is None


async def test_timezone_is_utc_aware(db):
    result = await db.scalar(text("SELECT now()"))
    assert result.tzinfo is not None
    offset = result.utcoffset()
    assert offset is not None and offset.total_seconds() == 0
