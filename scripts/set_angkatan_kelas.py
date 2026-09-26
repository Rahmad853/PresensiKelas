import sqlite3

con = sqlite3.connect("db_absensi.db")
cur = con.cursor()
cur.execute("PRAGMA foreign_keys=OFF")

# Update angkatan berbeda untuk Kelas A-E
angkatan_map = {
    2: 2022, # Kelas A
    3: 2023, # Kelas B
    4: 2024, # Kelas C
    5: 2025, # Kelas D
    6: 2026  # Kelas E
}

for kid, angkatan in angkatan_map.items():
    cur.execute("UPDATE kelas SET angkatan=? WHERE id=?", (angkatan, kid))

con.commit()
print("Angkatan unik untuk Kelas A-E berhasil diset.")
for r in cur.execute("SELECT id, nama_kelas, angkatan, nama_ketua_kelas FROM kelas ORDER BY id").fetchall():
    print(r)

con.close()
