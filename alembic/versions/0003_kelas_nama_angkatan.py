"""kelas unik per (nama, angkatan): 1 angkatan bisa punya Kelas A-E

Revision ID: 0003
Revises: 0002_mhs_kelas_nullable
Create Date: 2026-09-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003_kelas_nama_angkatan"
down_revision: Union[str, None] = "0002_mhs_kelas_nullable"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("kelas", recreate="always") as batch:
            try:
                batch.drop_index("ix_kelas_nama_kelas")
            except Exception:
                pass
            try:
                batch.drop_constraint("uq_kelas_nama_kelas", type_="unique")
            except Exception:
                pass
            batch.create_unique_constraint("uq_kelas_nama_angkatan", ["nama_kelas", "angkatan"])
            batch.create_index("ix_kelas_nama_kelas", ["nama_kelas"], unique=False)
    else:
        try:
            op.drop_index("ix_kelas_nama_kelas", table_name="kelas")
        except Exception:
            pass
        try:
            op.drop_constraint("uq_kelas_nama_kelas", "kelas", type_="unique")
        except Exception:
            pass
        op.create_unique_constraint("uq_kelas_nama_angkatan", "kelas", ["nama_kelas", "angkatan"])
        op.create_index("ix_kelas_nama_kelas", "kelas", ["nama_kelas"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("kelas", recreate="always") as batch:
            try:
                batch.drop_constraint("uq_kelas_nama_angkatan", type_="unique")
            except Exception:
                pass
            try:
                batch.drop_index("ix_kelas_nama_kelas")
            except Exception:
                pass
            batch.create_unique_constraint("uq_kelas_nama_kelas", ["nama_kelas"])
            batch.create_index("ix_kelas_nama_kelas", ["nama_kelas"], unique=True)
    else:
        op.drop_constraint("uq_kelas_nama_angkatan", "kelas", type_="unique")
        op.drop_index("ix_kelas_nama_kelas", table_name="kelas")
        op.create_unique_constraint("uq_kelas_nama_kelas", "kelas", ["nama_kelas"])
        op.create_index("ix_kelas_nama_kelas", "kelas", ["nama_kelas"], unique=True)
