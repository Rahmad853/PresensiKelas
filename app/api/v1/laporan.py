import calendar
from datetime import date
from io import BytesIO

import openpyxl
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.security import require_admin_or_ketua
from app.models import Kelas
from app.schemas.absensi import HarianResponse, RekapResponse
from app.services.absensi import hitung_rekap, laporan_harian

router = APIRouter(prefix="/laporan", tags=["Laporan & Rekap"])


@router.get("/rekap", response_model=RekapResponse)
def rekap_bulanan(kelas_id: int = Query(...), bulan: int = Query(..., ge=1, le=12), tahun: int = Query(...),
                  mata_kuliah_id: int | None = Query(None), db: Session = Depends(get_db),
                  current_user: dict = Depends(require_admin_or_ketua)):
    if current_user.get("role") == "ketua_kelas" and kelas_id != current_user.get("kelas_id"):
        raise HTTPException(403, "Anda hanya bisa melihat laporan kelas Anda sendiri")
    kelas = db.query(Kelas).filter(Kelas.id == kelas_id).first()
    if not kelas:
        raise HTTPException(404, "Kelas tidak ditemukan")
    return RekapResponse(kelas=kelas.nama_kelas, bulan=bulan, tahun=tahun,
                         data=hitung_rekap(db, kelas_id, bulan, tahun, mata_kuliah_id))


@router.get("/harian", response_model=HarianResponse)
def rekap_harian(kelas_id: int = Query(...), tanggal: date = Query(...),
                 mata_kuliah_id: int | None = Query(None), db: Session = Depends(get_db),
                 current_user: dict = Depends(require_admin_or_ketua)):
    if current_user.get("role") == "ketua_kelas" and kelas_id != current_user.get("kelas_id"):
        raise HTTPException(403, "Anda hanya bisa melihat laporan kelas Anda sendiri")
    if not db.query(Kelas).filter(Kelas.id == kelas_id).first():
        raise HTTPException(404, "Kelas tidak ditemukan")
    return laporan_harian(db, kelas_id, tanggal, mata_kuliah_id)


@router.get("/ekspor-excel")
def ekspor_excel(kelas_id: int = Query(...), bulan: int = Query(..., ge=1, le=12), tahun: int = Query(...),
                 mata_kuliah_id: int | None = Query(None), db: Session = Depends(get_db),
                 current_user: dict = Depends(require_admin_or_ketua)):
    if current_user.get("role") == "ketua_kelas" and kelas_id != current_user.get("kelas_id"):
        raise HTTPException(403, "Anda hanya bisa mengekspor laporan kelas Anda sendiri")
    kelas = db.query(Kelas).filter(Kelas.id == kelas_id).first()
    if not kelas:
        raise HTTPException(404, "Kelas tidak ditemukan")
    data = hitung_rekap(db, kelas_id, bulan, tahun, mata_kuliah_id)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Rekap {calendar.month_name[bulan]} {tahun}"
    BIRU, ABU, PUTIH = "1D4ED8", "F1F5F9", "FFFFFF"
    thin = Side(style="thin", color="CBD5E1")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    ws.merge_cells("A1:H1")
    ws["A1"] = f"Rekap Absensi — {kelas.nama_kelas}"
    ws["A1"].font = Font(bold=True, size=13, color=PUTIH)
    ws["A1"].fill = PatternFill("solid", fgColor=BIRU)
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws.merge_cells("A2:H2")
    ws["A2"] = f"{calendar.month_name[bulan]} {tahun}  |  Ketua Kelas: {kelas.nama_ketua_kelas or '-'}"
    headers = ["No", "NIM", "Nama Lengkap", "Hadir", "Sakit", "Izin", "Alfa", "% Hadir"]
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col, value=h)
        cell.font = Font(bold=True, color=PUTIH, size=10)
        cell.fill = PatternFill("solid", fgColor=BIRU)
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = border
    for i, mhs in enumerate(data, 1):
        row = 4 + i
        values = [i, mhs.nim, mhs.nama_lengkap, mhs.hadir, mhs.sakit, mhs.izin, mhs.alfa, f"{mhs.persentase_hadir}%"]
        bg = ABU if i % 2 == 0 else PUTIH
        for col, val in enumerate(values, 1):
            cell = ws.cell(row=row, column=col, value=val)
            cell.fill = PatternFill("solid", fgColor=bg)
            cell.alignment = Alignment(horizontal="center" if col != 3 else "left", vertical="center")
            cell.border = border
    for i, w in enumerate([5, 16, 30, 8, 8, 8, 8, 10], 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             headers={"Content-Disposition": f'attachment; filename="rekap_{kelas.nama_kelas}_{bulan}_{tahun}.xlsx"'})


