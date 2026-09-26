import sqlite3
import csv

con = sqlite3.connect("db_absensi.db")
cur = con.cursor()
cur.execute("PRAGMA foreign_keys=OFF")

# 1. Ambil list kelas valid (A-E)
kelas_list = cur.execute("SELECT id FROM kelas ORDER BY id").fetchall()
kelas_ids = [k[0] for k in kelas_list] # [2, 3, 4, 5, 6]

if not kelas_ids:
    print("Error: Tidak ada kelas. Jalankan seed/reset dulu.")
    con.close()
    exit()

# 2. Ambil list anggota (mahasiswa) dari users yang belum tertaut atau perlu di-refresh
# Kita pakai data dari users karena record mahasiswa banyak yang kosong
anggota_users = cur.execute("""
    SELECT id, username, nim FROM users 
    WHERE role='mahasiswa' AND nim IS NOT NULL
    ORDER BY id
""").fetchall()

print(f"Total user mahasiswa: {len(anggota_users)}")

# 3. Bagi rata (Round-robin)
# Kapasitas: (30 anggota - 1 ketua) = 29 mahasiswa per kelas
# 5 kelas * 29 = 145 kapasitas total. 117 mahasiswa cukup.
for idx, u in enumerate(anggota_users):
    u_id, username, nim = u
    kelas_id = kelas_ids[idx % len(kelas_ids)]
    
    # Update user
    cur.execute("UPDATE users SET kelas_id=? WHERE id=?", (kelas_id, u_id))
    
    # Upsert mahasiswa (nim PK)
    cur.execute("""
        INSERT INTO mahasiswa (nim, nama_lengkap, kelas_id, user_id, angkatan)
        VALUES (?, ?, ?, ?, 2025)
        ON CONFLICT(nim) DO UPDATE SET 
            kelas_id=excluded.kelas_id,
            user_id=excluded.user_id,
            nama_lengkap=excluded.nama_lengkap
    """, (nim, username, kelas_id, u_id))

con.commit()
print("Distribusi round-robin selesai.")

# 4. Verifikasi hitungan (termasuk ketua)
print("\n=== Hitungan Anggota Per Kelas (Mhs + Ketua) ===")
for kid in kelas_ids:
    nama = cur.execute("SELECT nama_kelas FROM kelas WHERE id=?", (kid,)).fetchone()[0]
    mhs_count = cur.execute("SELECT COUNT(*) FROM mahasiswa WHERE kelas_id=?", (kid,)).fetchone()[0]
    ketua_count = cur.execute("SELECT COUNT(*) FROM users WHERE role='ketua_kelas' AND kelas_id=?", (kid,)).fetchone()[0]
    print(f"{nama}: {mhs_count + ketua_count} Anggota ({mhs_count} Mhs, {ketua_count} Ketua)")

con.close()
