from fastapi import APIRouter

from app.api.v1 import absensi as m_absensi
from app.api.v1 import admin as m_admin
from app.api.v1 import auth as m_auth
from app.api.v1 import laporan as m_laporan
from app.api.v1 import mata_kuliah as m_mata_kuliah
from app.api.v1 import qr as m_qr
from app.api.v1 import siswa as m_siswa
from app.api.v1 import users as m_users

v1 = APIRouter(prefix="/api/v1")
v1.include_router(m_auth.router)
v1.include_router(m_users.router)
v1.include_router(m_admin.router)
v1.include_router(m_siswa.router)
v1.include_router(m_mata_kuliah.router)
v1.include_router(m_absensi.router)
v1.include_router(m_laporan.router)
v1.include_router(m_qr.router)

