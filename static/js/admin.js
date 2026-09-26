let allUsers = [];
let userPage = 1;
const USER_PER_PAGE = 20;
async function loadUsers() {
  try {
    allUsers = await api("/users/");
    userPage = 1;
    bindUserFilter();
    renderUsers();
  } catch(e) { notify(e.message, true); }
}
function bindUserFilter() {
  const s = $("#userSearch"), f = $("#userRoleFilter");
  if (s && !s.dataset.bound) { s.dataset.bound = "1"; s.oninput = () => { userPage = 1; renderUsers(); }; }
  if (f && !f.dataset.bound) { f.dataset.bound = "1"; f.onchange = () => { userPage = 1; renderUsers(); }; }
  const pv = $("#userPrev"), nx = $("#userNext");
  if (pv && !pv.dataset.bound) { pv.dataset.bound = "1"; pv.onclick = () => { if (userPage > 1) { userPage--; renderUsers(); } }; }
  if (nx && !nx.dataset.bound) { nx.dataset.bound = "1"; nx.onclick = () => { userPage++; renderUsers(); }; }
}
function filteredUsers() {
  const q = ($("#userSearch")?.value || "").toLowerCase();
  const rf = $("#userRoleFilter")?.value || "";
  return allUsers.filter(u =>
    (!rf || u.role === rf) && (!q || u.username.toLowerCase().includes(q) || (u.nim || "").toLowerCase().includes(q)));
}
function renderUsers() {
  const kelasMap = {};
  kelas.forEach(k => { kelasMap[k.id] = k.nama_kelas; });
  const list = filteredUsers();
  const pages = Math.max(1, Math.ceil(list.length / USER_PER_PAGE));
  if (userPage > pages) userPage = pages;
  const start = (userPage - 1) * USER_PER_PAGE;
  const rows = list.slice(start, start + USER_PER_PAGE);
  const cnt = $("#userCount");
  if (cnt) cnt.textContent = list.length + " dari " + allUsers.length + " akun";
  const info = $("#userPageInfo");
  if (info) info.textContent = "Hal " + userPage + " / " + pages;
  const pv = $("#userPrev"), nx = $("#userNext");
  if (pv) pv.disabled = userPage <= 1;
  if (nx) nx.disabled = userPage >= pages;
  const userListEl = $("#userList");
  if (!userListEl) return;
  userListEl.innerHTML = rows.map((u, idx) => {
      const tgl = (() => { try { return new Date(u.created_at).toLocaleDateString("id-ID"); } catch (_) { return "—"; } })();
      return "<tr><td class='c-no'>" + (start + idx + 1) + "</td><td><b>" + escHtml(u.username) + "</b></td>" +
      "<td class='c-nim'><b>" + escHtml(u.nim || "—") + "</b></td><td>" + roleBadge(u.role) + "</td>" +
      "<td>" + (u.kelas_id ? (kelasMap[u.kelas_id] || "ID:" + u.kelas_id) : "—") + "</td>" +
      "<td class='c-date'>" + tgl + "</td>" +
      "<td class='c-aksi'><div class='row-actions'>" +
      "<button class='button outline btn-sm' " +
      "onclick='openEditUserModal(" + u.id + ",\"" + escAttr(u.username) + "\",\"" + u.role + "\"," + (u.kelas_id || "null") + ",\"" + escAttr(u.nim || "") + "\")'>Edit</button> " +
      (u.role === "admin" ? "" : "<button class='button outline btn-sm btn-danger' " +
      "onclick='hapusUser(" + u.id + ",\"" + escAttr(u.username) + "\")'>Hapus</button>") + "</div></td></tr>";
    }).join("") || "<tr><td colspan='7' class='empty'>Belum ada user.</td></tr>";
}

// ─── ADMIN: HASIL & KELOLA KETUA KELAS ───────────────────────────────────────

