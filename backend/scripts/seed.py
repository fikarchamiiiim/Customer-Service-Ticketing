"""Seed data development. Idempotent: aman dijalankan berkali-kali.

Jalankan:  .venv/bin/python -m scripts.seed
"""

import asyncio

from sqlalchemy import func, select

from app.db.session import SessionLocal
from app.models.core import User
from app.models.enums import TicketPriority, TicketStatus
from app.models.ticket import Ticket, TicketMessage
from app.services.ticket_no import next_ticket_no

AGENTS = [
    ("agent1@example.com", "Agent Satu"),
    ("agent2@example.com", "Agent Dua"),
]
CUSTOMERS = [
    ("customer1@example.com", "Budi Customer"),
    ("customer2@example.com", "Siti Customer"),
]

TICKETS = [
    {
        "customer": "customer1@example.com",
        "assignee": "agent1@example.com",
        "subject": "Tidak bisa login ke akun",
        "description": "Sejak pagi saya tidak bisa login, selalu muncul pesan error.",
        "status": TicketStatus.in_progress,
        "priority": TicketPriority.high,
        "messages": [
            ("agent1@example.com", "Halo Budi, boleh kirimkan screenshot pesan error-nya?", False),
            ("customer1@example.com", "Sudah saya kirim lewat email ya.", False),
            ("agent1@example.com", "Catatan internal: cek log auth tanggal 20.", True),
        ],
    },
    {
        "customer": "customer2@example.com",
        "assignee": None,
        "subject": "Tagihan saya dobel",
        "description": "Saya terima dua tagihan untuk bulan yang sama.",
        "status": TicketStatus.open,
        "priority": TicketPriority.normal,
        "messages": [
            ("customer2@example.com", "Mohon dicek, terima kasih.", False),
        ],
    },
    {
        "customer": "customer1@example.com",
        "assignee": "agent2@example.com",
        "subject": "Fitur export CSV tidak jalan",
        "description": "Tombol export tidak merespons apa pun.",
        "status": TicketStatus.resolved,
        "priority": TicketPriority.low,
        "messages": [
            ("agent2@example.com", "Bug sudah kami perbaiki, silakan coba lagi.", False),
        ],
    },
]


async def upsert_user(db, email: str, name: str, role: str) -> User:
    user = await db.scalar(select(User).where(User.email == email))
    if user:
        return user
    user = User(email=email, name=name, role=role)
    db.add(user)
    await db.flush()
    return user


async def main() -> None:
    async with SessionLocal() as db:
        agents = {e: await upsert_user(db, e, n, "agent") for e, n in AGENTS}
        customers = {e: await upsert_user(db, e, n, "customer") for e, n in CUSTOMERS}

        created = 0
        for spec in TICKETS:
            existing = await db.scalar(select(Ticket).where(Ticket.subject == spec["subject"]))
            if existing:
                continue

            ticket = Ticket(
                ticket_no=await next_ticket_no(db),
                subject=spec["subject"],
                description=spec["description"],
                status=spec["status"],
                priority=spec["priority"],
                customer_id=customers[spec["customer"]].id,
                assignee_id=agents[spec["assignee"]].id if spec["assignee"] else None,
            )
            db.add(ticket)
            await db.flush()

            for sender_email, body, is_internal in spec["messages"]:
                sender = agents.get(sender_email) or customers.get(sender_email)
                db.add(
                    TicketMessage(
                        ticket_id=ticket.id,
                        sender_id=sender.id,
                        body=body,
                        is_internal=is_internal,
                    )
                )
            await db.flush()
            ticket.last_message_at = await db.scalar(
                select(func.max(TicketMessage.created_at)).where(
                    TicketMessage.ticket_id == ticket.id
                )
            )
            created += 1

        await db.commit()

        users_n = await db.scalar(select(func.count()).select_from(User))
        tickets_n = await db.scalar(select(func.count()).select_from(Ticket))
        messages_n = await db.scalar(select(func.count()).select_from(TicketMessage))
        print(f"seed selesai: tiket baru={created}, total users={users_n}, tickets={tickets_n}, messages={messages_n}")


if __name__ == "__main__":
    asyncio.run(main())
