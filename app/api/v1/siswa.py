from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import List

from app.core.deps import get_db
from app.core.security import get_current_user, require_admin, require_admin_or_ketua
from app.models import Kelas, MataKuliah, Mahasiswa, User
from app.schemas.kelas import KelasCreate, KelasDetail, KelasResponse, KelasUpdate
from app.schemas.mahasiswa import MahasiswaCreate, MahasiswaDetail, MahasiswaResponse, MahasiswaUpdate

router = APIRouter(tags=["Manajemen Kelas & Mahasiswa"])

# ─── KELAS ───────────────────────────────────────────────────────────────────

@router.get("/kelas", response_model=List[KelasResponse])
def list_kelas(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    role = current_user.get("role")
    if role == "mahasiswa":
        raise HTTPException(403, "Akses ditolak")
    if role == "ketua_kelas":
        kelas_id = current_user.get("kelas_id")
        return db.query(Kelas).filter(Kelas.id == kelas_id).all() if kelas_id else []
    return db.query(Kelas).order_by(Kelas.angkatan, Kelas.nama_kelas).all()

@router.post("/kelas", response_model=KelasResponse, status_code=201)
def buat_kelas(data: KelasCreate, db: Session = Depends(get_db), _=Depends(require_admin)):
    if db.query(Kelas).filter(
        Kelas.nama_kelas == data.nama_kelas, Kelas.angkatan == data.angkatan
    ).first():
        raise HTTPException(400, f"{data.nama_kelas} angkatan {data.angkatan} sudah ada")
    kelas = Kelas(**data.model_dump())
    db.add(kelas)
    db.commit()
    db.refresh(kelas)
    return kelas

@router.get("/kelas/{kelas_id}", response_model=KelasDetail)
def detail_kelas(kelas_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user.get("role") == "mahasiswa":
        raise HTTPException(403, "Akses ditolak")
    if current_user.get("role") == "ketua_kelas" and kelas_id != current_user.get("kelas_id"):
        raise HTTPException(403, "Anda hanya bisa melihat kelas Anda sendiri")
    kelas = db.query(Kelas).filter(Kelas.id == kelas_id).first()
    if not kelas:
        raise HTTPException(404, "Kelas tidak ditemukan")
    ketua = db.query(User).filter(User.role == "ketua_kelas", User.kelas_id == kelas.id).first()
    total_mhs = db.query(Mahasiswa).filter(Mahasiswa.kelas_id == kelas.id).count() or 0
    return KelasDetail(
        id=kelas.id, nama_kelas=kelas.nama_kelas, nama_ketua_kelas=kelas.nama_ketua_kelas,
        tahun_ajaran=kelas.tahun_ajaran, angkatan=kelas.angkatan,
        ketua_id=ketua.id if ketua else None, ketua_username=ketua.username if ketua else None,
        total_mahasiswa=total_mhs, total_anggota=total_mhs + (1 if ketua else 0),
    )

@router.put("/kelas/{kelas_id}", response_model=KelasResponse)
def update_kelas(kelas_id: int, data: KelasUpdate, db: Session = Depends(get_db), _=Depends(require_admin)):
    kelas = db.query(Kelas).filter(Kelas.id == kelas_id).first()
    if not kelas:
        raise HTTPException(404, "Kelas tidak ditemukan")
    patch = data.model_dump(exclude_none=True)
    nama_baru = patch.get("nama_kelas", kelas.nama_kelas)
    if isinstance(nama_baru, str):
        nama_baru = nama_baru.strip()
        if not nama_baru:
            raise HTTPException(400, "Nama kelas tidak boleh kosong")
    angkatan_baru = patch.get("angkatan", kelas.angkatan)
    dupe = db.query(Kelas).filter(
        Kelas.nama_kelas == nama_baru, Kelas.angkatan == angkatan_baru, Kelas.id != kelas_id
    ).first()
    if dupe:
        raise HTTPException(400, f"{nama_baru} angkatan {angkatan_baru} sudah ada")
    if "nama_kelas" in patch and patch["nama_kelas"] is not None:
        kelas.nama_kelas = nama_baru
    if "angkatan" in patch:
        kelas.angkatan = angkatan_baru
    if "tahun_ajaran" in patch and patch["tahun_ajaran"] is not None:
        kelas.tahun_ajaran = patch["tahun_ajaran"]
    db.commit()
    db.refresh(kelas)
    return kelas

@router.delete("/kelas/{kelas_id}", status_code=204)
def hapus_kelas(kelas_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    kelas = db.query(Kelas).filter(Kelas.id == kelas_id).first()
    if not kelas:
        raise HTTPException(404, "Kelas tidak ditemukan")
    # Set kelas_id to null for members before deleting class
    db.query(Mahasiswa).filter(Mahasiswa.kelas_id == kelas_id).update({"kelas_id": None})
    db.query(User).filter(User.kelas_id == kelas_id).update({"kelas_id": None})
    db.delete(kelas)
    db.commit()

# ─── MANAJEMEN ANGGOTA KELAS ──────────────────────────────────────────────────

@router.post("/kelas/{kelas_id}/anggota", status_code=200)
def tambah_anggota_ke_kelas(kelas_id: int, nims: List[str], db: Session = Depends(get_db), _=Depends(require_admin)):
    """Menambahkan mahasiswa (anggota) ke dalam kelas."""
    kelas = db.query(Kelas).filter(Kelas.id == kelas_id).first()
    if not kelas:
        raise HTTPException(404, "Kelas tidak ditemukan")
    
    # Hitung kapasitas (max 30)
    current_count = db.query(Mahasiswa).filter(Mahasiswa.kelas_id == kelas_id).count()
    if current_count + len(nims) > 30:
        raise HTTPException(400, f"Kapasitas kelas penuh (Max 30). Sisa kuota: {30 - current_count}")

    updated = 0
    for nim in nims:
        mhs = db.query(Mahasiswa).filter(Mahasiswa.nim == nim).first()
        if mhs:
            mhs.kelas_id = kelas_id
            if mhs.user_id:
                db.query(User).filter(User.id == mhs.user_id).update({"kelas_id": kelas_id})
            updated += 1
    db.commit()
    return {"message": f"Berhasil menambahkan {updated} mahasiswa ke {kelas.nama_kelas}"}

@router.delete("/kelas/{kelas_id}/anggota", status_code=200)
def keluarkan_anggota_dari_kelas(kelas_id: int, nims: List[str], db: Session = Depends(get_db), _=Depends(require_admin)):
    """Mengeluarkan mahasiswa dari kelas (set kelas_id ke NULL)."""
    updated = 0
    for nim in nims:
        mhs = db.query(Mahasiswa).filter(Mahasiswa.nim == nim, Mahasiswa.kelas_id == kelas_id).first()
        if mhs:
            mhs.kelas_id = None
            if mhs.user_id:
                db.query(User).filter(User.id == mhs.user_id).update({"kelas_id": None})
            updated += 1
    db.commit()
    return {"message": f"Berhasil mengeluarkan {updated} mahasiswa dari kelas"}

# ─── MAHASISWA (ANGGOTA) ─────────────────────────────────────────────────────

@router.get("/mahasiswa", response_model=List[MahasiswaDetail])
def list_mahasiswa(
    kelas_id: int = Query(None), 
    tanpa_kelas: bool = Query(False),
    db: Session = Depends(get_db), 
    current_user: dict = Depends(require_admin_or_ketua)
):
    """List mahasiswa dengan filter kelas atau yang belum punya kelas."""
    query = db.query(Mahasiswa).options(joinedload(Mahasiswa.kelas))
    
    if current_user["role"] == "ketua_kelas":
        k_id = current_user.get("kelas_id")
        if not k_id: return []
        query = query.filter(Mahasiswa.kelas_id == k_id)
    else:
        if tanpa_kelas:
            query = query.filter(Mahasiswa.kelas_id == None)
        elif kelas_id:
            query = query.filter(Mahasiswa.kelas_id == kelas_id)
            
    return query.order_by(Mahasiswa.nama_lengkap).all()

@router.post("/mahasiswa", response_model=MahasiswaResponse, status_code=201)
def tambah_mahasiswa(data: MahasiswaCreate, db: Session = Depends(get_db), _=Depends(require_admin)):
    if db.query(Mahasiswa).filter(Mahasiswa.nim == data.nim).first():
        raise HTTPException(400, f"NIM {data.nim} sudah terdaftar")
    
    mhs = Mahasiswa(**data.model_dump())
    db.add(mhs)
    db.commit()
    db.refresh(mhs)
    return mhs

@router.put("/mahasiswa/{nim}", response_model=MahasiswaResponse)
def update_mahasiswa(nim: str, data: MahasiswaUpdate, db: Session = Depends(get_db), _=Depends(require_admin)):
    mhs = db.query(Mahasiswa).filter(Mahasiswa.nim == nim).first()
    if not mhs:
        raise HTTPException(404, "Mahasiswa tidak ditemukan")
    
    patch = data.model_dump(exclude_none=True)
    for field, val in patch.items():
        setattr(mhs, field, val)
        
    # Sinkronisasi kelas ke user jika terhubung
    if "kelas_id" in patch and mhs.user_id:
        db.query(User).filter(User.id == mhs.user_id).update({"kelas_id": patch["kelas_id"]})
        
    db.commit()
    db.refresh(mhs)
    return mhs

@router.delete("/mahasiswa/{nim}", status_code=204)
def hapus_mahasiswa(nim: str, db: Session = Depends(get_db), _=Depends(require_admin)):
    mhs = db.query(Mahasiswa).filter(Mahasiswa.nim == nim).first()
    if not mhs:
        raise HTTPException(404, "Mahasiswa tidak ditemukan")
    
    # Hapus akun user terkait jika ada
    if mhs.user_id:
        db.query(User).filter(User.id == mhs.user_id).delete()
        
    db.delete(mhs)
    db.commit()
