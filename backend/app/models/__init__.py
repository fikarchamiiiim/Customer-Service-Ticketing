"""Import semua model di sini supaya Alembic mendeteksinya.

Tanpa import ini, Base.metadata kosong dan autogenerate akan mengira
semua tabel harus DIHAPUS.
"""

from app.models.core import User, UserRole
from app.models.ticket import Ticket, TicketMessage, TicketPriority, TicketStatus

__all__ = [
    "User",
    "UserRole",
    "Ticket",
    "TicketMessage",
    "TicketStatus",
    "TicketPriority",
]
