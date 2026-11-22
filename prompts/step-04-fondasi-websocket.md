# Step 04 — Fondasi WebSocket

> **Baca `prompts/CONTEXT.md` dulu** (aturan kerja, stack, format laporan).
> **Kerjakan HANYA step ini.** Setelah DoD terpenuhi, berhenti dan tanya apakah lanjut.

## Prompt (tempel ini ke agent)

```text
Kerjakan Step 04 (Fondasi WebSocket) dari proyek CS Ticketing.

Baca dulu: prompts/CONTEXT.md, ROADMAP.md, docs/ARCHITECTURE.md, docs/DATA-MODEL.md, docs/API.md.

## Tujuan
Koneksi realtime yang bisa diandalkan (auth, channel, heartbeat, reconnect) — **belum ada chat**.

## Prasyarat
Step 2 (auth cookie) dan Step 3 (otorisasi tiket) selesai.

## Sub-step
1. **4.1 Endpoint & manager** — `GET /ws` di `api/v1/ws.py`; `ConnectionManager` in-memory:
   `connections: dict[user_id, set[WebSocket]]`, `rooms: dict[channel, set[WebSocket]]`,
   method `connect`, `disconnect`, `join`, `leave`, `broadcast(channel, envelope)`,
   plus `send_to_user(user_id, envelope)`.
2. **4.2 Auth handshake** — baca cookie `session` dari `websocket.cookies` **sebelum** `accept()`;
   invalid → `await websocket.close(code=4401)`. Log setiap handshake (user, hasil).
3. **4.3 Envelope + loop** — loop `receive_json`: validasi Pydantic `ClientEvent`;
   `subscribe`/`unsubscribe` divalidasi otorisasi channel lalu balas `subscribed`/`unsubscribed`;
   payload tidak dikenal → `error BAD_MESSAGE` (jangan tutup koneksi).
4. **4.4 Heartbeat** — server mencatat `last_seen`; task background menutup koneksi yang diam > 60 detik;
   client `ping` → `pong`.
5. **4.5 Otorisasi channel** — fungsi `can_subscribe(user, channel)`:
   `ticket:{id}` pakai aturan `get_ticket_for`; `user:{id}` harus milik sendiri; `agents` harus role agent.
   Gagal → `error CHANNEL_FORBIDDEN`.
6. **4.6 FE socket.ts** — singleton `SocketClient`: `connect()`, `subscribe(channel, handler)` dengan ref-count,
   `reconnect` backoff 1-2-4-8-16-30s + jitter, antrian subscribe diputar ulang setelah reconnect,
   status `connecting|open|reconnecting|closed` diekspos via hook `useSocketStatus`.
   Komponen `ConnectionBadge` di header: ● hijau / ◍ kuning / ○ merah.

## Verifikasi
```bash
# tanpa cookie harus ditolak 4401
npx wscat -c ws://localhost:8000/ws 2>&1 | head -3
# dengan cookie (ambil dari browser atau dev-login)
```
Di browser: buka 2 tab `/tickets/1` → badge hijau di keduanya.
Matikan backend → badge kuning "reconnecting" → nyalakan lagi → hijau **tanpa refresh halaman**.
Coba `subscribe` ke `ticket:<id milik orang lain>` → terima `error CHANNEL_FORBIDDEN`, koneksi tetap hidup.

## Batasan
- **Belum ada** `message.created` atau event domain apa pun. Hanya infrastruktur.
- Jangan tambahkan Redis. In-memory cukup untuk 1 worker (`--workers 1`).

## Penutup
Berhenti dan tanya: *"Step 4 selesai. Lanjut ke Step 5 (Chat Realtime)?"*

Aturan: jangan kerjakan step berikutnya, jangan tambah dependency di luar stack,
setiap perubahan skema lewat migrasi Alembic, verifikasi dengan output nyata (bukan asumsi),
dan akhiri dengan blok laporan sesuai CONTEXT.md.
```
