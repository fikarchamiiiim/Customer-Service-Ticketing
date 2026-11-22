# CONTEXT — baca dulu sebelum mengerjakan step apa pun

## Proyek
Aplikasi **CS Ticketing** sederhana untuk **belajar**. Bukan produksi: utamakan kejelasan kode
dan pemahaman konsep di atas kelengkapan fitur. Kode harus tetap rapi, tapi jangan over-engineer.

Repo: `cs-ticketing/` di `/Users/zulfikarchamim/Development`
Dokumen acuan: `ROADMAP.md`, `docs/ARCHITECTURE.md`, `docs/DATA-MODEL.md`, `docs/API.md`

## Stack (jangan diganti tanpa alasan kuat)
- BE: Python 3.10, FastAPI, SQLAlchemy 2.0 async + asyncpg, Alembic, Pydantic v2, PyJWT, google-auth
- FE: React 19 + TypeScript, Vite, react-router v7, TanStack Query v5, Tailwind v4, npm
- DB: PostgreSQL 16 via Docker Compose (port 5432, db `ticketing`)
- Transport: HTTP untuk semua command, WebSocket untuk push event

## Lingkungan mesin ini
Python 3.10.0 · Node v26.13.1 · npm 11.20.0 · Docker 28.2.2 + Compose v2.36.2 · git 2.39.3
**Tidak tersedia:** pnpm, uv, psql lokal → pakai npm dan `docker compose exec db psql`.

## Aturan kerja yang WAJIB dipatuhi
1. **Kerjakan HANYA step yang diminta.** Jangan menyentuh step berikutnya walau "sekalian".
2. **Satu step = satu sesi.** Setelah semua DoD terpenuhi, **berhenti** dan tanya: "Step N selesai. Lanjut ke Step N+1?"
3. **Verifikasi, jangan asumsi.** Jalankan perintah verifikasi yang tertera dan tempelkan output nyata.
   Jangan menulis "seharusnya jalan".
4. **Setiap perubahan skema DB = file migrasi Alembic baru.** `create_all()` dilarang.
5. **Jangan kirim pesan/mutasi lewat WebSocket.** WS hanya event.
6. **Jangan tambahkan dependency baru** di luar daftar stack tanpa bertanya dulu.
7. **Jelaskan singkat "kenapa"** untuk setiap keputusan desain non-trivial (2-3 baris, bukan esai).
8. **Kalau ada yang ambigu, tanya.** Jangan mengarang keputusan produk.
9. Simpan rahasia di `.env` (gitignored); `.env.example` tanpa nilai rahasia.
10. Akhiri dengan blok **"Cek sendiri"** berisi 3-5 langkah manual yang bisa saya coba di browser/terminal.

## Format laporan akhir tiap step
```markdown
## Yang dikerjakan
- ...

## File yang dibuat/diubah
- path — alasan singkat

## Verifikasi
<perintah> → <output ringkas nyata>

## Keputusan desain
- X dipilih karena ...

## Cek sendiri
1. ...

## Status
DoD: semua terpenuhi / ada yang belum: ...
Lanjut ke Step N+1? (ya / belum)
```

## Konvensi penamaan
- Tabel & kolom: snake_case, plural untuk tabel (`tickets`, `ticket_messages`)
- Python: modul snake_case, kelas PascalCase
- TS: komponen PascalCase, hook `useXxx`, file util camelCase
- Endpoint: `/api/v1/{resource}`, plural, kebab-case kalau majemuk
- Event WS: `{entity}.{action}` past tense (`message.created`, `ticket.updated`)
