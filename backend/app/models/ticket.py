from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import TicketPriority, TicketStatus
from app.models.core import User


class Ticket(Base, TimestampMixin):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    # TKT-000001 — dibuat di service (lihat app/services/ticket_no.py), bukan di DB trigger.
    ticket_no: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[TicketStatus] = mapped_column(
        Enum(TicketStatus, name="ticket_status", native_enum=True),
        nullable=False,
        server_default=TicketStatus.open.value,
    )
    priority: Mapped[TicketPriority] = mapped_column(
        Enum(TicketPriority, name="ticket_priority", native_enum=True),
        nullable=False,
        server_default=TicketPriority.normal.value,
    )
    customer_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    assignee_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    last_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    customer: Mapped[User] = relationship(foreign_keys=[customer_id], lazy="raise")
    assignee: Mapped[User | None] = relationship(foreign_keys=[assignee_id], lazy="raise")
    messages: Mapped[list["TicketMessage"]] = relationship(
        back_populates="ticket", cascade="all, delete-orphan", lazy="raise"
    )

    __table_args__ = (
        # Dipakai untuk daftar tiket per status, terbaru dulu.
        Index("ix_tickets_status_last_message", "status", text("last_message_at DESC")),
        Index("ix_tickets_customer", "customer_id"),
        Index("ix_tickets_assignee", "assignee_id"),
    )

    def __repr__(self) -> str:
        return f"<Ticket {self.ticket_no} {self.status}>"


class TicketMessage(Base):
    __tablename__ = "ticket_messages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ticket_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False
    )
    sender_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    # Catatan internal agent: TIDAK boleh terlihat oleh customer.
    is_internal: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    ticket: Mapped[Ticket] = relationship(back_populates="messages", lazy="raise")
    sender: Mapped[User] = relationship(lazy="raise")

    __table_args__ = (
        # Cursor pagination: WHERE ticket_id = ? AND id < ? ORDER BY id DESC
        Index("ix_ticket_messages_ticket_id_desc", "ticket_id", text("id DESC")),
    )

    def __repr__(self) -> str:
        return f"<TicketMessage {self.id} ticket={self.ticket_id}>"