async function refreshAdminPage() {
  await loadData();
  if (currentSelectedClass) await selectKelas(currentSelectedClass.id);
  else await loadKelasManager();
  if (currentPage === "users") await loadUsers();
}

async function loadAdmin() {
  const bulanEl = $("#adminBulan");
  const tahunEl = $("#adminTahun");
  if (bulanEl && tahunEl && !bulanEl.children.length) {
    const now = new Date();
    bulanEl.innerHTML = [1,2,3,4,5,6,7,8,9,10,11,12].map(m =>
      "<option value='" + m + "'" + (m === now.getMonth()+1 ? " selected" : "") + ">" +
      ["Januari","Februari","Maret","April","Mei","Juni","Juli","Agustus","September","Oktober","November","Desember"][m-1] +
      "</option>"
    ).join("");
    tahunEl.innerHTML = [2024,2025,2026,2027].map(y =>
      "<option value='" + y + "'" + (y === now.getFullYear() ? " selected" : "") + ">" + y + "</option>"
    ).join("");
  }

  const filterBtn = $("#adminFilter");
  if (filterBtn) {
    filterBtn.onclick = async () => {
      try {
        await loadAdminData($("#adminBulan").value, $("#adminTahun").value);
      } catch (e) {
        notify(e.message, true);
      }
    };
  }

  const btnTambahKetua = $("#btnTambahKetuaModal");
  if (btnTambahKetua) {
    btnTambahKetua.onclick = () => openTambahKetuaModal();
  }

  const importForm = $("#importForm");
  if (importForm && !importForm.dataset.bound) {
    importForm.dataset.bound = "1";
    importForm.onsubmit = submitImportForm;
  }

  try {
    await loadAdminKetuaAccounts();
  } catch (e) {
    const tableEl = $("#ketuaAccountTable");
    if (tableEl) tableEl.innerHTML = "<tr><td colspan='5' class='empty'>Gagal memuat akun ketua kelas: " + escHtml(e.message) + "</td></tr>";
    notify(e.message, true);
  }
  if (bulanEl && tahunEl) {
    try {
      await loadAdminData(bulanEl.value, tahunEl.value);
    } catch (e) {
      const tableEl = $("#adminTable");
      if (tableEl) tableEl.innerHTML = "<tr><td colspan='8' class='empty'>Gagal memuat performa ketua kelas: " + escHtml(e.message) + "</td></tr>";
      notify(e.message, true);
    }
  }
}

async function loadAdminKetuaAccounts() {
    // Arsip: tabel ketua kini menyatu di panel Kelas terpadu.
    return;
}

async function loadAdminData(bulan, tahun) {
    const data = await api("/admin/ketua-kelas/performa?bulan=" + bulan + "&tahun=" + tahun);
    const tableEl = $("#adminTable");
    if (!tableEl) return;
    tableEl.innerHTML = data.data.map(d =>
      "<tr><td><b>@" + escHtml(d.ketua_username) + "</b></td><td>" + escHtml(d.kelas_nama) + "</td><td>" + escHtml(d.nama_ketua_kelas || "—") + "</td><td>" +
      Number(d.total_siswa) + "</td><td>" + Number(d.total_absensi) + "</td><td>" + Number(d.total_hadir) + "</td><td><b>" + Number(d.rata_kehadiran) + "%</b></td>" +
      "<td><button class='button outline' style='padding:5px 10px;font-size:12px' onclick='viewAdminDetail(" + Number(d.ketua_id) + ",\"" + escAttr(d.kelas_nama) + "\")'>Detail</button></td></tr>"
    ).join("") || "<tr><td colspan='8' class='empty'>Belum ada data performa ketua kelas pada periode ini.</td></tr>";
}

