"""Aturan bisnis tiket. Router sengaja TIPIS: hanya parsing + memanggil service.

Dua hal yang paling penting di file ini:
  1. ALLOWED        -> state machine status (fungsi murni, mudah di-test)
  2. scope_for()    -> satu tempat yang menentukan "user ini boleh lihat tiket apa"
"""

import logging
from collections.abc import Sequence
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.core import User
from app.models.enums import TicketStatus, UserRole
from app.models.ticket import Ticket, TicketMessage
from app.schemas.ticket import (
    MessageCreate,
    TicketCreate,
    TicketUpdate,
)
from app.services.ticket_no import next_ticket_no

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# State machine
# --------------------------------------------------------------------------

ALLOWED: dict[TicketStatus, set[TicketStatus]] = {
    TicketStatus.open: {TicketStatus.in_progress, TicketStatus.closed},
    TicketStatus.in_progress: {TicketStatus.resolved, TicketStatus.closed},
    TicketStatus.resolved: {TicketStatus.closed, TicketStatus.in_progress},  # reopen
    TicketStatus.closed: set(),  # tiket tertutup = final
}


def can_transition(current: TicketStatus, target: TicketStatus) -> bool:
    if current == target:
        return True  # tidak ada perubahan, bukan error
    return target in ALLOWED.get(current, set())


def assert_transition(current: TicketStatus, target: TicketStatus) -> None:
    if not can_transition(current, target):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "ILLEGAL_TRANSITION",
                "message": f"Status {current.value} tidak bisa langsung ke {target.value}",
                "details": {
                    "allowed": sorted(s.value for s in ALLOWED.get(current, set())),
                },
            },
        )


# --------------------------------------------------------------------------
# Otorisasi
# --------------------------------------------------------------------------

def is_staff(user: User) -> bool:
    return user.role in (UserRole.agent, UserRole.admin)


def not_found() -> HTTPException:
    """404, BUKAN 403.

    Kenapa: 403 memberitahu "tiket ini ada tapi kamu tidak berhak".
    Itu membocorkan keberadaan data. 404 menyembunyikan fakta itu.
    """
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"code": "NOT_FOUND", "message": "Tiket tidak ditemukan"},
    )


def scope_for(user: User) -> Select:
    """Query dasar tiket yang BOLEH dilihat user ini.

    Semua endpoint yang membaca tiket WAJIB lewat sini. Kalau aturannya berubah,
    hanya file ini yang perlu disentuh.
    """
    stmt = select(Ticket)
    if not is_staff(user):
        stmt = stmt.where(Ticket.customer_id == user.id)
    return stmt


def can_read(user: User, ticket: Ticket) -> bool:
    return is_staff(user) or ticket.customer_id == user.id


# --------------------------------------------------------------------------
# Loader (relationship memakai lazy="raise", jadi harus di-eager-load)
# --------------------------------------------------------------------------

def _with_relations(stmt: Select) -> Select:
    return stmt.options(
        selectinload(Ticket.customer),
        selectinload(Ticket.assignee),
    )


async def get_ticket_or_404(db: AsyncSession, user: User, ticket_id: int) -> Ticket:
    # populate_existing=True: kalau objek sudah ada di identity map, timpa isinya
    # dengan data terbaru dari DB. Tanpa ini, setelah PATCH, response bisa
    # menampilkan nilai LAMA (mis. assignee masih None).
    ticket = await db.scalar(
        _with_relations(scope_for(user))
        .where(Ticket.id == ticket_id)
        .execution_options(populate_existing=True)
    )
    if ticket is None:
        raise not_found()
    return ticket


# --------------------------------------------------------------------------
# Perintah (command)
# --------------------------------------------------------------------------

async def create_ticket(db: AsyncSession, user: User, payload: TicketCreate) -> Ticket:
    ticket = Ticket(
        ticket_no=await next_ticket_no(db),
        subject=payload.subject.strip(),
        description=payload.description.strip(),
        priority=payload.priority,
        customer_id=user.id,
        status=TicketStatus.open,
    )
    db.add(ticket)
    await db.flush()

    # Deskripsi juga disimpan sebagai pesan pertama, supaya thread langsung berisi
    # konteks dan customer bisa membalas dari situ.
    db.add(
        TicketMessage(
            ticket_id=ticket.id,
            sender_id=user.id,
            body=payload.description.strip(),
        )
    )
    ticket.last_message_at = datetime.now(timezone.utc)
    await db.commit()

    return await get_ticket_or_404(db, user, ticket.id)


