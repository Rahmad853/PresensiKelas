from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.security import get_current_user, require_admin, require_admin_or_ketua
from app.schemas.absensi import AbsensiBulk, AbsensiCreate, AbsensiResponse, AbsensiUpdate
from app.services import absensi as svc

router = APIRouter(prefix="/absensi", tags=["Absensi"])


@router.get("/", response_model=list[AbsensiResponse])
def list_absensi(kelas_id: int | None = None, tanggal: date | None = None, nim: str | None = None,
                 db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    return svc.query_absensi(db, current_user, kelas_id, tanggal, nim)


@router.post("/", response_model=AbsensiResponse, status_code=201)
def input_absensi(data: AbsensiCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    return svc.catat_absensi(db, data, current_user)


@router.post("/bulk", status_code=201)
def input_bulk(data: AbsensiBulk, db: Session = Depends(get_db), current_user: dict = Depends(require_admin_or_ketua)):
    return svc.catat_bulk(db, data, current_user)


@router.put("/{absen_id}", response_model=AbsensiResponse)
def update_absensi(absen_id: int, data: AbsensiUpdate, db: Session = Depends(get_db), current_user: dict = Depends(require_admin_or_ketua)):
    return svc.ubah_absensi(db, absen_id, data.status, data.keterangan, current_user)


@router.delete("/{absen_id}", status_code=204)
def hapus_absensi(absen_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    svc.hapus_absensi(db, absen_id)
