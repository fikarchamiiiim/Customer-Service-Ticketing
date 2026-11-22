# CS Ticketing

Aplikasi ticketing customer service sederhana — **proyek belajar**.
FastAPI + React TS + PostgreSQL, HTTP untuk command, WebSocket untuk event realtime.

Roadmap lengkap: [ROADMAP.md](ROADMAP.md)

## Status

| Step | Judul | Status |
|---|---|---|
| 0 | Fondasi & Scaffolding | ✅ |
| 1 | Data Layer | ✅ |
| 2 | Auth Google SSO | ✅ |
| 3 | Tiket via HTTP | ✅ |
| 4 | Fondasi WebSocket | ⬜ |
| 5 | Chat Realtime | ⬜ |
| 6 | Notifikasi & Presence | ⬜ |
| 7 | Hardening & Docs | ⬜ |

## Alur singkat

1. **Customer** login → `/tickets` → "Tiket baru" → mengisi subjek + deskripsi
2. **Agent** login → `/tickets` (scope=all) → filter status/assignee → buka tiket → ambil tiket → balas / internal note → ubah status
3. Status mengikuti state machine: `open → in_progress → resolved → closed` (+ reopen dari `resolved`)

## Prasyarat

- Python 3.10+
- Node 20+
- Docker + Docker Compose

## Menjalankan (3 terminal)

```bash
# 1. Database
make up

# 2. Backend  (http://localhost:8000)
#    Login Google? lihat docs/GOOGLE-SETUP.md. Tanpa itu, pakai panel Dev login.
make install-be        # sekali saja
make be

# 3. Frontend (http://localhost:5173)
make install-fe        # sekali saja
make fe
```

Buka http://localhost:5173/health → harus tampil **API: ok / DB: ok**.

## Perintah lain

| Perintah | Fungsi |
|---|---|
| `make health` | curl endpoint health, format JSON |
| `make psql` | shell psql ke database |
| `make db-reset` | hapus volume DB & buat ulang (data hilang) |
| `make build` | typecheck + build frontend |
| `make test` | jalankan pytest (DB test terpisah, auto rollback) |
| `make migrate` | `alembic upgrade head` |
| `make seed` | isi data contoh (aman diulang) |
| `make revision m="tambah tabel x"` | buat migrasi baru dari selisih model |
| `make reset-all` | hapus DB → migrasi → seed (mulai bersih) |

## Struktur

```
backend/   FastAPI (app/, venv/.venv)
frontend/  React + Vite
infra/     docker-compose.yml
docs/      arsitektur, data model, kontrak API, flow per step
           (mulai dari docs/FLOW-STEP-0.md)
prompts/   prompt per step
```

## Troubleshooting

| Gejala | Sebab / solusi |
|---|---|
| `DB: down` di halaman health | Postgres belum siap → `make up`, cek `make logs`, tunggu status *healthy* |
| `API: tidak terjangkau` | Backend belum jalan → `make be` |
| `port is already allocated` | Port 5432 dipakai Postgres lain → stop container itu atau ubah `ports` di infra/docker-compose.yml |
| Frontend jalan tapi API 404 | Pastikan `vite.config.ts` mem-proxy `/api`; jangan panggil `localhost:8000` langsung |

Catatan: proyek ini memakai satu origin (Vite proxy) — sengaja, supaya cookie sesi dan
WebSocket nanti tidak perlu konfigurasi CORS tambahan.
