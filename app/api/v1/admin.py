from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import extract, func
from sqlalchemy.orm import Session, joinedload

from app.core.deps import get_db
from app.core.security import hash_password, require_admin
from app.models import Absensi, Kelas, Mahasiswa, User
from app.schemas.mahasiswa import MahasiswaAdminUpdate, MahasiswaDetail
from app.schemas.user import KetuaKelasCreate, KetuaKelasItem, KetuaKelasUpdate, UserResponse
from app.services.absensi import baca_baris_import, sinkron_mahasiswa_csv

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])


@router.post("/import-mahasiswa")
def import_mahasiswa(file: UploadFile = File(...), dry_run: bool = Query(False),
                     db: Session = Depends(get_db), _=Depends(require_admin)):
    raw = file.file.read()
    if not raw:
        raise HTTPException(400, "File kosong")
    try:
        rows = baca_baris_import(file.filename or "", raw)
    except Exception:
        raise HTTPException(400, "File tidak bisa dibaca. Gunakan CSV atau XLSX.")
    if not rows:
        raise HTTPException(400, "File tidak berisi data")
    # ponytail: sinkron (buat + perbarui + petakan kolom Kelas), tanpa hapus/tanpa reset password
    return sinkron_mahasiswa_csv(db, rows, dry_run)


def _filter_periode(query, bulan: int | None, tahun: int | None):
    if bulan and tahun:
        query = query.filter(extract("month", Absensi.tanggal) == bulan, extract("year", Absensi.tanggal) == tahun)
    return query


@router.post("/init-kelas-abcde")
def init_kelas_abcde(db: Session = Depends(get_db), _=Depends(require_admin)):
    dibuat = []
    for nama, ketua in [("Kelas A", "Ketua A"), ("Kelas B", "Ketua B"), ("Kelas C", "Ketua C"),
                        ("Kelas D", "Ketua D"), ("Kelas E", "Ketua E")]:
        if not db.query(Kelas).filter(Kelas.nama_kelas == nama).first():
            db.add(Kelas(nama_kelas=nama, nama_ketua_kelas=ketua, tahun_ajaran=2026))
            dibuat.append(nama)
    db.commit()
    return {"message": "Inisialisasi kelas selesai", "kelas_dibuat": dibuat}


@router.get("/ketua-kelas", response_model=list[KetuaKelasItem])
def list_ketua_kelas(db: Session = Depends(get_db), _=Depends(require_admin)):
    hasil = []
    for k in db.query(Kelas).order_by(Kelas.angkatan, Kelas.nama_kelas).all():
        ketua = db.query(User).filter(User.role == "ketua_kelas", User.kelas_id == k.id).first()
        # Hitung anggota (mahasiswa) + ketua kelas (user dengan role ketua_kelas di kelas tersebut)
        total_mhs = db.query(func.count(Mahasiswa.nim)).filter(Mahasiswa.kelas_id == k.id).scalar() or 0
        total_anggota = total_mhs + (1 if ketua else 0)
        
        hasil.append(KetuaKelasItem(kelas_id=k.id, nama_kelas=k.nama_kelas, nama_ketua_kelas=k.nama_ketua_kelas,
                                    tahun_ajaran=k.tahun_ajaran, angkatan=k.angkatan,
                                    ketua_id=ketua.id if ketua else None,
                                    ketua_username=ketua.username if ketua else None, total_mahasiswa=total_anggota))
    return hasil