async def update_ticket(
    db: AsyncSession, user: User, ticket_id: int, payload: TicketUpdate
) -> Ticket:
    ticket = await get_ticket_or_404(db, user, ticket_id)
    changes = payload.model_dump(exclude_unset=True)

    # --- status ---
    if "status" in changes and changes["status"] is not None:
        target: TicketStatus = changes["status"]
        assert_transition(ticket.status, target)
        if not is_staff(user) and target != TicketStatus.closed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "FORBIDDEN",
                    "message": "Customer hanya boleh menutup tiketnya sendiri",
                },
            )
        ticket.status = target

    # --- priority ---
    if "priority" in changes and changes["priority"] is not None:
        if not is_staff(user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "message": "Hanya agent yang bisa ubah prioritas"},
            )
        ticket.priority = changes["priority"]

    # --- assignee ---
    if "assignee_id" in changes:
        if not is_staff(user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "message": "Hanya agent yang bisa assign tiket"},
            )
        new_assignee = changes["assignee_id"]
        if new_assignee is not None:
            assignee = await db.get(User, new_assignee)
            if assignee is None or not is_staff(assignee):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={
                        "code": "INVALID_ASSIGNEE",
                        "message": "Assignee harus user dengan role agent",
                    },
                )
        ticket.assignee_id = new_assignee

    await db.commit()
    # populate_existing (lihat get_ticket_or_404) memaksa muat ulang dari DB,
    # karena objek masih hidup di identity map: expire_on_commit=False membuat
    # relasi yang tadinya None tetap None walau assignee_id sudah berubah.
    return await get_ticket_or_404(db, user, ticket_id)


async def add_message(
    db: AsyncSession, user: User, ticket_id: int, payload: MessageCreate
) -> TicketMessage:
    ticket = await get_ticket_or_404(db, user, ticket_id)

    if ticket.status == TicketStatus.closed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "TICKET_CLOSED", "message": "Tiket sudah ditutup"},
        )

    if payload.is_internal and not is_staff(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "FORBIDDEN",
                "message": "Catatan internal hanya untuk agent",
            },
        )

    message = TicketMessage(
        ticket_id=ticket.id,
        sender_id=user.id,
        body=payload.body.strip(),
        is_internal=payload.is_internal,
    )
    db.add(message)

    # Pesan publik membangunkan tiket yang sudah resolved.
    if not payload.is_internal and ticket.status == TicketStatus.resolved:
        ticket.status = TicketStatus.in_progress

    now = datetime.now(timezone.utc)
    ticket.last_message_at = now
    await db.commit()

    return await db.scalar(
        select(TicketMessage)
        .options(selectinload(TicketMessage.sender))
        .where(TicketMessage.id == message.id)
    )


# --------------------------------------------------------------------------
# Query
# --------------------------------------------------------------------------

async def list_tickets(
    db: AsyncSession,
    user: User,
    *,
    status_filter: TicketStatus | None = None,
    scope: str = "mine",
    assignee: str | None = None,
    cursor: int | None = None,
    limit: int = 20,
) -> tuple[Sequence[Ticket], int | None]:
    stmt = scope_for(user)

    if scope == "all":
        if not is_staff(user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "message": "scope=all hanya untuk agent"},
            )
    elif scope == "mine":
        stmt = stmt.where(Ticket.customer_id == user.id)

    if status_filter is not None:
        stmt = stmt.where(Ticket.status == status_filter)

    if assignee == "me":
        stmt = stmt.where(Ticket.assignee_id == user.id)
    elif assignee == "unassigned":
        stmt = stmt.where(Ticket.assignee_id.is_(None))
    elif assignee is not None and assignee.isdigit():
        stmt = stmt.where(Ticket.assignee_id == int(assignee))

    if cursor is not None:
        stmt = stmt.where(Ticket.id < cursor)

    stmt = _with_relations(stmt).order_by(Ticket.id.desc()).limit(limit + 1)

    rows = list((await db.scalars(stmt)).unique().all())
    has_more = len(rows) > limit
    items = rows[:limit]
    next_cursor = items[-1].id if has_more and items else None
    return items, next_cursor


async def list_messages(
    db: AsyncSession,
    user: User,
    ticket_id: int,
    *,
    before_id: int | None = None,
    limit: int = 50,
) -> tuple[Sequence[TicketMessage], int | None]:
    ticket = await get_ticket_or_404(db, user, ticket_id)

    stmt = select(TicketMessage).where(TicketMessage.ticket_id == ticket.id)

    # Customer TIDAK PERNAH menerima catatan internal.
    if not is_staff(user):
        stmt = stmt.where(TicketMessage.is_internal.is_(False))

    if before_id is not None:
        stmt = stmt.where(TicketMessage.id < before_id)

    # Ambil yang terbaru dulu, lalu dibalik supaya tampil kronologis (lama -> baru).
    stmt = (
        stmt.options(selectinload(TicketMessage.sender))
        .order_by(TicketMessage.id.desc())
        .limit(limit + 1)
    )

    rows = list((await db.scalars(stmt)).unique().all())
    has_more = len(rows) > limit
    page = rows[:limit]
    next_cursor = page[-1].id if has_more and page else None
    return list(reversed(page)), next_cursor
