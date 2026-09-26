from pydantic import BaseModel
from typing import Optional


class MataKuliahCreate(BaseModel):
    kode: str
    nama: str
    semester: Optional[int] = None
    kelas_id: int


class MataKuliahUpdate(BaseModel):
    kode: Optional[str] = None
    nama: Optional[str] = None
    semester: Optional[int] = None
    kelas_id: Optional[int] = None


class MataKuliahResponse(MataKuliahCreate):
    id: int

    model_config = {"from_attributes": True}
