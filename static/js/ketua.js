// ─── ACTION HANDLERS ────────────────────────────────────────────────────────

window.hapusUser = async (id, username) => {
  if (typeof userRole !== "undefined" && userRole !== "admin") return notify("Hanya admin yang dapat menghapus user.", true);
  if (!confirm("Hapus user \"" + username + "\"?")) return;
  try {
    await api("/users/" + id, {method:"DELETE"});
    notify("User " + username + " berhasil dihapus.");
    await loadUsers();
  } catch(e) { notify(e.message, true); }
};

window.hapusKelas = async (id, nama) => {
  if (typeof userRole !== "undefined" && userRole !== "admin") return notify("Hanya admin yang dapat menghapus kelas.", true);
  if (!confirm("Hapus kelas \"" + nama + "\"?")) return;
  try {
    await api("/kelas/" + id, {method:"DELETE"});
    notify("Kelas " + nama + " berhasil dihapus.");
    await loadData();
  } catch(e) { notify(e.message, true); }
};

window.openEditKelasModal = (id, nama, tahun, angkatan) => {
  if (typeof userRole !== "undefined" && userRole !== "admin") return notify("Hanya admin yang dapat mengedit kelas.", true);
  openModal(
    "<h3>Edit Kelas</h3>" +
    "<form id='editKelasForm' data-kelas-id='" + id + "'>" +
    "<label>Nama kelas<input name='nama_kelas' value='" + escAttr(nama) + "' required></label>" +
    "<label>Tahun ajaran<input name='tahun_ajaran' type='number' value='" + tahun + "' required></label>" +
    "<label>Angkatan<input name='angkatan' type='number' min='2000' max='2100' value='" + (angkatan || "") + "' placeholder='Contoh: 2024'></label>" +
    "<button class='button primary'>Simpan Perubahan</button></form>"
  );
};

window.hapusMahasiswa = async (nim, nama) => {
  if (typeof userRole !== "undefined" && userRole !== "admin") return notify("Hanya admin yang dapat menghapus mahasiswa.", true);
  if (!confirm("Hapus mahasiswa \"" + nama + "\"?")) return;
  try {
    await api("/mahasiswa/" + nim, {method:"DELETE"});
    notify("Mahasiswa " + nama + " berhasil dihapus.");
    await loadData();
  } catch(e) { notify(e.message, true); }
};

window.openEditMataKuliahModal = (id) => {
  if (typeof userRole !== "undefined" && userRole !== "admin") return notify("Hanya admin yang dapat mengedit mata kuliah.", true);
  const item = (typeof mataKuliah !== "undefined" ? mataKuliah : []).find(m => Number(m.id) === Number(id));
  if (!item) return notify("Mata kuliah tidak ditemukan.", true);
  openModal(
    "<h3>Edit Mata Kuliah</h3><form id='editMataKuliahForm' data-mk-id='" + Number(item.id) + "'>" +
    "<label>Kode<input name='kode' value='" + escAttr(item.kode) + "' required></label>" +
    "<label>Nama mata kuliah<input name='nama' value='" + escAttr(item.nama) + "' required></label>" +
    "<label>Semester<input name='semester' type='number' min='1' value='" + (item.semester || "") + "' placeholder='Contoh: 1'></label>" +
    "<label>Kelas<select name='kelas_id' required>" +
    kelas.map(k => "<option value='" + k.id + "'" + (k.id === item.kelas_id ? " selected" : "") + ">" + escHtml(k.nama_kelas) + "</option>").join("") +
    "</select></label><button class='button primary'>Simpan Perubahan</button></form>"
  );
};

window.hapusMataKuliah = async (id) => {
  if (typeof userRole !== "undefined" && userRole !== "admin") return notify("Hanya admin yang dapat menghapus mata kuliah.", true);
  const item = (typeof mataKuliah !== "undefined" ? mataKuliah : []).find(m => Number(m.id) === Number(id));
  const nama = item ? item.nama : ("ID " + id);
  if (!confirm("Hapus mata kuliah \"" + nama + "\"?")) return;
  try {
    await api("/mata-kuliah/" + Number(id), {method:"DELETE"});
    notify("Mata kuliah " + nama + " berhasil dihapus.");
    await loadData();
  } catch(e) { notify(e.message, true); }
};

// ─── KELAS SAYA (ketua) ──────────────────────────────────────────────────────

