# Step 05 — Chat Realtime

> **Baca `prompts/CONTEXT.md` dulu** (aturan kerja, stack, format laporan).
> **Kerjakan HANYA step ini.** Setelah DoD terpenuhi, berhenti dan tanya apakah lanjut.

## Prompt (tempel ini ke agent)

```text
Kerjakan Step 05 (Chat Realtime) dari proyek CS Ticketing.

Baca dulu: prompts/CONTEXT.md, ROADMAP.md, docs/ARCHITECTURE.md, docs/DATA-MODEL.md, docs/API.md.

## Tujuan
Percakapan yang hidup: pesan sampai dalam < 1 detik ke semua tab, tanpa dobel, tanpa hilang.

## Prasyarat
Step 4 selesai: koneksi stabil, subscribe/otorisasi channel jalan.

## Sub-step
1. **5.1 EventBus** — `services/events.py`: `async def publish(channel: str, type: str, data: dict)`
   yang memanggil `ConnectionManager.broadcast`. Satu titik masuk untuk semua event domain —
   nanti gampang ditukar ke Redis pub/sub.
2. **5.2 Publish saat kirim pesan** — `POST /tickets/{id}/messages` (sudah ada di Step 3) sekarang
   memanggil `publish(f"ticket:{id}", "message.created", msg)` **setelah** commit. Pengirim juga menerima.
3. **5.3 Channel personal** — kirim juga ke `user:{recipient_id}` untuk lawan bicara
   (customer→assignee, agent→customer), supaya nanti bisa jadi notifikasi lintas tiket.
4. **5.4 FE append + dedupe** — `useTicketMessages(ticketId)`: muat riwayat via HTTP (`before_id`),
   lalu subscribe `ticket:{id}`. Saat `message.created`: kalau `id` sudah ada di cache → abaikan;
   kalau belum → append **dan** update `last_message_at`. Auto-scroll hanya kalau user sedang di bawah.
5. **5.5 Typing indicator** — `typing` dari client → broadcast ke channel **kecuali pengirim**;
   FE menampilkan "Agent sedang mengetik…" dan menghapusnya otomatis setelah 3 detik.
   Tidak disimpan ke DB, tidak di-ACK.
6. **5.6 Internal note aman** — pesan `is_internal=true` **tidak pernah** di-publish ke channel
   `ticket:{id}`; arahkan ke channel `agents` saja. Tulis test untuk ini.

## Verifikasi
```bash
pytest -q -k "message or internal"      # termasuk test: internal note tidak bocor ke customer
```
Dua browser, satu customer satu agent, buka tiket yang sama:
ketik dari customer → muncul di tab agent < 1 detik → balas dari agent → muncul di tab customer.
Refresh halaman → riwayat tetap lengkap, **tidak ada duplikat**.
Kirim internal note sebagai agent → customer **tidak** melihat apa pun.

## Batasan
- Belum ada notifikasi tiket baru / presence / activity log (Step 6).
- Jangan ubah kontrak pesan: pengiriman tetap lewat HTTP.

## Penutup
Berhenti dan tanya: *"Step 5 selesai. Lanjut ke Step 6 (Notifikasi & Presence)?"*

Aturan: jangan kerjakan step berikutnya, jangan tambah dependency di luar stack,
setiap perubahan skema lewat migrasi Alembic, verifikasi dengan output nyata (bukan asumsi),
dan akhiri dengan blok laporan sesuai CONTEXT.md.
```
