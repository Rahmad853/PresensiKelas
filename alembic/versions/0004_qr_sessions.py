"""buat tabel qr_sessions yang hilang (DB lama dibuat sebelum migrasi QR)

Revision ID: 0004
Revises: 0003_kelas_nama_angkatan
Create Date: 2026-09-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0004_qr_sessions"
down_revision: Union[str, None] = "0003_kelas_nama_angkatan"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if "qr_sessions" in sa.inspect(bind).get_table_names():
        return
    op.create_table(
        "qr_sessions",
        sa.Column("jti", sa.String(length=36), nullable=False),
        sa.Column("kelas_id", sa.Integer(), nullable=False),
        sa.Column("mata_kuliah_id", sa.Integer(), nullable=False),
        sa.Column("tanggal", sa.Date(), nullable=False),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name="fk_qr_sessions_created_by_users", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["kelas_id"], ["kelas.id"], name="fk_qr_sessions_kelas_id_kelas", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["mata_kuliah_id"], ["mata_kuliah.id"], name="fk_qr_sessions_mata_kuliah_id_mata_kuliah", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("jti", name="pk_qr_sessions"),
    )
    op.create_index("ix_qr_sessions_kelas_id", "qr_sessions", ["kelas_id"], unique=False)
    op.create_index("ix_qr_sessions_mata_kuliah_id", "qr_sessions", ["mata_kuliah_id"], unique=False)


def downgrade() -> None:
    op.drop_table("qr_sessions")
