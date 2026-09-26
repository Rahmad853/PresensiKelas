from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.security import hash_password, require_admin
from app.models import Kelas, Mahasiswa, User
from app.schemas.user import UserCreate, UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["Manajemen User"])


@router.get("/", response_model=list[UserResponse])
def list_user(db: Session = Depends(get_db), _=Depends(require_admin)):
    return db.query(User).order_by(User.role, User.username).all()


@router.post("/", response_model=UserResponse, status_code=201)
def tambah_user(data: UserCreate, db: Session = Depends(get_db), _=Depends(require_admin)):
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(400, "Username sudah digunakan")
    if len(data.password.strip()) < 4:
        raise HTTPException(400, "Password minimal 4 karakter")
    if data.nim and db.query(User).filter(User.nim == data.nim.strip()).first():
        raise HTTPException(400, f"NIM '{data.nim.strip()}' sudah dipakai akun lain")
    if data.kelas_id and not db.query(Kelas).filter(Kelas.id == data.kelas_id).first():
        raise HTTPException(404, "Kelas tidak ditemukan")
    # ponytail: nim disalin ke User.nim agar sinkron dengan Mahasiswa; upgrade: constraint DB satu sumber
    user = User(username=data.username, password_hash=hash_password(data.password.strip()), role=data.role, kelas_id=data.kelas_id, nim=data.nim.strip() if data.nim else None)
    db.add(user)
    db.commit()
    db.refresh(user)
    if data.role == "mahasiswa" and data.nim:
        mhs = db.query(Mahasiswa).filter(Mahasiswa.nim == data.nim).first()
        if mhs:
            mhs.user_id = user.id
            if data.kelas_id:
                mhs.kelas_id = data.kelas_id
            db.commit()
    return user


@router.put("/{user_id}", response_model=UserResponse)
def edit_user(user_id: int, data: UserUpdate, db: Session = Depends(get_db), _=Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User tidak ditemukan")
    if data.username and data.username != user.username:
        if db.query(User).filter(User.username == data.username).first():
            raise HTTPException(400, "Username sudah digunakan")
        user.username = " ".join(data.username.split())
    if data.nim is not None:
        nim_baru = data.nim.strip()
        if nim_baru and db.query(User).filter(User.nim == nim_baru, User.id != user_id).first():
            raise HTTPException(400, f"NIM '{nim_baru}' sudah dipakai akun lain")
        user.nim = nim_baru or None
    if data.password:
        if len(data.password.strip()) < 4:
            raise HTTPException(400, "Password minimal 4 karakter")
        user.password_hash = hash_password(data.password.strip())
    if data.role and data.role != user.role:
        user.role = data.role
    if data.kelas_id is not None:
        if data.kelas_id and not db.query(Kelas).filter(Kelas.id == data.kelas_id).first():
            raise HTTPException(404, "Kelas tidak ditemukan")
        user.kelas_id = data.kelas_id or None
    db.flush()
    # Sinkron dua arah user <-> mahasiswa agar langsung berubah di semua tampilan
    if user.role == "mahasiswa" and user.nim:
        mhs = db.query(Mahasiswa).filter(Mahasiswa.nim == user.nim).first()
        if mhs:
            if mhs.user_id != user.id:
                mhs.user_id = user.id
            if mhs.kelas_id != user.kelas_id:
                mhs.kelas_id = user.kelas_id
    if user.role == "ketua_kelas" and user.kelas_id is not None:
        kelas = db.query(Kelas).filter(Kelas.id == user.kelas_id).first()
        if kelas and kelas.nama_ketua_kelas != user.username:
            kelas.nama_ketua_kelas = user.username
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=204)
def hapus_user(user_id: int, db: Session = Depends(get_db), current_user: dict = Depends(require_admin)):
    if int(current_user["sub"]) == user_id:
        raise HTTPException(400, "Tidak bisa menghapus akun Anda sendiri")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User tidak ditemukan")
    if user.role == "admin":
        raise HTTPException(400, "Akun admin tidak dapat dihapus")
    db.delete(user)
    db.commit()
