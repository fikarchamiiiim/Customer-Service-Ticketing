# CS Ticketing — Roadmap Belajar Step-by-Step

> Dokumen ini adalah **kontrak proyek**. Setiap sesi kerja (tiap step) mengacu ke sini.
> Stack: FastAPI (Python) + React TS + PostgreSQL + HTTP/WebSocket.
> Tujuan: **belajar**, bukan produksi. Sederhana tapi tidak asal-asalan.

---

## 0. Ringkasan Penilaian

Ide kamu **sudah tepat dan realistis** untuk proyek belajar: domainnya jelas (tiket + percakapan),
ada realtime yang benar-benar bermakna (bukan realtime tempelan), dan pemisahan
"HTTP untuk non-realtime, WebSocket untuk realtime" itu justru keputusan arsitektur yang bagus.

**Skor kesiapan: 8/10.**

Yang kurang cuma 3 hal besar:

1. **Role / RBAC** — tanpa ini, ticketing tidak punya makna (customer dan agent harus beda hak akses).
2. **State machine status tiket** — tanpa aturan transisi, data status akan jadi sampah.
3. **Aturan tegas kapan pakai HTTP vs WebSocket** — ini yang paling sering bikin proyek realtime berantakan.

Ketiganya bisa ditambahkan **tanpa** menambah kompleksitas berarti, dan justru menambah materi belajar.

---

## 1. Masukan

### 1.1 Yang sudah bagus (pertahankan)

- **Stack mainstream.** FastAPI + React TS + Postgres = paling banyak referensi, gampang cari jawaban.
- **Pemisahan protokol benar.** Realtime hanya untuk *push event*, sisanya HTTP.
- **Google SSO.** Menghemat waktu, sekaligus jadi materi belajar OAuth/OIDC yang nyata.
- **Scope kecil.** "Hanya untuk belajar" = boleh memotong fitur. Ini kekuatan, bukan kelemahan.

### 1.2 Yang perlu ditambahkan (wajib, kecil tapi penting)

| # | Masukan | Kenapa | Ditaruh di |
|---|---------|--------|-----------|
| 1 | **2 role: customer & agent** (+ flag admin opsional) | Tanpa role, tidak ada beda hak akses → aplikasi tidak masuk akal | Step 1 & 2 |
| 2 | **State machine tiket** (open → in_progress → resolved → closed, + reopen) | Mencegah status acak, sekaligus materi belajar validasi domain | Step 3 |
| 3 | **Aturan: semua *command* lewat HTTP, WS hanya *event*** | WS tidak punya status code/retry/validasi. Command via HTTP = gampang di-test, gampang di-debug | Step 3-5 |
| 4 | **Auth WebSocket lewat cookie httpOnly** (bukan query token) | Token di URL ikut ke-log server/proxy. Cookie otomatis terkirim saat handshake | Step 4 |
| 5 | **Alembic dari hari pertama** | Jangan pakai `create_all()`. Migrasi = materi penting & bikin reset DB gampang | Step 1 |
| 6 | **Dev-login fallback** (`DEV_AUTH=true`) | Setup Google Cloud Console sering jadi tembok pertama. Fallback bikin kamu tidak macet | Step 2 |
| 7 | **Simpan waktu dalam UTC**, tampilkan di Asia/Jakarta | Klasik bug; belajar dari awal | Step 1 |
| 8 | **Postgres via Docker Compose** | Kamu belum punya `psql` lokal; Docker sudah ada. Sekali setup, konsisten | Step 0 |
| 9 | **Jangan simpan JWT di localStorage** → pakai cookie httpOnly | Aman dari XSS *dan* bikin auth WS jadi gratis | Step 2 |
| 10 | **Vite proxy `/api` & `/ws`** ke backend | FE & BE jadi satu origin → cookie & WS tanpa drama CORS | Step 0 |
| 11 | **Envelope event versi** (`type`, `channel`, `data`) | Kontrak realtime yang stabil, gampang ditambah event baru | Step 4 |
| 12 | **Dedupe pesan by id** di FE | Pesan muncul 2x (dari response POST + dari WS) adalah bug realtime #1 | Step 5 |

### 1.3 Yang sebaiknya JANGAN dulu (biar tetap "sederhana")

Simpan untuk setelah Step 7 selesai, kalau masih semangat:

