import sqlite3
con = sqlite3.connect('db_absensi.db')
cur = con.cursor()
print('=== KELAS ===')
for r in cur.execute('SELECT id, nama_kelas, nama_ketua_kelas, tahun_ajaran, angkatan FROM kelas ORDER BY id'):
    print(r)
print()
print('=== JUMLAH MAHASISWA PER KELAS ===')
for r in cur.execute('SELECT kelas_id, COUNT(*) FROM mahasiswa GROUP BY kelas_id'):
    print(r)
print()
print('=== MAHASISWA TANPA KELAS VALID ===')
for r in cur.execute('SELECT m.nim, m.nama_lengkap, m.kelas_id FROM mahasiswa m LEFT JOIN kelas k ON m.kelas_id=k.id WHERE k.id IS NULL'):
    print(r)
print()
print('=== CONTOH MAHASISWA ===')
for r in cur.execute('SELECT nim, nama_lengkap, kelas_id, angkatan FROM mahasiswa ORDER BY nim LIMIT 10'):
    print(r)
print()
print('=== USERS ===')
for r in cur.execute('SELECT id, username, nim, role, kelas_id FROM users WHERE role IN ("ketua_kelas","mahasiswa") LIMIT 15'):
    print(r)