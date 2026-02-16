# Struktur Folder Backend

Dokumen ini menjelaskan struktur folder project backend saat ini.

## Tree

```text
backend/
|-- app/
|   |-- api/
|   |   |-- v1/
|   |   |   |-- __init__.py
|   |   |   |-- auth.py
|   |   |   |-- categories.py
|   |   |   |-- dashboard.py
|   |   |   |-- items.py
|   |   |   `-- loans.py
|   |   |-- __init__.py
|   |   `-- deps.py
|   |-- core/
|   |   |-- config.py
|   |   |-- security.py
|   |   `-- __init__.py
|   |-- database/
|   |   `-- __init__.py
|   |-- models/
|   |   |-- __init__.py
|   |   |-- category.py
|   |   |-- item.py
|   |   |-- loan.py
|   |   `-- user.py
|   |-- schema/
|   |   |-- __init__.py
|   |   |-- auth.py
|   |   |-- category.py
|   |   |-- dashboard.py
|   |   |-- item.py
|   |   `-- loan.py
|   |-- services/
|   |   `-- __init__.py
|   |-- utils/
|   |   |-- create_user.py
|   |   `-- __init__.py
|   |-- __init__.py
|   `-- main.py
|-- docs/
|   |-- API.md
|   `-- Structure_folder.md
|-- .env
|-- .env.example
|-- .gitignore
|-- README.md
`-- requirements.txt
```

## Penjelasan Tiap Folder

### `app/`
Source code utama backend FastAPI.

### `app/main.py`
Entry point aplikasi FastAPI.
- Inisialisasi app.
- Menjalankan `init_db()` saat startup.
- Register semua router API.
- Menyediakan endpoint `/health`.

### `app/database/`
Konfigurasi database SQLAlchemy.
- `engine`
- `SessionLocal`
- `Base`
- dependency `get_db()`
- `init_db()` untuk create table otomatis.

### `app/models/`
Model ORM (struktur tabel database):
- `category.py`: tabel kategori.
- `item.py`: tabel item (termasuk `item_code`, foto binary, relasi kategori/loan).
- `loan.py`: tabel data peminjaman.
- `user.py`: tabel user login backend.

### `app/schema/`
Schema validasi request/response (Pydantic):
- `auth.py`: schema login/token/profil user.
- `category.py`: schema CRUD kategori.
- `dashboard.py`: schema response dashboard.
- `item.py`: schema CRUD item, validasi item code, validasi base64 foto.
- `loan.py`: schema CRUD loan, konfirmasi return, notifikasi overdue.

### `app/api/`
Layer routing API:
- `deps.py`: dependency injection (session database + current user dari bearer token).
- `v1/auth.py`: endpoint login dan profil user login.
- `v1/categories.py`: endpoint kategori.
- `v1/dashboard.py`: endpoint ringkasan dashboard.
- `v1/items.py`: endpoint item + endpoint ambil foto.
- `v1/loans.py`: endpoint loan + notifikasi + konfirmasi pengembalian.

### `app/core/`
Konfigurasi dan keamanan:
- `config.py`: baca config dari environment (`SECRET_KEY`, dll).
- `security.py`: hashing password dan JWT token helper.

### `app/utils/`
Utility script backend:
- `create_user.py`: script CLI untuk membuat akun login.

### `app/services/`
Masih placeholder untuk pengembangan berikutnya.

## Folder Dokumentasi

### `docs/API.md`
Dokumentasi endpoint API, payload, response, dan business rules.

### `docs/Structure_folder.md`
Dokumentasi struktur folder backend (dokumen ini).

## Catatan Runtime

- File database SQLite (`rental.db`) akan dibuat otomatis saat aplikasi dijalankan.
- Folder `__pycache__/` muncul otomatis saat Python compile/import.
