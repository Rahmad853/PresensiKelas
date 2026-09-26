import calendar
import csv
import io
from datetime import date

from fastapi import HTTPException
from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app.models import Absensi, Kelas, Mahasiswa, MataKuliah, User
from app.schemas.absensi import AbsensiBulk, AbsensiCreate, HarianItem, HarianResponse, RekapMahasiswa


def _kelas_milik_ketua(current_user: dict) -> int | None:
    return current_user.get("kelas_id")


def query_absensi(db: Session, current_user: dict, kelas_id=None, tanggal=None, nim=None):
    role = current_user.get("role")
    q = db.query(Absensi)
    if role == "mahasiswa":
        mhs = db.query(Mahasiswa).filter(Mahasiswa.user_id == int(current_user["sub"])).first()
        if not mhs:
            return []
        return q.filter(Absensi.nim == mhs.nim).order_by(Absensi.tanggal.desc()).all()
    if role == "ketua_kelas":
        kelas_id_user = _kelas_milik_ketua(current_user)
        nim_list = [m.nim for m in db.query(Mahasiswa).filter(Mahasiswa.kelas_id == kelas_id_user).all()]
        q = q.filter(Absensi.nim.in_(nim_list or ["-"]))
        if nim:
            q = q.filter(Absensi.nim == nim)
    else:
        if nim:
            q = q.filter(Absensi.nim == nim)
        if kelas_id:
            nim_list = [m.nim for m in db.query(Mahasiswa).filter(Mahasiswa.kelas_id == kelas_id).all()]
            q = q.filter(Absensi.nim.in_(nim_list or ["-"]))
    if tanggal:
        q = q.filter(Absensi.tanggal == tanggal)
    return q.order_by(Absensi.tanggal.desc()).all()


def catat_absensi(db: Session, data: AbsensiCreate, current_user: dict) -> Absensi:
    role = current_user.get("role")
    if data.tanggal > date.today():
        raise HTTPException(400, "Tanggal tidak boleh melebihi hari ini")
    mhs = db.query(Mahasiswa).filter(Mahasiswa.nim == data.nim).first()
    if not mhs:
        raise HTTPException(404, "NIM tidak ditemukan")
    if role == "ketua_kelas" and mhs.kelas_id != current_user.get("kelas_id"):
        raise HTTPException(403, "Anda hanya bisa mencatat absensi untuk kelas Anda sendiri")
    if role == "mahasiswa":
        raise HTTPException(403, "Mahasiswa tidak dapat mencatat absensi secara manual")
    mk = db.query(MataKuliah).filter(MataKuliah.id == data.mata_kuliah_id).first()
    if not mk:
        raise HTTPException(404, "Mata kuliah tidak ditemukan")
    if mhs.kelas_id and mk.kelas_id != mhs.kelas_id:
        raise HTTPException(400, "Mata kuliah bukan milik kelas mahasiswa ini")
    existing = db.query(Absensi).filter(
        Absensi.nim == data.nim, Absensi.tanggal == data.tanggal,
        Absensi.mata_kuliah_id == data.mata_kuliah_id,
    ).first()
    if existing:
        raise HTTPException(400, f"Absensi {data.nim} pada {data.tanggal} sudah tercatat")
    absen = Absensi(**data.model_dump(), dicatat_oleh=int(current_user["sub"]))
    db.add(absen)
    db.commit()
    db.refresh(absen)
    return absen


def catat_bulk(db: Session, data: AbsensiBulk, current_user: dict) -> dict:
    role = current_user.get("role")
    hasil = {"berhasil": 0, "duplikat": 0, "error": []}
    for item in data.data:
        if item.tanggal > date.today():
            hasil["error"].append(f"NIM {item.nim} tanggal melebihi hari ini")
            continue
        mhs = db.query(Mahasiswa).filter(Mahasiswa.nim == item.nim).first()
        if not mhs:
            hasil["error"].append(f"NIM {item.nim} tidak ditemukan")
            continue
        if role == "ketua_kelas" and mhs.kelas_id != current_user.get("kelas_id"):
            hasil["error"].append(f"NIM {item.nim} bukan mahasiswa kelas Anda")
            continue
        mk = db.query(MataKuliah).filter(MataKuliah.id == item.mata_kuliah_id).first()
        if not mk or (mhs.kelas_id and mk.kelas_id != mhs.kelas_id):
            hasil["error"].append(f"NIM {item.nim} mata kuliah tidak sesuai kelas")
            continue
        existing = db.query(Absensi).filter(
            Absensi.nim == item.nim, Absensi.tanggal == item.tanggal,
            Absensi.mata_kuliah_id == item.mata_kuliah_id,
        ).first()
        if existing:
            hasil["duplikat"] += 1
            continue
        db.add(Absensi(**item.model_dump(), dicatat_oleh=int(current_user["sub"])))
        hasil["berhasil"] += 1
    db.commit()
    return hasil


