const API_PREFIX = "/api/v1";
const $ = (selector) => document.querySelector(selector);
let token       = localStorage.getItem("presensi_token") || "";
let userRole    = localStorage.getItem("presensi_role") || "";
let userKelasId = Number(localStorage.getItem("presensi_kelas_id")) || null;
let currentPage = "dashboard";

let kelas = [], mahasiswa = [], mataKuliah = [], attendanceRecords = [];

// ─── API HELPER ─────────────────────────────────────────────────────────────

async function api(path, options = {}) {
  const headers = options.body ? {"Content-Type": "application/json"} : {};
  if (token) headers.Authorization = "Bearer " + token;
  const res = await fetch(API_PREFIX + path, {...options, headers: {...headers, ...(options.headers || {})}});
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    const d = err.detail;
    throw new Error(Array.isArray(d) ? d.map(x => x.msg || JSON.stringify(x)).join("; ") : (d || "Permintaan gagal."));
  }
  return res.status === 204 ? null : res.json();
}

function notify(msg, isError = false) {
  const node = $("#toast") || $("#mToast");
  if (!node) return;
  node.textContent = msg;
  node.classList.toggle("error", isError);
  node.classList.add("show");
  clearTimeout(node._t);
  node._t = setTimeout(() => node.classList.remove("show"), 3200);
}

function formatDate(v) {
  if (!v) return "—";
  const parts = String(v).split("-");
  if (parts.length === 3) {
    const d = new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]));
    return new Intl.DateTimeFormat("id-ID", {day:"numeric", month:"long", year:"numeric"}).format(d);
  }
  return v;
}

function badge(v) {
  if (!v) return "<span class='badge'>—</span>";
  const s = String(v);
  return "<span class='badge " + escHtml(s) + "'>" + escHtml(s.charAt(0).toUpperCase() + s.slice(1)) + "</span>";
}

function roleBadge(role) {
  const map   = {admin:"blue", ketua_kelas:"purple", mahasiswa:"green"};
  const label = {admin:"Admin", ketua_kelas:"Ketua Kelas", mahasiswa:"Mahasiswa"};
  return "<span class='badge " + (map[role] || "") + "'>" + (label[role] || role) + "</span>";
}

function fillClassOptions(el) {
  if (!el) return;
  el.innerHTML = "<option value=''>Pilih kelas</option>" +
    kelas.map(k => "<option value='" + Number(k.id) + "'>" + escHtml(k.nama_kelas) + "</option>").join("");
}

function escAttr(v) {
  return String(v ?? "").replace(/\\/g, "\\\\").replace(/'/g, "\\'").replace(/"/g, "&quot;");
}