- Attachment / upload file
- Email / WhatsApp notification
- SLA timer, eskalasi, CSAT rating
- Redis pub/sub & multi-instance WS
- Multi-tenant, i18n, dark mode, RBAC granular (permission matrix)
- Full-text search (Postgres `tsvector`)

### 1.4 Risiko yang paling sering bikin learner macet

1. **Google OAuth setup** (consent screen, redirect URI, "app not verified").
   → Mitigasi: Step 2 punya dev-login fallback + checklist Google Console.
2. **WebSocket "kenapa tidak connect"** tanpa pesan error jelas.
   → Mitigasi: Step 4 wajib ada badge status koneksi di UI + log handshake di BE.
3. **Bingung WS vs HTTP** → kirim pesan lewat WS, lalu bingung error handling.
   → Mitigasi: aturan tertulis di `docs/ARCHITECTURE.md`.
4. **DB schema berubah tapi lupa migrasi** → data rusak.
   → Mitigasi: Alembic sejak Step 1, `make db-reset`.
5. **Cookie tidak terkirim di dev** (beda port) → login "berhasil" tapi selalu 401.
   → Mitigasi: Vite proxy (satu origin), `SameSite=Lax`.

---

## 2. Keputusan Teknis Final

| Area | Pilihan | Alasan |
|------|---------|--------|
| BE framework | FastAPI + Uvicorn | async, docs otomatis, ringan |
| ORM | SQLAlchemy 2.0 **async** + asyncpg | standar, sudah support `async` |
| Migrasi | Alembic | jangan `create_all()` |
| Validasi | Pydantic v2 + pydantic-settings | bawaan ekosistem FastAPI |
| Auth | Google ID Token (GIS button) → **session JWT di cookie httpOnly** | paling sedikit langkah, tanpa redirect flow |
| JWT lib | PyJWT | sederhana; verifikasi Google pakai `google-auth` |
| FE build | Vite + React 19 + TS | cepat, minim konfigurasi |
| Router | react-router v7 (data router) | standar |
| Data fetching | TanStack Query v5 | cache, refetch, invalidate — cocok untuk "event → invalidate" |
| Styling | Tailwind CSS v4 | cepat, tidak perlu desain |
| WS client | `WebSocket` native + wrapper reconnect sendiri | belajar reconnection, bukan disembunyikan library |
| Testing BE | pytest + pytest-asyncio + httpx ASGITransport | ringan, tanpa server nyata |
| Testing FE | (opsional) Vitest | jangan di Step 0-5 |
| Package manager FE | `npm` | kamu belum punya pnpm; jangan tambah variabel |
| Python | 3.10 (terpasang) — kalau mau, upgrade ke 3.12 | 3.10 aman untuk stack ini |
| DB dev | Postgres 16 via Docker Compose | praktis |

Catatan lingkungan kamu (sudah dicek): Python 3.10.0, Node v26.13.1, npm 11.20.0, Docker 28.2.2 + Compose v2.36.2, git 2.39.3.
**Tidak ada** pnpm, uv, dan psql lokal → semua pakai Docker/npm.

---

## 3. Roadmap (8 Step)

| Step | Judul | Isi singkat | Estimasi |
|------|-------|-------------|----------|
| **0** | Fondasi & Scaffolding | repo, docker postgres, BE health check, FE shell, proxy | 2-3 jam |
| **1** | Data Layer | SQLAlchemy models, Alembic, seed, pytest DB fixture | 3-4 jam |
| **2** | Auth Google SSO | verifikasi ID token, session cookie, protected route, dev-login | 4-5 jam |
| **3** | Tiket via HTTP | CRUD tiket, RBAC, state machine, halaman list/detail/form | 5-6 jam |
| **4** | Fondasi WebSocket | endpoint `/ws`, auth cookie, channel/room, heartbeat, reconnect | 3-4 jam |
| **5** | Chat Realtime | broadcast pesan, append + dedupe, riwayat, typing indicator | 4-5 jam |
| **6** | Notifikasi & Presence | tiket baru → agent, update status live, presence, activity log | 3-4 jam |
| **7** | Hardening & Docs | error envelope, test, logging, README, docker compose full | 3-4 jam |

Total realistis: **± 30 jam** kerja santai (2-3 minggu kalau 1-2 jam/hari).

Alur tiap step: **kerjakan → verifikasi → tanya "lanjut?" → baru step berikutnya.**
Setiap step punya file prompt siap-pakai di folder `prompts/`.

