from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """Halaman hasil query berbasis cursor.

    cursor = id item TERAKHIR yang dikirim. Request berikutnya mengirim cursor ini
    untuk mengambil item yang LEBIH LAMA. Tidak ada offset, jadi data baru masuk
    tidak membuat halaman bergeser (masalah klasik pagination offset).
    """

    items: list[T]
    next_cursor: int | None = None