window.isiMkQr = () => {
  const qrKelas = $("#qrKelas"), qrMk = $("#qrMataKuliah");
  if (!qrKelas || !qrMk) return;
  const cid = Number(qrKelas.value);
  const prev = qrMk.value;
  const filtered = mataKuliah.filter(m => Number(m.kelas_id) === cid);
  qrMk.innerHTML = "<option value=''>Pilih mata kuliah</option>" +
    filtered.map(m => "<option value='" + m.id + "'>" + escHtml(m.kode) + " — " + escHtml(m.nama) + "</option>").join("");
  if (prev && filtered.some(m => String(m.id) === String(prev))) qrMk.value = prev;
  else if (filtered.length === 1) qrMk.value = String(filtered[0].id);
};

window.loadKelasSaya = async () => {
  const card = $("#kelasSayaCard");
  if (!card || userRole !== "ketua_kelas" || !userKelasId) { if (card) card.classList.add("hidden"); return; }
  try {
    const [detail, mk] = await Promise.all([
      api("/kelas/" + userKelasId),
      api("/mata-kuliah/?kelas_id=" + userKelasId),
    ]);
    card.classList.remove("hidden");
    $("#kelasSayaNama").textContent = detail.nama_kelas + " (Angkatan " + (detail.angkatan || "—") + ")";
    $("#kelasSayaMeta").textContent = "Ketua: @" + (detail.ketua_username || "—") + " · " + detail.total_mahasiswa + " mahasiswa";
    $("#kelasSayaAnggota").textContent = detail.total_mahasiswa;
    $("#kelasSayaMatkul").textContent = mk.length;
    const today = new Date().toISOString().slice(0, 10);
    const sudah = attendanceRecords.filter(r => r.tanggal === today).length;
    const hadir = attendanceRecords.filter(r => r.tanggal === today && r.status === "hadir").length;
    $("#kelasSayaHadir").textContent = hadir;
    $("#kelasSayaBelum").textContent = Math.max(0, detail.total_mahasiswa - sudah);
    $("#kelasSayaChips").innerHTML = mk.map(m =>
      "<span class='chip'>" + escHtml(m.kode) + " - " + escHtml(m.nama) + "</span>"
    ).join("") || "<p class='empty tight'>Belum ada mata kuliah.</p>";
    card.querySelectorAll("[data-goto]").forEach(b => { b.onclick = () => showPage(b.dataset.goto); });
  } catch(e) { card.classList.add("hidden"); }
};

// ─── SETUP DASHBOARD ─────────────────────────────────────────────────────────

let dashboardSetupDone = false;

