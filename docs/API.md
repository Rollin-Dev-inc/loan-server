# Backend API Documentation

Dokumen ini menjelaskan endpoint backend untuk sistem rental.

## Informasi Umum

- Framework: FastAPI
- Prefix API v1: `/api/v1`
- Data Format: `application/json` (kecuali upload foto via form-data jika nantinya diadaptasi, saat ini input foto item lewat `base64`)
- Database Utama: PostgreSQL (Atau menggunakan SQLite `rental.db` untuk fallback lokal)
- Storage Foto: Cloudinary (Atau menggunakan local binary db untuk fallback)
- Autentikasi: JWT Bearer (Token-based)
- Sistem Peran (RBAC): Admin & Staff

Contoh base URL lokal:
- `http://127.0.0.1:8000`

## Health Check

### GET `/health`

Response `200`:
```json
{
  "status": "ok"
}
```

## Auth

### POST `/api/v1/auth/login`
Login dengan username dan password.

Request body:
```json
{
  "username": "admin",
  "password": "admin123"
}
```

Response `200`:
```json
{
  "access_token": "<jwt-token>",
  "token_type": "bearer",
  "role": "ADMIN" // atau STAFF
}
```

Response `401` jika username/password salah:
```json
{
  "detail": "Invalid username or password"
}
```

### GET `/api/v1/auth/me`
Ambil profil user login.

Header:
- `Authorization: Bearer <jwt-token>`

Response `200`:
```json
{
  "id": 1,
  "username": "admin",
  "full_name": "Admin",
  "is_active": true,
  "role": "ADMIN",
  "created_at": "2026-02-16T10:00:00.000000"
}
```

## Dashboard

### GET `/api/v1/dashboard/`
Ambil ringkasan dashboard:
- Pendapatan total dari `loan.price_to_pay`
- Jumlah transaksi pinjaman
- Jumlah item unik yang dipinjam pada periode filter
- Jumlah item yang pernah dipinjam (all-time)
- Daftar item yang pernah dipinjam pada periode filter

Query parameter:
- `period` (opsional, default `1m`)

Nilai `period` yang didukung:
- `1m` (1 bulan)
- `3m` (3 bulan)
- `6m` (6 bulan)
- `1y` (1 tahun)
- `3y` (3 tahun)
- `5y` (5 tahun)

Contoh request:
- `GET /api/v1/dashboard/?period=3m`

Response `200`:
```json
{
  "period": "3m",
  "period_start": "2025-11-16",
  "period_end": "2026-02-16",
  "total_revenue": 1250000,
  "total_loans": 6,
  "unique_items_borrowed": 3,
  "items_ever_borrowed": 8,
  "borrowed_items": [
    {
      "item_id": 1,
      "item_code": "SUV001",
      "item_name": "Toyota Fortuner",
      "total_loans": 3,
      "total_revenue": 750000,
      "last_borrowed_at": "2026-02-14"
    }
  ]
}
```

## Kategori (Memerlukan Role ADMIN untuk modifikasi)

### GET `/api/v1/categories/`
Ambil semua kategori.

Response `200`:
```json
[
  {
    "id": 1,
    "name": "Mobil SUV"
  }
]
```

### GET `/api/v1/categories/{category_id}`
Ambil detail 1 kategori.

Response `404` jika tidak ditemukan:
```json
{
  "detail": "Category not found"
}
```

### POST `/api/v1/categories/`
Buat kategori baru.

Request body:
```json
{
  "name": "Mobil Sedan"
}
```

Response `201`:
```json
{
  "id": 2,
  "name": "Mobil Sedan"
}
```

Response `400` jika nama sudah ada:
```json
{
  "detail": "Category name already exists"
}
```

### PUT `/api/v1/categories/{category_id}`
Update nama kategori.

Request body:
```json
{
  "name": "Mobil MPV"
}
```

### DELETE `/api/v1/categories/{category_id}`
Hapus kategori.

Aturan:
- Tidak bisa dihapus jika masih dipakai oleh item.

Response `400` jika masih dipakai:
```json
{
  "detail": "Category cannot be deleted because it is used by items"
}
```

## Item (Memerlukan Role ADMIN untuk modifikasi)

### GET `/api/v1/items/`
Ambil daftar item.

Query parameter opsional (Filter):
- `q` (string): Cari berdasarkan nama item atau item code
- `category_id` (int): Filter by category
- `in_stock` (boolean): `true` untuk item dengan stok > 0, `false` untuk item dengan stok = 0

Response `200`:
```json
[
  {
    "id": 1,
    "name": "Toyota Fortuner",
    "item_code": "SUV001",
    "category_id": 1,
    "stock": 4,
    "created_at": "2026-02-16T10:00:00.000000",
    "has_photo": true,
    "photo_url": "https://res.cloudinary.com/.../image.jpg",
    "photo_content_type": "image/jpeg"
  }
]
```

### GET `/api/v1/items/{item_id}`
Ambil detail 1 item.

### POST `/api/v1/items/`
Buat item baru.

Request body:
```json
{
  "name": "Toyota Fortuner",
  "item_code": "SUV001",
  "category_id": 1,
  "stock": 4,
  "photo_base64": "data:image/jpeg;base64,/9j/4AAQSk...",
  "photo_content_type": "image/jpeg"
}
```

