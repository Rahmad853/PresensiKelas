from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.core.deps import get_db
from app.core.security import get_current_user, require_admin
from app.models import Kelas, Mahasiswa, MataKuliah
from app.schemas.mata_kuliah import MataKuliahCreate, MataKuliahResponse, MataKuliahUpdate

router = APIRouter(prefix="/mata-kuliah", tags=["Mata Kuliah"])


@router.get("/", response_model=list[MataKuliahResponse])
def list_mata_kuliah(kelas_id: int | None = None, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    query = db.query(MataKuliah).options(joinedload(MataKuliah.kelas))
    role = current_user.get("role")
    if role == "ketua_kelas":
        kelas_id = current_user.get("kelas_id")
        if kelas_id:
            query = query.filter(MataKuliah.kelas_id == kelas_id)
    elif role == "mahasiswa":
        mhs = db.query(Mahasiswa).filter(Mahasiswa.user_id == int(current_user["sub"])).first()
        if mhs:
            query = query.filter(MataKuliah.kelas_id == mhs.kelas_id)
        elif kelas_id:
            query = query.filter(MataKuliah.kelas_id == kelas_id)
    elif kelas_id:
        query = query.filter(MataKuliah.kelas_id == kelas_id)
    return query.order_by(MataKuliah.semester, MataKuliah.nama).all()


@router.post("/", response_model=MataKuliahResponse, status_code=status.HTTP_201_CREATED)
def tambah_mata_kuliah(data: MataKuliahCreate, db: Session = Depends(get_db), _=Depends(require_admin)):
    if db.query(MataKuliah).filter(MataKuliah.kode == data.kode).first():
        raise HTTPException(400, "Kode mata kuliah sudah digunakan")
    if not db.query(Kelas).filter(Kelas.id == data.kelas_id).first():
        raise HTTPException(404, "Kelas tidak ditemukan")
    mk = MataKuliah(**data.model_dump())
    db.add(mk)
    db.commit()
    db.refresh(mk)
    return mk


@router.put("/{mata_kuliah_id}", response_model=MataKuliahResponse)
def update_mata_kuliah(mata_kuliah_id: int, data: MataKuliahUpdate, db: Session = Depends(get_db), _=Depends(require_admin)):
    mk = db.query(MataKuliah).filter(MataKuliah.id == mata_kuliah_id).first()
    if not mk:
        raise HTTPException(404, "Mata kuliah tidak ditemukan")
    patch = data.model_dump(exclude_none=True)
    if not patch:
        raise HTTPException(400, "Tidak ada data yang diubah")
    if "kode" in patch and patch["kode"] is not None:
        kode = patch["kode"].strip()
        if not kode:
            raise HTTPException(400, "Kode tidak boleh kosong")
        if db.query(MataKuliah).filter(MataKuliah.kode == kode, MataKuliah.id != mk.id).first():
            raise HTTPException(400, "Kode mata kuliah sudah digunakan")
        mk.kode = kode
    if "nama" in patch and patch["nama"] is not None:
        nama = patch["nama"].strip()
        if not nama:
            raise HTTPException(400, "Nama tidak boleh kosong")
        mk.nama = nama
    if "semester" in patch:
        mk.semester = patch["semester"]
    if "kelas_id" in patch and patch["kelas_id"] is not None:
        if not db.query(Kelas).filter(Kelas.id == patch["kelas_id"]).first():
            raise HTTPException(404, "Kelas tidak ditemukan")
        mk.kelas_id = patch["kelas_id"]
    db.commit()
    db.refresh(mk)
    return mk


@router.delete("/{mata_kuliah_id}", status_code=status.HTTP_204_NO_CONTENT)
def hapus_mata_kuliah(mata_kuliah_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    mk = db.query(MataKuliah).filter(MataKuliah.id == mata_kuliah_id).first()
    if not mk:
        raise HTTPException(404, "Mata kuliah tidak ditemukan")
    db.delete(mk)
    db.commit()
