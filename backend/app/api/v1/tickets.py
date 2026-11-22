from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.deps import get_current_user
from app.models.core import User
from app.models.enums import TicketStatus
from app.models.ticket import Ticket, TicketMessage
from app.schemas.common import Page
from app.schemas.ticket import (
    MessageCreate,
    MessageOut,
    TicketCreate,
    TicketListItem,
    TicketOut,
    TicketUpdate,
)
from app.services import tickets as svc

router = APIRouter(prefix="/tickets", tags=["tickets"])


async def _to_ticket_out(db: AsyncSession, ticket: Ticket) -> TicketOut:
    count = await db.scalar(
        select(func.count())
        .select_from(TicketMessage)
        .where(TicketMessage.ticket_id == ticket.id)
    )
    data = TicketOut.model_validate(ticket)
    data.message_count = count or 0
    return data


@router.post("", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    payload: TicketCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TicketOut:
    ticket = await svc.create_ticket(db, user, payload)
    return await _to_ticket_out(db, ticket)


@router.get("", response_model=Page[TicketListItem])
async def list_tickets(
    status_filter: TicketStatus | None = Query(default=None, alias="status"),
    scope: str = Query(default="mine", pattern="^(mine|all)$"),
    assignee: str | None = Query(default=None, pattern="^(me|unassigned|\\d+)$"),
    cursor: int | None = Query(default=None, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Page[TicketListItem]:
    items, next_cursor = await svc.list_tickets(
        db,
        user,
        status_filter=status_filter,
        scope=scope,
        assignee=assignee,
        cursor=cursor,
        limit=limit,
    )
    return Page[TicketListItem](
        items=[TicketListItem.model_validate(t) for t in items],
        next_cursor=next_cursor,
    )


@router.get("/{ticket_id}", response_model=TicketOut)
async def get_ticket(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TicketOut:
    ticket = await svc.get_ticket_or_404(db, user, ticket_id)
    return await _to_ticket_out(db, ticket)


@router.patch("/{ticket_id}", response_model=TicketOut)
async def update_ticket(
    ticket_id: int,
    payload: TicketUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TicketOut:
    ticket = await svc.update_ticket(db, user, ticket_id, payload)
    return await _to_ticket_out(db, ticket)


@router.get("/{ticket_id}/messages", response_model=Page[MessageOut])
async def list_messages(
    ticket_id: int,
    before_id: int | None = Query(default=None, ge=1),
    limit: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Page[MessageOut]:
    items, next_cursor = await svc.list_messages(
        db, user, ticket_id, before_id=before_id, limit=limit
    )
    return Page[MessageOut](
        items=[MessageOut.model_validate(m) for m in items],
        next_cursor=next_cursor,
    )


@router.post(
    "/{ticket_id}/messages",
    response_model=MessageOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_message(
    ticket_id: int,
    payload: MessageCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> MessageOut:
    message = await svc.add_message(db, user, ticket_id, payload)
    return MessageOut.model_validate(message)
