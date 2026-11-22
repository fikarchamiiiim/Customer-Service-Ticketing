# Arsitektur

## 1. Gambaran

```
Browser (React TS, Vite)
   │
   ├── HTTP  /api/v1/*   → command & query (JSON, cookie httpOnly)
   └── WS    /ws         → push event (subscribe per channel)
            │
            ▼  (dev: Vite proxy → localhost:8000, jadi SATU origin)
     FastAPI (uvicorn)
       ├── api/v1/     (auth, tickets, messages, ws)
       ├── services/   (aturan bisnis: state machine, RBAC, otorisasi channel)
       ├── events.py   (EventBus in-process)
       └── db/         (SQLAlchemy async, Alembic)
            │
            ▼
     PostgreSQL 16 (docker)
```

**Satu origin** adalah kuncinya: cookie httpOnly terkirim otomatis saat handshake WebSocket,
dan tidak ada drama CORS. Di produksi, nginx melayani FE static dan mem-proxy `/api` + `/ws`.

## 2. Aturan Emas: Command vs Event

| | HTTP | WebSocket |
|---|---|---|
| Untuk | **semua perubahan state** (create, update, kirim pesan) | **push event** & sinyal ephemeral |
| Kenapa | status code, validasi, retry, gampang di-`curl`/test | latensi rendah, server→client, tanpa polling |
| Contoh | `POST /tickets/{id}/messages` | `message.created`, `typing`, `presence` |

**Larangan:** jangan kirim pesan lewat `ws.send()`. Kalau dikirim via WS, kamu kehilangan
error handling, validasi, dan idempotensi — lalu besok bingung "kenapa pesan saya hilang".

## 3. Alur Login (Google SSO)

```
1. FE render tombol "Sign in with Google" (Google Identity Services)
2. User pilih akun → Google kembalikan ID token (JWT) ke FE
3. FE: POST /api/v1/auth/google { id_token }
4. BE: verifikasi signature + audience + exp (google-auth)
5. BE: cari user by google_sub → kalau belum ada, buat (role dari allowlist email)
6. BE: terbitkan session JWT → Set-Cookie: session=...; HttpOnly; SameSite=Lax; Path=/
7. FE: simpan user di AuthContext → redirect: agent → /agent, customer → /tickets
8. Request berikutnya: cookie ikut otomatis (fetch credentials: 'include')
9. WS handshake: cookie ikut otomatis → BE decode → connection diterima
```

**Kenapa bukan redirect OAuth?** ID-token flow tidak butuh state/nonce/redirect-URI handling di BE —
jauh lebih sedikit kode untuk dipahami. Kalau nanti mau belajar lebih dalam, ganti ke Authorization Code + PKCE.

## 4. Alur Kirim Pesan (realtime)

```
FE ──POST /tickets/{id}/messages──▶ BE
                                   ├─ validasi + otorisasi (boleh akses tiket ini?)
                                   ├─ INSERT ticket_messages
                                   ├─ 201 { message }
                                   └─ EventBus.publish("ticket:{id}", "message.created", msg)
                                            │
        ┌───────────────────────────────────┴────────────────────────────┐
        ▼                                                                ▼
  tab pengirim                                                     tab lain (agent)
  event datang → id sudah ada di cache → ABAIKAN (dedupe)          append + render
```

**Aturan dedupe (pilih satu, jangan campur):** render dari event WS, tapi kalau `id` sudah ada → abaikan.
Alternatif lebih sederhana: render dari response POST, lalu abaikan event yang `id`-nya sudah dikenal.

## 5. Kontrak WebSocket

Endpoint: `GET /ws` (upgrade). Auth: cookie sesi.

Channel:
- `ticket:{ticket_id}` — percakapan tiket (butuh akses baca tiket)
- `user:{user_id}` — notifikasi personal (hanya milik sendiri)
- `agents` — queue agent (hanya role agent)

Envelope seragam:

```json
{ "v": 1, "type": "message.created", "channel": "ticket:12", "data": {}, "ts": "2026-11-22T08:00:00Z" }
```

Client → Server: `subscribe`, `unsubscribe`, `typing`, `ping`
Server → Client: `subscribed`, `unsubscribed`, `message.created`, `ticket.created`, `ticket.updated`, `typing`, `presence`, `error`, `pong`

Detail lengkap: `docs/API.md`.

## 6. Struktur Folder Target

```
cs-ticketing/
├── backend/
│   ├── app/
│   │   ├── main.py, config.py, deps.py
│   │   ├── api/v1/    auth.py, tickets.py, messages.py, ws.py
│   │   ├── models/    core.py, ticket.py
│   │   ├── schemas/   auth.py, ticket.py, ws.py
│   │   ├── services/  auth.py, tickets.py, events.py
│   │   └── db/        base.py, session.py
│   ├── alembic/
│   ├── tests/
│   └── pyproject.toml
├── frontend/
│   └── src/
│       ├── api/       client.ts, auth.ts, tickets.ts
│       ├── realtime/  socket.ts
│       ├── auth/      AuthContext.tsx, ProtectedRoute.tsx
│       ├── pages/     Login, TicketList, TicketDetail, TicketNew
│       └── components/
├── infra/  docker-compose.yml, nginx.conf
├── docs/   ARCHITECTURE.md, DATA-MODEL.md, API.md
└── prompts/ step-00 ... step-07
```

## 7. Yang Sengaja Belum Ada (dan kenapa)

| Fitur | Kenapa ditunda |
|-------|----------------|
| Redis pub/sub | in-process EventBus cukup untuk 1 worker. Redis baru perlu saat multi-instance. |
| Attachment | butuh storage + upload + validasi MIME; bukan inti belajar realtime. |
| Email notif | butuh SMTP/antrian; tidak menambah pemahaman arsitektur. |
| Refresh token | session 7 hari cukup; refresh token = materi lanjutan. |
| Rate limit | bagus untuk produksi, mengaburkan fokus step awal. |
