"""Salin data SQLite lama ke database target (Postgres/SQLite baru).

Pakai:  python scripts/etl_sqlite_to_postgres.py --src db_absensi.db
Target dibaca dari DATABASE_URL (.env). Jalankan `alembic upgrade head` dulu.
Baris absensi tanpa mata_kuliah_id dilewati dan dilaporkan (skema baru NOT NULL).
"""
import argparse
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


def _rows(src: sqlite3.Connection, table: str) -> list[dict]:
    cur = src.execute(f"SELECT * FROM {table}")
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="db_absensi.db")
    args = ap.parse_args()

    if not os.path.exists(args.src):
        print(f"Sumber tidak ada: {args.src}")
        sys.exit(1)

    src = sqlite3.connect(args.src)
    tables = {r[0] for r in src.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    need = {"users", "kelas", "mahasiswa", "mata_kuliah", "absensi"}
    if not need.issubset(tables):
        print(f"Tabel kurang: {need - tables}")
        sys.exit(1)

    engine = create_engine(settings.database_url)
    Session = sessionmaker(bind=engine)
    db = Session()
    from sqlalchemy import text

    stat = {"kelas": 0, "users": 0, "mahasiswa": 0, "mata_kuliah": 0, "absensi": 0,
            "absensi_skip_null_matkul": 0, "absensi_skip_duplikat": 0, "link_user_mhs": 0}

    for k in _rows(src, "kelas"):
        db.execute(text("INSERT INTO kelas (id, nama_kelas, nama_ketua_kelas, tahun_ajaran, angkatan)"
                        " VALUES (:id, :nama_kelas, :nama_ketua_kelas, :tahun_ajaran, :angkatan)"
                        " ON CONFLICT (id) DO NOTHING"
                        if engine.dialect.name == "postgresql" else
                        "INSERT OR IGNORE INTO kelas (id, nama_kelas, nama_ketua_kelas, tahun_ajaran, angkatan)"
                        " VALUES (:id, :nama_kelas, :nama_ketua_kelas, :tahun_ajaran, :angkatan)"),
                   {"id": k["id"], "nama_kelas": k["nama_kelas"], "nama_ketua_kelas": k.get("nama_ketua_kelas"),
                    "tahun_ajaran": k["tahun_ajaran"], "angkatan": k.get("angkatan")})
        stat["kelas"] += 1
    for u in _rows(src, "users"):
        db.execute(text("INSERT INTO users (id, username, nim, password_hash, role, kelas_id)"
                        " VALUES (:id, :username, :nim, :password_hash, :role, :kelas_id)"
                        " ON CONFLICT (id) DO NOTHING"
                        if engine.dialect.name == "postgresql" else
                        "INSERT OR IGNORE INTO users (id, username, nim, password_hash, role, kelas_id)"
                        " VALUES (:id, :username, :nim, :password_hash, :role, :kelas_id)"),
                   {"id": u["id"], "username": u["username"], "nim": u.get("nim"),
                    "password_hash": u["password_hash"], "role": u["role"], "kelas_id": u.get("kelas_id")})
        stat["users"] += 1
    for m in _rows(src, "mahasiswa"):
        db.execute(text("INSERT INTO mahasiswa (nim, nama_lengkap, kelas_id, user_id, foto, angkatan)"
                        " VALUES (:nim, :nama_lengkap, :kelas_id, :user_id, :foto, :angkatan)"
                        " ON CONFLICT (nim) DO NOTHING"
                        if engine.dialect.name == "postgresql" else
                        "INSERT OR IGNORE INTO mahasiswa (nim, nama_lengkap, kelas_id, user_id, foto, angkatan)"
                        " VALUES (:nim, :nama_lengkap, :kelas_id, :user_id, :foto, :angkatan)"),
                   {"nim": m["nim"], "nama_lengkap": m["nama_lengkap"], "kelas_id": m["kelas_id"],
                    "user_id": m.get("user_id"), "foto": m.get("foto"), "angkatan": m.get("angkatan")})
        stat["mahasiswa"] += 1
    for mk in _rows(src, "mata_kuliah"):
        db.execute(text("INSERT INTO mata_kuliah (id, kode, nama, semester, kelas_id)"
                        " VALUES (:id, :kode, :nama, :semester, :kelas_id)"
                        " ON CONFLICT (id) DO NOTHING"
                        if engine.dialect.name == "postgresql" else
                        "INSERT OR IGNORE INTO mata_kuliah (id, kode, nama, semester, kelas_id)"
                        " VALUES (:id, :kode, :nama, :semester, :kelas_id)"),
                   {"id": mk["id"], "kode": mk["kode"], "nama": mk["nama"],
                    "semester": mk.get("semester"), "kelas_id": mk["kelas_id"]})
        stat["mata_kuliah"] += 1
    seen: set[tuple] = set()
    for a in _rows(src, "absensi"):
        if not a.get("mata_kuliah_id"):
            stat["absensi_skip_null_matkul"] += 1
            continue
        key = (a["nim"] if "nim" in a else a.get("nis"), str(a["tanggal"]), a["mata_kuliah_id"])
        if key in seen:
            stat["absensi_skip_duplikat"] += 1
            continue
        seen.add(key)
        try:
            db.execute(text("INSERT INTO absensi (nim, tanggal, status, keterangan, metode, dicatat_oleh, mata_kuliah_id)"
                            " VALUES (:nim, :tanggal, :status, :keterangan, :metode, :dicatat_oleh, :mata_kuliah_id)"),
                       {"nim": key[0], "tanggal": key[1], "status": a["status"], "keterangan": a.get("keterangan"),
                        "metode": a.get("metode") or "manual", "dicatat_oleh": a.get("dicatat_oleh"),
                        "mata_kuliah_id": a["mata_kuliah_id"]})
            stat["absensi"] += 1
        except Exception:
            db.rollback()
            stat["absensi_skip_duplikat"] += 1
    db.commit()
    link = db.execute(text("UPDATE mahasiswa SET user_id = users.id FROM users"
                           " WHERE mahasiswa.user_id IS NULL AND users.nim = mahasiswa.nim"
                           if engine.dialect.name == "postgresql" else
                           "UPDATE mahasiswa SET user_id = (SELECT id FROM users WHERE users.nim = mahasiswa.nim)"
                           " WHERE user_id IS NULL AND EXISTS (SELECT 1 FROM users WHERE users.nim = mahasiswa.nim)"))
    stat["link_user_mhs"] = link.rowcount or 0
    db.commit()
    db.close()
    print(stat)


if __name__ == "__main__":
    main()
