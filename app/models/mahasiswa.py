from sqlalchemy import Column, Integer, String, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.db.base import Base


class Mahasiswa(Base):
    __tablename__ = "mahasiswa"

    nim = Column(String(20), primary_key=True, index=True)
    nama_lengkap = Column(String(100), nullable=False)
    kelas_id = Column(Integer, ForeignKey("kelas.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), unique=True, nullable=True)
    foto = Column(String(255), nullable=True)
    angkatan = Column(Integer, nullable=True)

    __table_args__ = (Index("ix_mahasiswa_kelas_nama", "kelas_id", "nama_lengkap"),)

    kelas = relationship("Kelas", back_populates="mahasiswa")
    user = relationship("User", back_populates="mahasiswa")
    absensi = relationship("Absensi", back_populates="mahasiswa", foreign_keys="Absensi.nim")
