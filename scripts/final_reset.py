"""Reset database from CSV with proper deduplication."""
import csv
import sqlite3

con = sqlite3.connect('db_absensi.db')
cur = con.cursor()
cur.execute('PRAGMA foreign_keys=OFF')

# Clear tables
cur.execute('DELETE FROM absensi')
cur.execute('DELETE FROM mata_kuliah')
cur.execute('DELETE FROM mahasiswa')
cur.execute('DELETE FROM users WHERE username != "admin"')
cur.execute('DELETE FROM kelas')
con.commit()

# Load CSV mapping
mapping = {}
with open('Data Akun Mahasiswa - Sheet1.csv', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        nim = row['NIM'].strip()
        if nim and nim not in mapping:
            mapping[nim] = {
                'nama': ' '.join(row['Nama'].split()),
                'angkatan': int(row['Angkatan'].strip()) if row['Angkatan'].strip().isdigit() else None,
                'role': row['Role'].strip().lower(),
            }
print(f'CSV unique NIM: {len(mapping)}')

# Kelompokkan berdasarkan angkatan dan role
ketua_by_angkatan = {}
anggota_by_angkatan = {}
for nim, info in mapping.items():
    if info['role'] == 'ketua kelas':
        ketua_by_angkatan[info['angkatan']] = (nim, info)
    else:
        angkatan = info['angkatan']
        if angkatan not in anggota_by_angkatan:
            anggota_by_angkatan[angkatan] = []
        anggota_by_angkatan[angkatan].append((nim, info))

print('Ketua per angkatan:', ketua_by_angkatan)
print('Jumlah anggota per angkatan:', {a: len(v) for a, v in anggota_by_angkatan.items()})

# Buat kelas per angkatan (1 angkatan = 1 kelas)
for angkatan, (nim_ketua, ketua_info) in ketua_by_angkatan.items():
    nama = f'Kelas {chr(65 + len(ketua_by_angkatan) - 1)}'
    cur.execute('INSERT INTO kelas (nama_kelas, nama_ketua_kelas, tahun_ajaran, angkatan) VALUES (?, ?, 2025, ?)',
                (nama, ketua_info['nama'], angkatan))
con.commit()

kelas_map = {}
for row in cur.execute('SELECT id, angkatan FROM kelas ORDER BY angkatan'):
    kelas_map[row[1]] = row[0]
print('Kelas angkatan:', kelas_map)

# Buat ketua kelas dan mahasiswa per angkatan
for angkatan, (nim_ketua, ketua_info) in ketua_by_angkatan.items():
    kelas_id = kelas_map[angkatan]
    # Ketua kelas
    cur.execute('INSERT INTO users (username, nim, password_hash, role, kelas_id) VALUES (?, ?, ?, ?, ?)',
                (ketua_info['nama'], nim_ketua, 'pbkdf2_sha256$390000$placeholder$hash', 'ketua_kelas', kelas_id))
    
    # Mahasiswa (maksimal 29 per angkatan)
    anggota = anggota_by_angkatan.get(angkatan, [])[:29]
    for nim_mhs, mhs_info in anggota:
        cur.execute('INSERT INTO mahasiswa (nim, nama_lengkap, kelas_id, angkatan) VALUES (?, ?, ?, ?)',
                    (nim_mhs, mhs_info['nama'], kelas_id, angkatan))
        cur.execute('INSERT INTO users (username, nim, password_hash, role, kelas_id) VALUES (?, ?, ?, ?, ?)',
                    (mhs_info['nama'], nim_mhs, 'pbkdf2_sha256$390000$placeholder$hash', 'mahasiswa', kelas_id))
con.commit()

print('Selesai: kelas + ketua + mahasiswa (maksimal 30 per kelas)')
print('=== DATA AKHIR ===')
print('Kelas:', cur.execute('SELECT * FROM kelas').fetchall())
print('Users:', cur.execute('SELECT id, username, nim, role FROM users').fetchall())
print('Mahasiswa:', cur.execute('SELECT * FROM mahasiswa').fetchall())