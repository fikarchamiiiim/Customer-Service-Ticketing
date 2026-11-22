# FLOW — Apa yang Barusan Dibuat (Step 0)

Dokumen ini menjawab satu pertanyaan: **"kalau saya buka http://localhost:5173/health, sebenarnya apa yang terjadi?"**
Semua isi Step 0 dijelaskan sebagai rentetan kejadian, bukan daftar file.

---

## 1. Peta Besar: 4 Proses yang Hidup Bersamaan

Ini yang harus kamu lihat pertama. Ada **empat** proses terpisah, bukan satu:

```text
┌──────────────────────────────────────────────────────────────────────┐
│  PROSES 1: Docker          cs-ticketing-db                           │
│  postgres:16-alpine        port 5432  ·  volume infra_pgdata         │
│  "tempat data"             hidup terus walau BE/FE mati              │
└──────────────────────────────────────────────────────────────────────┘
                              ▲
                              │ TCP 5432 (asyncpg)
┌──────────────────────────────────────────────────────────────────────┐
│  PROSES 2: Backend         uvicorn app.main:app                      │
│  Python / FastAPI          port 8000                                 │
│  "otak + data access"      mati saat kamu Ctrl+C                     │
└──────────────────────────────────────────────────────────────────────┘
                              ▲
                              │ HTTP 8000  (DIPROXY oleh Vite)
┌──────────────────────────────────────────────────────────────────────┐
│  PROSES 3: Frontend dev    vite                                      │
│  Node / Vite               port 5173                                 │
│  "server yang menyajikan React + proxy"                              │
└──────────────────────────────────────────────────────────────────────┘
                              ▲
                              │ HTTP 5173
┌──────────────────────────────────────────────────────────────────────┐
│  PROSES 4: Browser         Chrome/Safari                             │
│  React (sudah jadi JS)     tab http://localhost:5173                 │
│  "yang benar-benar dilihat user"                                     │
└──────────────────────────────────────────────────────────────────────┘
```

**Kunci pemahaman:** browser **tidak pernah** tahu ada port 8000.
Dari sudut pandang browser, semua ada di origin `http://localhost:5173`.

---

## 2. Flow A — Menyalakan Sistem (3 perintah)

```text
$ make up
  └─▶ docker compose -f infra/docker-compose.yml up -d db
        ├─ download image postgres:16-alpine (sekali saja)
        ├─ buat volume infra_pgdata
        ├─ start container cs-ticketing-db
        └─ healthcheck pg_isready tiap 5 detik sampai "healthy"
              (butuh ±40 detik saat pertama kali)

$ make be
  └─▶ uvicorn app.main:app --reload --port 8000
        ├─ import app/main.py
        │    ├─ config.py       → baca .env  → DATABASE_URL, dll
        │    ├─ db/session.py   → BIKIN ENGINE  (BELUM konek ke DB!)
        │    │                     engine itu "malas": koneksi baru dibuka
        │    │                     saat ada query pertama
        │    └─ lifespan()      → log "CS Ticketing API v0.1.0 starting"
        └─ listening 0.0.0.0:8000

$ make fe
  └─▶ vite
        ├─ compile React+TS on the fly (bukan build penuh)
        ├─ baca vite.config.ts → pasang proxy /api dan /ws
        └─ listening localhost:5173
```

**Yang penting di sini:** saat `make be`, backend **belum menyentuh database**.
Engine SQLAlchemy itu lazy. Koneksi baru terjadi saat request pertama datang.
Ini sebabnya kalau Postgres mati, backend **tetap bisa start** — dan baru ketahuan saat ada yang memanggil `/health`.

---

## 3. Flow B — Browser Minta Halaman (HTML + JS)

