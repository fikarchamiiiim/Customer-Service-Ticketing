# Step 06 — Notifikasi, Presence, Activity

> **Baca `prompts/CONTEXT.md` dulu** (aturan kerja, stack, format laporan).
> **Kerjakan HANYA step ini.** Setelah DoD terpenuhi, berhenti dan tanya apakah lanjut.

## Prompt (tempel ini ke agent)

```text
Kerjakan Step 06 (Notifikasi, Presence, Activity) dari proyek CS Ticketing.

Baca dulu: prompts/CONTEXT.md, ROADMAP.md, docs/ARCHITECTURE.md, docs/DATA-MODEL.md, docs/API.md.

## Tujuan
Aplikasi terasa hidup: tiket baru muncul sendiri di layar agent, status berubah live, ada jejak aktivitas.

## Prasyarat
Step 5 selesai: event bus dan chat realtime jalan.

## Sub-step
1. **6.1 tiket baru** — `POST /tickets` mem-publish `ticket.created` ke channel `agents`;
   FE agent: invalidate `['tickets']` + toast "Tiket baru: {ticket_no}".
2. **6.2 update tiket** — `PATCH /tickets/{id}` mem-publish `ticket.updated` ke `ticket:{id}`
   **dan** `agents` dengan `{ticket, changes}`; FE meng-invalidate query terkait.
3. **6.3 Presence** — dari `ConnectionManager`: siapa yang online; tampilkan "online" di daftar agent
   dan indikator di header tiket ("dilihat oleh Agent A"). Broadcast `presence` saat connect/disconnect.
4. **6.4 Activity log** — tabel `ticket_events` (migrasi baru!) + tulis event pada create/assign/status/message;
   endpoint `GET /tickets/{id}/events`; timeline di sisi kanan halaman detail.
5. **6.5 Unread counter** — tabel `ticket_participants` + `last_read_at`; endpoint
   `POST /tickets/{id}/read`; badge di daftar tiket. Cukup sederhana: hitung pesan dengan `id > last_read_message_id`.

## Verifikasi
```bash
pytest -q
```
Skenario manual: customer membuat tiket baru sementara tab agent terbuka → tiket muncul tanpa refresh.
Agent ubah status → tab customer ikut berubah. Buka detail tiket → unread hilang, badge turun.
Timeline menampilkan "dibuat", "di-assign ke Agent A", "status open → in_progress".

## Batasan
- Presence hanya in-memory (hilang saat restart) — itu **diterima** untuk sekarang.
- Jangan menambah email/WhatsApp.

## Penutup
Berhenti dan tanya: *"Step 6 selesai. Lanjut ke Step 7 (Hardening & Docs)?"*

Aturan: jangan kerjakan step berikutnya, jangan tambah dependency di luar stack,
setiap perubahan skema lewat migrasi Alembic, verifikasi dengan output nyata (bukan asumsi),
dan akhiri dengan blok laporan sesuai CONTEXT.md.
```