window.openTambahKetuaModal = (kelasId = null, namaKelas = null) => {
  const options = kelas.map(k =>
    "<option value='" + k.id + "'" + (kelasId && k.id === kelasId ? " selected" : "") + ">" + k.nama_kelas + "</option>"
  ).join("");

  openModal(
    "<h3>Tambah Akun Ketua Kelas</h3>" +
    "<p style='color:var(--muted);font-size:13px;margin-bottom:16px;'>Buat akun ketua kelas untuk mengelola presensi kelas (A, B, C, D, E, dll).</p>" +
    "<form id='ketuaKelasForm'>" +
    "<label>Pilih Kelas<select name='kelas_id' required>" +
    "<option value=''>— Pilih Kelas —</option>" + options +
    "</select></label>" +
    "<label>Username Ketua Kelas<input name='username' placeholder='Contoh: ketua_a / ketua_b' required></label>" +
    "<label>Password<input name='password' type='password' placeholder='Minimal 6 karakter' required></label>" +
    "<button class='button primary'>Simpan Akun Ketua Kelas</button></form>"
  );
};

window.openEditKetuaModal = (userId, username, kelasId) => {
  const options = kelas.map(k =>
    "<option value='" + k.id + "'" + (kelasId && k.id === kelasId ? " selected" : "") + ">" + escHtml(k.nama_kelas) + "</option>"
  ).join("");

  openModal(
    "<h3>Edit Akun Ketua Kelas</h3>" +
    "<p style='color:var(--muted);font-size:13px;margin-bottom:16px;'>Ubah username, password, atau penempatan kelas untuk @" + escHtml(username) + ".</p>" +
    "<form id='editKetuaKelasForm' data-user-id='" + userId + "'>" +
    "<label>Pilih Kelas<select name='kelas_id'>" + options + "</select></label>" +
    "<label>Username Ketua Kelas<input name='username' value='" + escAttr(username) + "' required></label>" +
    "<label>Password Baru (kosongkan jika tidak diubah)<input name='password' type='password' placeholder='Minimal 4 karakter'></label>" +
    "<button class='button primary'>Simpan Perubahan</button></form>"
  );
};

window.hapusKetuaKelas = async (userId, username, namaKelas) => {
  if (!confirm("Hapus akun ketua kelas @" + username + " untuk " + namaKelas + "?\nKetua tidak akan bisa login lagi.")) return;
  try {
    await api("/admin/ketua-kelas/" + userId, {method:"DELETE"});
    notify("Akun ketua kelas @" + username + " berhasil dihapus.");
    await refreshAdminPage();
  } catch(e) { notify(e.message, true); }
};

window.openEditUserModal = (userId, username, role, kelasId, nim) => {
  const roleOptions = ["admin", "ketua_kelas", "mahasiswa"].map(r =>
    "<option value='" + r + "'" + (role === r ? " selected" : "") + ">" +
    (r === "admin" ? "Admin" : r === "ketua_kelas" ? "Ketua Kelas" : "Mahasiswa") + "</option>"
  ).join("");
  const kelasOptions = "<option value=''>— Tanpa Kelas —</option>" + kelas.map(k =>
    "<option value='" + k.id + "'" + (kelasId && k.id === kelasId ? " selected" : "") + ">" + escHtml(k.nama_kelas) + "</option>"
  ).join("");

  openModal(
    "<h3>Edit Akun User</h3>" +
    "<p style='color:var(--muted);font-size:13px;margin-bottom:16px;'>Ubah username, password, role, atau kelas untuk @" + escHtml(username) + ".</p>" +
    "<form id='editUserForm' data-user-id='" + userId + "'>" +
    "<label>Nama (username)<input name='username' value='" + escAttr(username) + "' required></label>" +
    "<label>NIM<input name='nim' value='" + escAttr(nim || "") + "' placeholder='Contoh: 60900125005'></label>" +
    "<label>Password Baru (kosongkan jika tidak diubah)<input name='password' type='password' placeholder='Minimal 4 karakter'></label>" +
    "<label>Role<select name='role'>" + roleOptions + "</select></label>" +
    "<label>Kelas<select name='kelas_id'>" + kelasOptions + "</select></label>" +
    "<button class='button primary'>Simpan Perubahan</button></form>"
  );
};