---

## 4. Detail Per Step

### Step 0 — Fondasi & Scaffolding
**Tujuan:** tiga terminal jalan bersamaan: DB, BE, FE. Belum ada fitur, tapi sudah "hidup".

- **0.1** Struktur repo: `backend/`, `frontend/`, `infra/`, `docs/`, `prompts/`
- **0.2** `docker compose` untuk Postgres 16 (volume, healthcheck, port 5432, db `ticketing`)
- **0.3** `Makefile` (`make up`, `make be`, `make fe`, `make db-reset`) + `.env.example`
- **0.4** BE skeleton: `app/main.py`, `settings.py` (pydantic-settings), `GET /api/v1/health`
- **0.5** FE skeleton: Vite + TS + Tailwind, layout shell (header/sidebar), `/login` dummy
- **0.6** Vite proxy `/api` + `/ws` (`ws: true`) → lokal jadi satu origin
- **0.7** Halaman `/health` memanggil API dan menampilkan status DB

**DoD:** `docker compose up -d db` sehat; `make be` → `/docs` terbuka; `make fe` → UI menampilkan "API: ok / DB: ok".

---

### Step 1 — Data Layer
**Tujuan:** skema DB yang benar, dibuat lewat migrasi, plus data contoh.

- **1.1** Engine & session async, dependency `get_db`
- **1.2** Models: `User`, `Ticket`, `TicketMessage` (+ enum role/status/priority)
- **1.3** Alembic init + migrasi pertama; enum & index ikut
- **1.4** Seed script: 2 agent, 2 customer, 3 tiket, beberapa pesan
- **1.5** `ticket_no` human-readable dari sequence (`TKT-000001`)
- **1.6** pytest fixture DB (database test terpisah, transaksi di-rollback)

**DoD:** `alembic upgrade head` & `downgrade` jalan bolak-balik; seed idempotent; 1 test insert user lulus.

---

### Step 2 — Auth Google SSO
**Tujuan:** login Google → dapat sesi → endpoint terproteksi.

- **2.1** Checklist Google Cloud Console (project, OAuth consent, Client ID web, authorized origin)
- **2.2** `POST /api/v1/auth/google` { id_token } → verifikasi (`google-auth`) → find-or-create user
- **2.3** Terbitkan session JWT → cookie httpOnly/SameSite=Lax (7 hari)
- **2.4** `GET /api/v1/me`, `POST /api/v1/auth/logout`, dependency `get_current_user`, `require_role(...)`
- **2.5** `POST /api/v1/auth/dev-login` (hanya jika `DEV_AUTH=true`)
- **2.6** FE: tombol Google (GIS), `AuthContext`, `ProtectedRoute`, redirect by role, tombol logout
- **2.7** Tabel allowlist email agent → otomatis jadi `agent` saat login pertama

**DoD:** login Google → cookie ada (httpOnly) → `/me` 200; tanpa cookie → 401; customer buka `/agent` → ditolak; logout menghapus cookie.

---

### Step 3 — Tiket via HTTP
**Tujuan:** seluruh siklus tiket tanpa realtime dulu. Ini "tulang punggung" aplikasi.

- **3.1** Pydantic schemas (request/response) + validasi panjang field
- **3.2** `POST /tickets`, `GET /tickets` (filter status, `mine`, pagination), `GET /tickets/{id}`
- **3.3** RBAC scoping: customer hanya tiket miliknya; agent semua
- **3.4** `PATCH /tickets/{id}`: assign, ubah status (state machine + 422 kalau transisi ilegal), priority
- **3.5** `POST /tickets/{id}/messages`, `GET /tickets/{id}/messages` (cursor `before_id`), internal note (agent only)
- **3.6** FE: `/tickets` (customer: milikku, agent: queue + filter), `/tickets/new`, `/tickets/:id`

**DoD:** customer tidak bisa melihat tiket orang lain (403/404); agent lihat semua; `open→resolved` ditolak 422; UI bisa buat, balas, ubah status.

---

### Step 4 — Fondasi WebSocket
**Tujuan:** koneksi realtime yang bisa diandalkan — belum ada chat.

