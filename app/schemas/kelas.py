from pydantic import BaseModel
from typing import Optional


class KelasCreate(BaseModel):
    nama_kelas: str
    tahun_ajaran: int
    angkatan: Optional[int] = None

    model_config = {"extra": "forbid"}


class KelasUpdate(BaseModel):
    nama_kelas: Optional[str] = None
    tahun_ajaran: Optional[int] = None
    angkatan: Optional[int] = None


class KelasResponse(BaseModel):
    id: int
    nama_kelas: str
    nama_ketua_kelas: Optional[str]
    tahun_ajaran: int
    angkatan: Optional[int] = None

    model_config = {"from_attributes": True}


class KelasDetail(KelasResponse):
    ketua_id: Optional[int] = None
    ketua_username: Optional[str] = None
    total_mahasiswa: int = 0
    total_anggota: int = 0
