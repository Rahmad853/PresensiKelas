from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime


class UserCreate(BaseModel):
    username: str
    password: str
    role: Literal["admin", "ketua_kelas", "mahasiswa"] = "mahasiswa"
    kelas_id: Optional[int] = None
    nim: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    username: str
    nim: Optional[str] = None
    role: str
    kelas_id: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    username: Optional[str] = None
    nim: Optional[str] = None
    password: Optional[str] = None
    role: Optional[Literal["admin", "ketua_kelas", "mahasiswa"]] = None
    kelas_id: Optional[int] = None


class KetuaKelasCreate(BaseModel):
    username: str
    password: str
    kelas_id: int


class KetuaKelasUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    kelas_id: Optional[int] = None


class KetuaKelasItem(BaseModel):
    kelas_id: int
    nama_kelas: str
    nama_ketua_kelas: Optional[str] = None
    tahun_ajaran: int
    angkatan: Optional[int] = None
    ketua_id: Optional[int] = None
    ketua_username: Optional[str] = None
    total_mahasiswa: int = 0
