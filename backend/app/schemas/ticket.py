from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field

from app.models.enums import TicketPriority, TicketStatus
from app.schemas.auth import UserOut


class TicketCreate(BaseModel):
    subject: Annotated[str, Field(min_length=3, max_length=200)]
    description: Annotated[str, Field(min_length=1, max_length=5000)]
    priority: TicketPriority = TicketPriority.normal


class TicketUpdate(BaseModel):
    """Semua opsional: kirim hanya yang berubah.

    Gunakan model_dump(exclude_unset=True) supaya "tidak dikirim" beda dengan "dikirim null".
    """

    status: TicketStatus | None = None
    priority: TicketPriority | None = None
    assignee_id: int | None = None


class TicketOut(BaseModel):
    id: int
    ticket_no: str
    subject: str
    description: str
    status: TicketStatus
    priority: TicketPriority
    customer: UserOut
    assignee: UserOut | None = None
    last_message_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    model_config = {"from_attributes": True}


class TicketListItem(BaseModel):
    id: int
    ticket_no: str
    subject: str
    status: TicketStatus
    priority: TicketPriority
    customer: UserOut
    assignee: UserOut | None = None
    last_message_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageCreate(BaseModel):
    body: Annotated[str, Field(min_length=1, max_length=5000)]
    is_internal: bool = False


class MessageOut(BaseModel):
    id: int
    ticket_id: int
    body: str
    is_internal: bool
    sender: UserOut
    created_at: datetime

    model_config = {"from_attributes": True}