@router.get("/ekspor-pdf")
def ekspor_pdf(kelas_id: int = Query(...), bulan: int = Query(..., ge=1, le=12), tahun: int = Query(...),
               mata_kuliah_id: int | None = Query(None), db: Session = Depends(get_db),
               current_user: dict = Depends(require_admin_or_ketua)):
    if current_user.get("role") == "ketua_kelas" and kelas_id != current_user.get("kelas_id"):
        raise HTTPException(403, "Anda hanya bisa mengekspor laporan kelas Anda sendiri")
    kelas = db.query(Kelas).filter(Kelas.id == kelas_id).first()
    if not kelas:
        raise HTTPException(404, "Kelas tidak ditemukan")
    data = hitung_rekap(db, kelas_id, bulan, tahun, mata_kuliah_id)
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm)
    styles = getSampleStyleSheet()
    elemen = [Paragraph(f"Rekap Absensi Kelas {kelas.nama_kelas}",
                        ParagraphStyle("judul", parent=styles["Title"], fontSize=14, textColor=colors.HexColor("#1D4ED8")))]
    tabel_data = [["No", "NIM", "Nama Lengkap", "Hadir", "Sakit", "Izin", "Alfa", "% Hadir"]]
    for i, mhs in enumerate(data, 1):
        tabel_data.append([i, mhs.nim, mhs.nama_lengkap, mhs.hadir, mhs.sakit, mhs.izin, mhs.alfa, f"{mhs.persentase_hadir}%"])
    tabel = Table(tabel_data, colWidths=[1 * cm, 2.8 * cm, 6 * cm, 1.5 * cm, 1.5 * cm, 1.5 * cm, 1.5 * cm, 2 * cm], repeatRows=1)
    tabel.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1D4ED8")),
                               ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                               ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                               ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                               ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                               ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1"))]))
    elemen.append(tabel)
    elemen.append(Spacer(1, 0.5 * cm))
    elemen.append(Paragraph(f"Dicetak: {date.today().strftime('%d %B %Y')}", styles["Normal"]))
    doc.build(elemen)
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/pdf",
                             headers={"Content-Disposition": f'attachment; filename="rekap_{kelas.nama_kelas}_{bulan}_{tahun}.pdf"'})


@router.get("/harian/ekspor-excel")
def ekspor_harian_excel(kelas_id: int = Query(...), tanggal: date = Query(...),
                        mata_kuliah_id: int | None = Query(None), db: Session = Depends(get_db),
                        current_user: dict = Depends(require_admin_or_ketua)):
    if current_user.get("role") == "ketua_kelas" and kelas_id != current_user.get("kelas_id"):
        raise HTTPException(403, "Anda hanya bisa mengekspor laporan kelas Anda sendiri")
    rep = laporan_harian(db, kelas_id, tanggal, mata_kuliah_id)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Harian {tanggal.isoformat()}"
    BIRU, ABU, PUTIH = "1D4ED8", "F1F5F9", "FFFFFF"
    thin = Side(style="thin", color="CBD5E1")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    ws.merge_cells("A1:E1")
    ws["A1"] = f"Laporan Harian — {rep.kelas} — {tanggal.isoformat()}"
    ws["A1"].font = Font(bold=True, size=13, color=PUTIH)
    ws["A1"].fill = PatternFill("solid", fgColor=BIRU)
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws.merge_cells("A2:E2")
    ws["A2"] = rep.mata_kuliah or "Semua mata kuliah"
    for col, h in enumerate(["No", "NIM", "Nama Lengkap", "Status", "Keterangan"], 1):
        cell = ws.cell(row=4, column=col, value=h)
        cell.font = Font(bold=True, color=PUTIH, size=10)
        cell.fill = PatternFill("solid", fgColor=BIRU)
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = border
    for i, r in enumerate(rep.data, 1):
        for col, val in enumerate([i, r.nim, r.nama_lengkap, r.status or "belum tercatat", r.keterangan or "—"], 1):
            cell = ws.cell(row=4 + i, column=col, value=val)
            cell.fill = PatternFill("solid", fgColor=ABU if i % 2 == 0 else PUTIH)
            cell.alignment = Alignment(horizontal="center" if col != 3 else "left", vertical="center")
            cell.border = border
    for i, w in enumerate([5, 16, 30, 14, 30], 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             headers={"Content-Disposition": f'attachment; filename="harian_{rep.kelas}_{tanggal.isoformat()}.xlsx"'})


@router.get("/harian/ekspor-pdf")
def ekspor_harian_pdf(kelas_id: int = Query(...), tanggal: date = Query(...),
                      mata_kuliah_id: int | None = Query(None), db: Session = Depends(get_db),
                      current_user: dict = Depends(require_admin_or_ketua)):
    if current_user.get("role") == "ketua_kelas" and kelas_id != current_user.get("kelas_id"):
        raise HTTPException(403, "Anda hanya bisa mengekspor laporan kelas Anda sendiri")
    rep = laporan_harian(db, kelas_id, tanggal, mata_kuliah_id)
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm)
    styles = getSampleStyleSheet()
    elemen = [Paragraph(f"Laporan Harian {rep.kelas} — {tanggal.isoformat()}",
                        ParagraphStyle("judul", parent=styles["Title"], fontSize=14, textColor=colors.HexColor("#1D4ED8")))]
    if rep.mata_kuliah:
        elemen.append(Paragraph(rep.mata_kuliah, styles["Normal"]))
    tabel_data = [["No", "NIM", "Nama Lengkap", "Status", "Keterangan"]]
    for i, r in enumerate(rep.data, 1):
        tabel_data.append([i, r.nim, r.nama_lengkap, r.status or "belum tercatat", r.keterangan or "—"])
    tabel = Table(tabel_data, colWidths=[1 * cm, 2.8 * cm, 6 * cm, 3 * cm, 5 * cm], repeatRows=1)
    tabel.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1D4ED8")),
                               ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                               ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                               ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                               ("ALIGN", (2, 1), (2, -1), "LEFT"),
                               ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                               ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1"))]))
    elemen.append(tabel)
    doc.build(elemen)
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/pdf",
                             headers={"Content-Disposition": f'attachment; filename="harian_{rep.kelas}_{tanggal.isoformat()}.pdf"'})
