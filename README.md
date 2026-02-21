# General Inventory Loan System API

Backend sistem rental ini telah diperbarui menjadi **sistem pinjam-meminjam (loan system)** general yang cocok untuk segala macam inventaris (mobil, perangkat komputer, buku, dsb). Dibangun dengan FastAPI dan SQLAlchemy.

## 🚀 Fitur Utama
1. **Multi-Database Support**: Menggunakan PostgreSQL sebagai database utama dengan fallback otomatis ke SQLite jika `DATABASE_URL` tidak disetel di `.env`.
2. **Cloudinary Storage**: File gambar/foto item diunggah ke Cloudinary. Jika `CLOUDINARY_URL` tidak terkonfigurasi, sistem akan *fallback* menyimpan gambar sebagai `base64` di database.
3. **Role-Based Access Control (RBAC)**: Terdapat role `ADMIN` dan `STAFF`.
   - `ADMIN` memiliki akses penuh terhadap pengelolaan kategori barang dan master data barang.
   - `STAFF` bertugas mengamankan transaksi peminjaman (loan).
4. **Excel Report Export**: Admin dapat mengunduh seluruh transaksi peminjaman dalam bentuk file `.xlsx`.
5. **Audit Logging**: Semua perubahan (buat, ubah, hapus) di setiap modul tercatat rapi ke dalam tabel `AuditLog`.
6. **Advanced Filter & Search**: Pengambilan data barang dan peminjaman dilengkapi integrasi query string untuk mencari, mem-filter stok, mengecek yang terlambat, dan sebagainya.

## ⚙️ Menjalankan Backend

1. Install dependency:
```bash
pip install -r requirements.txt
```

2. Salin environment variabel:
```bash
cp .env.example .env
```
Isi konfigurasi database (PostgreSQL) dan Cloudinary (opsional). Jika tidak diset, sistem otomatis menggunakan setelan lokal/fallback.

3. Buat akun login pertama (Admin atau Staff):
```bash
python -m app.utils.create_user
```

4. Jalankan server lokal:
```bash
uvicorn app.main:app --reload
```

5. Buka Dokumentasi Interaktif (OpenAPI):
- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## 📡 Endpoint API

### 🔐 Auth
- `POST /api/v1/auth/login` - Login pengguna (dapatkan Token JWT)
- `GET /api/v1/auth/me` - Periksa informasi profil aktif (Gunakan Token Bearer)

### 📦 Category (Memerlukan Akses ADMIN untuk Modifikasi)
- `GET /api/v1/categories/`
- `GET /api/v1/categories/{category_id}`
- `POST /api/v1/categories/`
- `PUT /api/v1/categories/{category_id}`
- `DELETE /api/v1/categories/{category_id}`

### 🖥️ Item (Memerlukan Akses ADMIN untuk Modifikasi)
- `GET /api/v1/items/` *(Dilengkapi parameter search `q`, `category_id`, `in_stock`)*
- `GET /api/v1/items/{item_id}`
- `GET /api/v1/items/{item_id}/photo`
- `POST /api/v1/items/`
- `PUT /api/v1/items/{item_id}`
- `DELETE /api/v1/items/{item_id}`

### 📝 Loan (Sirkulasi Pinjaman & Pengembalian)
- `GET /api/v1/loans/` *(Dilengkapi parameter search `borrower_name`, `item_code`, `status`, `start_date`, `end_date`)*
- `GET /api/v1/loans/{loan_id}`
- `POST /api/v1/loans/` - Mencatat pinjaman baru
- `PUT /api/v1/loans/{loan_id}` - Membarui struktur pinjaman yang salah input
- `PATCH /api/v1/loans/{loan_id}/confirm-return` - (Cepat) Konfirmasi barang dikembalikan
- `DELETE /api/v1/loans/{loan_id}`
- `GET /api/v1/loans/notifications` - Pengecekan barang yang lewat jatuh tempo pengembalian

### 📊 Dashboard & Reports (Akses Tertentu)
- `GET /api/v1/dashboard/` - (Admin Only) Ringkasan statistik performa sewa/pinjam
- `GET /api/v1/reports/loans/export` - (Admin Only) Download Laporan Excel
