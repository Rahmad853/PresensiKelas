from sqlalchemy import Column, Integer, String, Date, Enum, ForeignKey, TIMESTAMP, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Absensi(Base):
    __tablename__ = "absensi"
    __table_args__ = (
        UniqueConstraint("nim", "tanggal", "mata_kuliah_id", name="uq_absen_per_matkul_hari"),
        Index("ix_absensi_matkul_tanggal", "mata_kuliah_id", "tanggal"),
    )

    id = Column(Integer, primary_key=True, index=True)
    nim = Column(String(20), ForeignKey("mahasiswa.nim", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False, index=True)
    tanggal = Column(Date, nullable=False, index=True)
    status = Column(Enum("hadir", "sakit", "izin", "alfa", name="absensi_status"), nullable=False)
    keterangan = Column(String(255), nullable=True)
    metode = Column(Enum("manual", "qr", "gps", name="absensi_metode"), default="manual", nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    dicatat_oleh = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    mata_kuliah_id = Column(Integer, ForeignKey("mata_kuliah.id", ondelete="RESTRICT"), nullable=False, index=True)

    mahasiswa = relationship("Mahasiswa", back_populates="absensi", foreign_keys=[nim])
    pencatat = relationship("User", back_populates="absensi_dicatat", foreign_keys=[dicatat_oleh])
    mata_kuliah = relationship("MataKuliah", back_populates="absensi")
