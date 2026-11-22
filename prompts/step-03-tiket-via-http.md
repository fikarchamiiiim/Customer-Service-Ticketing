# Step 03 — Tiket via HTTP

> **Baca `prompts/CONTEXT.md` dulu** (aturan kerja, stack, format laporan).
> **Kerjakan HANYA step ini.** Setelah DoD terpenuhi, berhenti dan tanya apakah lanjut.

## Prompt (tempel ini ke agent)

```text
Kerjakan Step 03 (Tiket via HTTP) dari proyek CS Ticketing.

Baca dulu: prompts/CONTEXT.md, ROADMAP.md, docs/ARCHITECTURE.md, docs/DATA-MODEL.md, docs/API.md.

## Tujuan
Siklus tiket lengkap **tanpa realtime**. Ini tulang punggung aplikasi; semua realtime menumpang di sini.

## Prasyarat
Step 2 selesai: bisa login, `/me` mengembalikan user dengan role.

## Sub-step
1. **3.1 Schemas** — `schemas/ticket.py`: `TicketCreate` (subject 3..200, description 1..5000),
   `TicketUpdate` (semua opsional), `TicketOut`, `MessageCreate`, `MessageOut`,
   `Page[T]` (`items` + `next_cursor`).
2. **3.2 Service layer** — `services/tickets.py`: `create_ticket`, `list_tickets(actor, filters, cursor, limit)`,
   `get_ticket_for(actor, id)` (raise 404 kalau bukan haknya), `update_ticket`, `add_message`.
   Router **tipis**: hanya parsing + memanggil service.
3. **3.3 RBAC scoping** — customer difilter `customer_id = me`; agent melihat semua.
   Akses tiket orang lain oleh customer → **404** (bukan 403).
4. **3.4 State machine** — `ALLOWED = {open: {in_progress, closed}, in_progress: {resolved, closed}, resolved: {closed, in_progress}, closed: set()}`
   dengan izin tambahan: customer hanya boleh `close` tiket miliknya. Transisi ilegal → **422 ILLEGAL_TRANSITION**.
   Assign: agent bisa `assignee_id = me` (ambil tiket) atau `null` (lepas).
5. **3.5 Messages** — cursor pagination `before_id`; `is_internal=true` hanya agent **dan** disembunyikan
   dari customer di semua query; update `tickets.last_message_at` setiap pesan masuk.
6. **3.6 FE** — `/tickets` (customer: tiket saya; agent: queue + filter status/assignee = saya/belum diambil),
   `/tickets/new` (form), `/tickets/:id` (detail: header status/priority/assignee, thread pesan,
   form balas, tombol aksi sesuai role). TanStack Query dengan query key `['tickets', filters]` & `['ticket', id]`.
   Refetch **manual** dulu (tombol refresh) — realtime menyusul di Step 4-5.

## Verifikasi
```bash
# customer A tidak boleh lihat tiket customer B
curl -s -b /tmp/customerA.txt localhost:8000/api/v1/tickets/3 -i   # 404
# agent boleh
curl -s -b /tmp/agent.txt localhost:8000/api/v1/tickets/3 | jq .status
# transisi ilegal
curl -s -b /tmp/agent.txt -X PATCH localhost:8000/api/v1/tickets/3 \
  -H 'content-type: application/json' -d '{"status":"resolved"}' -i   # 422 open→resolved
pytest -q
```
Tambahkan unit test `ALLOWED` (tanpa DB) — cepat dan jadi contoh bagus.

## Batasan
- **Belum ada** WebSocket, notifikasi, presence, activity log.
- Jangan menambah attachment/upload.

## Penutup
Berhenti dan tanya: *"Step 3 selesai. Lanjut ke Step 4 (Fondasi WebSocket)?"*

Aturan: jangan kerjakan step berikutnya, jangan tambah dependency di luar stack,
setiap perubahan skema lewat migrasi Alembic, verifikasi dengan output nyata (bukan asumsi),
dan akhiri dengan blok laporan sesuai CONTEXT.md.
```
