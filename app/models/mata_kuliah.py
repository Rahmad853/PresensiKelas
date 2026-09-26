from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import Base


class MataKuliah(Base):
    __tablename__ = "mata_kuliah"

    id = Column(Integer, primary_key=True, index=True)
    kode = Column(String(20), unique=True, nullable=False, index=True)
    nama = Column(String(120), nullable=False)
    semester = Column(Integer, nullable=True)
    kelas_id = Column(Integer, ForeignKey("kelas.id", ondelete="RESTRICT"), nullable=False, index=True)

    kelas = relationship("Kelas", back_populates="mata_kuliah")
    absensi = relationship("Absensi", back_populates="mata_kuliah")
