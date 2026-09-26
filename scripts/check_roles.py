import sqlite3
con = sqlite3.connect("db_absensi.db")
cur = con.cursor()
print("ROLES:", cur.execute("SELECT DISTINCT role FROM users").fetchall())
print("NONSTANDAR:", cur.execute("SELECT id, username, role FROM users WHERE role NOT IN ('admin','ketua_kelas','mahasiswa')").fetchall())
con.close()
