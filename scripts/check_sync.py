import sqlite3
con = sqlite3.connect("db_absensi.db")
cur = con.cursor()
print("=== mismatch user.kelas vs mahasiswa.kelas ===")
rows = cur.execute("""
  SELECT u.id, u.username, u.kelas_id AS uk, m.nim, m.kelas_id AS mk
  FROM users u JOIN mahasiswa m ON m.user_id = u.id
  WHERE u.kelas_id IS NOT m.kelas_id
""").fetchall()
print(f"mismatch: {len(rows)}")
for r in rows[:10]:
    print(r)
print("=== mahasiswa tanpa user ===")
print(cur.execute("SELECT COUNT(*) FROM mahasiswa WHERE user_id IS NULL").fetchone())
print("=== user mahasiswa tanpa record mahasiswa ===")
print(cur.execute("""
  SELECT COUNT(*) FROM users u WHERE u.role='mahasiswa'
  AND NOT EXISTS (SELECT 1 FROM mahasiswa m WHERE m.user_id=u.id OR m.nim=u.nim)
""").fetchone())
con.close()
