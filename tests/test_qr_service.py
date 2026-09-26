from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models import Kelas, Mahasiswa, MataKuliah, User
from app.services import qr as svc


def _db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(bind=engine)
    db = sessionmaker(bind=engine)()
    db.add(Kelas(id=1, nama_kelas="A", tahun_ajaran=2026))
    db.add(MataKuliah(id=1, kode="K1", nama="M1", kelas_id=1))
    db.add(User(id=9, username="ketua", password_hash="x", role="ketua_kelas", kelas_id=1))
    db.add(User(id=7, username="mhs", password_hash="x", role="mahasiswa", kelas_id=1))
    db.add(Mahasiswa(nim="1", nama_lengkap="M", kelas_id=1, user_id=7))
    db.commit()
    return db


def test_generate_scan_matikan():
    db = _db()
    sesi = svc.buat_sesi_qr(db, 1, 1, None, 9)
    assert sesi["token"]
    r = svc.scan_qr(db, sesi["token"], "1", {"sub": "7", "role": "mahasiswa"})
    assert r["status"] == "hadir" and r["sudah_tercatat"] is False
    r2 = svc.scan_qr(db, sesi["token"], "1", {"sub": "7", "role": "mahasiswa"})
    assert r2["sudah_tercatat"] is True
    svc.matikan_sesi(db, sesi["token"], {"sub": "9", "role": "ketua_kelas", "kelas_id": 1})
    try:
        svc.gambar_qr(db, sesi["token"])
        raise AssertionError("sesi mati masih bisa dibuka")
    except Exception as e:
        assert "dimatikan atau kadaluarsa" in str(getattr(e, "detail", e))


def test_generate_tolak_matkul_beda_kelas():
    db = _db()
    db.add(Kelas(id=2, nama_kelas="B", tahun_ajaran=2026))
    db.commit()
    try:
        svc.buat_sesi_qr(db, 2, 1, None, 9)
        raise AssertionError("matkul beda kelas lolos")
    except Exception as e:
        assert "bukan milik kelas" in str(getattr(e, "detail", e))
