let currentSelectedClass = null;
let currentDetail = null;

async function loadKelasManager() {
  try {
    const list = await api("/kelas");
    kelas = list;
    renderKelasSidebar();
    if (currentSelectedClass) {
      const masih = list.find(k => k.id === currentSelectedClass.id);
      if (masih) await selectKelas(masih.id);
      else {
        currentSelectedClass = null;
        currentDetail = null;
        const area = $("#manageMembersArea");
        if (area) area.classList.add("hidden");
        const empty = $("#noClassSelected");
        if (empty) empty.style.display = "";
      }
    }
  } catch (e) {
    notify(e.message, true);
  }
}

function renderKelasSidebar() {
  const container = $("#kelasListSidebar");
  if (!container) return;
  if (!kelas.length) {
    container.innerHTML = "<p class='empty'>Belum ada kelas.</p>";
    return;
  }
  const order = [...kelas].sort((a, b) => (a.angkatan || 0) - (b.angkatan || 0) || a.nama_kelas.localeCompare(b.nama_kelas));
  let lastAkt = null;
  container.innerHTML = order.map(k => {
    const head = k.angkatan !== lastAkt
      ? `<div class="angkatan-head">Angkatan ${k.angkatan || '—'}</div>` : "";
    lastAkt = k.angkatan;
    return head + `
    <div class="class-list-item ${currentSelectedClass && currentSelectedClass.id === k.id ? 'active' : ''}" onclick="selectKelas(${k.id})">
      <h4>${escHtml(k.nama_kelas)}</h4>
      <small>Ketua: ${escHtml(k.nama_ketua_kelas || '—')} | Tahun: ${k.tahun_ajaran}</small>
    </div>`;
  }).join("");
}

async function selectKelas(id) {
  currentSelectedClass = kelas.find(k => k.id === id);
  if (!currentSelectedClass) return;
  renderKelasSidebar();
  const noSel = $("#noClassSelected");
  if (noSel) noSel.style.display = "none";
  const area = $("#manageMembersArea");
  if (area) area.classList.remove("hidden");
  $("#currentClassName").textContent = `${currentSelectedClass.nama_kelas} (Angkatan ${currentSelectedClass.angkatan || '—'})`;
  $("#btnEditKelas").onclick = () => openEditKelasModal(
    currentSelectedClass.id,
    currentSelectedClass.nama_kelas,
    currentSelectedClass.tahun_ajaran,
    currentSelectedClass.angkatan
  );
  const matkulForm = $("#addMatkulForm");
  if (matkulForm) {
    matkulForm.onsubmit = async (e) => {
      e.preventDefault();
      const fd = new FormData(matkulForm);
      try {
        await api("/mata-kuliah/", {
          method: "POST",
          body: JSON.stringify({
            kode: (fd.get("kode") || "").toString().trim(),
            nama: (fd.get("nama") || "").toString().trim(),
            kelas_id: currentSelectedClass.id,
          }),
        });
        notify("Mata kuliah berhasil ditambahkan.");
        matkulForm.reset();
        await loadClassMatkul(currentSelectedClass.id);
      } catch (err) {
        notify(err.message, true);
      }
    };
  }
  await Promise.all([
    loadClassDetail(id),
    loadClassMembers(id),
    loadClassMatkul(id),
    setupClassReport(id),
  ]);
}

function pilihanBulan(selected) {
  const nama = ["Januari","Februari","Maret","April","Mei","Juni","Juli","Agustus","September","Oktober","November","Desember"];
  const now = new Date();
  return nama.map((n, i) => `<option value="${i + 1}"${(selected || now.getMonth() + 1) === i + 1 ? " selected" : ""}>${n}</option>`).join("");
}

function unduhLaporan(url, nama) {
  fetch(API_PREFIX + url, {headers: {Authorization: "Bearer " + token}})
    .then(res => { if (!res.ok) throw new Error("Gagal mengunduh laporan."); return res.blob(); })
    .then(blob => {
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = nama;
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(a.href), 1000);
    })
    .catch(e => notify(e.message, true));
}

