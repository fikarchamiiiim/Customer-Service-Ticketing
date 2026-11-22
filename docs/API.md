# API Contract

Base URL (dev, lewat Vite proxy): `/api/v1`
Auth: cookie `session` (httpOnly, SameSite=Lax). Semua request FE pakai `credentials: 'include'`.

## Error Envelope (dibakukan di Step 7, dipakai sejak awal)

```json
{ "error": { "code": "ILLEGAL_TRANSITION", "message": "open tidak bisa langsung ke resolved", "details": null } }
```

Kode yang dipakai: `UNAUTHORIZED`, `FORBIDDEN`, `NOT_FOUND`, `VALIDATION_ERROR`,
`ILLEGAL_TRANSITION`, `CONFLICT`, `INTERNAL`.

## HTTP Endpoints

### System
| Method | Path | Auth | Keterangan |
|---|---|---|---|
| GET | `/health` | – | `{status, db, version}` |

### Auth
| Method | Path | Auth | Body / Keterangan |
|---|---|---|---|
| POST | `/auth/google` | – | `{id_token}` → set cookie, balikan `user` |
| POST | `/auth/dev-login` | – (hanya `DEV_AUTH=true`) | `{email}` → set cookie |
| GET | `/me` | ✔ | `user` |
| POST | `/auth/logout` | ✔ | hapus cookie |

### Tickets
| Method | Path | Auth | Keterangan |
|---|---|---|---|
| POST | `/tickets` | ✔ | `{subject, description, priority?}` → 201 `ticket` |
| GET | `/tickets` | ✔ | query: `status`, `assignee=me|unassigned`, `scope=mine|all`, `cursor`, `limit` |
| GET | `/tickets/{id}` | ✔ | 404 kalau bukan miliknya (customer) |
| PATCH | `/tickets/{id}` | ✔ | `{status?, assignee_id?, priority?}` → 422 kalau transisi ilegal |
| GET | `/tickets/{id}/messages` | ✔ | query `before_id`, `limit` (default 50) |
| POST | `/tickets/{id}/messages` | ✔ | `{body, is_internal?}` → 201 `message` |

Pagination: cursor-based (`id DESC`), bukan offset — konsisten walau ada data baru masuk.

## WebSocket

Endpoint: `GET /ws` — handshake membawa cookie `session`.
Kalau cookie tidak valid: tutup dengan kode **4401** (aplikasi), bukan 1008, supaya FE bisa bedakan.

### Envelope
```json
{ "v": 1, "type": "message.created", "channel": "ticket:12", "data": { ... }, "ts": "2026-11-22T08:00:00Z" }
```

### Client → Server
```json
{ "type": "subscribe",   "channel": "ticket:12" }
{ "type": "unsubscribe", "channel": "ticket:12" }
{ "type": "typing",      "channel": "ticket:12" }
{ "type": "ping" }
```

### Server → Client
| type | channel | data |
|---|---|---|
| `subscribed` | – | `{channel}` |
| `unsubscribed` | – | `{channel}` |
| `message.created` | `ticket:{id}` | objek message lengkap |
| `ticket.created` | `agents` | objek ticket |
| `ticket.updated` | `ticket:{id}`, `agents` | `{ticket, changes}` |
| `typing` | `ticket:{id}` | `{user_id, name}` |
| `presence` | `ticket:{id}` | `{user_id, online}` |
| `error` | – | `{code, message}` (mis. `CHANNEL_FORBIDDEN`) |
| `pong` | – | `{ts}` |

### Otorisasi channel
| channel | syarat |
|---|---|
| `ticket:{id}` | user boleh membaca tiket itu (aturan sama seperti `GET /tickets/{id}`) |
| `user:{id}` | `id == me.id` |
| `agents` | role `agent` atau `admin` |

Ditolak → kirim `error CHANNEL_FORBIDDEN`, **jangan** tutup koneksi (satu channel salah tidak boleh mematikan sesi).

### Heartbeat
Client kirim `ping` tiap 25 detik. Server tidak menerima apa pun selama 60 detik → tutup koneksi.
FE mendeteksi close → reconnect dengan exponential backoff (1s, 2s, 4s, 8s, maks 30s + jitter).
