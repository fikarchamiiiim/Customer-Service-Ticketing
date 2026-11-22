# Step 07 — Hardening & Dokumentasi

> **Baca `prompts/CONTEXT.md` dulu** (aturan kerja, stack, format laporan).
> **Kerjakan HANYA step ini.** Setelah DoD terpenuhi, berhenti dan tanya apakah lanjut.

## Prompt (tempel ini ke agent)

```text
Kerjakan Step 07 (Hardening & Dokumentasi) dari proyek CS Ticketing.

Baca dulu: prompts/CONTEXT.md, ROADMAP.md, docs/ARCHITECTURE.md, docs/DATA-MODEL.md, docs/API.md.

## Tujuan
Aplikasi bisa dijalankan orang lain dengan satu perintah, error konsisten, ada test yang menjaga.

## Prasyarat
Step 0-6 selesai.

## Sub-step
1. **7.1 Error envelope** — handler global untuk `HTTPException`, `RequestValidationError`, `Exception`
   → `{error:{code,message,details}}`. FE: satu parser error di `api/client.ts` + tampilan toast/inline.
2. **7.2 Test** — pytest: auth (401 flow), RBAC (customer vs agent), state machine (semua transisi legal/ilegal),
   WS subscribe (ditolak/diizinkan), internal note tidak bocor. Target: test yang **bermakna**, bukan coverage 100%.
   `make test` menjalankan BE + (opsional) Vitest FE.
3. **7.3 Logging** — structured log (request id, user id, durasi), log handshake WS, log publish event.
   Jangan pernah log isi cookie atau token.
4. **7.4 README** — prasyarat, cara run (3 perintah), cara login (Google + dev-login),
   tabel troubleshooting minimal 5 masalah umum (origin_mismatch, cookie tidak terkirim, WS 4401, db belum healthy, port bentrok).
5. **7.5 Docker compose full** — service `db`, `api` (Dockerfile multi-stage), `web` (nginx:
   serve `dist/` + `proxy_pass` `/api` dan `/ws` dengan header upgrade). Satu `docker compose up` → jalan.
6. **7.6 Next steps** — `docs/NEXT-STEPS.md`: Redis pub/sub multi-instance, attachment, SLA, CSAT,
   refresh token, rate limiting, observability. Masing-masing 2 baris: kapan butuh, apa yang berubah.

## Verifikasi
```bash
make test
docker compose -f infra/docker-compose.yml up -d --build
curl -s localhost:8080/api/v1/health | jq
```
Buka aplikasi dari compose (`http://localhost:8080`) → login → buat tiket → balas → realtime jalan.

## Penutup
Ini step terakhir. Setelah selesai: ringkas **apa yang sudah dipelajari per step** (5-10 baris)
dan tanyakan mau lanjut ke fitur dari `docs/NEXT-STEPS.md` atau tidak.

Aturan: jangan kerjakan step berikutnya, jangan tambah dependency di luar stack,
setiap perubahan skema lewat migrasi Alembic, verifikasi dengan output nyata (bukan asumsi),
dan akhiri dengan blok laporan sesuai CONTEXT.md.
```
