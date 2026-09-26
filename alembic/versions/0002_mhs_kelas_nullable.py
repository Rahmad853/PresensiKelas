"""mahasiswa.kelas_id nullable agar anggota bisa tanpa kelas

Revision ID: 0002
Revises: 0001_baseline_standar
Create Date: 2026-09-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002_mhs_kelas_nullable"
down_revision: Union[str, None] = "0001_baseline_standar"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("mahasiswa") as batch:
            batch.alter_column("kelas_id", existing_type=sa.Integer(), nullable=True)
    else:
        op.alter_column("mahasiswa", "kelas_id", existing_type=sa.Integer(), nullable=True)
        try:
            op.drop_constraint("fk_mahasiswa_kelas_id_kelas", "mahasiswa", type_="foreignkey")
        except Exception:
            pass
        op.create_foreign_key("fk_mahasiswa_kelas_id_kelas", "mahasiswa", "kelas",
                              ["kelas_id"], ["id"], ondelete="SET NULL")


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("mahasiswa") as batch:
            batch.alter_column("kelas_id", existing_type=sa.Integer(), nullable=False)
    else:
        op.alter_column("mahasiswa", "kelas_id", existing_type=sa.Integer(), nullable=False)
