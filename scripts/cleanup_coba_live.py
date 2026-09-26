import sqlite3
con = sqlite3.connect('db_absensi.db')
cur = con.cursor()

# Hapus mahasiswa 'Coba Live'
cur.execute('DELETE FROM users WHERE username = "Coba Live"')
cur.execute('DELETE FROM mahasiswa WHERE nama_lengkap = "Coba Live"')

# Validasi mahasiswa ada di kelas yang benar (sinkronisasi user kelas_id)
# Update user.kelas_id agar sesuai dengan mahasiswa.kelas_id
cur.execute('''
    UPDATE users 
    SET kelas_id = (SELECT kelas_id FROM mahasiswa WHERE mahasiswa.nim = users.nim)
    WHERE role = 'mahasiswa' AND nim IS NOT NULL
''')

con.commit()
print("Akun 'Coba Live' dihapus dan relasi kelas mahasiswa/users disinkronkan.")
con.close()
