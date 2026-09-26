import sqlite3
con = sqlite3.connect("db_absensi.db")
cur = con.cursor()
cur.execute("PRAGMA foreign_keys=OFF")

# Recreate tabel mahasiswa dengan kelas_id NULLABLE
cur.execute("""
CREATE TABLE mahasiswa_new (
	nim VARCHAR(20) NOT NULL, 
	nama_lengkap VARCHAR(100) NOT NULL, 
	kelas_id INTEGER, 
	user_id INTEGER, 
	foto VARCHAR(255), 
	angkatan INTEGER, 
	PRIMARY KEY (nim), 
	FOREIGN KEY(kelas_id) REFERENCES kelas (id) ON DELETE RESTRICT, 
	UNIQUE (user_id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE SET NULL
)
""")

# Salin data lama dengan kelas_id NULL
cur.execute("""
INSERT INTO mahasiswa_new (nim, nama_lengkap, kelas_id, user_id, foto, angkatan)
SELECT nim, nama_lengkap, NULL, user_id, foto, angkatan FROM mahasiswa
""")

cur.execute("DROP TABLE mahasiswa")
cur.execute("ALTER TABLE mahasiswa_new RENAME TO mahasiswa")
cur.execute("CREATE INDEX IF NOT EXISTS ix_mahasiswa_kelas_id ON mahasiswa (kelas_id)")
cur.execute("CREATE INDEX IF NOT EXISTS ix_mahasiswa_kelas_nama ON mahasiswa (kelas_id, nama_lengkap)")

# Set user mahasiswa kelas_id = NULL
cur.execute("UPDATE users SET kelas_id = NULL WHERE role = 'mahasiswa'")

# Pastikan ketua kelas tetap di kelasnya
ketua_rows = cur.execute("SELECT id, nama_ketua_kelas FROM kelas").fetchall()
for kid, nama_ketua in ketua_rows:
    cur.execute("UPDATE users SET kelas_id=? WHERE username=? AND role='ketua_kelas'", (kid, nama_ketua))

con.commit()
print("Selesai: Semua mahasiswa sekarang bebas kelas (kelas_id = NULL). Data akan masuk hanya saat Anda tambahkan kelasnya.")
con.close()