function escHtml(v) {
  return String(v ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// ─── NAVIGASI HALAMAN ───────────────────────────────────────────────────────

function showPage(name, pushState = true) {
  if (name !== "qr" && window._qrPoll) { clearInterval(window._qrPoll); window._qrPoll = null; }
  if (name === "admin" || name === "mataKuliah") name = "kelas";
  if (userRole !== "admin" && ["users", "kelas"].includes(name)) name = "dashboard";
  document.querySelectorAll(".page").forEach(n => n.classList.remove("active-page"));
  document.querySelectorAll(".nav-item[data-page]").forEach(n =>
    n.classList.toggle("active", n.dataset.page === name)
  );
  const el = $("#" + name);
  if (el) el.classList.add("active-page");

  const map = {
    dashboard:  ["DASHBOARD",        "Ringkasan Kehadiran"],
    users:      ["MANAJEMEN",         "Manajemen User"],
    kelas:      ["MANAJEMEN DATA",    "Kelas, Ketua & Mata Kuliah"],
    absensi:    ["PRESENSI",          "Input Presensi"],
    laporan:    ["LAPORAN",           "Laporan Kehadiran"],
    qr:         ["PRESENSI DIGITAL",  "Presensi QR"],
  };
  if (map[name]) {
    const pageCrumb = $("#pageCrumb");
    const pageTitle = $("#pageTitle");
    if (pageCrumb) pageCrumb.textContent = map[name][0];
    if (pageTitle) pageTitle.textContent  = map[name][1];
  }

  if (pushState && name !== currentPage) {
    history.pushState({page: name}, "", "#" + name);
  }
  currentPage = name;

  if (name === "users") loadUsers();
  if (name === "kelas") loadKelasManager();
}

window.addEventListener("popstate", (e) => {
  const page = (e.state && e.state.page) || "dashboard";
  showPage(page, false);
});

function setupNav(role) {
  document.querySelectorAll(".admin-only").forEach(el => {
    el.style.display = role === "admin" ? "" : "none";
  });
  document.querySelectorAll(".ketua-only").forEach(el => {
    el.style.display = role === "ketua_kelas" ? "" : "none";
  });
}

function bindNavButtons() {
  document.querySelectorAll(".nav-item[data-page]").forEach(btn => {
    btn.onclick = () => {
      showPage(btn.dataset.page);
      const sb = $(".sidebar");
      if (sb) sb.classList.remove("mobile-open");
    };
  });
  const toggle = $("#mobileMenuToggle");
  if (toggle) {
    toggle.onclick = () => {
      const sb = $(".sidebar");
      if (sb) sb.classList.toggle("mobile-open");
    };
  }
}

// ─── DATA LOADER ────────────────────────────────────────────────────────────

async function loadAbsensi() {
  const records = await api("/absensi/");
  attendanceRecords = records;
  const today = new Date().toISOString().slice(0, 10);
  const current = records.filter(r => r.tanggal === today);
  const unikHariIni = new Set(current.map(r => r.nim));
  const hadirEl = $("#hadirHariIni");
  const belumEl = $("#belumTercatat");
  if (hadirEl) hadirEl.textContent = current.filter(r => r.status === "hadir").length;
  if (belumEl) belumEl.textContent = Math.max(0, mahasiswa.length - unikHariIni.size);

  const recentEl = $("#recentAbsensi");
  if (recentEl) {
    recentEl.innerHTML = records.slice(0, 6).map(r =>
      "<tr><td><b>" + escHtml(r.nim) + "</b></td><td>" + formatDate(r.tanggal) + "</td><td>" +
      badge(r.status) + "</td><td>" + escHtml((r.metode || "—").toUpperCase()) + "</td></tr>"
    ).join("") || "<tr><td colspan='4' class='empty'>Belum ada presensi tercatat.</td></tr>";
  }

  const historyEl = $("#absensiList");
  if (historyEl) {
    historyEl.innerHTML = records.map(r =>
      "<tr><td>" + escHtml(r.nim) + "</td><td>" + formatDate(r.tanggal) + "</td><td>" +
      badge(r.status) + "</td><td>" + escHtml(r.keterangan || "—") + "</td></tr>"
    ).join("") || "<tr><td colspan='4' class='empty'>Belum ada riwayat presensi.</td></tr>";
  }
  renderQuickAttendance();
}

function renderQuickAttendance() {
  const container = $("#quickAttendance");
  if (!container) return;
  const date     = ($("#absenTanggal") || {}).value || new Date().toISOString().slice(0, 10);
  const courseId = Number(($("#absenMataKuliah") || {}).value) || null;
  if (!courseId) {
    container.innerHTML = "<p class='empty'>Pilih mata kuliah terlebih dahulu.</p>";
    return;
  }
  const statusByNim = new Map(attendanceRecords
    .filter(r => r.tanggal === date && Number(r.mata_kuliah_id) === courseId)
    .map(r => [r.nim, r.status]));
  container.innerHTML = mahasiswa.map(mhs => {
    const status = statusByNim.get(mhs.nim);
    const actions = status
      ? "<span class='attendance-done'>" + badge(status) + "</span>"
      : "<div class='attendance-actions'>" +
        "<button data-nim='" + escAttr(mhs.nim) + "' data-status='hadir' class='present'>Hadir</button>" +
        "<button data-nim='" + escAttr(mhs.nim) + "' data-status='sakit' class='permission'>Sakit</button>" +
        "<button data-nim='" + escAttr(mhs.nim) + "' data-status='izin'  class='permission'>Izin</button>" +
        "<button data-nim='" + escAttr(mhs.nim) + "' data-status='alfa'  class='absent'>Alfa</button>" +
        "</div>";
    return "<article class='member-card'>" +
      "<div class='member-avatar'>" + escHtml((mhs.nama_lengkap || "?").charAt(0).toUpperCase()) + "</div>" +
      "<div class='member-info'><b>" + escHtml(mhs.nama_lengkap) + "</b>" +
      "<small>" + escHtml(mhs.nim) + " · " + escHtml(mhs.kelas ? mhs.kelas.nama_kelas : "—") + "</small></div>" +
      actions + "</article>";
  }).join("") || "<p class='empty'>Tambahkan mahasiswa terlebih dahulu.</p>";
  container.querySelectorAll("button[data-nim]").forEach(btn => {
    btn.onclick = async () => {
      if (btn.disabled) return;
      btn.disabled = true;
      try {
        await api("/absensi/", {method:"POST", body: JSON.stringify({
          nim: btn.dataset.nim, tanggal: date, status: btn.dataset.status,
          metode: "manual", mata_kuliah_id: courseId,
        })});
        notify("Absensi berhasil dicatat.");
        await loadAbsensi();
      } catch(e) { notify(e.message, true); btn.disabled = false; }
    };
  });
}

async function loadData() {
  try {
    if (userRole === "mahasiswa") {
      [mahasiswa, mataKuliah] = await Promise.all([api("/mahasiswa"), api("/mata-kuliah/")]);
      kelas = [];
    } else {
      const results = await Promise.all([api("/mahasiswa"), api("/mata-kuliah/"), api("/kelas")]);
      mahasiswa  = results[0];
      mataKuliah = results[1];
      kelas      = results[2];
    }
  } catch(e) {
    notify("Gagal memuat data: " + e.message, true);
    return;
  }

  fillClassOptions($("#reportKelas"));
  fillClassOptions($("#qrKelas"));
  if (userRole === "ketua_kelas" && kelas.length === 1 && Number(kelas[0].id) !== Number(userKelasId)) {
    userKelasId = Number(kelas[0].id);
    localStorage.setItem("presensi_kelas_id", userKelasId || "");
  }
  if (userRole === "ketua_kelas" && userKelasId) {
    ["#reportKelas", "#qrKelas"].forEach(sel => {
      const el = $(sel);
      if (el) { el.value = String(userKelasId); el.disabled = true; }
    });
    if (typeof isiMkQr === "function") isiMkQr();
  }

  const ketuaScope = userRole === "ketua_kelas" ? (Number(userKelasId) || "kosong") : null;
  const absenSiswa = $("#absenSiswa");
  if (absenSiswa) {
    const list = ketuaScope ? mahasiswa.filter(m => Number(m.kelas_id) === ketuaScope) : mahasiswa;
    absenSiswa.innerHTML = "<option value=''>Pilih mahasiswa</option>" +
      list.map(m => "<option value='" + escAttr(m.nim) + "'>" + escHtml(m.nama_lengkap) + " — " + escHtml(m.nim) + "</option>").join("");
  }
  const absenMk = $("#absenMataKuliah");
  if (absenMk) {
    const list = ketuaScope ? mataKuliah.filter(m => Number(m.kelas_id) === ketuaScope) : mataKuliah;
    absenMk.innerHTML = "<option value=''>Pilih mata kuliah</option>" +
      list.map(m => "<option value='" + Number(m.id) + "'>" + escHtml(m.kode) + " — " + escHtml(m.nama) + "</option>").join("");
  }

  const totalSiswa = $("#totalSiswa");
  const totalKelas = $("#totalKelas");
  if (totalSiswa) totalSiswa.textContent = mahasiswa.length;
  if (totalKelas) totalKelas.textContent = kelas.length;

  await loadAbsensi();
  if (userRole === "ketua_kelas" && userKelasId && typeof loadKelasSaya === "function") loadKelasSaya();
}

function openModal(content) {
  $("#modalContent").innerHTML = content;
  $("#modal").classList.remove("hidden");
}

// ─── AUTH LOGIC ─────────────────────────────────────────────────────────────

function logout() {
  ["presensi_token","presensi_role","presensi_kelas_id","presensi_username"]
    .forEach(k => localStorage.removeItem(k));
  location.replace("/");
}

function masukApp(result) {
  token       = result.access_token;
  userRole    = result.role;
  userKelasId = result.kelas_id || null;
  localStorage.setItem("presensi_token",    token);
  localStorage.setItem("presensi_role",     userRole);
  localStorage.setItem("presensi_kelas_id", userKelasId || "");
  localStorage.setItem("presensi_username", result.username);

  $("#loginView").classList.add("hidden");

  if (userRole === "mahasiswa") {
    $("#mahasiswaView").classList.remove("hidden");
    setupMahasiswaView(result.username);
  } else {
    $("#appView").classList.remove("hidden");
    const uName = $("#userName");
    const wName = $("#welcomeName");
    const uInit = $("#userInitial");
    if (uName) uName.textContent = result.username;
    if (wName) wName.textContent = result.username;
    if (uInit) uInit.textContent = result.username.charAt(0).toUpperCase();
    setupDashboard();
  }
}

$("#loginForm").onsubmit = async (e) => {
  e.preventDefault();
  const errEl = $("#loginError");
  if (errEl) errEl.textContent = "";
  try {
    const data   = Object.fromEntries(new FormData(e.target));
    const result = await api("/auth/login", {method:"POST", body: JSON.stringify(data)});
    masukApp(result);
  } catch(err) {
    if (errEl) errEl.textContent = err.message;
  }
};

// Auto Login
if (token) {
  api("/absensi/").then(() => {
    const username = localStorage.getItem("presensi_username") || "User";
    $("#loginView").classList.add("hidden");
    if (userRole === "mahasiswa") {
      $("#mahasiswaView").classList.remove("hidden");
      setupMahasiswaView(username);
    } else {
      $("#appView").classList.remove("hidden");
      const uName = $("#userName");
      const wName = $("#welcomeName");
      const uInit = $("#userInitial");
      if (uName) uName.textContent = username;
      if (wName) wName.textContent = username;
      if (uInit) uInit.textContent = username.charAt(0).toUpperCase();
      setupDashboard();
    }
  }).catch(logout);
}
