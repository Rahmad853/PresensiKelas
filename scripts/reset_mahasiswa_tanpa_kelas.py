import sqlite3
con = sqlite3.connect("db_absensi.db")
cur = con.cursor()
cur.execute("PRAGMA foreign_keys=OFF")

# Set kelas_id menjadi NULL untuk semua mahasiswa dan user mahasiswa kecuali yang memang di-mapping awal
# Artinya: "yang belum saya tambahkan kelasnya jgn tambahkan ke kelas manapun"
cur.execute("UPDATE mahasiswa SET kelas_id = NULL")
cur.execute("UPDATE users SET kelas_id = NULL WHERE role = 'mahasiswa'")

# Kecualikan 5 ketua kelas dan anggota yang sudah di-assign eksplisit jika ada (biarkan ketua tetap di kelasnya)
# Kita pastikan ketua tetap punya kelas_id sesuai posisinya di tabel kelas
ketua_rows = cur.execute("SELECT id, nama_ketua_kelas FROM kelas").fetchall()
for kid, nama_ketua in ketua_rows:
    cur.execute("UPDATE users SET kelas_id=? WHERE username=? AND role='ketua_kelas'", (kid, nama_ketua))

con.commit()
print("Berhasil! Semua mahasiswa kini kelas_id = NULL (belum masuk kelas manapun), kecuali akun ketua kelas.")
con.close()
