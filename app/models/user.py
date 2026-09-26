from sqlalchemy import Column, Integer, String, Enum, ForeignKey, TIMESTAMP, func
from sqlalchemy.orm import relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    nim = Column(String(20), nullable=True, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum("admin", "ketua_kelas", "mahasiswa", name="user_role"), nullable=False, default="mahasiswa")
    kelas_id = Column(Integer, ForeignKey("kelas.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    mahasiswa = relationship("Mahasiswa", back_populates="user", uselist=False)
    absensi_dicatat = relationship("Absensi", back_populates="pencatat", foreign_keys="Absensi.dicatat_oleh")
    kelas = relationship("Kelas", foreign_keys=[kelas_id])
