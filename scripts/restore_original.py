"""Restore original state from backup."""
import shutil
import sqlite3

# Restore original database from backup
shutil.copy("db_absensi_backup_20260924_1315.db", "db_absensi.db")
con = sqlite3.connect("db_absensi.db")
cur = con.cursor()
print("Kelas:", cur.execute("SELECT * FROM kelas").fetchall())
print("Users:", cur.execute("SELECT id, username, nim, role, kelas_id FROM users").fetchall())
print("Mahasiswa:", cur.execute("SELECT nim, nama_lengkap, kelas_id FROM mahasiswa").fetchall())
con.close()

# Restore original seed.py script (with safe encoding)
original_seed = '''"""
Jalankan sekali untuk mengisi data awal:
    python seed.py
"""
from database import SessionLocal, engine
from models.models import Base, User, Kelas, Mahasiswa, MataKuliah
from core.security import hash_password

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# ── Kelas ──
kelas = db.query(Kelas).filter(Kelas.nama_kelas == "TI-2A").first()
if not kelas:
    kelas = Kelas(nama_kelas="TI-2A", nama_ketua_kelas="Dr. Budi Santoso", tahun_ajaran=2026)
    db.add(kelas)
    db.flush()

# ── User admin ──
if not db.query(User).filter(User.username == "admin").first():
    db.add(User(
        username="admin",
        password_hash=hash_password("admin123"),
        role="admin",
    ))

# ── User ketua_kelas ──
if not db.query(User).filter(User.username == "ketua").first():
    db.add(User(
        username="ketua",
        password_hash=hash_password("ketua123"),
        role="ketua_kelas",
        kelas_id=kelas.id,
    ))

# ── Mahasiswa + akun login ──
mahasiswa_data = [
    ("2024001", "Ahmad Hidayat",   "ahmad"),
    ("2024002", "Dewi Sartika",    "dewi"),
    ("2024003", "Fajar Ramadan",   "fajar"),
    ("2024004", "Nadia Putri",     "nadia"),
    ("2024005", "Rizky Maulana",   "rizky"),
]

db.flush()

for nim, nama, username in mahasiswa_data:
    # Buat user login mahasiswa
    user_mhs = db.query(User).filter(User.username == username).first()
    if not user_mhs:
        user_mhs = User(
            username=username,
            password_hash=hash_password(username + "123"),
            role="mahasiswa",
        )
        db.add(user_mhs)
        db.flush()

    # Buat data mahasiswa
    if not db.query(Mahasiswa).filter(Mahasiswa.nim == nim).first():
        db.add(Mahasiswa(
            nim=nim,
            nama_lengkap=nama,
            kelas_id=kelas.id,
            user_id=user_mhs.id,
        ))

# ── Mata Kuliah ──
if not db.query(MataKuliah).filter(MataKuliah.kode == "IF101").first():
    db.add(MataKuliah(
        kode="IF101",
        nama="Pengantar Teknologi Informasi",
        semester=1,
        kelas_id=kelas.id,
    ))

if not db.query(MataKuliah).filter(MataKuliah.kode == "IF102").first():
    db.add(MataKuliah(
        kode="IF102",
        nama="Pemrograman Dasar",
        semester=1,
        kelas_id=kelas.id,
    ))

db.commit()
db.close()
print("Seed selesai! Akun yang tersedia:")
print("-" * 45)
print("ADMIN    -> username: admin   | password: admin123")
print("KETUA    -> username: ketua   | password: ketua123")
print("MAHASISWA:")
for _, nama, username in mahasiswa_data:
    print(f"  {nama:<18} -> {username} / {username}123")
print("=" * 45)
'''

# Write the original seed.py with UTF-8 encoding
with open("seed.py", "w", encoding="utf-8") as f:
    f.write(original_seed)

print("Restored to original state with TI-2A class")
print("Original seed.py restored")

# Print final state
import sqlite3
con = sqlite3.connect("db_absensi.db")
cur = con.cursor()
print("\n=== FINAL STATE ===")
print("Kelas:", cur.execute("SELECT * FROM kelas").fetchall())
print("Users:", cur.execute("SELECT id, username, nim, role, kelas_id FROM users").fetchall())
print("Mahasiswa:", cur.execute("SELECT nim, nama_lengkap, kelas_id FROM mahasiswa").fetchall())
print("MataKuliah:", cur.execute("SELECT * FROM mata_kuliah").fetchall())
con.close()
