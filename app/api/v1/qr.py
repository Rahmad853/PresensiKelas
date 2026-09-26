from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.security import require_ketua_kelas, require_mahasiswa
from app.models import Absensi, Mahasiswa
from app.services import qr as svc

router = APIRouter(prefix="/qr", tags=["QR Code Presensi"])


@router.post("/generate")
def generate_qr_token(kelas_id: int, mata_kuliah_id: int, tanggal: date | None = None,
                      db: Session = Depends(get_db), current_user: dict = Depends(require_ketua_kelas)):
    if current_user.get("role") == "ketua_kelas" and kelas_id != current_user.get("kelas_id"):
        raise HTTPException(403, "Anda hanya bisa membuat QR untuk kelas Anda sendiri")
    return svc.buat_sesi_qr(db, kelas_id, mata_kuliah_id, tanggal, int(current_user["sub"]))


@router.post("/matikan")
def matikan_qr(token: str, db: Session = Depends(get_db), current_user: dict = Depends(require_ketua_kelas)):
    svc.matikan_sesi(db, token, current_user)
    return {"pesan": "QR berhasil dimatikan"}


@router.get("/image")
def gambar_qr(token: str, db: Session = Depends(get_db)):
    return StreamingResponse(svc.gambar_qr(db, token), media_type="image/png")


@router.get("/scan-page", include_in_schema=False)
def halaman_scan():
    return FileResponse(Path(__file__).parent.parent.parent.parent / "static" / "scan.html")


@router.post("/scan")
def scan_qr(token: str, nim: str | None = None, db: Session = Depends(get_db),
             current_user: dict = Depends(require_mahasiswa)):
    return svc.scan_qr(db, token, nim, current_user)


@router.get("/status")
def status_qr(token: str, kelas_id: int, mata_kuliah_id: int, tanggal: date | None = None,
              db: Session = Depends(get_db), current_user: dict = Depends(require_ketua_kelas)):
    if current_user.get("role") == "ketua_kelas" and kelas_id != current_user.get("kelas_id"):
        raise HTTPException(403, "Anda hanya bisa melihat status kelas Anda sendiri")
    tgl = tanggal or date.today()
    mhs_kelas = db.query(Mahasiswa).filter(Mahasiswa.kelas_id == kelas_id).all()
    nim_set = {m.nim for m in mhs_kelas}
    sudah = {a.nim for a in db.query(Absensi).filter(
        Absensi.nim.in_(nim_set or ["-"]), Absensi.tanggal == tgl,
        Absensi.metode == "qr", Absensi.mata_kuliah_id == mata_kuliah_id).all()} if nim_set else set()
    return {"tanggal": str(tgl), "total_mahasiswa": len(mhs_kelas), "sudah_scan": len(sudah),
            "belum_scan": len(nim_set) - len(sudah),
            "detail": [{"nim": m.nim, "nama": m.nama_lengkap, "sudah_scan": m.nim in sudah} for m in mhs_kelas]}