def ubah_absensi(db: Session, absen_id: int, status: str, keterangan, current_user: dict) -> Absensi:
    absen = db.query(Absensi).filter(Absensi.id == absen_id).first()
    if not absen:
        raise HTTPException(404, "Data absensi tidak ditemukan")
    if current_user.get("role") == "ketua_kelas":
        mhs = db.query(Mahasiswa).filter(Mahasiswa.nim == absen.nim).first()
        if not mhs or mhs.kelas_id != current_user.get("kelas_id"):
            raise HTTPException(403, "Anda tidak berhak mengubah absensi ini")
    absen.status = status
    if keterangan is not None:
        absen.keterangan = keterangan
    db.commit()
    db.refresh(absen)
    return absen


def hapus_absensi(db: Session, absen_id: int) -> None:
    absen = db.query(Absensi).filter(Absensi.id == absen_id).first()
    if not absen:
        raise HTTPException(404, "Data absensi tidak ditemukan")
    db.delete(absen)
    db.commit()


def hitung_rekap(db: Session, kelas_id: int, bulan: int, tahun: int, mata_kuliah_id=None) -> list[RekapMahasiswa]:
    mahasiswa_list = db.query(Mahasiswa).filter(Mahasiswa.kelas_id == kelas_id).all()
    if mata_kuliah_id:
        total_hari = db.query(func.count(func.distinct(Absensi.tanggal))).filter(
            Absensi.mata_kuliah_id == mata_kuliah_id,
            extract("month", Absensi.tanggal) == bulan,
            extract("year", Absensi.tanggal) == tahun,
        ).scalar() or 0
        if not total_hari:
            total_hari = sum(1 for d in range(1, calendar.monthrange(tahun, bulan)[1] + 1) if date(tahun, bulan, d).weekday() < 5)
    else:
        total_hari = sum(1 for d in range(1, calendar.monthrange(tahun, bulan)[1] + 1) if date(tahun, bulan, d).weekday() < 5)
    hasil = []
    for mhs in mahasiswa_list:
        q = db.query(Absensi.status, func.count(Absensi.id).label("n")).filter(
            Absensi.nim == mhs.nim,
            extract("month", Absensi.tanggal) == bulan,
            extract("year", Absensi.tanggal) == tahun,
        )
        if mata_kuliah_id:
            q = q.filter(Absensi.mata_kuliah_id == mata_kuliah_id)
        rows = q.group_by(Absensi.status).all()
        stat = {r.status: r.n for r in rows}
        h = stat.get("hadir", 0)
        total_catat = sum(stat.values())
        denom = total_catat if mata_kuliah_id and total_catat else total_hari
        hasil.append(RekapMahasiswa(
            nim=mhs.nim, nama_lengkap=mhs.nama_lengkap, hadir=h,
            sakit=stat.get("sakit", 0), izin=stat.get("izin", 0), alfa=stat.get("alfa", 0),
            total_hari=denom,
            persentase_hadir=round(min(h / denom * 100, 100), 1) if denom else 0,
        ))
    return sorted(hasil, key=lambda x: x.nama_lengkap)


def laporan_harian(db: Session, kelas_id: int, tanggal: date, mata_kuliah_id=None) -> HarianResponse:
    kelas = db.query(Kelas).filter(Kelas.id == kelas_id).first()
    nama_kelas = kelas.nama_kelas if kelas else "—"
    nama_mk = None
    if mata_kuliah_id is not None:
        mk = db.query(MataKuliah).filter(MataKuliah.id == mata_kuliah_id).first()
        nama_mk = f"{mk.kode} — {mk.nama}" if mk else None
    mahasiswa_list = db.query(Mahasiswa).filter(Mahasiswa.kelas_id == kelas_id).order_by(Mahasiswa.nama_lengkap).all()
    q = db.query(Absensi).filter(Absensi.tanggal == tanggal)
    if mata_kuliah_id is not None:
        q = q.filter(Absensi.mata_kuliah_id == mata_kuliah_id)
    catat = {a.nim: a for a in q.all()}
    return HarianResponse(
        kelas=nama_kelas, tanggal=tanggal, mata_kuliah=nama_mk,
        data=[HarianItem(
            nim=m.nim, nama_lengkap=m.nama_lengkap,
            status=catat[m.nim].status if m.nim in catat else None,
            keterangan=catat[m.nim].keterangan if m.nim in catat else None,
            metode=catat[m.nim].metode if m.nim in catat else None,
        ) for m in mahasiswa_list],
    )


