import sqlite3
con = sqlite3.connect("db_absensi.db")
cur = con.cursor()
print("SEBELUM:", cur.execute("SELECT id, nama_kelas, angkatan FROM kelas ORDER BY id").fetchall())
cur.execute("PRAGMA foreign_keys=OFF")
# Coba hapus tapi abaikan error jika tabel tidak ada
for table in ["absensi", "mata_kuliah", "mahasiswa", "users", "qr_sessions", "kelas"]:
    try:
        cur.execute(f"DELETE FROM {table} WHERE kelas_id IN (7,8)")
    except: pass
cur.execute("DELETE FROM kelas WHERE id IN (7,8)")
con.commit()
print("SESUDAH:", cur.execute("SELECT id, nama_kelas, nama_ketua_kelas, angkatan FROM kelas ORDER BY id").fetchall())
con.close()