window.openEditAnggotaModal = async (nim) => {
  try {
    const data = await api("/admin/anggota/" + encodeURIComponent(nim));
    const kelasOptions = kelas.map(k =>
      "<option value='" + k.id + "'" + (data.kelas_id === k.id ? " selected" : "") + ">" + escHtml(k.nama_kelas) + "</option>"
    ).join("");

    openModal(
      "<h3>Edit Data Anggota</h3>" +
      "<p style='color:var(--muted);font-size:13px;margin-bottom:16px;'>Ubah NIM, nama, kelas, username, dan password anggota.</p>" +
      "<form id='editAnggotaForm' data-nim='" + escAttr(nim) + "'>" +
      "<label>NIM<input name='nim_baru' value='" + escAttr(data.nim) + "' required></label>" +
      "<label>Nama Lengkap<input name='nama_lengkap' value='" + escAttr(data.nama_lengkap) + "' required></label>" +
      "<label>Kelas<select name='kelas_id'>" + kelasOptions + "</select></label>" +
      "<label>Angkatan<input name='angkatan' type='number' min='2000' max='2100' value='" + (data.angkatan || "") + "' placeholder='Contoh: 2024'></label>" +
      "<label>Username Login (kosongkan untuk melepas akun)<input name='username' value='" + escAttr(data.user ? data.user.username : "") + "' placeholder='Contoh: ahmad'></label>" +
      "<label>Password Baru (kosongkan jika tidak diubah)<input name='password' type='password' placeholder='Minimal 4 karakter'></label>" +
      "<button class='button primary'>Simpan Perubahan</button></form>"
    );
  } catch(e) { notify(e.message, true); }
};