def baca_baris_import(filename: str, raw: bytes) -> list[dict]:
    name = (filename or "").lower()
    if name.endswith((".xlsx", ".xlsm", ".xltx", ".xltm")):
        from openpyxl import load_workbook
        wb = load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            return []
        header = [str(c or "").strip().lower() for c in rows[0]]
        return [dict(zip(header, [c if c is None else str(c) for c in r])) for r in rows[1:]]
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    return [{(k or "").strip().lower(): v for k, v in (r or {}).items()} for r in reader]


def _sel_str(v) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v).strip()


def _resolve_kelas_sinkron(db: Session, kode, angkatan, kelas_dibuat: list):
    kode = _sel_str(kode)
    if not kode:
        return None
    # ponytail: pin ke Kelas angkatan 2025 (data CSV dominan); upgrade: kolom Tahun di CSV
    ingin = "KELAS " + kode.upper().removeprefix("KELAS ").strip()
    if not ingin.strip():
        return None
    semua = [k for k in db.query(Kelas).all() if (k.nama_kelas or "").strip().upper() == ingin]
    pin = [k for k in semua if k.angkatan == 2025] or [k for k in semua if not k.angkatan] or semua
    if pin:
        return sorted(pin, key=lambda k: k.id)[0]
    k = Kelas(nama_kelas="Kelas " + ingin.title().removeprefix("Kelas ").strip() or ingin,
              tahun_ajaran=2025, angkatan=2025)
    db.add(k)
    db.flush()
    kelas_dibuat.append(k.nama_kelas)
    return k


def _lepas_ketua_lain(db: Session, kelas_id, kecuali_id) -> list:
    if not kelas_id:
        return []
    lain = db.query(User).filter(User.role == "ketua_kelas", User.kelas_id == kelas_id, User.id != kecuali_id).all()
    for u in lain:
        u.kelas_id = None
    return [u.username for u in lain]


