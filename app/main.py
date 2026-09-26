from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1 import absensi, admin, auth, laporan, mata_kuliah, qr, router as v1, siswa, users
from app.core.config import settings

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


def create_app() -> FastAPI:
    app = FastAPI(
        title="Presensi Mahasiswa",
        description="API presensi mahasiswa per mata kuliah.",
        version="2.0.0",
        docs_url=None,
        redoc_url=None,
    )
    origins = [o.strip() for o in settings.frontend_origins.split(",") if o.strip()]
    app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True,
                       allow_methods=["*"], allow_headers=["*"])
    app.include_router(v1.v1)
    # ponytail: dual-mount legacy tanpa prefix; hapus setelah frontend pindah /api/v1
    for r in (auth.router, users.router, admin.router, siswa.router, mata_kuliah.router,
              absensi.router, laporan.router, qr.router):
        app.include_router(r)
    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

        @app.get("/", include_in_schema=False)
        def root():
            return FileResponse(STATIC_DIR / "index.html")

    return app


app = create_app()