```text
Browser: GET http://localhost:5173/health
   │
   ▼
┌─────────────────── Vite (5173) ───────────────────┐
│ 1. Vite tidak punya file "/health"                 │
│    → karena ini SPA, semua path dikembalikan       │
│      ke index.html (fallback)                      │
│ 2. Kirim index.html                                │
└────────────────────────────────────────────────────┘
   │
   ▼
Browser menerima HTML:
   <div id="root"></div>
   <script type="module" src="/src/main.tsx"></script>
   │
   ▼
Browser minta /src/main.tsx → Vite compile TypeScript
   → React, React Router, TanStack Query di-inject
   → CSS Tailwind diproses
   │
   ▼
React mulai jalan. Urutan mount:
   main.tsx
     └─ StrictMode
        └─ QueryClientProvider   ← "gudang cache" hidup di sini
           └─ BrowserRouter      ← baca URL "/health"
              └─ App
                 └─ Routes
                    └─ Route element={<Layout/>}   ← dipilih karena path cocok
                       ├─ <header> CS Ticketing | Health | Login
                       ├─ <Outlet/>  ← DI SINI HealthPage dimasukkan
                       │    └─ HealthPage → useQuery({...})
                       └─ <footer> Step 0 — scaffolding
```

**Rantai file-nya** (urutan eksekusi, bukan urutan folder):

| # | File | Perannya |
|---|---|---|
| 1 | [index.html](../frontend/index.html) | kerangka kosong + `<div id="root">` |
| 2 | [main.tsx](../frontend/src/main.tsx) | pasang provider (Query + Router) lalu render `<App/>` |
| 3 | [App.tsx](../frontend/src/App.tsx) | tabel URL → komponen (`/health` → `HealthPage`) |
| 4 | [Layout.tsx](../frontend/src/components/Layout.tsx) | bingkai halaman + `<Outlet/>` (lubang tempat halaman masuk) |
| 5 | [HealthPage.tsx](../frontend/src/pages/HealthPage.tsx) | halaman yang memicu `useQuery` |

`<Outlet/>` itu **lubang**: Layout mengelilingi SEMUA halaman. Halaman lain nanti
(`/tickets`, `/tickets/:id`) otomatis ikut punya header yang sama tanpa menulis ulang.

---

## 4. Flow C — Halaman Minta Data (inti Step 0)

Ini bagian paling penting. Perhatikan **dua origin yang berbeda**:

```text
HealthPage render
   │
   │ useQuery({ queryKey:['health'], queryFn: fetchHealth, refetchInterval:10_000 })
   ▼
fetchHealth()
   └─▶ api.get('/api/v1/health')
         └─▶ fetch('/api/v1/health', { credentials:'include' })
                │
                │  ⚠️ PATH RELATIF. Tidak ada "localhost:8000" di sini.
                ▼
        ═══════════ BROWSER: origin = http://localhost:5173 ═══════════
                │
                │  browser kirim: GET http://localhost:5173/api/v1/health
                ▼
┌───────────────────── Vite dev server (5173) ──────────────────────┐
│  vite.config.ts:                                                  │
│    '/api' → { target: 'http://localhost:8000' }                   │
│                                                                   │
│  Vite MELIHAT path /api → TIDAK menyajikan file.                  │
│  Vite meneruskan (proxy) ke localhost:8000, dengan               │
│  path yang SAMA: /api/v1/health                                   │
└───────────────────────────────────────────────────────────────────┘
                │
                │  server-to-server: GET http://localhost:8000/api/v1/health
                ▼
┌───────────────────── FastAPI (8000) ──────────────────────────────┐
│  router: app/api/v1/health.py → GET /health                       │
│  (prefix /api/v1 ditambahkan di main.py)                          │
│                                                                   │
│  async def health():                                              │
│      db_ok, db_error = await check_db()                           │
│                        │                                          │
│                        └─▶ db/session.py:                         │
│                            engine.connect()   ← BARU sekarang     │
│                            execute("SELECT 1") ← BARU sekarang    │
│                                   │                               │
│                                   ▼                               │
│                        ═══ Postgres (5432) ═══                    │
│                              SELECT 1 → 1                         │
│                                   │                               │
│                            sukses → (True, None)                  │
│                            gagal  → (False, "pesan error")        │
│                                                                   │
│  return {"status":"ok", "db":"ok", "db_error":null, "version":...}│
└───────────────────────────────────────────────────────────────────┘
                │
                │  HTTP 200 JSON
                ▼
        ═══════════ kembali ke BROWSER (5173) ═══════════
                │
                ▼
api/client.ts:                                                   
   res.ok → true                                                   
   text = '{"status":"ok",...}'                                    
   JSON.parse → object                                             
   return data                                                     
                │
                ▼
TanStack Query menyimpan ke cache dengan key ['health']
                │
                ▼
data = {...},  isLoading = false,  isFetching = false
                │
                ▼
React render ulang:
   <StatusDot ok={data.status==='ok'} label="API: ok" />
   <StatusDot ok={data.db==='ok'}     label="DB: ok"  />
   <pre>{JSON.stringify(data,null,2)}</pre>
                │
                ▼
🟢 API: ok   🟢 DB: ok
```

