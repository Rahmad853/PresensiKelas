"""Seed idempoten: python scripts/seed.py (target = DATABASE_URL)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import Kelas, Mahasiswa, MataKuliah, User

db = SessionLocal()

kelas = db.query(Kelas).filter(Kelas.nama_kelas == "TI-2A").first()
if not kelas:
    kelas = Kelas(nama_kelas="TI-2A", nama_ketua_kelas="Dr. Budi Santoso", tahun_ajaran=2026)
    db.add(kelas)
    db.flush()

if not db.query(User).filter(User.username == "admin").first():
    db.add(User(username="admin", password_hash=hash_password("admin123"), role="admin"))
if not db.query(User).filter(User.username == "ketua").first():
    db.add(User(username="ketua", password_hash=hash_password("ketua123"), role="ketua_kelas", kelas_id=kelas.id))
db.flush()

for nim, nama, username in [
    ("2024001", "Ahmad Hidayat", "ahmad"), ("2024002", "Dewi Sartika", "dewi"),
    ("2024003", "Fajar Ramadan", "fajar"), ("2024004", "Nadia Putri", "nadia"),
    ("2024005", "Rizky Maulana", "rizky"),
]:
    u = db.query(User).filter(User.username == username).first()
    if not u:
        u = User(username=username, nim=nim, password_hash=hash_password(username + "123"), role="mahasiswa")
        db.add(u)
        db.flush()
    if not db.query(Mahasiswa).filter(Mahasiswa.nim == nim).first():
        db.add(Mahasiswa(nim=nim, nama_lengkap=nama, kelas_id=kelas.id, user_id=u.id))

for kode, nama in [("IF101", "Pengantar Teknologi Informasi"), ("IF102", "Pemrograman Dasar")]:
    if not db.query(MataKuliah).filter(MataKuliah.kode == kode).first():
        db.add(MataKuliah(kode=kode, nama=nama, semester=1, kelas_id=kelas.id))

db.commit()
db.close()
print("Seed selesai: admin/admin123, ketua/ketua123, mahasiswa <nama>/<nama>123")
