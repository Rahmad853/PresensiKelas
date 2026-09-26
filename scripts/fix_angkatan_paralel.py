import sqlite3

con = sqlite3.connect("db_absensi.db")
cur = con.cursor()
cur.execute("PRAGMA foreign_keys=OFF")

# 1. Samakan: 1 angkatan (2025) punya Kelas A-E paralel
for kid in (2, 3, 4, 5, 6):
    cur.execute("UPDATE kelas SET angkatan=2025, tahun_ajaran=2025 WHERE id=?", (kid,))

# 2. FK mahasiswa.kelas_id -> SET NULL (bangun ulang tabel)
cur.execute("""
CREATE TABLE mahasiswa_new (
    nim VARCHAR(20) NOT NULL,
    nama_lengkap VARCHAR(100) NOT NULL,
    kelas_id INTEGER,
    user_id INTEGER,
    foto VARCHAR(255),
    angkatan INTEGER,
    PRIMARY KEY (nim),
    FOREIGN KEY(kelas_id) REFERENCES kelas (id) ON DELETE SET NULL,
    UNIQUE (user_id),
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE SET NULL
)
""")
cur.execute("INSERT INTO mahasiswa_new SELECT nim, nama_lengkap, kelas_id, user_id, foto, angkatan FROM mahasiswa")
cur.execute("DROP TABLE mahasiswa")
cur.execute("ALTER TABLE mahasiswa_new RENAME TO mahasiswa")
cur.execute("CREATE INDEX IF NOT EXISTS ix_mahasiswa_kelas_id ON mahasiswa (kelas_id)")
cur.execute("CREATE INDEX IF NOT EXISTS ix_mahasiswa_kelas_nama ON mahasiswa (kelas_id, nama_lengkap)")
cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_kelas_nama_angkatan ON kelas (nama_kelas, angkatan)")

# 3. Sinkron user <-> mahasiswa
cur.execute("UPDATE users SET kelas_id=NULL WHERE role='mahasiswa'")
cur.execute("""
UPDATE users SET kelas_id=(SELECT m.kelas_id FROM mahasiswa m WHERE m.user_id=users.id)
WHERE role='mahasiswa' AND EXISTS (SELECT 1 FROM mahasiswa m WHERE m.user_id=users.id AND m.kelas_id IS NOT NULL)
""")
ketua = {2: "Abd. Rahmad", 3: "Muh Ghulam Al Firdaus Ramadhan", 4: "A.Muh.Agussalim.Z",
         5: "Rahmat Ramadhan azis", 6: "Rizki Al Gifahri"}
for kid, nama in ketua.items():
    cur.execute("UPDATE kelas SET nama_ketua_kelas=? WHERE id=?", (nama, kid))
    cur.execute("UPDATE users SET kelas_id=? WHERE username=? AND role='ketua_kelas'", (kid, nama))

con.commit()
print("KELAS:", cur.execute("SELECT id,nama_kelas,angkatan,nama_ketua_kelas FROM kelas ORDER BY id").fetchall())
print("MHS_DIST:", cur.execute("SELECT kelas_id,COUNT(*) FROM mahasiswa GROUP BY kelas_id").fetchall())
print("KETUA:", cur.execute("SELECT username,kelas_id FROM users WHERE role='ketua_kelas' ORDER BY kelas_id").fetchall())
con.close()
