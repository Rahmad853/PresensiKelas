from pydantic import BaseModel, field_validator
from typing import Optional
from app.schemas.kelas import KelasResponse
from app.schemas.user import UserResponse


class MahasiswaCreate(BaseModel):
    nim: str
    nama_lengkap: str
    kelas_id: Optional[int] = None
    user_id: Optional[int] = None
    angkatan: Optional[int] = None

    @field_validator("nim")
    @classmethod
    def nim_tidak_kosong(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("NIM tidak boleh kosong")
        return v.strip()


class MahasiswaUpdate(BaseModel):
    nama_lengkap: Optional[str] = None
    kelas_id: Optional[int] = None
    user_id: Optional[int] = None
    angkatan: Optional[int] = None


class MahasiswaAdminUpdate(BaseModel):
    nim_baru: Optional[str] = None
    nama_lengkap: Optional[str] = None
    kelas_id: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    angkatan: Optional[int] = None


class MahasiswaResponse(BaseModel):
    nim: str
    nama_lengkap: str
    kelas_id: Optional[int] = None
    user_id: Optional[int]
    angkatan: Optional[int] = None

    model_config = {"from_attributes": True}


class MahasiswaDetail(MahasiswaResponse):
    kelas: Optional[KelasResponse] = None
    user: Optional[UserResponse] = None

    model_config = {"from_attributes": True}
