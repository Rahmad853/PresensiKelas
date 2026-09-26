from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models import Absensi, Kelas, Mahasiswa, MataKuliah, User
from app.schemas.absensi import AbsensiCreate
from app.services import absensi as svc
from app.services.absensi import hitung_rekap


def _db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def test_catat_duplikat_ditolak():
    db = _db()
    db.add(Kelas(id=1, nama_kelas="A", tahun_ajaran=2026))
    db.add(Mahasiswa(nim="1", nama_lengkap="A", kelas_id=1))
    db.add(MataKuliah(id=1, kode="K1", nama="M1", kelas_id=1))
    db.commit()
    admin = {"sub": "9", "role": "admin"}
    svc.catat_absensi(db, AbsensiCreate(nim="1", tanggal=date(2026, 1, 5), status="hadir", mata_kuliah_id=1), admin)
    try:
        svc.catat_absensi(db, AbsensiCreate(nim="1", tanggal=date(2026, 1, 5), status="izin", mata_kuliah_id=1), admin)
        raise AssertionError("duplikat lolos")
    except Exception as e:
        assert "sudah tercatat" in str(e.detail if hasattr(e, "detail") else e)


def test_rekap_hitungan_benar():
    db = _db()
    db.add(Kelas(id=1, nama_kelas="A", tahun_ajaran=2026))
    db.add(Mahasiswa(nim="1", nama_lengkap="B", kelas_id=1))
    db.add(MataKuliah(id=1, kode="K1", nama="M1", kelas_id=1))
    db.add(Absensi(nim="1", tanggal=date(2026, 2, 2), status="hadir", metode="manual", mata_kuliah_id=1))
    db.add(Absensi(nim="1", tanggal=date(2026, 2, 3), status="alfa", metode="manual", mata_kuliah_id=1))
    db.add(User(id=1, username="a", password_hash="x", role="admin"))
    db.commit()
    rows = hitung_rekap(db, 1, 2, 2026, 1)
    assert rows[0].hadir == 1 and rows[0].alfa == 1 and rows[0].total_hari == 2
