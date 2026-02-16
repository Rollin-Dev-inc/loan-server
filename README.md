# Rental Backend API

Backend ini dibuat dengan FastAPI + SQLite untuk kebutuhan:
- Login backend (JWT Bearer)
- CRUD kategori
- CRUD item (nama item, kode barang alphanumeric, kategori dari data kategori, tanggal otomatis saat create, stock, foto tersimpan di database)
- CRUD daftar barang dipinjam + notifikasi keterlambatan

## Menjalankan backend

1. Install dependency:
```bash
pip install -r requirements.txt
```

2. Salin env:
```bash
copy .env.example .env
```

3. Buat akun login pertama:
```bash
python -m app.utils.create_user
```

4. Jika sebelumnya sudah ada `rental.db` dari skema lama, hapus dulu file tersebut agar tabel baru terbentuk ulang.

5. Jalankan server:
```bash
uvicorn app.main:app --reload
```

6. Buka dokumentasi:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Endpoint

### Auth
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me` (Bearer token)

### Category
- `GET /api/v1/categories/`
- `GET /api/v1/categories/{category_id}`
- `POST /api/v1/categories/`
- `PUT /api/v1/categories/{category_id}`
- `DELETE /api/v1/categories/{category_id}`

### Item
- `GET /api/v1/items/`
- `GET /api/v1/items/{item_id}`
- `GET /api/v1/items/{item_id}/photo`
- `POST /api/v1/items/`
- `PUT /api/v1/items/{item_id}`
- `DELETE /api/v1/items/{item_id}`

### Loan (Daftar Barang Dipinjam)
- `GET /api/v1/loans/`
- `GET /api/v1/loans/{loan_id}`
- `POST /api/v1/loans/`
- `PUT /api/v1/loans/{loan_id}`
- `PATCH /api/v1/loans/{loan_id}/confirm-return`
- `DELETE /api/v1/loans/{loan_id}`
- `GET /api/v1/loans/notifications` (warning jatuh tempo untuk frontend)

## Contoh payload

Create category:
```json
{
  "name": "Mobil SUV"
}
```

Login:
```json
{
  "username": "admin",
  "password": "admin123"
}
```

Create item:
```json
{
  "item_code": "SUV001",
  "name": "Toyota Fortuner",
  "category_id": 1,
  "stock": 4,
  "photo_base64": "data:image/jpeg;base64,/9j/4AAQSk...",
  "photo_content_type": "image/jpeg"
}
```

Create loan:
```json
{
  "borrower_name": "Budi",
  "item_id": 1,
  "duration_days": 3,
  "borrowed_at": "2026-02-16",
  "price_to_pay": 350000
}
```

Konfirmasi pengembalian (dari notifikasi frontend):
```json
{
  "is_returned": true
}
```

`created_at` item dan `due_at` loan dihitung otomatis oleh backend.
