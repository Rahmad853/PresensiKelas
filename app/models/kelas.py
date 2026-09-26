from sqlalchemy import Column, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.base import Base


class Kelas(Base):
    __tablename__ = "kelas"
    __table_args__ = (
        UniqueConstraint("nama_kelas", "angkatan", name="uq_kelas_nama_angkatan"),
    )

    id = Column(Integer, primary_key=True, index=True)
    nama_kelas = Column(String(20), nullable=False, index=True)
    nama_ketua_kelas = Column(String(100), nullable=True)
    tahun_ajaran = Column(Integer, nullable=False)
    angkatan = Column(Integer, nullable=True)

    mahasiswa = relationship("Mahasiswa", back_populates="kelas")
    mata_kuliah = relationship("MataKuliah", back_populates="kelas")
