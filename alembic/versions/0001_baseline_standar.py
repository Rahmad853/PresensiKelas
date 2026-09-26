"""baseline skema standar

Revision ID: 0001
Revises:
Create Date: 2026-09-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001_baseline_standar"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

user_role = sa.Enum("admin", "ketua_kelas", "mahasiswa", name="user_role")
absensi_status = sa.Enum("hadir", "sakit", "izin", "alfa", name="absensi_status")
absensi_metode = sa.Enum("manual", "qr", "gps", name="absensi_metode")


def upgrade() -> None:
    bind = op.get_bind()
    for enum in (user_role, absensi_status, absensi_metode):
        if bind.dialect.name == "postgresql":
            enum.create(bind, checkfirst=True)
    op.create_table(
        "kelas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nama_kelas", sa.String(length=20), nullable=False),
        sa.Column("nama_ketua_kelas", sa.String(length=100), nullable=True),
        sa.Column("tahun_ajaran", sa.Integer(), nullable=False),
        sa.Column("angkatan", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_kelas"),
        sa.UniqueConstraint("nama_kelas", name="uq_kelas_nama_kelas"),
    )
    op.create_index("ix_kelas_nama_kelas", "kelas", ["nama_kelas"], unique=True)
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("nim", sa.String(length=20), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", user_role, nullable=False, server_default="mahasiswa"),
        sa.Column("kelas_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["kelas_id"], ["kelas.id"], name="fk_users_kelas_id_kelas", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("username", name="uq_users_username"),
        sa.UniqueConstraint("nim", name="uq_users_nim"),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_index("ix_users_nim", "users", ["nim"], unique=False)
    op.create_table(
        "mahasiswa",
        sa.Column("nim", sa.String(length=20), nullable=False),
        sa.Column("nama_lengkap", sa.String(length=100), nullable=False),
        sa.Column("kelas_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("foto", sa.String(length=255), nullable=True),
        sa.Column("angkatan", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["kelas_id"], ["kelas.id"], name="fk_mahasiswa_kelas_id_kelas", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_mahasiswa_user_id_users", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("nim", name="pk_mahasiswa"),
        sa.UniqueConstraint("user_id", name="uq_mahasiswa_user_id"),
    )
    op.create_index("ix_mahasiswa_kelas_id", "mahasiswa", ["kelas_id"], unique=False)
    op.create_index("ix_mahasiswa_kelas_nama", "mahasiswa", ["kelas_id", "nama_lengkap"], unique=False)
    op.create_table(
        "mata_kuliah",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("kode", sa.String(length=20), nullable=False),
        sa.Column("nama", sa.String(length=120), nullable=False),
        sa.Column("semester", sa.Integer(), nullable=True),
        sa.Column("kelas_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["kelas_id"], ["kelas.id"], name="fk_mata_kuliah_kelas_id_kelas", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_mata_kuliah"),
        sa.UniqueConstraint("kode", name="uq_mata_kuliah_kode"),
    )
    op.create_index("ix_mata_kuliah_kode", "mata_kuliah", ["kode"], unique=True)
    op.create_index("ix_mata_kuliah_kelas_id", "mata_kuliah", ["kelas_id"], unique=False)
    op.create_table(
        "absensi",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nim", sa.String(length=20), nullable=False),
        sa.Column("tanggal", sa.Date(), nullable=False),
        sa.Column("status", absensi_status, nullable=False),
        sa.Column("keterangan", sa.String(length=255), nullable=True),
        sa.Column("metode", absensi_metode, nullable=False, server_default="manual"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("dicatat_oleh", sa.Integer(), nullable=True),
        sa.Column("mata_kuliah_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["dicatat_oleh"], ["users.id"], name="fk_absensi_dicatat_oleh_users", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["mata_kuliah_id"], ["mata_kuliah.id"], name="fk_absensi_mata_kuliah_id_mata_kuliah", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["nim"], ["mahasiswa.nim"], name="fk_absensi_nim_mahasiswa", onupdate="CASCADE", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_absensi"),
        sa.UniqueConstraint("nim", "tanggal", "mata_kuliah_id", name="uq_absen_per_matkul_hari"),
    )
    op.create_index("ix_absensi_nim", "absensi", ["nim"], unique=False)
    op.create_index("ix_absensi_tanggal", "absensi", ["tanggal"], unique=False)
    op.create_index("ix_absensi_mata_kuliah_id", "absensi", ["mata_kuliah_id"], unique=False)
    op.create_index("ix_absensi_matkul_tanggal", "absensi", ["mata_kuliah_id", "tanggal"], unique=False)
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
    op.drop_table("absensi")
    op.drop_table("mata_kuliah")
    op.drop_table("mahasiswa")
    op.drop_table("users")
    op.drop_table("kelas")
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        for enum in (absensi_metode, absensi_status, user_role):
            enum.drop(bind, checkfirst=True)
