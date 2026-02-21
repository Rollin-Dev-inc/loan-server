# General Inventory Loan System API

Sistem Backend yang bertenaga FastAPI ini dibangun untuk menangani siklus pinjam-meminjam (rental/loan) segala macam inventaris (kendaraan, elektronik, arsip, dsb). Dibekali dengan arsitektur Database Relasional kokoh dan lapisan keamanan ganda.

## 🚀 Fitur Utama & Keunggulan
1. **Multi-Database Support**: Menggunakan **PostgreSQL** sebagai database utama dengan fallback otomatis ke **SQLite** lokal jika `DATABASE_URL` tidak disetel di `.env`. Memiliki dukungan integritas relasi yang tinggi termasuk mekanisme *Soft-Delete*.
2. **Cloudinary Storage Multidimensi**: Mendukung unggahan banyak stok gambar (Multi-Photo) per Item secara bersamaan ke Cloudinary. Mendukung penyusutan otomatis *(fallback)* ke wujud *binary string Base64* SQLite jika jaringan awan terputus.
3. **Role-Based Access Control (RBAC)**: Pemisahan yurisdiksi ketat dengan dua Role:
   - `ADMIN`: Menguasai modifikasi Master Barang, Pemeliharaan Kategori, Manajemen Foto, Akses Dasbor Keuangan Terpusat, serta Jejak Log Audit.
   - `STAFF`: Pasukan Lapangan yang fokus memfasilitasi formulir peminjaman, pelacakan jatuh tempo, dan pengembalian stok barang.
4. **Excel Report Export**: Mesin Laporan (`openpyxl`) agar *Admin* dapat merangkum dan mengunduh seluruh transaksi periode peminjaman dalam berkas *Spreadsheet* (`.xlsx`).
5. **Auto Stock Adjustment**: Validasi stok yang saling terkait. Meminjam barang akan mengurangi stok aslinya. Pengembalian otomatis merestorasi kuantitas stok di Gudang Master.
6. **Audit & Activity Logging**: Jejak tak terlihat dari semua perubahan (Hapus Barang, Edit Pinjaman, Pembaruan Status) akan tercatat sekuensial permanen ke tabel `AuditLog`.
7. **Pencarian Agresif & Filter Lanjut**: Modul pengambilan data cerdas. Anda dapat membedah data berdasar keyword, ID kategori, ketersediaan sisa stok `in_stock`, nama peminjam, hingga rentang waktu.
8. **Proteksi API Tingkat Rendah (Watermark)**: Penempelan hak cipta absolut lewat modul *Custom Middleware* HTTP. Semua amplop respons server disandarkan header paten `X-Powered-By: Rollindev | Pabloraka` yang tidak dapat dirusak dari _Frontend_.

---

## ⚙️ Persiapan & Menjalankan Backend

### 1. Prasyarat Instalasi
Sistem ini menggunakan ekosistem Python 3.10+.
```bash
pip install -r requirements.txt
```

### 2. Konfigurasi Lingkungan (`.env`)
Menyambungkan Database dan Penyimpanan Gambar:
```bash
cp .env.example .env
```
_(Sunting isi fail `.env` jika Anda mempunyai koneksi otentik PostgreSQL/Cloudinary)_

### 3. Migrasi & Registrasi Perdana
Jalankan utilitas pra-instal untuk menginisialisasi tabel database dan melahirkan akun Root/Staf pertama:
```bash
python -m app.utils.create_user
```

### 4. Nyalakan Mesin Server
```bash
uvicorn app.main:app --reload
```

---

## 📡 Rute Singkat Endpoint API

Interactive Documentation Framework (Swagger UI) telah disediakan otomatis di:
👉 **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**

| Grup | Endpoint Utama | Deskripsi Logika Tambahan | Hak Akses |
|-------|-------|-------|-------|
| **Kunci Auth** | `POST /login`, `GET /me` | Pengesahan Token Standard Bearer JWT. | Publik / General |
| **Kategori** | `GET`, `POST`, `PUT`, `DELETE` *(/categories)* | Kategori barang tidak bisa dihapus sepihak bila masih digunakan unit Item (Restriksi Integritas). | Hanya Admin |
| **Benda Fisik** | `GET`, `POST`, `PUT`, `DELETE` *(/items)* | Integrasi _Soft-Delete_ mutakhir: Item valid dihapus selama tidak *sedang* dipinjam. Riwayat _Loans_ lawas dibalikkan *Null* sehingga histori finansial kebal. | Hanya Admin / Staff View-Only |
| **Logistik Foto** | `GET /items/{id}/photo` (ataupun `/photos/{id}`) | Saluran umum publik (Tanpa Auth) untuk mengambil profil dan galeri tambahan wujud barang dari Cloud/Lokal. | Terbuka |
| **Peminjaman** | `GET`, `POST`, `PUT`, `DELETE`, `PATCH` *(/loans)* | Mencegah status Un-return jika item asli musnah. Terdapat modul `/notifications` yang memburu keterlambatan otomatis. | Admin & Staff |
| **Logistik Audit**| `GET /audits/` | Catatan aktivitas harian. _Immutable log_ perihal siapa merombak apa. | Hanya Admin |
| **Dasbor Finansial**| `GET /dashboard/`, `GET /reports/loans/export` | Penghitungan kalkulatif margin Keuangan bulanan serta pencetakan rekap Laporan Excel murni | Hanya Admin |
