# Data Model

Postgres 16. Semua waktu `TIMESTAMPTZ`, disimpan dalam **UTC**, ditampilkan di Asia/Jakarta oleh FE.

## Enum

```sql
CREATE TYPE user_role     AS ENUM ('customer', 'agent', 'admin');
CREATE TYPE ticket_status AS ENUM ('open', 'in_progress', 'resolved', 'closed');
CREATE TYPE ticket_priority AS ENUM ('low', 'normal', 'high');
```

## Tabel

### users
| kolom | tipe | catatan |
|---|---|---|
| id | bigserial PK | |
| email | citext UNIQUE NOT NULL | dari Google |
| name | text | |
| avatar_url | text NULL | |
| role | user_role NOT NULL DEFAULT 'customer' | |
| google_sub | text UNIQUE NULL | subject Google (immutable) |
| is_active | boolean NOT NULL DEFAULT true | |
| created_at / updated_at | timestamptz | |

### tickets
| kolom | tipe | catatan |
|---|---|---|
| id | bigserial PK | |
| ticket_no | text UNIQUE NOT NULL | `TKT-000123` (dari sequence) |
| subject | text NOT NULL | 3..200 char |
| description | text NOT NULL | pesan pembuka |
| status | ticket_status NOT NULL DEFAULT 'open' | |
| priority | ticket_priority NOT NULL DEFAULT 'normal' | |
| customer_id | bigint FK users | pembuat |
| assignee_id | bigint FK users NULL | agent |
| last_message_at | timestamptz NULL | untuk sorting |
| created_at / updated_at | timestamptz | |

Index: `(status, last_message_at DESC)`, `(customer_id)`, `(assignee_id)`

### ticket_messages
| kolom | tipe | catatan |
|---|---|---|
| id | bigserial PK | |
| ticket_id | bigint FK tickets ON DELETE CASCADE | |
| sender_id | bigint FK users | |
| body | text NOT NULL | 1..5000 char |
| is_internal | boolean NOT NULL DEFAULT false | note agent, tidak terlihat customer |
| created_at | timestamptz | |

Index: `(ticket_id, id DESC)` — dipakai untuk cursor pagination.

### ticket_events (Step 6)
| kolom | tipe | catatan |
|---|---|---|
| id | bigserial PK | |
| ticket_id | bigint FK tickets | |
| actor_id | bigint FK users NULL | null = sistem |
| kind | text | `created`, `status_changed`, `assigned`, ... |
| payload | jsonb | `{"from":"open","to":"resolved"}` |
| created_at | timestamptz | |

### ticket_participants (Step 6)
| kolom | tipe | catatan |
|---|---|---|
| ticket_id | bigint FK | PK gabungan |
| user_id | bigint FK | PK gabungan |
| last_read_at | timestamptz NULL | dasar unread counter |

## Aturan Transisi Status (state machine)

```
open ──────────▶ in_progress ──────▶ resolved ──────▶ closed
 │                    │                  │
 │                    └──────────────────┘
 │                  (resolved ─▶ in_progress = reopen)
 └──────────────────────────────────▶ closed
        (customer boleh menutup sendiri)

Dilarang (→ 422 ILLEGAL_TRANSITION):
  closed → apa pun (kecuali reopen oleh admin, kalau nanti ada)
  open   → resolved  (harus lewat in_progress)
  resolved → open
```

Implementasi: satu fungsi murni `ALLOWED: dict[status, set[status]]` di
`services/tickets.py` — gampang di-unit-test tanpa DB.

## Aturan Otorisasi (RBAC + scoping)

| Aksi | customer | agent |
|---|---|---|
| list tiket | hanya `customer_id = me` | semua |
| baca detail / pesan | hanya miliknya (selain itu **404**) | semua |
| buat tiket | ya | ya |
| kirim pesan publik | hanya miliknya | semua |
| kirim internal note | tidak | ya |
| ubah status / assign | hanya `close` tiket sendiri | ya (sesuai state machine) |
| subscribe `agents` | tidak | ya |

**Gunakan 404, bukan 403**, untuk tiket milik orang lain — jangan bocorkan keberadaan data.

## Sequence ticket_no

```sql
CREATE SEQUENCE ticket_no_seq;
-- ticket_no = 'TKT-' || lpad(nextval('ticket_no_seq')::text, 6, '0')
```
Bukan `id` — supaya nomor tiket tidak membocorkan jumlah data & enak dibaca manusia.
