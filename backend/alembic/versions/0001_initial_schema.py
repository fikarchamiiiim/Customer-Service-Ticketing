"""initial schema: users, tickets, ticket_messages, enums, sequence

Revision ID: 0001
Revises:
Create Date: 2026-11-22

Ditulis manual (bukan autogenerate) supaya kamu bisa membaca setiap barisnya.
Perhatikan urutan: enum -> tabel -> index. Urutan ini WAJIB, karena kolom
bertipe enum butuh tipenya sudah ada lebih dulu.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

user_role = postgresql.ENUM("customer", "agent", "admin", name="user_role", create_type=False)
ticket_status = postgresql.ENUM(
    "open", "in_progress", "resolved", "closed", name="ticket_status", create_type=False
)
ticket_priority = postgresql.ENUM(
    "low", "normal", "high", name="ticket_priority", create_type=False
)


def upgrade() -> None:
    bind = op.get_bind()

    # --- 1. Tipe enum -------------------------------------------------------
    user_role.create(bind, checkfirst=True)
    ticket_status.create(bind, checkfirst=True)
    ticket_priority.create(bind, checkfirst=True)

    # --- 2. Sequence untuk ticket_no ---------------------------------------
    op.execute("CREATE SEQUENCE IF NOT EXISTS ticket_no_seq START WITH 1")

    # --- 3. users -----------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("avatar_url", sa.String(length=500), nullable=True),
        sa.Column("role", user_role, server_default="customer", nullable=False),
        sa.Column("google_sub", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("google_sub", name="uq_users_google_sub"),
    )
    # Email unik + sering dicari -> satu unique index cukup.
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # --- 4. tickets ---------------------------------------------------------
    op.create_table(
        "tickets",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("ticket_no", sa.String(length=20), nullable=False),
        sa.Column("subject", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", ticket_status, server_default="open", nullable=False),
        sa.Column("priority", ticket_priority, server_default="normal", nullable=False),
        sa.Column("customer_id", sa.BigInteger(), nullable=False),
        sa.Column("assignee_id", sa.BigInteger(), nullable=True),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["assignee_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ticket_no", name="uq_tickets_ticket_no"),
    )
    op.create_index(
        "ix_tickets_status_last_message",
        "tickets",
        ["status", sa.text("last_message_at DESC")],
    )
    op.create_index("ix_tickets_customer", "tickets", ["customer_id"])
    op.create_index("ix_tickets_assignee", "tickets", ["assignee_id"])

    # --- 5. ticket_messages -------------------------------------------------
    op.create_table(
        "ticket_messages",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("ticket_id", sa.BigInteger(), nullable=False),
        sa.Column("sender_id", sa.BigInteger(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("is_internal", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sender_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ticket_messages_ticket_id_desc",
        "ticket_messages",
        ["ticket_id", sa.text("id DESC")],
    )


def downgrade() -> None:
    op.drop_index("ix_ticket_messages_ticket_id_desc", table_name="ticket_messages")
    op.drop_table("ticket_messages")
    op.drop_index("ix_tickets_assignee", table_name="tickets")
    op.drop_index("ix_tickets_customer", table_name="tickets")
    op.drop_index("ix_tickets_status_last_message", table_name="tickets")
    op.drop_table("tickets")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    op.execute("DROP SEQUENCE IF EXISTS ticket_no_seq")
    ticket_priority.drop(op.get_bind(), checkfirst=True)
    ticket_status.drop(op.get_bind(), checkfirst=True)
    user_role.drop(op.get_bind(), checkfirst=True)
