import sqlite3

con = sqlite3.connect("db_absensi.db")
cur = con.cursor()
cur.execute("PRAGMA foreign_keys=OFF")
print("SEBELUM:", cur.execute("SELECT id,nama_kelas,angkatan,nama_ketua_kelas FROM kelas ORDER BY id").fetchall())

# 1 angkatan = 2025 punya Kelas A-E (5 kelas paralel)
for kid in (2, 3, 4, 5, 6):
    cur.execute("UPDATE kelas SET angkatan=2025, tahun_ajaran=2025 WHERE id=?", (kid,))

con.commit()
print("SESUDAH:", cur.execute("SELECT id,nama_kelas,angkatan,nama_ketua_kelas FROM kelas ORDER BY id").fetchall())
print("ketua:", cur.execute("SELECT username,kelas_id FROM users WHERE role='ketua_kelas' ORDER BY kelas_id").fetchall())
con.close()