def sinkron_mahasiswa_csv(db: Session, rows: list[dict], dry_run: bool = False) -> dict:
    from app.core.security import hash_password
    out = {"dry_run": dry_run, "total_baris": len(rows), "dibuat": [], "diperbarui": [], "skip": [], "kelas_dibuat": []}
    users_nim = {u.nim: u for u in db.query(User).all() if u.nim}
    users_nm = {u.username: u for u in db.query(User).all()}
    mhs_nim = {m.nim: m for m in db.query(Mahasiswa).all()}
    seen: set[str] = set()
    ketua_csv: dict[str, int | None] = {}
    for i, r in enumerate(rows, start=2):
        nama = " ".join(_sel_str(r.get("nama")).split())
        nim = _sel_str(r.get("nim"))
        role_csv = _sel_str(r.get("role")).lower()
        try:
            angkatan = int(_sel_str(r.get("angkatan")))
        except ValueError:
            angkatan = None
        if not nama:
            out["skip"].append({"baris": i, "nim": nim, "alasan": "Nama kosong"})
            continue
        if not nim:
            out["skip"].append({"baris": i, "nim": nim, "alasan": "NIM kosong"})
            continue
        if nim in seen:
            out["skip"].append({"baris": i, "nim": nim, "alasan": "NIM duplikat dalam file"})
            continue
        seen.add(nim)
        role = "ketua_kelas" if role_csv in ("ketua kelas", "ketua_kelas", "ketua") else "mahasiswa"
        kelas = _resolve_kelas_sinkron(db, r.get("kelas"), angkatan, out["kelas_dibuat"])
        kid = kelas.id if kelas else None
        if role == "ketua_kelas" and kid is not None and nim not in ketua_csv and kid in ketua_csv.values():
            out["skip"].append({"baris": i, "nim": nim, "alasan": "Sudah ada ketua lain untuk kelas ini di file"})
            continue
        if role == "ketua_kelas":
            ketua_csv[nim] = kid
        user = users_nim.get(nim)
        if user and user.role == "admin":
            out["skip"].append({"baris": i, "nim": nim, "alasan": "Akun admin tidak disentuh"})
            continue
        if user is None and nama in users_nm:
            out["skip"].append({"baris": i, "nim": nim, "alasan": f"Nama '{nama}' dipakai akun lain"})
            continue
        if user is None:
            yatim = None
            if nama in users_nm and not users_nm[nama].nim:
                calon = users_nm[nama]
                if calon.role == role or (role == "mahasiswa" and calon.role == "mahasiswa"):
                    yatim = calon
            if yatim is None and nim in mhs_nim and mhs_nim[nim].user_id:
                calon = db.query(User).filter(User.id == mhs_nim[nim].user_id).first()
                if calon is not None and not calon.nim:
                    yatim = calon
            if yatim is not None:
                ch0: list[str] = ["adopsi akun"]
                users_nim[nim] = yatim
                yatim.nim = nim
                del users_nm[yatim.username]
                yatim.username = nama
                users_nm[nama] = yatim
                yatim.kelas_id = kid
                if role == "ketua_kelas" and kelas:
                    for x in _lepas_ketua_lain(db, kid, yatim.id):
                        ch0.append(f"lepas ketua @{x}")
                    kelas.nama_ketua_kelas = nama
                m0 = mhs_nim.get(nim)
                if m0 is not None:
                    if m0.nama_lengkap != nama:
                        m0.nama_lengkap = nama
                        ch0.append("nama_lengkap")
                    if m0.angkatan != angkatan:
                        m0.angkatan = angkatan
                        ch0.append("angkatan")
                    if m0.kelas_id != kid:
                        m0.kelas_id = kid
                        ch0.append("kelas_mhs")
                    if m0.user_id != yatim.id:
                        m0.user_id = yatim.id
                        ch0.append("taut_user")
                out["diperbarui"].append({"baris": i, "nim": nim, "nama": nama, "perubahan": ch0})
                continue
            u = User(username=nama, nim=nim, password_hash=hash_password(nim), role=role, kelas_id=kid)
            db.add(u)
            db.flush()
            if role == "ketua_kelas" and kelas:
                _lepas_ketua_lain(db, kid, u.id)
                kelas.nama_ketua_kelas = nama
            if role == "mahasiswa" and nim not in mhs_nim:
                mhs_nim[nim] = Mahasiswa(nim=nim, nama_lengkap=nama, kelas_id=kid, user_id=u.id, angkatan=angkatan)
                db.add(mhs_nim[nim])
            users_nim[nim] = u
            users_nm[nama] = u
            out["dibuat"].append({"baris": i, "nama": nama, "nim": nim, "username": nama, "role": role,
                                  "kelas": kelas.nama_kelas if kelas else None})
            continue
        ch: list[str] = []
        if user.username != nama:
            bentrok = users_nm.get(nama)
            if bentrok is not None and bentrok.id != user.id:
                ch.append("username dipakai akun lain (tetap)")
            else:
                del users_nm[user.username]
                user.username = nama
                users_nm[nama] = user
                ch.append("nama")
        if user.role != role:
            user.role = role
            ch.append("role")
        if user.kelas_id != kid:
            user.kelas_id = kid
            ch.append("kelas")
        if role == "ketua_kelas" and kelas:
            for x in _lepas_ketua_lain(db, kid, user.id):
                ch.append(f"lepas ketua @{x}")
            if kelas.nama_ketua_kelas != user.username:
                kelas.nama_ketua_kelas = user.username
        m = mhs_nim.get(nim)
        if role == "mahasiswa" and m is None:
            mhs_nim[nim] = Mahasiswa(nim=nim, nama_lengkap=nama, kelas_id=kid, user_id=user.id, angkatan=angkatan)
            db.add(mhs_nim[nim])
            ch.append("data mahasiswa dibuat")
        if m is not None:
            if m.nama_lengkap != nama:
                m.nama_lengkap = nama
                ch.append("nama_lengkap")
            if m.angkatan != angkatan:
                m.angkatan = angkatan
                ch.append("angkatan")
            if m.kelas_id != kid:
                m.kelas_id = kid
                ch.append("kelas_mhs")
            if m.user_id != user.id:
                m.user_id = user.id
                ch.append("taut_user")
        if ch:
            out["diperbarui"].append({"baris": i, "nim": nim, "nama": nama, "perubahan": ch})
    if dry_run:
        db.rollback()
    else:
        db.commit()
    return out


def import_mahasiswa_users(db: Session, rows: list[dict], dry_run: bool) -> dict:
    # ponytail: arsip — diganti sinkron_mahasiswa_csv (buat + perbarui + petakan Kelas)
    return sinkron_mahasiswa_csv(db, rows, dry_run)
