import sqlite3
con = sqlite3.connect("db_absensi.db")
cur = con.cursor()
cur.execute("PRAGMA foreign_keys=OFF")
mapping = [(3, "Muh Ghulam Al Firdaus Ramadhan"), (4, "A.Muh.Agussalim.Z"),
           (5, "Rahmat Ramadhan azis"), (6, "Rizki Al Gifahri")]
for kid, nama in mapping:
    cur.execute("UPDATE kelas SET nama_ketua_kelas=? WHERE id=?", (nama, kid))
    cur.execute("UPDATE users SET kelas_id=? WHERE username=? AND role='ketua_kelas'", (kid, nama))
con.commit()
print("KELAS:", cur.execute("SELECT id, nama_kelas, nama_ketua_kelas FROM kelas ORDER BY id").fetchall())
print("KETUA:", cur.execute("SELECT username, kelas_id FROM users WHERE role='ketua_kelas'").fetchall())
con.close()
