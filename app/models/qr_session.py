import uuid
from sqlalchemy import Column, String, Integer, Date, TIMESTAMP, Boolean, ForeignKey
from sqlalchemy.sql import func

from app.db.base import Base


class QrSession(Base):
    __tablename__ = "qr_sessions"

    jti = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    kelas_id = Column(Integer, ForeignKey("kelas.id", ondelete="CASCADE"), nullable=False, index=True)
    mata_kuliah_id = Column(Integer, ForeignKey("mata_kuliah.id", ondelete="CASCADE"), nullable=False, index=True)
    tanggal = Column(Date, nullable=False)
    expires_at = Column(TIMESTAMP(timezone=True), nullable=False)
    revoked = Column(Boolean, nullable=False, default=False)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