- **4.1** Endpoint `GET /ws` + `ConnectionManager` (registry koneksi & room/channel)
- **4.2** Auth handshake: baca cookie sesi → decode → tolak 4401 kalau invalid
- **4.3** Kontrak envelope: `v`, `type`, `channel`, `data`, `ts` + `subscribe`/`unsubscribe`
- **4.4** Heartbeat: client `ping` / server `pong`; server tutup koneksi mati
- **4.5** Otorisasi channel: subscribe `ticket:{id}` divalidasi sama seperti `GET /tickets/{id}`
- **4.6** FE `socket.ts`: connect, reconnect backoff, queue subscribe, badge status (● connected / ○ reconnecting)

**DoD:** buka 2 tab → keduanya "connected"; kill BE → badge jadi reconnecting → BE naik → auto connected tanpa refresh; subscribe tiket orang lain ditolak `error`.

---

### Step 5 — Chat Realtime
**Tujuan:** percakapan hidup. Ini inti fitur.

- **5.1** Event bus in-process: `publish(channel, type, data)` (nol dependency, cukup `asyncio`)
- **5.2** `POST /messages` → simpan → publish `message.created` ke `ticket:{id}` (sender ikut terima)
- **5.3** Emit `message.created` juga ke channel `user:{id}` penerima (notifikasi)
- **5.4** FE: optimistic append + dedupe by `id`, auto-scroll, riwayat `before_id` saat buka
- **5.5** Typing indicator (ephemeral, tidak disimpan, auto-expire 3 detik)
- **5.6** Internal note tidak pernah dikirim ke channel customer

**DoD:** pesan muncul <1 detik di tab lain tanpa refresh; tidak dobel; refresh tetap lengkap; indicator typing tampil dan hilang.

---

### Step 6 — Notifikasi, Presence, Activity
**Tujuan:** produk terasa "hidup", bukan cuma chat.

- **6.1** `ticket.created` → channel `agents` → queue agent auto-refresh (TanStack invalidate) + toast
- **6.2** `ticket.updated` (status/assignee) → detail & list ikut update
- **6.3** Presence: daftar agent online (in-memory) + indikator "dilihat oleh"
- **6.4** Tabel `ticket_events` (jsonb payload) sebagai activity log + timeline di detail
- **6.5** Unread counter per user (last_read_at pada partisipan tiket)

**DoD:** tiket baru muncul di tab agent tanpa refresh; status berubah live di tab lain; timeline menampilkan riwayat; angka unread masuk akal.

---

### Step 7 — Hardening & Dokumentasi
- **7.1** Error envelope seragam: `{ "error": { "code", "message", "details" } }` + handler global
- **7.2** Test: auth, RBAC, state machine, WS subscribe (pytest), jalankan di `make test`
- **7.3** Logging (`structlog`/logging) + request id + log handshake WS
- **7.4** README: cara run, cara login, troubleshooting 5 error tersering
- **7.5** Docker Compose full: db + api + nginx (FE static + proxy `/api`, `/ws`)
- **7.6** "Next steps" doc: Redis pub/sub untuk multi-instance, attachment, dsb.

**DoD:** `docker compose up` satu perintah → aplikasi jalan; `make test` hijau; README cukup untuk orang lain menjalankan.

---

## 5. Aturan Main Sesi Belajar

1. **Satu step per sesi.** Selesai → verifikasi → **AI berhenti dan bertanya** "Step X selesai. Lanjut Step X+1?" Jangan lanjut sendiri.
2. **Jangan lompat step.** Step 4 (WS) bergantung pada Step 2 (auth) dan Step 3 (otorisasi tiket).
3. **Verifikasi dulu, baru lanjut.** Kalau DoD gagal, perbaiki di step yang sama.
4. **Tanya "kenapa", bukan cuma "buatkan".** Setiap prompt meminta penjelasan singkat alasan desain.
5. **Commit per step** (`feat: step-0 scaffolding`) supaya bisa balik kalau rusak.

---

## 6. File Pendukung

| File | Isi |
|------|-----|
| `docs/ARCHITECTURE.md` | diagram, alur login, alur kirim pesan, aturan HTTP vs WS |
| `docs/DATA-MODEL.md` | tabel, kolom, enum, index, aturan transisi status |
| `docs/API.md` | kontrak HTTP + kontrak event WebSocket |
| `prompts/CONTEXT.md` | konteks bersama yang dipakai semua step prompt |
| `prompts/step-00..07*.md` | prompt siap-pakai per step |