### Rantai 4 lapis yang perlu kamu hafal

```text
fetch('/api/v1/health')
      ↓  (1) Vite mem-proxy
http://localhost:8000/api/v1/health
      ↓  (2) FastAPI memilih router
health.router → GET /health
      ↓  (3) service memanggil DB
engine.connect() → SELECT 1
      ↓  (4) hasil naik kembali lewat jalur yang sama
JSON → cache TanStack → render
```

Kalau suatu hari halaman bilang "DB: down", kamu bisa menebak di lapis mana masalahnya:
koneksi internet? proxy? router? atau Postgres?

---

## 5. Flow D — Polling (Kenapa Berkedip Tiap 10 Detik)

```text
t = 0s     mount → isLoading=true, isFetching=true → fetch #1
t = 0.2s   sukses → data ada, isLoading=false
t = 10s    refetchInterval menyala → isFetching=true  (data LAMA tetap tampil!)
t = 10.2s  sukses → isFetching=false
t = 20s    ... ulangi
```

Bedanya:

- `isLoading` → hanya **sekali**, saat belum punya data sama sekali.
- `isFetching` → **setiap kali** ada permintaan, termasuk yang di latar belakang.

Itu sebabnya halaman ini memakai:
- `isLoading` untuk teks "Memeriksa…" (hanya muncul saat buka halaman)
- `isFetching` untuk label tombol (berubah tiap 10 detik)

---

## 6. Flow E — Tiga Skenario Kegagalan

Sengaja dirancang supaya kamu bisa membedakan **di mana** masalahnya.

### E1. Backend mati (Postgres hidup)
```text
fetch('/api/v1/health')
  → Vite proxy gagal konek ke :8000
  → proxy balas 500 (atau koneksi ditolak)
  → api/client.ts: res.ok=false → throw ApiError
  → useQuery: isError=true
  → UI: "API: tidak terjangkau" 🔴
```

### E2. Postgres mati (backend hidup)
```text
fetch → :8000 sampai di FastAPI ✓
  → check_db() → engine.connect() DITOLAK
  → except → return (False, "Connect call failed ...")
  → HTTP 200 tapi body: {"status":"degraded","db":"down","db_error":"..."}
  → api/client.ts: res.ok=TRUE (200 kan) → tidak throw
  → useQuery: data.db === 'down'
  → UI: "API: ok" 🟢  "DB: down" 🔴
```

**Perhatikan bedanya:** kalau backend mati, kamu dapat **error** (merah semua).
Kalau cuma DB mati, kamu dapat **200 dengan status degraded** — karena backend masih
sehat, dia hanya melaporkan bahwa DB-nya bermasalah. Ini desain sengaja: satu layar
bisa menunjukkan "yang mana yang rusak".

### E3. Keduanya hidup tapi tabel belum ada
Tidak terjadi di Step 0, karena belum ada tabel. Mulai Step 1, ini akan relevan:
`SELECT 1` selalu jalan (tidak butuh tabel), tapi query ke `tickets` akan gagal
sampai `alembic upgrade head` dijalankan.

---

## 7. Flow F — Kenapa Harus Proxy (Bukan `localhost:8000` Langsung)

Kalau FE memanggil `http://localhost:8000` langsung:

```text
Browser melihat: origin FE = 5173, tujuan = 8000
  → BEDA ORIGIN
  → CORS harus diaktifkan (sudah ada di main.py, tapi...)
  → cookie httpOnly dengan SameSite=Lax TIDAK terkirim lintas origin
  → WebSocket butuh pengecualian CORS lagi
  → di produksi harus diubah lagi
```

Dengan proxy:

