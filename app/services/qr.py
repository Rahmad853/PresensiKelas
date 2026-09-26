import json
from datetime import date, datetime, timedelta, timezone
from io import BytesIO

import qrcode
from fastapi import HTTPException
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import buat_token, decode_token
from app.models import Absensi, Mahasiswa, QrSession


def buat_sesi_qr(db: Session, kelas_id: int, mata_kuliah_id: int, tanggal: date | None, dibuat_oleh: int) -> dict:
    from app.models import Kelas, MataKuliah
    if not db.query(Kelas).filter(Kelas.id == kelas_id).first():
        raise HTTPException(404, "Kelas tidak ditemukan")
    mk = db.query(MataKuliah).filter(MataKuliah.id == mata_kuliah_id).first()
    if not mk:
        raise HTTPException(404, "Mata kuliah tidak ditemukan")
    if mk.kelas_id != kelas_id:
        raise HTTPException(400, "Mata kuliah bukan milik kelas ini")
    tgl = tanggal or date.today()
    if tgl > date.today():
        raise HTTPException(400, "Tanggal QR tidak boleh melebihi hari ini")
    exp = datetime.now(timezone.utc) + timedelta(minutes=settings.qr_expire_minutes)
    db.query(QrSession).filter(QrSession.kelas_id == kelas_id, QrSession.mata_kuliah_id == mata_kuliah_id,
                               QrSession.revoked.is_(False)).update({QrSession.revoked: True}, synchronize_session=False)
    sesi = QrSession(kelas_id=kelas_id, mata_kuliah_id=mata_kuliah_id, tanggal=tgl, expires_at=exp, created_by=dibuat_oleh)
    db.add(sesi)
    db.commit()
    db.refresh(sesi)
    token = buat_token({"tipe": "presensi_qr", "jti": sesi.jti, "kelas_id": kelas_id,
                        "mata_kuliah_id": mata_kuliah_id, "tanggal": str(tgl),
                        "dibuat_oleh": str(dibuat_oleh), "exp": exp})
    return {"token": token, "berlaku_sampai": exp.isoformat(), "kelas_id": kelas_id,
            "mata_kuliah_id": mata_kuliah_id, "tanggal": str(tgl),
            "petunjuk": "Tampilkan QR code dari endpoint GET /api/v1/qr/image?token=<token>"}


def _sadar(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _sesi_aktif(db: Session, token: str) -> tuple[QrSession, dict]:
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(400, "Token tidak valid atau sudah kadaluarsa")
    if payload.get("tipe") != "presensi_qr":
        raise HTTPException(400, "Token bukan untuk presensi QR")
    sesi = db.query(QrSession).filter(QrSession.jti == payload.get("jti")).first()
    if not sesi or sesi.revoked or _sadar(sesi.expires_at) < datetime.now(timezone.utc):
        raise HTTPException(401, "QR sudah dimatikan atau kadaluarsa")
    return sesi, payload


def matikan_sesi(db: Session, token: str, current_user: dict) -> None:
    from jose import jwt
    from app.core.config import settings
    try:
        payload = decode_token(token)
    except Exception:
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm],
                                 options={"verify_exp": False})
            if payload.get("tipe") != "presensi_qr":
                raise ValueError("bukan sesi QR")
        except Exception:
            raise HTTPException(400, "Token tidak valid atau sudah kadaluarsa")
    sesi = db.query(QrSession).filter(QrSession.jti == payload.get("jti")).first()
    if not sesi:
        raise HTTPException(404, "Sesi QR tidak ditemukan")
    if current_user.get("role") == "ketua_kelas" and sesi.kelas_id != current_user.get("kelas_id"):
        raise HTTPException(403, "Anda hanya bisa mematikan QR kelas Anda sendiri")
    sesi.revoked = True
    db.commit()


def gambar_qr(db: Session, token: str) -> BytesIO:
    sesi, payload = _sesi_aktif(db, token)
    qr_data = json.dumps({"token": token, "kelas_id": payload["kelas_id"], "tanggal": payload["tanggal"]})
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=4)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def scan_qr(db: Session, token: str, nim: str | None, current_user: dict) -> dict:
    sesi, payload = _sesi_aktif(db, token)
    try:
        tanggal = date.fromisoformat(payload["tanggal"])
    except ValueError:
        raise HTTPException(400, "Tanggal token QR tidak valid")
    mhs = db.query(Mahasiswa).filter(Mahasiswa.user_id == int(current_user["sub"])).first()
    if not mhs:
        raise HTTPException(403, "Akun belum terhubung ke data mahasiswa")
    if nim and nim.strip() != mhs.nim:
        raise HTTPException(403, "NIM tidak sesuai dengan akun login Anda")
    if mhs.kelas_id != sesi.kelas_id:
        raise HTTPException(403, "Mahasiswa tidak terdaftar di kelas ini")
    existing = db.query(Absensi).filter(
        and_(Absensi.nim == mhs.nim, Absensi.tanggal == tanggal,
             Absensi.mata_kuliah_id == sesi.mata_kuliah_id)).first()
    if existing:
        return {"pesan": "Absensi sudah tercatat sebelumnya", "nama": mhs.nama_lengkap,
                "status": existing.status, "tanggal": str(tanggal), "sudah_tercatat": True}
    absen = Absensi(nim=mhs.nim, tanggal=tanggal, status="hadir", metode="qr", mata_kuliah_id=sesi.mata_kuliah_id)
    db.add(absen)
    db.commit()
    return {"pesan": "Absensi berhasil dicatat", "nama": mhs.nama_lengkap, "status": "hadir",
            "tanggal": str(tanggal), "metode": "qr", "sudah_tercatat": False}
