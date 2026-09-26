from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.security import buat_token, hash_password, verify_password
from app.models import Kelas as _Kelas
from app.models import Mahasiswa as _Mhs
from app.models import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserCreate, UserResponse

router = APIRouter(prefix="/auth", tags=["Autentikasi"])


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Username atau password salah")
    token = buat_token({"sub": str(user.id), "username": user.username, "role": user.role, "kelas_id": user.kelas_id})
    return TokenResponse(access_token=token, role=user.role, username=user.username, kelas_id=user.kelas_id)


@router.post("/register", response_model=UserResponse, status_code=201)
def register(data: UserCreate, db: Session = Depends(get_db)):
    if data.role != "mahasiswa":
        raise HTTPException(403, "Registrasi publik hanya untuk akun mahasiswa")
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(400, "Username sudah digunakan")
    mhs = db.query(_Mhs).filter(_Mhs.nim == data.nim).first() if data.nim else None
    if data.nim and not mhs:
        raise HTTPException(404, "NIM tidak terdaftar")
    if mhs and mhs.user_id:
        raise HTTPException(400, "NIM sudah terhubung ke akun lain")
    kelas_id = mhs.kelas_id if mhs else data.kelas_id
    if kelas_id and not db.query(_Kelas).filter(_Kelas.id == kelas_id).first():
        raise HTTPException(404, "Kelas tidak ditemukan")
    user = User(username=data.username, password_hash=hash_password(data.password), role="mahasiswa", kelas_id=kelas_id)
    db.add(user)
    db.flush()
    if mhs:
        mhs.user_id = user.id
    db.commit()
    db.refresh(user)
    return user