```text
Browser melihat: origin FE = 5173, tujuan = 5173  (SAMA)
  → tidak ada CORS
  → cookie terkirim otomatis  ✅ (penting di Step 2)
  → handshake WebSocket lolos otomatis  ✅ (penting di Step 4)
  → di produksi: nginx melakukan hal yang sama persis
```

Itulah alasan [vite.config.ts](../frontend/vite.config.ts) punya blok `/ws` **sejak Step 0**,
padahal WebSocket baru dipakai di Step 4. Lebih murah menyiapkannya sekarang
daripada mengubah struktur di tengah jalan.

---

## 8. Peta File → Peran dalam Flow

```text
infra/docker-compose.yml  ── proses 1 (Postgres)          Flow A
.env / .env.example       ── sumber DATABASE_URL           Flow A, C
Makefile                  ── pintasan 3 perintah            Flow A

backend/app/config.py     ── baca env → Settings           Flow A
backend/app/db/session.py ── engine + check_db()           Flow A, C, E2
backend/app/api/v1/health.py ── router GET /health         Flow C
backend/app/main.py       ── rakit router + CORS + lifespan Flow C

frontend/vite.config.ts   ── proxy /api & /ws              Flow B, C, F
frontend/index.html       ── kerangka HTML                 Flow B
frontend/src/main.tsx     ── provider + render             Flow B
frontend/src/App.tsx      ── tabel URL → komponen          Flow B
frontend/src/components/Layout.tsx ── bingkai + <Outlet/>  Flow B
frontend/src/pages/HealthPage.tsx  ── useQuery + render    Flow C, D, E
frontend/src/api/health.ts ── fetchHealth()                Flow C
frontend/src/api/client.ts ── satu pintu HTTP + ApiError   Flow C, E
frontend/src/components/StatusDot.tsx ── titik hijau/merah Flow C, E
```

---

## 9. Di Mana Step Berikutnya "Menyisip"

Flow di atas adalah kerangka kosong yang akan diisi. Ini peta penyisipannya:

```text
Flow C sekarang:
  fetch /api/v1/health → FastAPI → SELECT 1

Step 1 (Data Layer):
  + tabel users, tickets, ticket_messages di Postgres
  + Alembic (cara membuat tabel, bukan create_all)
  + SELECT 1 tetap ada, tapi kini ada data nyata untuk di-query

Step 2 (Auth):
  Flow C ditambah SEBELUM router:
     cookie 'session' ada? → decode → user  (atau 401)
  + halaman /login benar-benar memanggil Google
  + ProtectedRoute menyisip di App.tsx

Step 3 (Tiket):
  Flow C dipakai untuk GET /api/v1/tickets
  + queryKey ['tickets', filter] — pola key berparameter
  + refetch MANUAL (tombol), belum realtime

Step 4 (WebSocket):
  + jalur BARU di samping Flow C:
     browser ──ws──▶ /ws ──proxy──▶ FastAPI
     (bukan request-response, tapi koneksi yang TETAP TERBUKA)
  + ConnectionBadge di header

Step 5 (Chat):
  + Flow C untuk POST pesan (masih HTTP!)
  + WebSocket hanya MENGIRIM event balik ke semua tab
  + refetchInterval di halaman tiket DIHAPUS, diganti subscribe
```

**Poin besar yang perlu kamu bawa ke Step 4:** WebSocket **tidak menggantikan** HTTP.
Ia menambah jalur kedua yang hidup bersamaan. HTTP tetap dipakai untuk semua perintah;
WS hanya untuk memberi tahu "ada yang berubah".

---

## 10. Ringkasan Satu Paragraf

Kamu membuka `localhost:5173`, Vite menyajikan React, React memakai TanStack Query untuk
meminta `/api/v1/health` dengan path relatif, Vite mem-proxy request itu ke
`localhost:8000` sehingga browser tetap merasa satu origin, FastAPI memilih router,
router memanggil `check_db()`, SQLAlchemy membuka koneksi pertama ke Postgres dan
menjalankan `SELECT 1`, hasilnya naik kembali lewat jalur yang sama, Query menyimpannya
di cache dengan key `['health']`, dan React merender dua titik hijau. Sepuluh detik
kemudian seluruh rantai itu diulang otomatis.
