# Step 00 — Fondasi & Scaffolding

> **Baca `prompts/CONTEXT.md` dulu** (aturan kerja, stack, format laporan).
> **Kerjakan HANYA step ini.** Setelah DoD terpenuhi, berhenti dan tanya apakah lanjut.

## Prompt (tempel ini ke agent)

```text
Kerjakan Step 00 (Fondasi & Scaffolding) dari proyek CS Ticketing.

Baca dulu: prompts/CONTEXT.md, ROADMAP.md, docs/ARCHITECTURE.md, docs/DATA-MODEL.md, docs/API.md.

## Tujuan
Tiga proses jalan bersamaan: **DB, backend, frontend**. Belum ada fitur, tapi sistemnya "hidup" end-to-end.

## Prasyarat
`~/Development/cs-ticketing` sudah ada (berisi `ROADMAP.md`, `docs/`, `prompts/`).

## Sub-step (kerjakan berurutan)
1. **0.1 Struktur repo** — buat folder `backend/`, `frontend/`, `infra/`, `docs/`, `prompts/`; `.gitignore` (Python venv, node_modules, .env, __pycache__, dist); `git init` + commit awal.
2. **0.2 Postgres** — `infra/docker-compose.yml`: service `db`, image `postgres:16-alpine`, `POSTGRES_DB=ticketing`, `POSTGRES_USER=ticketing`, password dari `.env`, port `5432:5432`, volume named, `healthcheck pg_isready`.
3. **0.3 Konfigurasi** — `.env.example` di root: `DATABASE_URL`, `JWT_SECRET`, `GOOGLE_CLIENT_ID`, `SESSION_COOKIE_NAME=session`, `DEV_AUTH=true`, `ALLOWED_ORIGINS`. `Makefile` di root: `up`, `down`, `be`, `fe`, `db-reset`, `psql`.
4. **0.4 Skeleton BE** — venv + `pip install fastapi "uvicorn[standard]" sqlalchemy asyncpg alembic pydantic-settings python-dotenv`. `app/main.py`, `app/config.py` (pydantic-settings baca `.env`), CORS untuk `http://localhost:5173`. Endpoint `GET /api/v1/health` → `{status:"ok", db:"ok"|"down", version}` dengan `SELECT 1` async.
5. **0.5 Skeleton FE** — `npm create vite@latest frontend -- --template react-ts`, lalu Tailwind v4 + `react-router-dom` + `@tanstack/react-query`. Layout shell (header + outlet), halaman `/login` dummy, `/health` yang memanggil API dan menampilkan status BE + DB.
6. **0.6 Vite proxy** — `server.proxy` di `vite.config.ts`: `/api → http://localhost:8000` dan `/ws → ws://localhost:8000` dengan `ws: true`. FE memanggil `/api/v1/...` (relatif), **bukan** `localhost:8000`.
7. **0.7 README** — cara run: `make up && make be && make fe`.

## Verifikasi (tempel output nyata)
```bash
docker compose -f infra/docker-compose.yml up -d db
docker compose -f infra/docker-compose.yml ps      # db harus "healthy"
curl -s localhost:8000/api/v1/health | jq          # {"status":"ok","db":"ok",...}
cd frontend && npm run build                       # harus sukses tanpa error TS
```
Buka `http://localhost:5173/health` → tampil "API: ok / DB: ok".

## Batasan
- **Belum ada** model SQLAlchemy, tabel, login sungguhan, atau WebSocket.
- Jangan pakai pnpm/uv (tidak tersedia di mesin ini).

## Penutup
Setelah semua verifikasi lolos dan DoD tercapai: **berhenti** dan tanya
*"Step 0 selesai. Lanjut ke Step 1 (Data Layer)?"* — jangan mengerjakan Step 1.

Aturan: jangan kerjakan step berikutnya, jangan tambah dependency di luar stack,
setiap perubahan skema lewat migrasi Alembic, verifikasi dengan output nyata (bukan asumsi),
dan akhiri dengan blok laporan sesuai CONTEXT.md.
```
