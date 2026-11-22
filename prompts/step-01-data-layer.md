# Step 01 — Data Layer

> **Baca `prompts/CONTEXT.md` dulu** (aturan kerja, stack, format laporan).
> **Kerjakan HANYA step ini.** Setelah DoD terpenuhi, berhenti dan tanya apakah lanjut.

## Prompt (tempel ini ke agent)

```text
Kerjakan Step 01 (Data Layer) dari proyek CS Ticketing.

Baca dulu: prompts/CONTEXT.md, ROADMAP.md, docs/ARCHITECTURE.md, docs/DATA-MODEL.md, docs/API.md.

## Tujuan
Skema database yang benar, dikelola lewat migrasi, plus data contoh untuk development.

## Prasyarat
Step 0 selesai: DB sehat, `/health` menjawab `db: ok`.

## Sub-step
1. **1.1 Engine & session** — `app/db/session.py` (`create_async_engine`, `async_sessionmaker`),
   `app/db/base.py` (`DeclarativeBase` + mixin `created_at/updated_at` timezone-aware),
   dependency `get_db` di `app/deps.py`.
2. **1.2 Models** — sesuai `docs/DATA-MODEL.md`: `User`, `Ticket`, `TicketMessage`
   + enum Python (`sa.Enum(..., native_enum=True, name=...)`).
3. **1.3 Alembic** — `alembic init` (versi async), `env.py` ambil URL dari settings,
   `target_metadata = Base.metadata`; buat migrasi pertama; verifikasi `upgrade` **dan** `downgrade` bolak-balik.
4. **1.4 Seed** — `scripts/seed.py` idempotent (pakai `ON CONFLICT DO NOTHING` / cek by email):
   2 agent, 2 customer, 3 tiket (status berbeda), 5 pesan.
5. **1.5 ticket_no** — sequence Postgres + generator `TKT-000001`; pastikan tetap unik dan tidak
   bergantung pada `id`. Tulis sebagai default di service saat create, bukan di DB trigger (lebih mudah dibaca).
6. **1.6 Test fixture** — `tests/conftest.py`: database test terpisah (`ticketing_test`),
   buat skema via Alembic, tiap test dibungkus transaksi yang di-rollback, override `get_db`.
   Satu test contoh: insert user → query balik → assert.

## Verifikasi
```bash
alembic upgrade head && alembic downgrade base && alembic upgrade head
python -m scripts.seed && python -m scripts.seed      # dua kali, tetap sama jumlahnya
make psql -c "select ticket_no, status from tickets order by id;"
pytest -q
```

## Batasan
- Tidak ada endpoint tiket, tidak ada auth. Hanya lapisan data.
- Jangan membuat tabel yang belum ada di `docs/DATA-MODEL.md`.

## Penutup
Berhenti dan tanya: *"Step 1 selesai. Lanjut ke Step 2 (Auth Google SSO)?"*

Aturan: jangan kerjakan step berikutnya, jangan tambah dependency di luar stack,
setiap perubahan skema lewat migrasi Alembic, verifikasi dengan output nyata (bukan asumsi),
dan akhiri dengan blok laporan sesuai CONTEXT.md.
```