async function submitImportForm(e) {
  e.preventDefault();
  const f = $("#importFile").files[0];
  if (!f) return;
  const dry = $("#importDryRun").checked;
  const box = $("#importResult");
  box.innerHTML = "<p class='empty'>Mengunggah...</p>";
  try {
    const fd = new FormData();
    fd.append("file", f);
    const res = await fetch(API_PREFIX + "/admin/import-mahasiswa?dry_run=" + dry, {
      method: "POST",
      headers: token ? {Authorization: "Bearer " + token} : {},
      body: fd,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Import gagal.");
    }
    const r = await res.json();
    const ubah = (r.diperbarui || []).map(d =>
      "<tr><td>" + d.baris + "</td><td><b>" + escHtml(d.nim) + "</b></td><td>" + escHtml(d.perubahan.join(", ")) + "</td></tr>"
    ).join("");
    const rows = r.dibuat.map(d =>
      "<tr><td>" + d.baris + "</td><td>" + escHtml(d.nama) + "</td><td><b>" + escHtml(d.nim) + "</b></td>" +
      "<td><b>@" + escHtml(d.username) + "</b></td><td>" + roleBadge(d.role) + "</td></tr>"
    ).join("");
    const skips = r.skip.map(s =>
      "<tr><td>" + s.baris + "</td><td>" + escHtml(s.nim || "—") + "</td><td>" + escHtml(s.alasan) + "</td></tr>"
    ).join("");
    box.innerHTML =
      "<p><b>" + (r.dry_run ? "[DRY RUN] " : "") + r.dibuat.length + " dibuat, " + (r.diperbarui || []).length + " diperbarui</b>, " + r.skip.length + " dilewati.</p>" +
      (r.dry_run ? "<p class='empty'>Uncheck 'Cek dulu' lalu import ulang untuk menyimpan + salin tabel username/password (password = NIM).</p>" : "<p class='empty'>Salin tabel ini sekarang — password = NIM masing-masing.</p>") +
      "<div class='table-wrap'><table><thead><tr><th>BARIS</th><th>NAMA</th><th>NIM / PASSWORD</th><th>USERNAME</th><th>ROLE</th></tr></thead><tbody>" +
      (rows || "<tr><td colspan='5' class='empty'>Tidak ada.</td></tr>") + "</tbody></table></div>" +
      (ubah ? "<div class='table-wrap' style='margin-top:12px'><table><thead><tr><th>BARIS</th><th>NIM</th><th>PERUBAHAN</th></tr></thead><tbody>" + ubah + "</tbody></table></div>" : "") +
      (skips ? "<div class='table-wrap' style='margin-top:12px'><table><thead><tr><th>BARIS</th><th>NIM</th><th>ALASAN SKIP</th></tr></thead><tbody>" + skips + "</tbody></table></div>" : "");
    notify(r.dry_run ? "Cek selesai." : "Import selesai: " + r.dibuat.length + " dibuat, " + (r.diperbarui || []).length + " diperbarui.");
    if (!r.dry_run) refreshAdminPage();
  } catch(err) {
    box.innerHTML = "<p class='empty'>Gagal: " + escHtml(err.message) + "</p>";
    notify(err.message, true);
  }
}

window.viewAdminDetail = async (ketuaId, kelasNama) => {
  try {
    const bulan = $("#adminBulan") ? $("#adminBulan").value : "";
    const tahun = $("#adminTahun") ? $("#adminTahun").value : "";
    const query = bulan && tahun ? `?bulan=${bulan}&tahun=${tahun}` : "";
    const data = await api("/admin/ketua-kelas/" + ketuaId + "/detail" + query);
    const detailEl = $("#adminDetail");
    if (!detailEl) return;
    detailEl.classList.remove("hidden");

    let siswaRows = data.detail_siswa.map(s =>
      "<tr><td><b>" + escHtml(s.nim) + "</b></td><td>" + escHtml(s.nama) + "</td><td>" + escHtml(s.angkatan || "—") + "</td><td>" +
      Number(s.total_absensi) + "</td><td>" + Number(s.hadir) + "</td><td>" + Number(s.sakit) + "</td><td>" + Number(s.izin) + "</td><td>" + Number(s.alfa) + "</td><td><b>" + Number(s.persentase) + "%</b></td></tr>"
    ).join("") || "<tr><td colspan='9' class='empty'>Belum ada data mahasiswa.</td></tr>";

    detailEl.innerHTML =
      "<div class='page-actions'><div><h3>Detail Presensi " + escHtml(kelasNama) + "</h3><p>Performa detail mahasiswa di bawah bimbingan ketua kelas @" + escHtml(data.ketua.username) + ".</p></div><button id='closeAdminDetail' class='button outline'>Tutup</button></div>" +
      "<section class='panel'><div class='panel-header'><h3>Statistik Kelas</h3></div>" +
      "<div class='stat-grid' style='margin:20px 0'>" +
      "<article class='stat-card blue'><span>👥</span><div><small>TOTAL SISWA</small><b>" + Number(data.total_siswa) + "</b></div></article>" +
      "<article class='stat-card green'><span>✓</span><div><small>RATA-RATA HADIR</small><b>" + Number(data.rata_kehadiran_kelas) + "%</b></div></article>" +
      "<article class='stat-card amber'><span>◷</span><div><small>PERIODE</small><b>" + escHtml(data.bulan || "Semua") + " / " + escHtml(data.tahun || "—") + "</b></div></article>" +
      "</div></section>" +
      "<section class='panel'><div class='panel-header'><h3>Detail Presensi Siswa</h3></div><div class='table-wrap'><table><thead><tr><th>NIM</th><th>NAMA</th><th>ANGKATAN</th><th>TOTAL</th><th>HADIR</th><th>SAKIT</th><th>IZIN</th><th>ALFA</th><th>% HADIR</th></tr></thead><tbody>" + siswaRows + "</tbody></table></div></section>";

    const closeBtn = $("#closeAdminDetail");
    if (closeBtn) closeBtn.onclick = () => detailEl.classList.add("hidden");
  } catch(e) { notify(e.message, true); }
};

