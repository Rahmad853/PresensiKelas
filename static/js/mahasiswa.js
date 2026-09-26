// ─── MAHASISWA VIEW ─────────────────────────────────────────────────────────

async function setupMahasiswaView(username) {
  const mUserName    = $("#mUserName");
  const mUserInitial = $("#mUserInitial");
  const mLogoutBtn   = $("#mLogoutButton");
  if (mUserName)    mUserName.textContent    = username;
  if (mUserInitial) mUserInitial.textContent = username.charAt(0).toUpperCase();
  if (mLogoutBtn)   mLogoutBtn.onclick       = logout;

  try {
    const [records, mk] = await Promise.all([api("/absensi/"), api("/mata-kuliah/")]);
    const matkulMap = {};
    mk.forEach(m => { matkulMap[m.id] = m.nama; });

    const hadir  = records.filter(r => r.status === "hadir").length;
    const sakit  = records.filter(r => r.status === "sakit").length;
    const izin   = records.filter(r => r.status === "izin").length;
    const alfa   = records.filter(r => r.status === "alfa").length;
    const total  = records.length;
    const persen = total > 0 ? Math.round(hadir / total * 100) : 0;

    const set = (id, val) => { const el = $("#" + id); if (el) el.textContent = val; };
    set("mHadir",     hadir);
    set("mSakitIzin", sakit + izin);
    set("mAlfa",      alfa);
    set("mPersen",    persen + "%");

    const listEl = $("#mAbsensiList");
    if (listEl) {
      listEl.innerHTML = records.map(r =>
        "<tr><td>" + formatDate(r.tanggal) + "</td><td>" + (matkulMap[r.mata_kuliah_id] || "—") +
        "</td><td>" + badge(r.status) + "</td><td>" + (r.keterangan || "—") + "</td></tr>"
      ).join("") || "<tr><td colspan='4' class='empty'>Belum ada riwayat absensi.</td></tr>";
    }
  } catch(e) {
    const listEl = $("#mAbsensiList");
    if (listEl) listEl.innerHTML = "<tr><td colspan='4' class='empty'>Gagal memuat data.</td></tr>";
  }
}