@router.post("/ketua-kelas", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def tambah_ketua_kelas(data: KetuaKelasCreate, db: Session = Depends(get_db), _=Depends(require_admin)):
    username = data.username.strip()
    if not username:
        raise HTTPException(400, "Username tidak boleh kosong")
    if len(data.password.strip()) < 4:
        raise HTTPException(400, "Password minimal 4 karakter")
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(400, f"Username '{username}' sudah digunakan")
    kelas = db.query(Kelas).filter(Kelas.id == data.kelas_id).first()
    if not kelas:
        raise HTTPException(404, "Kelas tidak ditemukan")
    ketua_lama = db.query(User).filter(User.role == "ketua_kelas", User.kelas_id == data.kelas_id).first()
    if ketua_lama:
        raise HTTPException(400, f"{kelas.nama_kelas} sudah memiliki ketua kelas: @{ketua_lama.username}.")
    user = User(username=username, password_hash=hash_password(data.password.strip()), role="ketua_kelas", kelas_id=data.kelas_id)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.put("/ketua-kelas/{user_id}", response_model=UserResponse)
def edit_ketua_kelas(user_id: int, data: KetuaKelasUpdate, db: Session = Depends(get_db), _=Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id, User.role == "ketua_kelas").first()
    if not user:
        raise HTTPException(404, "Akun Ketua Kelas tidak ditemukan")
    if data.username and data.username != user.username:
        if db.query(User).filter(User.username == data.username).first():
            raise HTTPException(400, f"Username '{data.username}' sudah digunakan")
        user.username = data.username.strip()
    if data.password:
        if len(data.password.strip()) < 4:
            raise HTTPException(400, "Password minimal 4 karakter")
        user.password_hash = hash_password(data.password.strip())
    if data.kelas_id is not None and data.kelas_id != user.kelas_id:
        kelas = db.query(Kelas).filter(Kelas.id == data.kelas_id).first()
        if not kelas:
            raise HTTPException(404, "Kelas tidak ditemukan")
        ketua_lama = db.query(User).filter(User.role == "ketua_kelas", User.kelas_id == data.kelas_id, User.id != user.id).first()
        if ketua_lama:
            raise HTTPException(400, f"{kelas.nama_kelas} sudah memiliki ketua kelas: @{ketua_lama.username}.")
        lama = db.query(Kelas).filter(Kelas.id == user.kelas_id).first()
        if lama and lama.nama_ketua_kelas == user.username:
            lama.nama_ketua_kelas = None
        user.kelas_id = data.kelas_id
    db.flush()
    kelas_tujuan = db.query(Kelas).filter(Kelas.id == user.kelas_id).first()
    if kelas_tujuan and kelas_tujuan.nama_ketua_kelas != user.username:
        kelas_tujuan.nama_ketua_kelas = user.username
    db.commit()
    db.refresh(user)
    return user


@router.delete("/ketua-kelas/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def hapus_ketua_kelas(user_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id, User.role == "ketua_kelas").first()
    if not user:
        raise HTTPException(404, "Akun Ketua Kelas tidak ditemukan")
    db.delete(user)
    db.commit()


@router.get("/anggota/{nim}", response_model=MahasiswaDetail)
def detail_anggota_admin(nim: str, db: Session = Depends(get_db), _=Depends(require_admin)):
    mhs = db.query(Mahasiswa).options(joinedload(Mahasiswa.kelas), joinedload(Mahasiswa.user)).filter(Mahasiswa.nim == nim).first()
    if not mhs:
        raise HTTPException(404, "Mahasiswa tidak ditemukan")
    return mhs


@router.put("/anggota/{nim}")
def edit_anggota_admin(nim: str, data: MahasiswaAdminUpdate, db: Session = Depends(get_db), _=Depends(require_admin)):
    mhs = db.query(Mahasiswa).options(joinedload(Mahasiswa.user)).filter(Mahasiswa.nim == nim).first()
    if not mhs:
        raise HTTPException(404, "Mahasiswa tidak ditemukan")
    if data.nim_baru and data.nim_baru.strip() != mhs.nim:
        nim_baru = data.nim_baru.strip()
        if db.query(Mahasiswa).filter(Mahasiswa.nim == nim_baru).first():
            raise HTTPException(400, f"NIM '{nim_baru}' sudah terdaftar")
        db.query(Absensi).filter(Absensi.nim == mhs.nim).update({Absensi.nim: nim_baru}, synchronize_session=False)
        mhs.nim = nim_baru
    if data.nama_lengkap:
        mhs.nama_lengkap = data.nama_lengkap.strip()
    if data.kelas_id is not None:
        if data.kelas_id and not db.query(Kelas).filter(Kelas.id == data.kelas_id).first():
            raise HTTPException(404, "Kelas tidak ditemukan")
        mhs.kelas_id = data.kelas_id or None
    if data.angkatan is not None:
        mhs.angkatan = data.angkatan
    if data.username is not None or data.password:
        user = mhs.user
        if data.username is not None and data.username.strip() == "" and user:
            mhs.user_id = None
            db.flush()
            user = None
        elif data.username:
            username_baru = data.username.strip()
            pemilik = db.query(User).filter(User.username == username_baru).first()
            if pemilik and (not user or pemilik.id != user.id):
                raise HTTPException(400, f"Username '{username_baru}' sudah digunakan")
            if not user:
                user = User(username=username_baru, password_hash=hash_password((data.password or "mahasiswa123").strip()), role="mahasiswa")
                db.add(user)
                db.flush()
                mhs.user_id = user.id
            else:
                user.username = username_baru
        if data.password and user:
            if len(data.password.strip()) < 4:
                raise HTTPException(400, "Password minimal 4 karakter")
            user.password_hash = hash_password(data.password.strip())
    user = mhs.user
    if user and user.kelas_id != mhs.kelas_id:
        user.kelas_id = mhs.kelas_id
    db.commit()
    db.refresh(mhs)
    return {"nim": mhs.nim, "nama_lengkap": mhs.nama_lengkap, "kelas_id": mhs.kelas_id,
            "angkatan": mhs.angkatan, "user_id": mhs.user_id,
            "username": mhs.user.username if mhs.user else None}


@router.get("/ketua-kelas/performa")
def performa_ketua_kelas(bulan: int | None = Query(None, ge=1, le=12), tahun: int | None = Query(None),
                         db: Session = Depends(get_db), _=Depends(require_admin)):
    hasil = []
    for ketua in db.query(User).filter(User.role == "ketua_kelas").all():
        kelas = db.query(Kelas).filter(Kelas.id == ketua.kelas_id).first()
        if not kelas:
            continue
        nim_list = [m.nim for m in db.query(Mahasiswa).filter(Mahasiswa.kelas_id == kelas.id).all()]
        q = db.query(func.count(Absensi.id)).filter(Absensi.nim.in_(nim_list) if nim_list else False)
        total = _filter_periode(q, bulan, tahun).scalar() or 0
        qh = db.query(func.count(Absensi.id)).filter(Absensi.status == "hadir").filter(Absensi.nim.in_(nim_list) if nim_list else False)
        hadir = _filter_periode(qh, bulan, tahun).scalar() or 0
        hasil.append({"ketua_id": ketua.id, "ketua_username": ketua.username, "kelas_id": kelas.id,
                      "kelas_nama": kelas.nama_kelas, "nama_ketua_kelas": kelas.nama_ketua_kelas,
                      "total_siswa": len(nim_list), "total_absensi": total, "total_hadir": hadir,
                      "rata_kehadiran": min(round(hadir / total * 100, 1) if total else 0, 100)})
    return {"bulan": bulan, "tahun": tahun, "data": sorted(hasil, key=lambda x: x["rata_kehadiran"], reverse=True)}


@router.get("/ketua-kelas/{ketua_id}/detail")
def detail_ketua_kelas(ketua_id: int, bulan: int | None = Query(None, ge=1, le=12), tahun: int | None = Query(None),
                       db: Session = Depends(get_db), _=Depends(require_admin)):
    ketua = db.query(User).filter(User.id == ketua_id, User.role == "ketua_kelas").first()
    if not ketua:
        raise HTTPException(404, "Ketua kelas tidak ditemukan")
    kelas = db.query(Kelas).filter(Kelas.id == ketua.kelas_id).first()
    if not kelas:
        raise HTTPException(404, "Kelas tidak ditemukan")
    detail = []
    for mhs in db.query(Mahasiswa).filter(Mahasiswa.kelas_id == kelas.id).all():
        records = _filter_periode(db.query(Absensi).filter(Absensi.nim == mhs.nim), bulan, tahun).all()
        total = len(records)
        hadir = sum(1 for a in records if a.status == "hadir")
        detail.append({"nim": mhs.nim, "nama": mhs.nama_lengkap, "angkatan": mhs.angkatan, "total_absensi": total,
                       "hadir": hadir, "sakit": sum(1 for a in records if a.status == "sakit"),
                       "izin": sum(1 for a in records if a.status == "izin"),
                       "alfa": sum(1 for a in records if a.status == "alfa"),
                       "persentase": min(round(hadir / total * 100, 1) if total else 0, 100)})
    rata = round(sum(s["persentase"] for s in detail) / len(detail), 1) if detail else 0
    return {"ketua": {"id": ketua.id, "username": ketua.username},
            "kelas": {"id": kelas.id, "nama": kelas.nama_kelas, "nama_ketua_kelas": kelas.nama_ketua_kelas,
                      "tahun_ajaran": kelas.tahun_ajaran, "angkatan": kelas.angkatan},
            "bulan": bulan, "tahun": tahun, "total_siswa": len(detail),
            "rata_kehadiran_kelas": rata, "detail_siswa": sorted(detail, key=lambda x: x["persentase"], reverse=True)}
