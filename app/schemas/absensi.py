from pydantic import BaseModel
from typing import Optional, Literal
from datetime import date, datetime


class AbsensiCreate(BaseModel):
    nim: str
    tanggal: date
    status: Literal["hadir", "sakit", "izin", "alfa"]
    keterangan: Optional[str] = None
    metode: Literal["manual", "qr", "gps"] = "manual"
    mata_kuliah_id: int


class AbsensiBulk(BaseModel):
    data: list[AbsensiCreate]


class AbsensiUpdate(BaseModel):
    status: Literal["hadir", "sakit", "izin", "alfa"]
    keterangan: Optional[str] = None


class AbsensiResponse(BaseModel):
    id: int
    nim: str
    tanggal: date
    status: str
    keterangan: Optional[str]
    metode: str
    created_at: datetime
    mata_kuliah_id: int

    model_config = {"from_attributes": True}


class RekapMahasiswa(BaseModel):
    nim: str
    nama_lengkap: str
    hadir: int
    sakit: int
    izin: int
    alfa: int
    total_hari: int
    persentase_hadir: float


class RekapResponse(BaseModel):
    kelas: str
    bulan: int
    tahun: int
    data: list[RekapMahasiswa]


class HarianItem(BaseModel):
    nim: str
    nama_lengkap: str
    status: Optional[str] = None
    keterangan: Optional[str] = None
    metode: Optional[str] = None


class HarianResponse(BaseModel):
    kelas: str
    tanggal: date
    mata_kuliah: Optional[str] = None
    data: list[HarianItem]
