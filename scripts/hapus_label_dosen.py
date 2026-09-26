import sqlite3
con = sqlite3.connect("db_absensi.db")
cur = con.cursor()
cur.execute("PRAGMA foreign_keys=OFF")
rows = cur.execute("SELECT id, nama_kelas, nama_ketua_kelas FROM kelas").fetchall()
print("SEBELUM:", rows)
for kid, nama, penanggung in rows:
    ketua = cur.execute("SELECT username FROM users WHERE role='ketua_kelas' AND kelas_id=?", (kid,)).fetchone()
    baru = ketua[0] if ketua else penanggung.replace("Dosen Wali ", "")
    cur.execute("UPDATE kelas SET nama_ketua_kelas=? WHERE id=?", (baru, kid))
con.commit()
print("SESUDAH:", cur.execute("SELECT id, nama_kelas, nama_ketua_kelas FROM kelas ORDER BY id").fetchall())
print("ROLES:", cur.execute("SELECT DISTINCT role FROM users").fetchall())
con.close()