function setupDashboard() {
  setupNav(userRole);
  bindNavButtons();
  if (dashboardSetupDone) { loadData(); return; }
  dashboardSetupDone = true;

  const now = new Date();
  $("#todayDate").textContent = new Intl.DateTimeFormat("id-ID",
    {weekday:"long", day:"numeric", month:"short"}).format(now);
  $("#absenTanggal").value = now.toISOString().slice(0, 10);
  $("#absenTanggal").max = now.toISOString().slice(0, 10);
  $("#reportTahun").value  = now.getFullYear();
  $("#reportTahun").min = 2000;
  $("#reportTahun").max = now.getFullYear() + 1;
  $("#reportBulan").innerHTML = ["Januari","Februari","Maret","April","Mei","Juni",
    "Juli","Agustus","September","Oktober","November","Desember"]
    .map((n, i) => "<option value='" + (i+1) + "'" + (i === now.getMonth() ? " selected" : "") + ">" + n + "</option>")
    .join("");

  const roleLabel = {admin:"Administrator", ketua_kelas:"Ketua Kelas"};
  const roleLabelEl = $("#userRoleLabel");
  if (roleLabelEl) roleLabelEl.textContent = roleLabel[userRole] || userRole;

  const jumpAbsen = $(".jump-absen");
  if (jumpAbsen) jumpAbsen.onclick = () => showPage("absensi");
  $("#logoutButton").onclick = logout;
  $("#closeModal").onclick   = () => $("#modal").classList.add("hidden");

  const showKelasBtn = $("#showKelasForm");
  if (showKelasBtn && userRole !== "admin") showKelasBtn.style.display = "none";
  if (showKelasBtn && userRole === "admin") {
    showKelasBtn.onclick = () => openModal(
      "<h3>Tambah Kelas</h3><form id='kelasForm'>" +
      "<label>Nama kelas<input name='nama_kelas' placeholder='Contoh: TI-2A' required></label>" +
      "<label>Tahun ajaran<input name='tahun_ajaran' type='number' value='2026' required></label>" +
      "<label>Angkatan<input name='angkatan' type='number' min='2000' max='2100' placeholder='Contoh: 2024'></label>" +
      "<button class='button primary'>Simpan Kelas</button></form>"
    );
  }

  // Tombol tambah user (admin only)
  const showUserBtn = $("#showUserForm");
  if (showUserBtn && userRole !== "admin") showUserBtn.style.display = "none";
  if (showUserBtn && userRole === "admin") {
    showUserBtn.onclick = () => {
      openModal(
        "<h3>Tambah User</h3><form id='userForm'>" +
        "<label>Username<input name='username' required></label>" +
        "<label>Password<input name='password' type='password' required></label>" +
        "<label>Role<select name='role' id='modalRoleSelect'>" +
        "<option value='mahasiswa'>Mahasiswa</option>" +
        "<option value='ketua_kelas'>Ketua Kelas</option>" +
        "<option value='admin'>Admin</option>" +
        "</select></label>" +
        "<label id='kelasLabel'>Kelas (untuk ketua kelas)" +
        "<select name='kelas_id'><option value=''>— Pilih kelas —</option>" +
        kelas.map(k => "<option value='" + k.id + "'>" + k.nama_kelas + "</option>").join("") +
        "</select></label>" +
        "<label id='nimLabel' style='display:none;'>Hubungkan NIM (untuk mahasiswa)" +
        "<select name='nim'><option value=''>— Pilih mahasiswa (opsional) —</option>" +
        mahasiswa.map(m => "<option value='" + m.nim + "'>" + m.nim + " - " + m.nama_lengkap + "</option>").join("") +
        "</select></label>" +
        "<button class='button primary'>Simpan User</button></form>"
      );
      setTimeout(() => {
        const rs = $("#modalRoleSelect");
        const kl = $("#kelasLabel");
        const nl = $("#nimLabel");
        if (rs && kl && nl) {
          const toggle = () => {
            const isMhs = rs.value === "mahasiswa";
            kl.style.display = (rs.value === "ketua_kelas" || isMhs) ? "" : "none";
            kl.childNodes[0].textContent = isMhs ? "Kelas (untuk mahasiswa)" : "Kelas (untuk ketua kelas)";
            nl.style.display = isMhs ? "" : "none";
          };
          toggle();
          rs.onchange = toggle;
        }
      }, 50);
    };
  }

  // Tombol tambah mata kuliah
  const showMkBtn = $("#showMataKuliahForm");
  if (showMkBtn) {
    showMkBtn.onclick = () => openModal(
      "<h3>Tambah Mata Kuliah</h3><form id='mataKuliahForm'>" +
      "<label>Kode<input name='kode' placeholder='Contoh: IF101' required></label>" +
      "<label>Nama mata kuliah<input name='nama' placeholder='Contoh: Pemrograman Web' required></label>" +
      "<label>Semester<input name='semester' type='number' min='1' placeholder='Contoh: 1'></label>" +
      "<label>Kelas<select name='kelas_id' required>" +
      kelas.map(k => "<option value='" + k.id + "'>" + escHtml(k.nama_kelas) + "</option>").join("") +
      "</select></label><button class='button primary'>Simpan Mata Kuliah</button></form>"
    );
  }

  // Modal submit
  const modalEl = $("#modal");
  modalEl.addEventListener("submit", async (e) => {
    e.preventDefault();
    const form = e.target;
    const data = Object.fromEntries(new FormData(form));
    let endpoint = "";
    let method = "POST";
    if (form.id === "kelasForm")      { endpoint = "/kelas"; data.tahun_ajaran = Number(data.tahun_ajaran); data.angkatan = data.angkatan ? Number(data.angkatan) : null; }
    if (form.id === "editKelasForm") {
      endpoint = "/kelas/" + form.dataset.kelasId;
      method = "PUT";
      data.tahun_ajaran = Number(data.tahun_ajaran);
      data.angkatan = data.angkatan ? Number(data.angkatan) : null;
    }
    if (form.id === "mataKuliahForm") { endpoint = "/mata-kuliah/"; data.kelas_id = Number(data.kelas_id); data.semester = data.semester ? Number(data.semester) : null; }
    if (form.id === "editMataKuliahForm") {
      endpoint = "/mata-kuliah/" + form.dataset.mkId;
      method = "PUT";
      data.kelas_id = Number(data.kelas_id);
      data.semester = data.semester ? Number(data.semester) : null;
    }
    if (form.id === "userForm") {
      endpoint = "/users/";
      data.kelas_id = data.kelas_id ? Number(data.kelas_id) : undefined;
      if (!data.kelas_id) delete data.kelas_id;
      if (!data.nim) delete data.nim;
    }
    if (form.id === "ketuaKelasForm") {
      endpoint = "/admin/ketua-kelas";
      data.kelas_id = Number(data.kelas_id);
    }
    if (form.id === "editKetuaKelasForm") {
      const userId = form.dataset.userId;
      endpoint = "/admin/ketua-kelas/" + userId;
      method = "PUT";
      data.kelas_id = Number(data.kelas_id);
      if (!data.password) delete data.password;
    }
    if (form.id === "editUserForm") {
      const userId = form.dataset.userId;
      endpoint = "/users/" + userId;
      method = "PUT";
      data.kelas_id = data.kelas_id ? Number(data.kelas_id) : null;
      if (!data.password) delete data.password;
    }
    if (form.id === "editAnggotaForm") {
      const nimLama = form.dataset.nim;
      endpoint = "/admin/anggota/" + encodeURIComponent(nimLama);
      method = "PUT";
      data.kelas_id = Number(data.kelas_id);
      data.angkatan = data.angkatan ? Number(data.angkatan) : null;
      if (!data.password) delete data.password;
    }
    if (!endpoint) return;
    if (userRole !== "admin" && /^\/(kelas|users|admin|mata-kuliah)/.test(endpoint)) {
      notify("Hanya admin yang dapat menyimpan data ini.", true);
      return;
    }
    try {
      await api(endpoint, {method, body: JSON.stringify(data)});
      modalEl.classList.add("hidden");
      notify("Data berhasil disimpan.");
      await loadData();
      if (currentPage === "kelas") {
        await loadKelasManager();
        if (currentSelectedClass) await selectKelas(currentSelectedClass.id);
      }
      if (currentPage === "users") await loadUsers();
    } catch(err) { notify(err.message, true); }
  });

  // Form absensi manual
  const absensiForm = $("#absensiForm");
  if (absensiForm) {
    absensiForm.onsubmit = async (e) => {
      e.preventDefault();
      const data = Object.fromEntries(new FormData(e.target));
      if (!data.nim) return notify("Pilih mahasiswa terlebih dahulu.", true);
      if (!data.mata_kuliah_id) return notify("Pilih mata kuliah terlebih dahulu.", true);
      if (data.tanggal > new Date().toISOString().slice(0, 10)) return notify("Tanggal tidak boleh melebihi hari ini.", true);
      data.mata_kuliah_id = Number(data.mata_kuliah_id);
      try {
        await api("/absensi/", {method:"POST", body: JSON.stringify(data)});
        notify("Presensi berhasil dicatat.");
        e.target.reset();
        $("#absenTanggal").value = new Date().toISOString().slice(0, 10);
        await loadAbsensi();
      } catch(err) { notify(err.message, true); }
    };
  }
  const absenTgl = $("#absenTanggal");
  const absenMk  = $("#absenMataKuliah");
  if (absenTgl) absenTgl.onchange = () => renderQuickAttendance();
  if (absenMk)  absenMk.onchange  = () => renderQuickAttendance();

  // Panel presensi cepat
  const manualPanel = $("#absensi .form-panel");
  if (manualPanel && !$("#quickAttendance")) {
    manualPanel.insertAdjacentHTML("afterend",
      "<section class='panel quick-attendance-panel'>" +
      "<div class='panel-header'><div><p class='eyebrow'>PRESENSI CEPAT</p>" +
      "<h3>Catat kehadiran mahasiswa</h3>" +
      "<p>Pilih status setiap mahasiswa untuk tanggal dan mata kuliah yang dipilih.</p></div>" +
      "<span class='quick-tip'>Klik status untuk menyimpan</span></div>" +
      "<div id='quickAttendance' class='member-grid'></div></section>"
    );
  }

  // Laporan
  const reportForm = $("#reportForm");
  if (reportForm) {
    reportForm.onsubmit = async (e) => {
      e.preventDefault();
      const classId = (userRole === "ketua_kelas" && userKelasId) ? userKelasId : $("#reportKelas").value;
      const month   = $("#reportBulan").value;
      const year    = Number($("#reportTahun").value);
      if (!classId) return notify("Pilih kelas terlebih dahulu.", true);
      if (!year || year < 2000 || year > 2100) return notify("Tahun 2000–2100.", true);
      try {
        const data = await api("/laporan/rekap?kelas_id=" + classId + "&bulan=" + month + "&tahun=" + year);
        const resultEl = $("#reportResult");
        resultEl.classList.remove("hidden");

        resultEl.innerHTML =
          "<div class='panel-header'><div><h3>Rekap " + escHtml(data.kelas) + "</h3><p>Periode " + Number(month) + "/" + Number(year) + "</p></div>" +
          "<div>" +
          "<button class='button outline' onclick='downloadLaporan(\"excel\"," + Number(classId) + "," + Number(month) + "," + Number(year) + ")'>Excel</button> " +
          "<button class='button primary' onclick='downloadLaporan(\"pdf\"," + Number(classId) + "," + Number(month) + "," + Number(year) + ")'>PDF</button>" +
          "</div></div>" +
          "<div class='table-wrap'><table><thead><tr><th>NIM</th><th>NAMA</th><th>HADIR</th><th>SAKIT</th><th>IZIN</th><th>ALFA</th><th>% HADIR</th></tr></thead><tbody>" +
          data.data.map(r =>
            "<tr><td>" + escHtml(r.nim) + "</td><td>" + escHtml(r.nama_lengkap) + "</td><td>" + Number(r.hadir) +
            "</td><td>" + Number(r.sakit) + "</td><td>" + Number(r.izin) + "</td><td>" + Number(r.alfa) +
            "</td><td>" + Number(r.persentase_hadir) + "%</td></tr>"
          ).join("") +
          "</tbody></table></div>";
      } catch(err) { notify(err.message, true); }
    };
  }

  // QR
  const qrKelas = $("#qrKelas");
  const qrMk = $("#qrMataKuliah");
  if (qrKelas && qrMk) {
    qrKelas.onchange = () => window.isiMkQr();
    if (userRole === "ketua_kelas" && userKelasId) {
      qrKelas.value = String(userKelasId);
      qrKelas.disabled = true;
    }
    window.isiMkQr();
  }

  const qrForm = $("#qrForm");
  if (qrForm) {
    qrForm.onsubmit = async (e) => {
      e.preventDefault();
      const btn = qrForm.querySelector("button[type=submit]");
      const classId = $("#qrKelas").value;
      const mkId = $("#qrMataKuliah").value;
      if (!classId || !mkId) return notify("Pilih kelas dan mata kuliah terlebih dahulu.", true);
      if (btn) { btn.disabled = true; btn.textContent = "Membuat..."; }
      $("#qrResult").innerHTML = "<p class='empty'>Membuat kode QR...</p>";
      try {
        const data = await api(`/qr/generate?kelas_id=${classId}&mata_kuliah_id=${mkId}`, {method:"POST"});
        window._qrTokenAktif = data.token;
        window._qrSesiAktif = {kelas_id: Number(classId), mata_kuliah_id: Number(mkId)};
        const jam = (() => { try { return new Date(data.berlaku_sampai).toLocaleTimeString("id-ID", {hour:"2-digit", minute:"2-digit"}); } catch(_) { return data.berlaku_sampai; } })();
        const imgSrc = API_PREFIX + "/qr/image?token=" + encodeURIComponent(data.token);
        const namaMk = ($("#qrMataKuliah") || {}).selectedOptions?.[0]?.textContent || "";
        const boxEl = $("#qrResult");
        if (!boxEl) return;
        boxEl.innerHTML =
          "<div class='qr-stage'>" +
          (namaMk ? "<p class='qr-title'>" + escHtml(namaMk) + "</p>" : "") +
          "<img src='" + imgSrc + "' alt='Kode QR presensi' " +
          "onerror=\"this.outerHTML='<p class=\\'empty\\'>Gagal memuat gambar QR. Token masih valid, coba muat ulang.</p>'\">" +
          "<p class='qr-expire'>Berlaku hingga " + escHtml(jam) + "</p>" +
          "<div class='qr-bar'><i id='qrBarFill'></i></div>" +
          "<div id='qrLiveStatus' class='qr-live'>Menunggu scan...</div>" +
          "<div class='qr-actions'>" +
          "<button class='button outline btn-sm' id='btnRefreshQrStatus' type='button'>Refresh Status</button>" +
          "<button class='button outline btn-sm btn-danger' id='btnMatikanQr' type='button'>Matikan QR</button></div>" +
          "</div>";
        const badgeEl = $("#qrPageBadge");
        if (badgeEl) badgeEl.classList.remove("hidden");
        const btnMati = $("#btnMatikanQr");
        if (btnMati) btnMati.onclick = matikanQrAktif;
        const btnRefresh = $("#btnRefreshQrStatus");
        if (btnRefresh) btnRefresh.onclick = refreshQrStatus;
        refreshQrStatus();
        if (window._qrPoll) clearInterval(window._qrPoll);
        window._qrPoll = setInterval(refreshQrStatus, 5000);
      } catch(err) { notify(err.message, true); const bx = $("#qrResult"); if (bx) bx.innerHTML = "<div class='qr-empty'><span class='qr-empty-ico'>⌘</span><b>Gagal membuat QR</b><p>" + escHtml(err.message) + "</p></div>"; }
      finally { if (btn) { btn.disabled = false; btn.textContent = "Buat Kode QR"; } }
    };
  }

  // Restore halaman dari URL hash setelah data dimuat
  loadData()
    .then(() => {
      const hash = location.hash.replace("#", "");
      const validPages = ["dashboard","users","kelas","absensi","laporan","qr"];
      if (hash && validPages.includes(hash)) {
        showPage(hash, false);
      } else {
        history.replaceState({page: "dashboard"}, "", "#dashboard");
      }
    })
    .catch(err => notify(err.message, true));
}