Aturan:
- `item_code` harus gabungan huruf dan angka (alphanumeric, wajib mengandung huruf dan angka).
- `item_code` harus unik.
- `category_id` harus valid.
- `photo_base64` wajib valid base64 dan tidak boleh kosong.
- `created_at` diisi otomatis oleh backend.

### PUT `/api/v1/items/{item_id}`
Update data item (partial by field yang dikirim).

Request body contoh:
```json
{
  "name": "Toyota Fortuner GR",
  "item_code": "SUV002",
  "stock": 5,
  "photo_base64": "data:image/jpeg;base64,/9j/4AAQSk...",
  "photo_content_type": "image/jpeg"
}
```

### DELETE `/api/v1/items/{item_id}`
Hapus item.

Aturan:
- Tidak bisa dihapus jika pernah dipakai di data pinjaman.

Response `400`:
```json
{
  "detail": "Item cannot be deleted because it is used by loan data"
}
```

### GET `/api/v1/items/{item_id}/photo`
Ambil binary foto item.

Response:
- `200` dengan content-type sesuai `photo_content_type` (misal `image/jpeg`).
- `404` jika item/foto tidak ada.

## Loan (Sirkulasi Pinjaman & Pengembalian)

### GET `/api/v1/loans/`
Ambil semua data pinjaman.

Query parameter opsional (Filter):
- `borrower_name` (string): Cari berdasarkan nama peminjam
- `item_code` (string): Cari berdasarkan kode item
- `status` (string): filter berdasarkan status `active`, `returned`, atau `overdue`
- `start_date` (date: YYYY-MM-DD): filter awal rentang tanggal peminjaman
- `end_date` (date: YYYY-MM-DD): filter akhir rentang tanggal peminjaman

Response `200`:
```json
[
  {
    "id": 1,
    "borrower_name": "Raka",
    "item_id": 1,
    "item_code": "SUV001",
    "duration_days": 3,
    "borrowed_at": "2026-02-16",
    "due_at": "2026-02-19",
    "price_to_pay": 350000,
    "is_returned": false,
    "returned_at": null,
    "is_overdue": false
  }
]
```

### GET `/api/v1/loans/{loan_id}`
Ambil detail 1 data pinjaman.

### POST `/api/v1/loans/`
Buat data pinjaman baru.

Request body:
```json
{
  "borrower_name": "Raka",
  "item_id": 1,
  "item_code": "SUV001",
  "duration_days": 3,
  "borrowed_at": "2026-02-16",
  "price_to_pay": 350000,
  "is_returned": false
}
```

Aturan:
- `due_at` dihitung otomatis: `borrowed_at + duration_days`.
- Jika `item_code` dikirim, harus cocok dengan `item_id`.
- `price_to_pay` diisi manual.

### PUT `/api/v1/loans/{loan_id}`
Update data pinjaman.

Field yang bisa diupdate:
- `borrower_name`
- `item_id`
- `item_code` (validasi harus cocok dengan item)
- `duration_days`
- `borrowed_at`
- `price_to_pay`
- `is_returned`

Aturan:
- Setelah update `duration_days` atau `borrowed_at`, `due_at` dihitung ulang otomatis.

### PATCH `/api/v1/loans/{loan_id}/confirm-return`
Endpoint konfirmasi pengembalian dari notifikasi frontend.

Request body:
```json
{
  "is_returned": true
}
```

Hasil:
- Jika `true`, backend set `is_returned=true` dan `returned_at` otomatis.
- Jika `false`, backend set `is_returned=false` dan `returned_at=null`.

### DELETE `/api/v1/loans/{loan_id}`
Hapus data pinjaman.

## Notifikasi Jatuh Tempo

### GET `/api/v1/loans/notifications`
Ambil daftar pinjaman yang:
- `is_returned = false`
- `due_at <= tanggal hari ini`

Response `200`:
```json
[
  {
    "loan_id": 1,
    "borrower_name": "Raka",
    "item_id": 1,
    "item_code": "SUV001",
    "due_at": "2026-02-19",
    "days_overdue": 2,
    "message": "Barang dengan kode SUV001 sudah jatuh tempo. Apakah barang sudah dikembalikan?"
  }
]
```

Workflow frontend yang disarankan:
1. Polling `GET /api/v1/loans/notifications`.
2. Tampilkan notifikasi dan pertanyaan konfirmasi.
3. Jika user jawab sudah kembali, panggil `PATCH /api/v1/loans/{loan_id}/confirm-return` dengan `is_returned=true`.

## Report & Eksport

### GET `/api/v1/reports/loans/export`
Membutuhkan Auth Bearer dengan role **ADMIN**. Mengunduh seluruh histori peminjaman ke dalam format file Microsoft Excel (`.xlsx`). Backend menggunakan library openpyxl, akan mengembalikan `StreamingResponse`. Valid sebagai attachment header document.

## Ringkasan Status Code

- `200` sukses baca/update
- `201` berhasil create
- `204` berhasil delete (tanpa body)
- `400` validasi bisnis gagal
- `401` gagal autentikasi
- `403` user tidak aktif / akses ditolak
- `404` data tidak ditemukan

## Catatan Error Format

Format error standar:
```json
{
  "detail": "..."
}
```
