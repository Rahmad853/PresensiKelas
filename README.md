# Presensi Mahasiswa — struktur standar

```
app/
  main.py            # factory create_app, mount /api/v1 + legacy + static
  core/              # config (pydantic-settings), security JWT, deps get_db
  db/                # base (naming convention), session engine
  models/            # user, kelas, mahasiswa (NIM=PK), mata_kuliah, absensi, qr_session
  schemas/           # per domain: auth, user, kelas, mahasiswa, mata_kuliah, absensi
  services/          # logika bisnis: absensi (+rekap+import), qr (DB session)
  api/v1/            # router tipis: auth, users, admin, siswa, mata_kuliah, absensi, laporan, qr
alembic/             # migrasi versi (baseline 0001)
scripts/             # seed.py idempoten, etl_sqlite_to_postgres.py
tests/               # pytest service absensi
static/              # frontend (path bare lama tetap hidup via dual-mount)
```

## Perintah standar

```bash
pip install -r requirements.txt
# produksi: isi .env DATABASE_URL=postgresql+psycopg://...
#   docker compose up -d db   (opsional, Postgres lokal)
alembic upgrade head
python scripts/seed.py
python run_server.py            # uvicorn app.main:app
pytest -q
```

## Migrasi data lama (SQLite -> Postgres)

```bash
alembic upgrade head
python scripts/etl_sqlite_to_postgres.py --src db_absensi.db
```

Catatan: baris absensi tanpa `mata_kuliah_id` dilewati (skema baru NOT NULL),
laporan dihitung per mata kuliah. Dual-mount path lama tanpa prefix tetap aktif
sampai frontend pindah ke `/api/v1`; lalu hapus blok legacy di `app/main.py`.
Sesi QR kini persisten di tabel `qr_sessions` (ganti blacklist in-memory).