window.matikanQrAktif = async () => {
  if (!window._qrTokenAktif) return notify("Belum ada QR aktif.", true);
  if (!confirm("Matikan QR ini? Mahasiswa tidak bisa scan lagi.")) return;
  try {
    await api("/qr/matikan?token=" + encodeURIComponent(window._qrTokenAktif), {method:"POST"});
    notify("QR berhasil dimatikan.");
    const bx = $("#qrResult");
    if (bx) bx.innerHTML = "<div class='qr-empty'><span class='qr-empty-ico'>⌘</span><b>Sesi dimatikan</b><p>Buat sesi baru bila perlu.</p></div>";
    window._qrTokenAktif = null;
    window._qrSesiAktif = null;
    if (window._qrPoll) { clearInterval(window._qrPoll); window._qrPoll = null; }
    const badgeEl = $("#qrPageBadge");
    if (badgeEl) badgeEl.classList.add("hidden");
  } catch(e) { notify(e.message, true); }
};

window.refreshQrStatus = async () => {
  const box = $("#qrLiveStatus");
  if (!window._qrTokenAktif || !window._qrSesiAktif) {
    if (window._qrPoll) { clearInterval(window._qrPoll); window._qrPoll = null; }
    return;
  }
  try {
    const s = window._qrSesiAktif;
    const data = await api("/qr/status?token=" + encodeURIComponent(window._qrTokenAktif) +
      "&kelas_id=" + s.kelas_id + "&mata_kuliah_id=" + s.mata_kuliah_id);
    if (box) box.textContent = "Sudah scan " + data.sudah_scan + " / " + data.total_mahasiswa + " mahasiswa";
    const bar = $("#qrBarFill");
    if (bar && data.total_mahasiswa) bar.style.width = Math.min(100, Math.round(data.sudah_scan / data.total_mahasiswa * 100)) + "%";
  } catch(e) {
    if (box) box.textContent = "Gagal memuat status: " + e.message;
    if (/kadaluarsa|dimatikan|valid/i.test(e.message)) {
      window._qrTokenAktif = null; window._qrSesiAktif = null;
      if (window._qrPoll) { clearInterval(window._qrPoll); window._qrPoll = null; }
      const badgeEl = $("#qrPageBadge");
      if (badgeEl) badgeEl.classList.add("hidden");
    }
  }
};

window.downloadLaporan = async (tipe, kelasId, bulan, tahun) => {
  const endpoint = tipe === "excel"
    ? "/laporan/ekspor-excel?kelas_id=" + kelasId + "&bulan=" + bulan + "&tahun=" + tahun
    : "/laporan/ekspor-pdf?kelas_id="   + kelasId + "&bulan=" + bulan + "&tahun=" + tahun;
  try {
    const res = await fetch(API_PREFIX + endpoint, {headers: {Authorization: "Bearer " + token}});
    if (!res.ok) { notify("Gagal mengunduh laporan.", true); return; }
    const blob = await res.blob();
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement("a");
    a.href     = url;
    a.download = (tipe === "excel" ? "rekap.xlsx" : "rekap.pdf");
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  } catch(e) { notify("Gagal mengunduh: " + e.message, true); }
};

