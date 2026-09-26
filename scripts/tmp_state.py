import sqlite3
con = sqlite3.connect("db_absensi.db")
print([r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")])
try:
    print("version:", list(con.execute("SELECT * FROM alembic_version")))
except Exception as e:
    print("no version table")
print(con.execute("SELECT sql FROM sqlite_master WHERE name='kelas'").fetchone()[0][:800])
print(con.execute("SELECT sql FROM sqlite_master WHERE name='mahasiswa'").fetchone()[0][:800])
con.close()