async function setupClassReport(kelasId) {
  document.querySelectorAll("#manageMembersArea .tab-btn").forEach(btn => {
    btn.onclick = () => {
      document.querySelectorAll("#manageMembersArea .tab-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      $("#tabHarian").classList.toggle("hidden", btn.dataset.tab !== "harian");
      $("#tabBulanan").classList.toggle("hidden", btn.dataset.tab !== "bulanan");
    };
  });
  let mk = [];
  try { mk = await api(`/mata-kuliah/?kelas_id=${kelasId}`); } catch (e) { notify(e.message, true); }
  const opsi = `<option value="">Semua matkul</option>` + mk.map(m => `<option value="${m.id}">${escHtml(m.kode)} — ${escHtml(m.nama)}</option>`).join("");
  const fH = $("#classHarianForm");
  const fB = $("#classBulananForm");
  if (fH) {
    fH.tanggal.value = new Date().toISOString().slice(0, 10);
    fH.mata_kuliah_id.innerHTML = opsi;
    fH.onsubmit = async (e) => {
      e.preventDefault();
      const tgl = fH.tanggal.value;
      const mkId = fH.mata_kuliah_id.value;
      if (!tgl) return notify("Pilih tanggal dulu.", true);
      const q = `/laporan/harian?kelas_id=${kelasId}&tanggal=${tgl}${mkId ? `&mata_kuliah_id=${mkId}` : ""}`;
      const box = $("#classHarianResult");
      box.innerHTML = "<p class='empty'>Memuat...</p>";
      try {
        const r = await api(q);
        const hadir = r.data.filter(x => x.status === "hadir").length;
        box.innerHTML = `<p><b>${hadir}/${r.data.length}</b> hadir pada ${formatDate(r.tanggal)}${r.mata_kuliah ? ` · ${escHtml(r.mata_kuliah)}` : ""}</p>`
          + `<div class="report-actions"><button class="button outline btn-sm" id="dlHarianXls" type="button">Excel</button>`
          + `<button class="button outline btn-sm" id="dlHarianPdf" type="button">PDF</button></div>`
          + `<table><thead><tr><th>NIM</th><th>NAMA</th><th>STATUS</th><th>KETERANGAN</th></tr></thead><tbody>`
          + (r.data.map(x => `<tr><td>${escHtml(x.nim)}</td><td>${escHtml(x.nama_lengkap)}</td><td>${x.status ? badge(x.status) : "<span class='badge alfa'>Belum tercatat</span>"}</td><td>${escHtml(x.keterangan || "—")}</td></tr>`).join("") || "<tr><td colspan='4' class='empty'>Belum ada anggota.</td></tr>")
          + `</tbody></table>`;
        $("#dlHarianXls").onclick = () => unduhLaporan(`${q.replace("/laporan/harian", "/laporan/harian/ekspor-excel")}`, `harian_${tgl}.xlsx`);
        $("#dlHarianPdf").onclick = () => unduhLaporan(`${q.replace("/laporan/harian", "/laporan/harian/ekspor-pdf")}`, `harian_${tgl}.pdf`);
      } catch (err) { box.innerHTML = `<p class='empty'>${escHtml(err.message)}</p>`; }
    };
  }
  if (fB) {
    fB.bulan.innerHTML = pilihanBulan();
    fB.tahun.value = new Date().getFullYear();
    fB.mata_kuliah_id.innerHTML = opsi;
    fB.onsubmit = async (e) => {
      e.preventDefault();
      const q = `/laporan/rekap?kelas_id=${kelasId}&bulan=${fB.bulan.value}&tahun=${fB.tahun.value}${fB.mata_kuliah_id.value ? `&mata_kuliah_id=${fB.mata_kuliah_id.value}` : ""}`;
      const box = $("#classBulananResult");
      box.innerHTML = "<p class='empty'>Memuat...</p>";
      try {
        const r = await api(q);
        box.innerHTML = `<p><b>Rekap ${r.kelas}</b> · ${fB.bulan.value}/${fB.tahun.value}</p>`
          + `<div class="report-actions"><button class="button outline btn-sm" id="dlBulXls" type="button">Excel</button>`
          + `<button class="button outline btn-sm" id="dlBulPdf" type="button">PDF</button></div>`
          + `<table><thead><tr><th>NIM</th><th>NAMA</th><th>H</th><th>S</th><th>I</th><th>A</th><th>%</th></tr></thead><tbody>`
          + (r.data.map(x => `<tr><td>${escHtml(x.nim)}</td><td>${escHtml(x.nama_lengkap)}</td><td>${x.hadir}</td><td>${x.sakit}</td><td>${x.izin}</td><td>${x.alfa}</td><td>${x.persentase_hadir}%</td></tr>`).join("") || "<tr><td colspan='7' class='empty'>Belum ada anggota.</td></tr>")
          + `</tbody></table>`;
        $("#dlBulXls").onclick = () => unduhLaporan(`${q.replace("/laporan/rekap", "/laporan/ekspor-excel")}`, `rekap_${fB.bulan.value}_${fB.tahun.value}.xlsx`);
        $("#dlBulPdf").onclick = () => unduhLaporan(`${q.replace("/laporan/rekap", "/laporan/ekspor-pdf")}`, `rekap_${fB.bulan.value}_${fB.tahun.value}.pdf`);
      } catch (err) { box.innerHTML = `<p class='empty'>${escHtml(err.message)}</p>`; }
    };
  }
}

async function loadClassDetail(kelasId) {
  try {
    const d = await api(`/kelas/${kelasId}`);
    currentDetail = d;
    kelas = kelas.map(k => k.id === d.id ? {...k, nama_kelas: d.nama_kelas, nama_ketua_kelas: d.nama_ketua_kelas, tahun_ajaran: d.tahun_ajaran, angkatan: d.angkatan} : k);
    renderKelasSidebar();
    $("#currentClassName").textContent = `${d.nama_kelas} (Angkatan ${d.angkatan || '—'})`;
    $("#currentClassStats").textContent = `Total: ${d.total_anggota} Anggota (${d.total_mahasiswa} Mahasiswa, ${d.ketua_id ? 1 : 0} Ketua)`;
    const box = $("#classKetuaBox");
    if (box) {
      box.innerHTML = d.ketua_id
        ? `<div class="member-item ketua-card"><div class="grow"><b class="accent-username">@${escHtml(d.ketua_username || '')}</b><br><small>${escHtml(d.nama_ketua_kelas || '')}</small></div>`
          + `<div class="row-actions"><button class="button outline btn-sm" onclick="openEditKetuaModal(${d.ketua_id},'${escAttr(d.ketua_username || '')}',${d.id})">Edit</button> `
          + `<button class="button outline btn-sm btn-danger" onclick="hapusKetuaDariKelas(${d.ketua_id},'${escAttr(d.ketua_username || '')}')">Hapus</button></div></div>`
        : `<p class="empty">Belum ada akun ketua. <button class="button primary btn-sm" onclick="openTambahKetuaModal(${d.id},'${escAttr(d.nama_kelas)}')">+ Buat Akun Ketua</button></p>`;
    }
  } catch (e) {
    notify("Gagal memuat detail kelas: " + e.message, true);
  }
}

async function loadClassMatkul(kelasId) {
  try {
    const list = await api(`/mata-kuliah/?kelas_id=${kelasId}`);
    const container = $("#classMatkulList");
    if (!container) return;
    container.innerHTML = list.length === 0
      ? "<p class='empty tight'>Belum ada mata kuliah untuk kelas ini.</p>"
      : list.map(m => `
        <span class="chip">
          ${escHtml(m.kode)} - ${escHtml(m.nama)}
          <button type="button" onclick="hapusMatkulKelas(${m.id})" title="Hapus">×</button>
        </span>
      `).join("");
  } catch (e) {
    notify("Gagal load mata kuliah: " + e.message, true);
  }
}

async function hapusMatkulKelas(id) {
  if (!confirm("Hapus mata kuliah ini?")) return;
  try {
    await api(`/mata-kuliah/${id}`, {method: "DELETE"});
    notify("Mata kuliah dihapus.");
    await loadClassMatkul(currentSelectedClass.id);
  } catch (e) {
    notify(e.message, true);
  }
}

async function loadClassMembers(kelasId) {
  try {
    const [assigned, unassigned] = await Promise.all([
      api(`/mahasiswa?kelas_id=${kelasId}`),
      api(`/mahasiswa?tanpa_kelas=true`),
    ]);
    const ketuaAda = currentDetail ? (currentDetail.ketua_id ? 1 : 0) : (currentSelectedClass.nama_ketua_kelas ? 1 : 0);
    const stats = $("#currentClassStats");
    if (stats) stats.textContent = `Total: ${assigned.length + ketuaAda} Anggota (${assigned.length} Mahasiswa, ${ketuaAda} Ketua)`;
    const assignedContainer = $("#classMembersList");
    if (assignedContainer) {
      assignedContainer.innerHTML = assigned.length === 0
        ? "<p class='empty'>Belum ada mahasiswa di kelas ini.</p>"
        :       assigned.map(m => `
          <div class="member-item">
            <input type="checkbox" class="chk-assigned" value="${escAttr(m.nim)}">
            <div class="grow">
              <b>${escHtml(m.nama_lengkap)}</b><br>
              <small>NIM: ${escHtml(m.nim)} | Akun: ${m.user ? '@' + escHtml(m.user.username) : 'Belum Ada'}</small>
            </div>
            <button class="button outline btn-sm" onclick="openEditAnggotaModal('${escAttr(m.nim)}')">Edit</button>
          </div>
        `).join("");
    }
    const unassignedContainer = $("#unassignedMembersList");
    if (unassignedContainer) {
      unassignedContainer.innerHTML = unassigned.length === 0
        ? "<p class='empty'>Tidak ada mahasiswa tanpa kelas.</p>"
        : unassigned.map(m => `
          <div class="member-item">
            <input type="checkbox" class="chk-unassigned" value="${escAttr(m.nim)}">
            <div class="grow">
              <b>${escHtml(m.nama_lengkap)}</b><br>
              <small>NIM: ${escHtml(m.nim)}</small>
            </div>
          </div>
        `).join("");
    }
    const btnR = $("#btnRemoveSelected");
    if (btnR) btnR.onclick = () => removeMembers(kelasId);
    const btnA = $("#btnAddSelected");
    if (btnA) btnA.onclick = () => addMembers(kelasId);
  } catch (e) {
    notify("Gagal memuat anggota: " + e.message, true);
  }
}

async function addMembers(kelasId) {
  const selected = Array.from(document.querySelectorAll(".chk-unassigned:checked")).map(el => el.value);
  if (selected.length === 0) return notify("Pilih mahasiswa yang ingin dimasukkan.", true);
  try {
    await api(`/kelas/${kelasId}/anggota`, {method: "POST", body: JSON.stringify(selected)});
    notify("Berhasil menambahkan anggota.");
    await loadClassMembers(kelasId);
    await loadClassDetail(kelasId);
    await loadData();
  } catch (e) {
    notify(e.message, true);
  }
}

async function removeMembers(kelasId) {
  const selected = Array.from(document.querySelectorAll(".chk-assigned:checked")).map(el => el.value);
  if (selected.length === 0) return notify("Pilih anggota yang ingin dikeluarkan.", true);
  if (!confirm(`Keluarkan ${selected.length} mahasiswa dari kelas ini?`)) return;
  try {
    await api(`/kelas/${kelasId}/anggota`, {method: "DELETE", body: JSON.stringify(selected)});
    notify("Berhasil mengeluarkan anggota.");
    await loadClassMembers(kelasId);
    await loadClassDetail(kelasId);
    await loadData();
  } catch (e) {
    notify(e.message, true);
  }
}

async function hapusKetuaDariKelas(userId, username) {
  if (!confirm(`Hapus akun ketua @${username}?`)) return;
  try {
    await api(`/admin/ketua-kelas/${userId}`, {method: "DELETE"});
    notify("Akun ketua dihapus.");
    await loadKelasManager();
    if (currentSelectedClass) await selectKelas(currentSelectedClass.id);
  } catch (e) {
    notify(e.message, true);
  }
}
