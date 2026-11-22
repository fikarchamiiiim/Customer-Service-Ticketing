from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

TICKET_NO_SEQ = "ticket_no_seq"


async def next_ticket_no(db: AsyncSession) -> str:
    """Ambil nomor tiket berikutnya: TKT-000001.

    Sengaja di service, bukan di trigger DB:
      - mudah dibaca dan mudah di-test
      - nomor hanya dibuat saat benar-benar ada tiket baru
      - tidak bergantung pada id (id bisa bolong setelah rollback)

    nextval() milik Postgres aman dipanggil bersamaan (concurrent):
    dua request tidak akan pernah dapat nomor yang sama.
    """
    value = await db.scalar(text(f"SELECT nextval('{TICKET_NO_SEQ}')"))
    return f"TKT-{int(value):06d}"
