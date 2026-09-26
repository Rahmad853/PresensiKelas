"""Cleanup: hapus kelas TI-2A (7) + semua data terkait, reset dari CSV."""
import csv
import shutil
import sqlite3

shutil.copy("db_absensi.db", "db_absensi_backup_cleanup.db")

con = sqlite3.connect("db_absensi.db")
con.execute("PRAGMA foreign_keys=OFF")
cur = con.cursor()

kelas_id_ti2a = 7

# Hapus absensi, mahasiswa, matakuliah kelas TI-2A
cur.execute("DELETE FROM absensi WHERE nim IN (SELECT nim FROM mahasiswa WHERE kelas_id=?)", (kelas_id_ti2a,))
cur.execute("DELETE FROM mata_kuliah WHERE kelas_id=?", (kelas_id_ti2a,))
cur.execute("DELETE FROM mahasiswa WHERE kelas_id=?", (kelas_id_ti2a,))
# Hapus users seed TI-2A (ahmad/dewi/fajar/nadia/rizky + ketua) yang kelas_id NULL atau kelas TI-2A
cur.execute("DELETE FROM users WHERE nim IN ('2024001','2024002','2024003','2024004','2024005')")
cur.execute("DELETE FROM users WHERE kelas_id=? AND username!='admin'", (kelas_id_ti2a,))
cur.execute("DELETE FROM users WHERE username IN ('ketua')")
# Hapus kelas TI-2A
cur.execute("DELETE FROM kelas WHERE id=?", (kelas_id_ti2a,))
con.commit()

# Load CSV
mapping = {}
with open("Data Akun Mahasiswa - Sheet1.csv", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        nim = row["NIM"].strip()
        if nim and nim not in mapping:
            mapping[nim] = {
                "nama": " ".join(row["Nama"].split()),
                "angkatan": int(row["Angkatan"].strip()) if row["Angkatan"].strip().isdigit() else None,
                "role": row["Role"].strip().lower(),
            }
print(f"CSV unique NIM: {len(mapping)}")

# Tabel kelas: perbarui Kelas A-E dengan ketua dari CSV (role ketua kelas)
# Sinkron User ketua_kelas yang sudah ada dengan kelas benar.
users = list(cur.execute("SELECT id, username, nim, role, kelas_id FROM users"))
user_by_nim = {u[2]: u for u in users if u[2]}
kelas_rows = list(cur.execute("SELECT id, nama_kelas FROM kelas ORDER BY id"))
kelas_by_name = {k[1]: k[0] for k in kelas_rows}
print("Kelas sekarang:", kelas_rows)

con.commit()
con.close()
print("Selesai fase 1: TI-2A + datanya dihapus, backup dibuat.")