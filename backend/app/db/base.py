from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base deklaratif untuk semua model.

    Metadata inilah yang dibaca Alembic (via target_metadata di alembic/env.py)
    untuk mendeteksi selisih model vs database.
    """


class TimestampMixin:
    """created_at / updated_at otomatis, disimpan dalam UTC (timezone-aware).

    server_default=func.now() -> jam yang dipakai adalah jam Postgres, bukan jam Python.
    Ini penting: satu sumber kebenaran waktu, tidak terpengaruh timezone mesin.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
