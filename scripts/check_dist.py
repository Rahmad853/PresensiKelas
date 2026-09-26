import sqlite3
con = sqlite3.connect("db_absensi.db")
cur = con.cursor()
print("users mahasiswa per kelas_id:")
for r in cur.execute("SELECT kelas_id, COUNT(*) FROM users WHERE role='mahasiswa' GROUP BY kelas_id"):
    print(r)
print("mahasiswa per kelas_id:")
for r in cur.execute("SELECT kelas_id, COUNT(*) FROM mahasiswa GROUP BY kelas_id"):
    print(r)
print("contoh user tanpa mhs record:")
for r in cur.execute("SELECT id, username, nim, kelas_id FROM users WHERE role='mahasiswa' AND nim IS NOT NULL LIMIT 5"):
    print(r)
print("skema mahasiswa:", cur.execute("SELECT sql FROM sqlite_master WHERE name='mahasiswa'").fetchone()[0][:400])
con.close()
