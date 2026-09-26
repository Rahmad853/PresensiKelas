import sqlite3
con = sqlite3.connect('db_absensi.db')
cur = con.cursor()
cur.execute("PRAGMA foreign_keys=OFF")

# Kosongkan kelas_id pada tabel mahasiswa dan users bagi yang tidak valid atau belum terdistribusi
# Kita set kelas_id = NULL jika mahasiswa tidak terdaftar resmi di pemetaan kelas awal
# Atau biarkan sesuai mapping CSV asli. Mari buat skrip sinkronisasi murni dari CSV.

import csv
csv_path = "Data Akun Mahasiswa - Sheet1.csv"
valid_nims = set()
with open(csv_path, encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        nim = r['NIM'].strip()
        if nim:
            valid_nims.add(nim)

# Ambil semua mahasiswa di DB
mhs_db = cur.execute("SELECT nim, nama_lengkap FROM mahasiswa").fetchall()
print(f"Total mahasiswa di DB: {len(mhs_db)}")

# Set mahasiswa yang tidak ada di CSV atau tidak punya kelas valid menjadi kelas_id = NULL
# Atau pastikan hanya mahasiswa yang ada di CSV yang punya kelas, sisanya NULL.
cur.execute("UPDATE mahasiswa SET kelas_id = NULL WHERE nim NOT IN (" + ",".join([f"'{n}'" for n in valid_nims]) + ")")
cur.execute("UPDATE users SET kelas_id = NULL WHERE nim NOT IN (" + ",".join([f"'{n}'" for n in valid_nims]) + ") AND role = 'mahasiswa'")

con.commit()
print("Mahasiswa tanpa kelas valid di-NULL-kan.")
print("Distribusi jumlah mahasiswa per kelas sekarang:")
for row in cur.execute("SELECT k.nama_kelas, COUNT(m.nim) FROM kelas k LEFT JOIN mahasiswa m ON k.id = m.kelas_id GROUP BY k.id"):
    print(row)
con.close()
