# Checklist Setup Google SSO

Ikuti ini **hanya kalau kamu ingin login dengan akun Google sungguhan**.
Kalau belum, aplikasi tetap bisa dipakai lewat **dev-login** (`DEV_AUTH=true`).

Perkiraan waktu: 10-15 menit. Tidak perlu kartu kredit, tidak perlu bayar.

---

## 1. Buat Project

1. Buka https://console.cloud.google.com/
2. Klik dropdown project di kiri atas → **New Project**
3. Nama: `cs-ticketing` → **Create**
4. Pastikan project aktif (dropdown menampilkan `cs-ticketing`)

## 2. OAuth Consent Screen

Ini "layar izin" yang muncul saat user login pertama kali.

1. Menu kiri → **APIs & Services** → **OAuth consent screen**
2. User Type: **External** → **Create**
   - External = bisa dipakai akun Google mana pun (termasuk Gmail pribadi)
   - Internal = hanya untuk Google Workspace organisasi (butuh domain)
3. Isi:
   - App name: `CS Ticketing`
   - User support email: email kamu
   - Developer contact: email kamu
4. **Save and Continue**
5. Scopes: **tidak perlu menambah apa pun**. Cukup `email`, `profile`, `openid` yang otomatis.
   → **Save and Continue**
6. **Test users** ← LANGKAH PALING SERING TERLEWAT
   - **Add users** → masukkan email Google yang akan kamu pakai login
   - Bisa lebih dari satu
   - **Save and Continue**
7. Ringkasan → **Back to Dashboard**

> Kalau langkah 6 dilewati, login akan gagal dengan **"Access blocked: app has not completed verification"**.
> Menambah diri sendiri sebagai *test user* menyelesaikannya tanpa perlu verifikasi Google.

## 3. Buat OAuth Client ID

1. Menu kiri → **APIs & Services** → **Credentials**
2. **Create Credentials** → **OAuth client ID**
3. Application type: **Web application**
4. Name: `cs-ticketing-web`
5. **Authorized JavaScript origins** ← tambahkan:
   ```
   http://localhost:5173
   ```
   > Harus **persis** seperti itu: ada `http://`, ada port, **tanpa** trailing slash.
   > `http://localhost:5173/` (pakai slash) akan ditolak dengan `origin_mismatch`.
6. **Authorized redirect URIs**: **boleh dikosongkan**.
   Alur kita memakai *ID token* (bukan redirect), jadi tidak butuh redirect URI.
7. **Create** → muncul dialog berisi **Client ID** dan **Client Secret**
8. **Copy Client ID saja**. Client Secret **tidak dipakai** di alur ini.

## 4. Pasang di Proyek

Ada **dua** tempat yang butuh Client ID, dan keduanya harus sama:

```bash
# 1) backend/.env — atau .env di root repo (dipakai backend untuk verifikasi)
GOOGLE_CLIENT_ID=123456789-abcdefg.apps.googleusercontent.com

# 2) frontend/.env.local — dipakai browser untuk menampilkan tombol Google
VITE_GOOGLE_CLIENT_ID=123456789-abcdefg.apps.googleusercontent.com
```

⚠️ Awalan `VITE_` **wajib** di FE. Tanpa itu, Vite tidak akan meneruskannya ke browser.

Restart backend (`make be`) dan Vite (`make fe`) setelah mengubah env.

## 5. Verifikasi

Buka http://localhost:5173/login

- Tombol **"Sign in with Google"** muncul (bukan lagi kotak peringatan abu-abu)
- Klik → pilih akun → kembali ke aplikasi dalam keadaan login
- DevTools → **Application** → **Cookies** → `localhost:5173` → ada cookie `session`
  dengan kolom **HttpOnly** ✔ dan **SameSite: Lax**

Cek dari terminal:

```bash
curl -s localhost:8000/api/v1/dev/config | python3 -m json.tool
# "google_enabled": true   <- kalau masih false, GOOGLE_CLIENT_ID belum terbaca
```

## 6. Error yang Sering Muncul

| Pesan | Penyebab | Solusi |
|---|---|---|
| `origin_mismatch` | Origin di Console tidak sama persis | Tambahkan `http://localhost:5173` (tanpa slash) |
| `Access blocked: app has not completed verification` | Email belum jadi *test user* | Tambahkan di **Test users** |
| `The given origin is not allowed for the given client ID` | Client ID FE ≠ Client ID BE | Samakan `GOOGLE_CLIENT_ID` dan `VITE_GOOGLE_CLIENT_ID` |
| `GOOGLE_NOT_CONFIGURED` (500) | Backend tidak menemukan Client ID | Isi `.env`, lalu **restart** backend |
| `INVALID_GOOGLE_TOKEN` (401) | Token kedaluwarsa / audience beda | Login ulang; pastikan Client ID sama |
| Tombol Google tidak muncul | Skrip GIS diblokir | Cek Console browser; pastikan tidak ada AdBlock |
| Login sukses tapi langsung logout | Cookie ditolak browser | Pastikan akses lewat `localhost:5173`, **bukan** `127.0.0.1:5173` (beda host = beda cookie) |

## 7. Kalau Macet

Tidak perlu memaksakan. Set `DEV_AUTH=true` di `.env` (default: sudah true) dan pakai
panel **Dev login** di halaman login. Semua fitur lain (tiket, chat, WebSocket) tetap
bisa dipelajari. Google SSO bisa dinyalakan kapan saja nanti.

## 8. (Opsional) Publikasi

Kalau nanti aplikasi di-deploy:
- Tambahkan origin produksi (mis. `https://ticketing.contoh.com`) ke **Authorized JavaScript origins**
- Set `COOKIE_SECURE=true` di `.env` (cookie hanya dikirim lewat HTTPS)
- Kalau dibuka untuk publik luas, Google akan meminta **verifikasi aplikasi** (butuh privacy policy).
  Untuk belajar, cukup tetap di mode **Testing** dengan test users.
