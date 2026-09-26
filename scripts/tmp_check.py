import sqlite3
con = sqlite3.connect("db_absensi.db")
cur = con.cursor()
print(cur.execute("SELECT id,nama_kelas,angkatan,nama_ketua_kelas FROM kelas ORDER BY id").fetchall())
print(cur.execute("SELECT kelas_id,COUNT(*) FROM mahasiswa GROUP BY kelas_id").fetchall())
print("ketua:", cur.execute("SELECT username,kelas_id FROM users WHERE role='ketua_kelas'").fetchall())
print("mk:", cur.execute("SELECT kelas_id,COUNT(*) FROM mata_kuliah GROUP BY kelas_id").fetchall())
con.close()
