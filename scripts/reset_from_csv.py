"""Reset database dari CSV dengan kelas terstruktur per ketua kelas."""
import csv
import shutil
import sqlite3

shutil.copy("db_absensi.db", "db_absensi_backup_cleanup.db")
con = sqlite3.connect("db_absensi.db")
cur = con.cursor()
cur.execute("PRAGMA foreign_keys=OFF")

# 1. Reset data lama
cur.execute("DELETE FROM absensi")
cur.execute("DELETE FROM mata_kuliah")
cur.execute("DELETE FROM mahasiswa")
cur.execute("DELETE FROM users WHERE role IN ('ketua_kelas','mahasiswa')")
cur.execute("DELETE FROM kelas WHERE id > 1")

# 2. Load CSV mapping
mapping = {}
with open("Data Akun Mahasiswa - Sheet1.csv", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        nim = row["NIM"].strip()
        if nim and nim not in mapping:
            mapping[nim] = {
                "nama": " ".join(row["Nama"].split()),
                "angkatan": int(row["Angkatan"].strip()) if row["Angkatan"].strip().isdigit() else None,
                "role": row["Role"].strip().lower(),
            }
print(f"CSV unique NIM: {len(mapping)}")

# 3. Kelas per ketua kelas dari CSV (5 kelas)
kelas_data = {}
# Filter hanya mengambil mahasiswa dengan role 'ketua kelas'
ketua_list = [m for m in mapping.items() if m[1]["role"] == "ketua kelas"][:5]
for idx, (nim_ketua, ketua_info) in enumerate(ketua_list):
    nama = f"Kelas {chr(65+idx)}"
    cur.execute("INSERT INTO kelas (nama_kelas, nama_ketua_kelas, tahun_ajaran, angkatan) VALUES (?, ?, 2025, ?)",
                (nama, ketua_info["nama"], ketua_info["angkatan"]))
con.commit()
kelas_map = {row[1]: row[0] for row in cur.execute("SELECT id, nama_kelas FROM kelas")}
print("Kelas dibuat:", kelas_map)

# 4. Create ketua_kelas + mahasiswa per kelas (Maksimal 30 per kelas)
for idx, (nim_ketua, ketua_info) in enumerate(ketua_list):
    nama_ketua = ketua_info["nama"]
    kelas_id = cur.execute("SELECT id FROM kelas WHERE nama_kelas = ?", (f"Kelas {chr(65+idx)}",)).fetchone()[0]
    
    # User ketua_kelas
    cur.execute("INSERT INTO users (username, nim, password_hash, role, kelas_id) VALUES (?, ?, ?, ?, ?)",
                (nama_ketua, nim_ketua, "pbkdf2_sha256$390000$placeholder$hash", "ketua_kelas", kelas_id))
    
    # Mahasiswa dalam kelas ini (anggota, limit 29 karena 1 ketua)
    anggota = [(n, m) for n, m in mapping.items() if m["role"] == "anggota" and m["angkatan"] == ketua_info["angkatan"]][:29]
    for nim_mhs, mhs_info in anggota:
        cur.execute("INSERT INTO mahasiswa (nim, nama_lengkap, kelas_id, angkatan) VALUES (?, ?, ?, ?)",
                    (nim_mhs, mhs_info["nama"], kelas_id, mhs_info["angkatan"]))
        cur.execute("INSERT INTO users (username, nim, password_hash, role, kelas_id) VALUES (?, ?, ?, ?, ?)",
                    (mhs_info["nama"], nim_mhs, "pbkdf2_sha256$390000$placeholder$hash", "mahasiswa", kelas_id))
con.commit()
print("Selesai: kelas + ketua + mahasiswa (max 30)")

print("Fase 1 selesai: kelas + ketua + mahasiswa")