# Step 02 — Auth Google SSO

> **Baca `prompts/CONTEXT.md` dulu** (aturan kerja, stack, format laporan).
> **Kerjakan HANYA step ini.** Setelah DoD terpenuhi, berhenti dan tanya apakah lanjut.

## Prompt (tempel ini ke agent)

```text
Kerjakan Step 02 (Auth Google SSO) dari proyek CS Ticketing.

Baca dulu: prompts/CONTEXT.md, ROADMAP.md, docs/ARCHITECTURE.md, docs/DATA-MODEL.md, docs/API.md.

## Tujuan
Login dengan akun Google → dapat sesi (cookie httpOnly) → endpoint terproteksi berfungsi.

## Prasyarat
Step 1 selesai: tabel `users` ada, seed jalan.

## Sub-step
1. **2.1 Google Console (manual, saya lakukan sendiri)** — beri checklist persis:
   buat project → OAuth consent screen (External, Testing, tambahkan email saya sebagai test user) →
   Credentials → OAuth Client ID → Web application → Authorized JavaScript origins
   `http://localhost:5173` → salin Client ID ke `.env`. Sebutkan error umum:
   `origin_mismatch`, "app not verified", dan cara menambah test user.
2. **2.2 Verifikasi ID token** — `POST /api/v1/auth/google` `{id_token}`:
   `google.oauth2.id_token.verify_oauth2_token(token, Request(), client_id)`; validasi `aud` & `exp`;
   tolak kalau `email_verified` false.
3. **2.3 Find-or-create + role** — cari by `google_sub` (fallback `email`); kalau baru, buat dengan
   role `customer` **kecuali** email ada di `AGENT_EMAILS` (env, comma-separated) → `agent`.
4. **2.4 Session cookie** — terbitkan JWT (`sub`=user id, `exp`=7 hari, `iat`) dengan PyJWT;
   `Set-Cookie: session=...; HttpOnly; SameSite=Lax; Path=/; Max-Age=604800`
   (`Secure` hanya kalau `COOKIE_SECURE=true`, karena dev pakai http).
5. **2.5 Dependencies** — `get_current_user` (baca cookie → decode → load user; 401 kalau gagal) dan
   `require_role("agent")`. Endpoint: `GET /me`, `POST /auth/logout` (hapus cookie).
6. **2.6 Dev login** — `POST /auth/dev-login {email}`, **hanya aktif** kalau `DEV_AUTH=true`;
   kalau tidak, kembalikan 404. Ini jaring pengaman kalau Google Console bermasalah.
7. **2.7 FE** — `AuthContext` (fetch `/me` saat mount, state `loading|user|null`),
   `ProtectedRoute` (redirect ke `/login`), `api/client.ts` dengan `credentials:'include'` +
   helper yang melempar error terstruktur saat 401.
8. **2.8 Tombol Google** — Google Identity Services (`script` + `google.accounts.id.initialize`);
   callback → `POST /auth/google` → simpan user → redirect by role.
   Kalau `DEV_AUTH=true`, tampilkan juga panel dev-login (pilih email seed) supaya bisa lanjut tanpa Google.

## Verifikasi
```bash
# tanpa cookie
curl -i localhost:8000/api/v1/me                      # 401
# dev-login lalu pakai cookie
curl -ic /tmp/c.txt -X POST localhost:8000/api/v1/auth/dev-login \
  -H 'content-type: application/json' -d '{"email":"agent1@example.com"}'
grep -i set-cookie /tmp/c.txt                          # HttpOnly; SameSite=Lax
curl -s -b /tmp/c.txt localhost:8000/api/v1/me | jq    # role: agent
```
Di browser: login → cookie terlihat di DevTools (HttpOnly ✔) → refresh tetap login → logout → kembali ke `/login`.

## Batasan
- **Jangan** simpan token di localStorage.
- **Belum ada** endpoint tiket dan belum ada WebSocket.

## Penutup
Berhenti dan tanya: *"Step 2 selesai. Lanjut ke Step 3 (Tiket via HTTP)?"*

Aturan: jangan kerjakan step berikutnya, jangan tambah dependency di luar stack,
setiap perubahan skema lewat migrasi Alembic, verifikasi dengan output nyata (bukan asumsi),
dan akhiri dengan blok laporan sesuai CONTEXT.md.
```
