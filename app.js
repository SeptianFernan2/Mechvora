"use strict";
/* ====================================================================
   SIPIL-APP — logika antarmuka (tanpa library luar, jalan offline)
   ==================================================================== */

// ---------- util ----------
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const nf = (n, d = 0) => Number(n || 0).toLocaleString("id-ID", { minimumFractionDigits: d, maximumFractionDigits: d });
const rp = n => "Rp " + nf(Math.round(Number(n) || 0));
const rpS = n => {   // singkat: 1,25 M / 350 jt
  n = Number(n) || 0; const a = Math.abs(n);
  if (a >= 1e12) return "Rp " + nf(n / 1e12, 2) + " T";
  if (a >= 1e9) return "Rp " + nf(n / 1e9, 2) + " M";
  if (a >= 1e6) return "Rp " + nf(n / 1e6, 1) + " jt";
  return rp(n);
};
const fmtDate = d => { if (!d) return "-"; const t = new Date(String(d).slice(0, 10) + "T00:00:00"); return isNaN(t) ? d : t.toLocaleDateString("id-ID", { day: "2-digit", month: "short", year: "numeric" }); };
const today = () => { const d = new Date(); d.setMinutes(d.getMinutes() - d.getTimezoneOffset()); return d.toISOString().slice(0, 10); };
const COLORS = ["var(--c1)", "var(--c2)", "var(--c3)", "var(--c4)", "var(--c5)", "var(--c6)"];

const ICON = {
  home: '<path d="M3 11l9-8 9 8v10a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1z"/>',
  folder: '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
  truck: '<path d="M2 17V6h11v11M13 10h5l3 4v3h-3"/><circle cx="7" cy="18" r="2"/><circle cx="17" cy="18" r="2"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  wrench: '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94z"/>',
  calc: '<rect x="4" y="2" width="16" height="20" rx="2"/><path d="M8 6h8M16 14v4M8 10h.01M12 10h.01M16 10h.01M8 14h.01M12 14h.01M8 18h.01M12 18h.01"/>',
  report: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M8 13h8M8 17h8"/>',
  sliders: '<path d="M4 6h10M18 6h2M4 12h4M12 12h8M4 18h12M20 18h0"/><circle cx="16" cy="6" r="2"/><circle cx="10" cy="12" r="2"/><circle cx="18" cy="18" r="2"/>',
  grid: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
  plus: '<path d="M12 5v14M5 12h14"/>', x: '<path d="M6 6l12 12M18 6L6 18"/>',
  moon: '<path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/>',
  download: '<path d="M12 3v12M7 10l5 5 5-5M5 21h14"/>',
  printer: '<path d="M6 9V3h12v6M6 18H4a1 1 0 0 1-1-1v-6a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v6a1 1 0 0 1-1 1h-2"/><rect x="6" y="14" width="12" height="7"/>',
};
const ico = n => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICON[n] || ""}</svg>`;
const LOGO = '<svg viewBox="0 0 64 64" aria-hidden="true"><path d="M8 46h30l10-14H33l-5-12H12z" fill="#1b2127"/><circle cx="19" cy="49" r="6" fill="#1b2127"/><circle cx="41" cy="49" r="6" fill="#F5B700"/><circle cx="41" cy="49" r="2.5" fill="#1b2127"/><circle cx="19" cy="49" r="2.5" fill="#F5B700"/></svg>';

// ---------- API ----------
async function api(path, method = "GET", body = null) {
  try {
    const res = await fetch("/api" + path, { method, headers: { "Content-Type": "application/json" }, body: body ? JSON.stringify(body) : undefined });
    const data = await res.json().catch(() => null);
    if (!res.ok) { toast((data && data.detail) || "Terjadi kesalahan (" + res.status + ")", true); return null; }
    return data;
  } catch (e) { toast("Tidak bisa terhubung ke server. Pastikan server masih berjalan.", true); return null; }
}
let toastT;
function toast(msg, err = false) {
  const t = $("#toast"); t.textContent = msg; t.className = "show" + (err ? " err" : "");
  clearTimeout(toastT); toastT = setTimeout(() => t.className = "", err ? 4500 : 2400);
}

// ---------- data bersama ----------
const S = { projects: [], equipment: [], settings: null, labels: null, catalog: null };
async function loadCommon(force = false) {
  const [p, e] = await Promise.all([api("/projects"), api("/equipment")]);
  S.projects = p || []; S.equipment = e || [];
  if (!S.settings || force) { const s = await api("/settings"); if (s) { S.settings = s.values; S.labels = s.labels; S.defaults = s.defaults; } }
  if (!S.catalog) S.catalog = await api("/catalog") || {};
}

// ---------- komponen kecil ----------
const STATUS_CLS = { Ready: "ok", Dipakai: "info", Maintenance: "warn", Rusak: "bad", Aktif: "ok", Selesai: "", Ditunda: "warn", Aman: "ok", Segera: "warn", Terlambat: "bad" };
const badge = s => `<span class="badge ${STATUS_CLS[s] ?? ""}">${esc(s)}</span>`;
const field = (label, input, hint = "", cls = "") => `<div class="field ${cls}"><label>${label}</label>${input}${hint ? `<div class="hint">${hint}</div>` : ""}</div>`;
const num = (name, val = "", ph = "", unit = "", extra = "") =>
  `<div class="input-unit"><input name="${name}" type="number" inputmode="decimal" step="any" value="${esc(val)}" placeholder="${esc(ph)}" ${extra}>${unit ? `<span>${unit}</span>` : ""}</div>`;
const options = (arr, sel, blank) => (blank !== undefined ? `<option value="">${blank}</option>` : "") + arr.map(([v, t]) => `<option value="${esc(v)}" ${String(v) === String(sel) ? "selected" : ""}>${esc(t)}</option>`).join("");
const eqOpts = sel => options(S.equipment.map(e => [e.id, `${e.code} — ${e.name}`]), sel);
const prOpts = (sel, blank) => options(S.projects.map(p => [p.id, p.name]), sel, blank);
const alertHtml = (level, title, text) => `<div class="alert ${level}"><span class="dot"></span><div>${title ? `<b>${esc(title)}</b>` : ""}${esc(text)}</div></div>`;
const empty = (cat, msg, btn = "") => `<div class="empty">${ART.svg(cat)}<p>${msg}</p>${btn}</div>`;
const barCls = p => p > 100 ? "bad" : p > 85 ? "warn" : "ok";

function donut(items, center) {
  const total = items.reduce((a, b) => a + Math.max(b.value, 0), 0);
  if (!total) return `<p class="muted small">Belum ada data biaya.</p>`;
  let off = 25, segs = "";
  items.forEach((it, i) => {
    const pct = Math.max(it.value, 0) / total * 100; if (pct <= 0) return;
    segs += `<circle cx="21" cy="21" r="15.9155" fill="none" stroke="${COLORS[i % 6]}" stroke-width="6" stroke-dasharray="${pct} ${100 - pct}" stroke-dashoffset="${off}"></circle>`;
    off -= pct;
  });
  const leg = items.map((it, i) => `<li><i style="background:${COLORS[i % 6]}"></i><span>${esc(it.label)}<br><small>${nf(it.value / total * 100, 1)}%</small></span><span class="v">${rpS(it.value)}</span></li>`).join("");
  return `<div class="donut-wrap"><svg class="donut" viewBox="0 0 42 42" role="img" aria-label="Komposisi biaya">
    <circle cx="21" cy="21" r="15.9155" fill="none" stroke="var(--surface2)" stroke-width="6"></circle>${segs}
    <text x="21" y="20" text-anchor="middle" font-size="3" font-weight="700">${esc(center || rpS(total))}</text>
    <text x="21" y="24.2" text-anchor="middle" font-size="2.2" opacity=".6">total</text></svg><ul class="legend">${leg}</ul></div>`;
}

// ---------- modal ----------
const modal = $("#modal");
function openModal(title, html, onMount) {
  $("#modalCard").innerHTML = `<div class="modal-head"><h3>${title}</h3><button class="icon-btn" data-close aria-label="Tutup">${ico("x")}</button></div>${html}`;
  modal.showModal(); if (onMount) onMount($("#modalCard"));
}
const closeModal = () => modal.open && modal.close();
modal.addEventListener("click", e => { if (e.target === modal || e.target.closest("[data-close]")) closeModal(); });

// ====================================================================
//  HALAMAN
// ====================================================================
const view = $("#view");

// ---------- DASHBOARD ----------
async function pgDashboard() {
  const d = await api("/dashboard"); if (!d) return;
  await loadCommon();
  const hero = `<div class="hero"><div class="hero-txt"><h2>Kelola alat berat,<br>kendalikan biaya proyek</h2>
      <p>Catat pemakaian, jadwalkan servis, dan analisa anggaran operasional alat dalam satu aplikasi.</p>
      <div class="actions"><a class="btn dark" href="#/analisa">${ico("calc")} Analisa Biaya</a><a class="btn ghost" href="#/pemakaian" style="background:rgba(255,255,255,.6)">${ico("clock")} Catat Pemakaian</a></div></div>${ART.hero()}</div>`;
  if (!d.total_equipment && !d.total_projects) {
    view.innerHTML = hero + `<div class="card">${empty("Excavator", "Belum ada data. Mulai dengan menambah proyek &amp; alat, atau muat data contoh untuk melihat cara kerja aplikasi.",
      `<div class="actions" style="justify-content:center"><button class="btn" id="seedBtn">Muat Data Contoh</button><a class="btn ghost" href="#/alat">Tambah Alat</a><a class="btn ghost" href="#/proyek">Tambah Proyek</a></div>`)}</div>`;
    $("#seedBtn").onclick = async () => { if (await api("/seed", "POST")) { toast("Data contoh dimuat"); pgDashboard(); } };
    return;
  }
  const pctAll = d.total_budget_active ? d.total_actual_active / d.total_budget_active * 100 : 0;
  const stats = `<div class="stats">
    <div class="stat accent"><div class="lbl">Proyek Aktif</div><div class="num">${d.active_projects}</div><div class="sub">dari ${d.total_projects} proyek</div></div>
    <div class="stat accent"><div class="lbl">Unit Alat Berat</div><div class="num">${d.total_equipment}</div><div class="sub">${d.equipment_status.Dipakai || 0} dipakai · ${d.equipment_status.Ready || 0} ready</div></div>
    <div class="stat accent"><div class="lbl">Dalam Maintenance</div><div class="num">${d.equipment_maintenance}</div><div class="sub">${d.alerts.length} peringatan servis</div></div>
    <div class="stat accent"><div class="lbl">Realisasi (Proyek Aktif)</div><div class="num ${pctAll > 100 ? "bad" : ""}">${rpS(d.total_actual_active)}</div><div class="sub">${nf(pctAll, 1)}% dari ${rpS(d.total_budget_active)}</div></div></div>`;

  const comp = Object.entries(d.composition).map(([label, value]) => ({ label, value }));
  const alerts = d.alerts.length ? d.alerts.map(a => alertHtml(a.level, `${a.equipment} · ${a.name}`, a.text)).join("") : alertHtml("ok", "Semua alat aman", "Tidak ada servis yang jatuh tempo dalam waktu dekat.");
  const projs = d.projects.length ? d.projects.map(p => `<div class="proj-row"><div class="top"><a href="#/laporan/${p.id}"><strong>${esc(p.name)}</strong></a>${badge(p.status)}</div>
      <div class="bar ${barCls(p.pct)}"><i style="width:${Math.min(p.pct, 100)}%"></i></div>
      <div class="small muted" style="margin-top:4px">${rpS(p.actual)} dari ${rpS(p.budget)} · <b>${nf(p.pct, 1)}%</b></div></div>`).join("") : `<p class="muted">Belum ada proyek.</p>`;
  const fleet = d.equipment.map(e => fleetMini(e)).join("");
  view.innerHTML = hero + stats + `
    <div class="grid g-main"><div class="card"><h3>Komposisi Biaya Operasional</h3>${donut(comp)}</div>
    <div class="card"><h3>Peringatan Servis</h3>${alerts}</div></div>
    <div class="card" style="margin-top:16px"><h3>Anggaran vs Realisasi per Proyek</h3>${projs}</div>
    <div class="card"><h3>Armada <a class="btn ghost sm" href="#/alat">Kelola</a></h3><div class="fleet">${fleet}</div></div>`;
}
function fleetMini(e) {
  const sv = e.service, interval = (S.catalog[e.category] || {}).interval || 250;
  const used = Math.max(0, Math.min(100, (1 - sv.sisa_hm / interval) * 100));
  const cls = sv.status === "Terlambat" ? "bad" : sv.status === "Segera" ? "warn" : "ok";
  return `<div class="eq-card"><div class="eq-art">${ART.svg(e.category)}${badge(e.status)}</div><div class="eq-body">
    <span class="eq-code">${esc(e.code)}</span><h4>${esc(e.name)}</h4>
    <div class="eq-meta"><span>${nf(e.hm)} HM</span><span>${rpS(e.cost_hour)}/jam</span></div>
    <div class="bar ${cls}" title="Menuju servis berikutnya"><i style="width:${used}%"></i></div>
    <div class="small muted">${badge(sv.status)} ${sv.sisa_hm > 0 ? "servis " + nf(sv.sisa_hm) + " HM lagi" : "lewat " + nf(-sv.sisa_hm) + " HM"}</div></div></div>`;
}

// ---------- PROYEK ----------
async function pgProyek() {
  await loadCommon();
  const list = S.projects.map(p => {
    const pct = p.persentase_terpakai || 0;
    return `<div class="card proj-card"><div class="card-h"><h3>${esc(p.name)}</h3>${badge(p.status)}</div>
      <div class="meta"><span>📍 ${esc(p.location || "-")}</span><span>${fmtDate(p.start_date)} → ${fmtDate(p.end_date)}</span>${p.volume_target ? `<span>Target ${nf(p.volume_target)} m³</span>` : ""}</div>
      <div><div class="bar ${barCls(pct)}"><i style="width:${Math.min(pct, 100)}%"></i></div>
      <div class="small" style="margin-top:5px"><b>${rp(p.actual_cost)}</b> <span class="muted">dari anggaran ${rp(p.budget)} (${nf(pct, 1)}%)</span></div></div>
      <div class="actions"><a class="btn sm" href="#/laporan/${p.id}">${ico("report")} Laporan</a><a class="btn ghost sm" href="#/analisa/${p.id}">${ico("calc")} Analisa</a>
      <button class="btn ghost sm" data-edit="${p.id}">Edit</button><button class="btn danger sm" data-del="${p.id}">Hapus</button></div></div>`;
  }).join("");
  view.innerHTML = `<div class="page-head"><div><h2>Proyek</h2><p>Anggaran dan jadwal tiap pekerjaan</p></div><div class="actions"><button class="btn" id="addP">${ico("plus")} Tambah Proyek</button></div></div>
    <div class="grid g2">${list || ""}</div>${S.projects.length ? "" : `<div class="card">${empty("Bulldozer", "Belum ada proyek.")}</div>`}`;
  $("#addP").onclick = () => projectForm();
  $$("[data-edit]").forEach(b => b.onclick = () => projectForm(S.projects.find(p => p.id == b.dataset.edit)));
  $$("[data-del]").forEach(b => b.onclick = async () => {
    if (!confirm("Hapus proyek ini beserta seluruh catatan pemakaiannya?")) return;
    if (await api("/projects/" + b.dataset.del, "DELETE")) { toast("Proyek dihapus"); pgProyek(); }
  });
}
function projectForm(p = null) {
  p = p || {};
  openModal(p.id ? "Edit Proyek" : "Tambah Proyek", `<form class="form" id="fP">
    ${field("Nama proyek *", `<input name="name" required value="${esc(p.name)}" placeholder="Pembangunan Jalan ...">`, "", "full")}
    ${field("Lokasi", `<input name="location" value="${esc(p.location)}">`, "", "full")}
    ${field("Tanggal mulai", `<input type="date" name="start_date" value="${esc((p.start_date || "").slice(0, 10))}">`)}
    ${field("Tanggal selesai", `<input type="date" name="end_date" value="${esc((p.end_date || "").slice(0, 10))}">`)}
    ${field("Anggaran alat berat", num("budget", p.budget || "", "0", "Rp"), "Anggaran khusus biaya operasional alat")}
    ${field("Target volume", num("volume_target", p.volume_target || "", "0", "m³"))}
    ${field("Status", `<select name="status">${options(["Aktif", "Ditunda", "Selesai"].map(x => [x, x]), p.status || "Aktif")}</select>`)}
    <div class="full form-actions"><button class="btn">Simpan</button><button type="button" class="btn ghost" data-close>Batal</button></div></form>`,
    c => $("#fP", c).onsubmit = async e => {
      e.preventDefault();
      const r = await api(p.id ? "/projects/" + p.id : "/projects", p.id ? "PUT" : "POST", Object.fromEntries(new FormData(e.target)));
      if (r) { closeModal(); toast("Proyek tersimpan"); pgProyek(); }
    });
}

// ---------- ALAT BERAT ----------
let eqFilter = "Semua";
async function pgAlat() {
  await loadCommon();
  const cats = ["Semua", ...ART.categories];
  const items = S.equipment.filter(e => eqFilter === "Semua" || e.category === eqFilter);
  const cards = items.map(e => {
    const sv = e.service;
    return `<div class="eq-card"><div class="eq-art">${ART.svg(e.category)}${badge(e.status)}</div><div class="eq-body">
      <span class="eq-code">${esc(e.code)}</span><h4>${esc(e.name)}</h4>
      <div class="small muted">${esc([e.brand, e.year, e.category].filter(Boolean).join(" · "))}</div>
      <div class="eq-meta"><span>${nf(e.hm_total)} HM</span><span>${rpS(e.cost_hour)}/jam</span></div>
      <div class="small">Servis: ${badge(sv.status)}</div>
      <div class="eq-actions"><button class="btn sm" data-card="${e.id}">Rincian Biaya</button><button class="btn ghost sm" data-edit="${e.id}">Edit</button><button class="btn danger sm" data-del="${e.id}">Hapus</button></div></div></div>`;
  }).join("");
  view.innerHTML = `<div class="page-head"><div><h2>Alat Berat</h2><p>Data armada, biaya per jam, dan status</p></div><div class="actions"><button class="btn" id="addE">${ico("plus")} Tambah Alat</button></div></div>
    <div class="chip-row" style="margin-bottom:14px">${cats.map(c => `<button class="chip ${c === eqFilter ? "on" : ""}" data-f="${c}">${c}</button>`).join("")}</div>
    ${items.length ? `<div class="fleet">${cards}</div>` : `<div class="card">${empty("Excavator", "Belum ada alat" + (eqFilter !== "Semua" ? " pada kategori ini" : "") + ".")}</div>`}`;
  $("#addE").onclick = () => equipmentForm();
  $$("[data-f]").forEach(b => b.onclick = () => { eqFilter = b.dataset.f; pgAlat(); });
  $$("[data-edit]").forEach(b => b.onclick = () => equipmentForm(S.equipment.find(e => e.id == b.dataset.edit)));
  $$("[data-card]").forEach(b => b.onclick = () => costCardModal(b.dataset.card));
  $$("[data-del]").forEach(b => b.onclick = async () => {
    if (!confirm("Hapus alat ini beserta riwayat pemakaian dan maintenance-nya?")) return;
    if (await api("/equipment/" + b.dataset.del, "DELETE")) { toast("Alat dihapus"); pgAlat(); }
  });
}
function equipmentForm(e = null) {
  e = e || {};
  let cat = e.category || "Excavator";
  const cd = c => S.catalog[c] || S.catalog.Lainnya;
  openModal(e.id ? "Edit Alat" : "Tambah Alat Berat", `<form class="form" id="fE">
    <div class="full field"><label>Kategori alat</label><input type="hidden" name="category" value="${esc(cat)}">
      <div class="pick" id="pickCat">${ART.categories.map(c => `<button type="button" data-c="${c}" class="${c === cat ? "on" : ""}">${ART.svg(c)}<span>${c}</span></button>`).join("")}</div></div>
    ${field("Kode alat *", `<input name="code" required value="${esc(e.code)}" placeholder="EXC-01">`)}
    ${field("Nama / tipe *", `<input name="name" required value="${esc(e.name)}" placeholder="Komatsu PC200-8">`)}
    ${field("Merek", `<input name="brand" value="${esc(e.brand)}">`)}
    ${field("Tahun", num("year", e.year || "", "2022"))}
    ${field("Harga beli (B)", num("purchase_price", e.purchase_price || "", "", "Rp"), `<span id="hPrice"></span>`)}
    ${field("Daya mesin (HP)", num("engine_hp", e.engine_hp || "", "", "HP"), `<span id="hHp"></span>`)}
    ${field("Umur ekonomis (A)", num("life_years", e.life_years || "", "", "tahun"), `<span id="hLife"></span>`)}
    ${field("Nilai sisa", num("salvage_pct", e.salvage_pct || "", "", "%"), "Kosong = pakai pengaturan umum")}
    ${field(`<span id="capLbl"></span>`, num("capacity", e.capacity || "", ""), "Dipakai untuk hitung produktivitas")}
    ${field("HM awal (hour meter)", num("initial_hm", e.initial_hm || 0, "0", "HM"), "Angka HM saat alat mulai dicatat")}
    ${field("Interval servis", num("service_interval", e.service_interval || 250, "250", "HM"))}
    ${field("Status", `<select name="status">${options(["Ready", "Dipakai", "Maintenance", "Rusak"].map(x => [x, x]), e.status || "Ready")}</select>`)}
    <div class="full form-actions"><button class="btn">Simpan</button><button type="button" class="btn ghost" data-close>Batal</button></div></form>`,
    c => {
      const upd = () => {
        const k = cd(cat); $("[name=category]", c).value = cat;
        $("#capLbl", c).textContent = k.kap_label;
        $("[name=purchase_price]", c).placeholder = nf(k.harga); $("[name=engine_hp]", c).placeholder = k.hp; $("[name=life_years]", c).placeholder = k.umur;
        $("#hPrice", c).textContent = "Kosong = acuan " + rpS(k.harga); $("#hHp", c).textContent = "Kosong = acuan " + k.hp + " HP"; $("#hLife", c).textContent = "Kosong = acuan " + k.umur + " tahun";
        $("[name=capacity]", c).placeholder = k.kapasitas || "";
        $$("#pickCat button", c).forEach(b => b.classList.toggle("on", b.dataset.c === cat));
      };
      upd();
      $$("#pickCat button", c).forEach(b => b.onclick = () => { cat = b.dataset.c; upd(); });
      $("#fE", c).onsubmit = async ev => {
        ev.preventDefault();
        const r = await api(e.id ? "/equipment/" + e.id : "/equipment", e.id ? "PUT" : "POST", Object.fromEntries(new FormData(ev.target)));
        if (r) { closeModal(); toast("Alat tersimpan"); pgAlat(); }
      };
    });
}
async function costCardModal(id) {
  const r = await api(`/equipment/${id}/costcard`); if (!r) return;
  const e = r.equipment;
  openModal(`Kartu Biaya — ${esc(e.code)}`, `<p class="muted small" style="margin-bottom:10px">${esc(e.name)} · biaya alat per jam kerja (rupiah/jam)</p>${costCard(r.cost, r.settings)}`);
}

// kartu biaya alat per jam (rumus + angka) — dipakai di Alat & Analisa
function costCard(c, s, solar) {
  const ms = solar || s.harga_solar;
  const row = (k, f, v, cls = "") => `<tr class="${cls}"><td><b>${k}</b></td><td class="step">${f}</td><td class="num">${rp(v)}</td></tr>`;
  const head = t => `<tr class="total-row"><td colspan="3">${t}</td></tr>`;
  return `<div class="table-wrap"><table><thead><tr><th>Komponen</th><th>Perhitungan</th><th class="num">Rp/jam</th></tr></thead><tbody>
    ${head("Data dasar")}
    <tr class="sub-row"><td>B</td><td colspan="2">Harga alat ${rp(c.B)} · nilai sisa C = ${nf(s.nilai_sisa, 1)}% × B = ${rp(c.C)} · A = ${c.A} th · W = ${nf(c.W)} jam/th · i = ${nf(c.i * 100, 1)}%</td></tr>
    <tr class="sub-row"><td>D</td><td colspan="2" class="step">Faktor angsuran = i(1+i)^A / ((1+i)^A − 1) = <b>${c.D.toFixed(4)}</b></td></tr>
    ${head("I. Biaya pasti")}
    ${row("E", "(B − C) × D / W — pengembalian modal", c.E)}
    ${row("F", `${nf(s.asuransi, 2)}% × B / W — asuransi &amp; pajak`, c.F)}
    ${row("G", "E + F", c.biaya_pasti, "total-row")}
    ${head("II. Biaya operasi")}
    ${row("H", `BBM: ${nf(s.koef_bbm, 1)}% × ${c.HP} HP = ${nf(c.liter_bbm_jam, 2)} L/jam × ${rp(ms)}`, c.H_bbm)}
    ${row("I", `Pelumas: ${nf(s.koef_pelumas, 2)}% × ${c.HP} HP = ${nf(c.liter_pelumas_jam, 2)} L/jam × ${rp(s.harga_pelumas)}`, c.I_pelumas)}
    ${row("K", `Perawatan: ${nf(s.koef_perawatan, 1)}% × B / W`, c.K_perawatan)}
    ${row("L", "Upah operator", c.L_operator)}${row("M", "Upah pembantu operator", c.M_pembantu)}
    ${row("P", "H + I + K + L + M", c.biaya_operasi, "total-row")}
    </tbody><tfoot><tr><td><b>Biaya alat</b></td><td class="step">G + P</td><td class="num">${rp(c.total)}</td></tr>
    <tr><td><b>Tarif sewa</b></td><td class="step">Biaya alat + overhead &amp; profit ${nf(s.overhead_profit, 1)}%</td><td class="num">${rp(c.tarif_sewa)}</td></tr></tfoot></table></div>`;
}

// ---------- PEMAKAIAN ----------
let usageProj = "";
async function pgPemakaian() {
  await loadCommon();
  const rows = await api("/usage" + (usageProj ? "?project_id=" + usageProj : "")) || [];
  const eq = Object.fromEntries(S.equipment.map(e => [e.id, e])), pr = Object.fromEntries(S.projects.map(p => [p.id, p]));
  const body = rows.map(u => {
    const lph = u.work_hours ? u.fuel_liters / u.work_hours : 0, prod = u.work_hours ? u.volume_m3 / u.work_hours : 0;
    return `<tr><td data-l="Tanggal">${fmtDate(u.date)}</td><td data-l="Alat"><b>${esc((eq[u.equipment_id] || {}).code || u.equipment_id)}</b></td>
      <td data-l="Proyek">${esc((pr[u.project_id] || {}).name || u.project_id)}</td><td class="num" data-l="HM">${nf(u.work_hours, 1)}</td>
      <td class="num" data-l="Solar (L)">${nf(u.fuel_liters, 1)} <span class="muted small">(${nf(lph, 1)}/jam)</span></td><td class="num" data-l="Biaya solar">${rp(u.fuel_liters * u.fuel_price)}</td>
      <td class="num" data-l="Volume">${u.volume_m3 ? nf(u.volume_m3) + " m³ <span class='muted small'>(" + nf(prod) + "/jam)</span>" : "-"}</td><td data-l="Operator">${esc(u.operator_name || "-")}</td>
      <td class="act"><button class="btn danger sm" data-del="${u.id}">Hapus</button></td></tr>`;
  }).join("");
  view.innerHTML = `<div class="page-head"><div><h2>Pemakaian Harian</h2><p>Jam kerja (HM), solar, dan hasil pekerjaan tiap alat</p></div>
    <div class="actions"><select id="fProj" style="width:auto;min-width:180px">${prOpts(usageProj, "Semua proyek")}</select><button class="btn" id="addU">${ico("plus")} Catat</button></div></div>
    <div class="card">${rows.length ? `<div class="table-wrap"><table class="stack"><thead><tr><th>Tanggal</th><th>Alat</th><th>Proyek</th><th class="num">HM</th><th class="num">Solar</th><th class="num">Biaya solar</th><th class="num">Volume</th><th>Operator</th><th></th></tr></thead><tbody>${body}</tbody></table></div>`
      : empty("Dump Truck", "Belum ada catatan pemakaian.")}</div>`;
  $("#fProj").onchange = e => { usageProj = e.target.value; pgPemakaian(); };
  $("#addU").onclick = usageForm;
  $$("[data-del]").forEach(b => b.onclick = async () => { if (confirm("Hapus catatan ini?") && await api("/usage/" + b.dataset.del, "DELETE")) pgPemakaian(); });
}
function usageForm() {
  if (!S.equipment.length || !S.projects.length) { toast("Tambahkan minimal 1 alat dan 1 proyek terlebih dahulu", true); return; }
  openModal("Catat Pemakaian Alat", `<form class="form" id="fU">
    ${field("Alat *", `<select name="equipment_id">${eqOpts()}</select>`, "", "wide")}
    ${field("Proyek *", `<select name="project_id">${prOpts(usageProj)}</select>`, "", "wide")}
    ${field("Tanggal", `<input type="date" name="date" value="${today()}">`)}
    ${field("Jam kerja", num("work_hours", "", "0", "HM", "step=0.5 required"))}
    ${field("Solar terpakai", num("fuel_liters", "", "0", "liter"))}
    ${field("Harga solar", num("fuel_price", S.settings.harga_solar, "", "Rp/L"))}
    ${field("Volume hasil", num("volume_m3", "", "0", "m³"), "Opsional — untuk hitung Rp/m³")}
    ${field("Operator", `<input name="operator_name">`)}
    <div class="full" id="uPrev"></div>
    <div class="full form-actions"><button class="btn">Simpan</button><button type="button" class="btn ghost" data-close>Batal</button></div></form>`,
    c => {
      const f = $("#fU", c), v = n => parseFloat(f.elements[n].value) || 0;
      const prev = () => {
        const e = S.equipment.find(x => x.id == f.elements.equipment_id.value), h = v("work_hours"), l = v("fuel_liters");
        if (!h) { $("#uPrev", c).innerHTML = ""; return; }
        const exp = e ? e.hp_eff * (S.settings.koef_bbm / 100) : 0, lph = l / h;
        let html = `<div class="alert info"><span class="dot"></span><div>Biaya solar <b>${rp(l * v("fuel_price"))}</b> · konsumsi <b>${nf(lph, 1)} L/jam</b>${exp ? ` (acuan ±${nf(exp, 1)} L/jam)` : ""}${v("volume_m3") ? ` · produktivitas <b>${nf(v("volume_m3") / h)} m³/jam</b>` : ""}</div></div>`;
        if (exp && l && lph > exp * 1.3) html += alertHtml("warn", "Konsumsi tinggi", "Pemakaian solar lebih dari 30% di atas acuan. Periksa kondisi mesin atau pencatatan.");
        $("#uPrev", c).innerHTML = html;
      };
      f.addEventListener("input", prev);
      f.onsubmit = async ev => { ev.preventDefault(); if (await api("/usage", "POST", Object.fromEntries(new FormData(f)))) { closeModal(); toast("Pemakaian tersimpan"); pgPemakaian(); } };
    });
}

// ---------- MAINTENANCE ----------
async function pgMaintenance() {
  await loadCommon();
  const rows = await api("/maintenance") || [];
  const eq = Object.fromEntries(S.equipment.map(e => [e.id, e]));
  const sched = S.equipment.map(e => {
    const sv = e.service;
    return `<tr><td data-l="Alat"><b>${esc(e.code)}</b> <span class="muted small">${esc(e.name)}</span></td><td data-l="Status">${badge(e.status)}</td>
      <td class="num" data-l="HM sekarang">${nf(e.hm_total)}</td><td class="num" data-l="Jatuh tempo">${nf(sv.next_due_hm)}${sv.estimated ? " <span class='muted small'>(perk.)</span>" : ""}</td>
      <td class="num" data-l="Sisa HM">${nf(sv.sisa_hm)}</td><td data-l="Servis">${badge(sv.status)}</td>
      <td class="act"><button class="btn sm" data-svc="${e.id}">Catat Servis</button>${e.status === "Maintenance" ? ` <button class="btn ghost sm" data-ready="${e.id}">Selesai → Ready</button>` : ""}</td></tr>`;
  }).join("");
  const hist = rows.map(m => {
    const tot = m.sparepart_cost + m.labor_cost + m.other_cost;
    return `<tr><td data-l="Tanggal">${fmtDate(m.date)}</td><td data-l="Alat"><b>${esc((eq[m.equipment_id] || {}).code || m.equipment_id)}</b></td><td data-l="Jenis">${esc(m.mtype)}</td>
      <td data-l="Pekerjaan">${esc(m.description || "-")}</td><td class="num" data-l="Sparepart">${rp(m.sparepart_cost)}</td><td class="num" data-l="Jasa">${rp(m.labor_cost)}</td>
      <td class="num" data-l="Lain">${rp(m.other_cost)}</td><td class="num" data-l="Total"><b>${rp(tot)}</b></td><td class="act"><button class="btn danger sm" data-del="${m.id}">Hapus</button></td></tr>`;
  }).join("");
  view.innerHTML = `<div class="page-head"><div><h2>Maintenance</h2><p>Jadwal servis berkala berdasarkan hour meter (HM) dan riwayat biaya perawatan</p></div>
    <div class="actions"><button class="btn" id="addM">${ico("plus")} Catat Servis</button></div></div>
    <div class="card"><h3>Jadwal Servis Berkala</h3>${S.equipment.length ? `<div class="table-wrap"><table class="stack"><thead><tr><th>Alat</th><th>Status</th><th class="num">HM sekarang</th><th class="num">Jatuh tempo</th><th class="num">Sisa HM</th><th>Servis</th><th></th></tr></thead><tbody>${sched}</tbody></table></div>` : empty("Excavator", "Belum ada alat.")}</div>
    <div class="card"><h3>Riwayat Maintenance</h3>${rows.length ? `<div class="table-wrap"><table class="stack"><thead><tr><th>Tanggal</th><th>Alat</th><th>Jenis</th><th>Pekerjaan</th><th class="num">Sparepart</th><th class="num">Jasa</th><th class="num">Lain</th><th class="num">Total</th><th></th></tr></thead><tbody>${hist}</tbody></table></div>` : `<p class="muted">Belum ada riwayat.</p>`}</div>`;
  $("#addM").onclick = () => maintForm();
  $$("[data-svc]").forEach(b => b.onclick = () => maintForm(b.dataset.svc));
  $$("[data-ready]").forEach(b => b.onclick = async () => { if (await api(`/equipment/${b.dataset.ready}/status`, "PUT", { status: "Ready" })) { toast("Alat kembali Ready"); pgMaintenance(); } });
  $$("[data-del]").forEach(b => b.onclick = async () => { if (confirm("Hapus catatan ini?") && await api("/maintenance/" + b.dataset.del, "DELETE")) pgMaintenance(); });
}
function maintForm(eid = "") {
  if (!S.equipment.length) { toast("Tambahkan alat terlebih dahulu", true); return; }
  openModal("Catat Servis / Perbaikan", `<form class="form" id="fM">
    ${field("Alat *", `<select name="equipment_id">${eqOpts(eid)}</select>`, "", "wide")}
    ${field("Proyek (opsional)", `<select name="project_id">${prOpts("", "— Tidak terkait proyek —")}</select>`, "Biaya dibebankan ke proyek ini", "wide")}
    ${field("Tanggal", `<input type="date" name="date" value="${today()}">`)}
    ${field("Jenis", `<select name="mtype">${options(["Preventif", "Korektif", "Inspeksi", "Overhaul"].map(x => [x, x]))}</select>`)}
    ${field("HM saat servis", num("hm_at_service", "", "", "HM"), "Kosong = HM sekarang")}
    ${field("HM servis berikutnya", num("next_due_hours", "", "", "HM"), "Kosong = HM + interval")}
    ${field("Deskripsi pekerjaan", `<input name="description" placeholder="Ganti oli mesin, filter, ...">`, "", "full")}
    ${field("Biaya sparepart", num("sparepart_cost", "", "0", "Rp"))}${field("Biaya jasa", num("labor_cost", "", "0", "Rp"))}${field("Biaya lain", num("other_cost", "", "0", "Rp"))}
    <label class="full" style="display:flex;gap:10px;align-items:center;min-height:44px"><input type="checkbox" name="set_ready" style="width:22px;min-height:22px"> Servis selesai — langsung set alat ke <b>Ready</b></label>
    <div class="full form-actions"><button class="btn">Simpan</button><button type="button" class="btn ghost" data-close>Batal</button></div></form>`,
    c => $("#fM", c).onsubmit = async ev => {
      ev.preventDefault();
      const o = Object.fromEntries(new FormData(ev.target)); o.set_ready = !!o.set_ready;
      if (await api("/maintenance", "POST", o)) { closeModal(); toast("Servis tercatat"); pgMaintenance(); }
    });
}

// ---------- ANALISA / KONSULTASI ----------
const AN = { category: "Excavator", equipment_id: "", project_id: "", volume: "20000", hours: "", work_days: "30", hours_per_day: "8", units: "", solar_price: "", mobdemob: "", budget: "", market_rent: "", price: "", hp: "", life_years: "", params: {} };
async function pgAnalisa(arg) {
  await loadCommon();
  if (arg && S.projects.find(p => p.id == arg)) AN.project_id = arg;
  view.innerHTML = `<div class="page-head"><div><h2>Analisa Biaya Operasional</h2><p>Konsultasi anggaran: hitung produktivitas, jumlah unit, biaya per m³, dan risikonya sebelum alat dikerahkan</p></div></div>
    <div class="an-layout"><div class="card" id="anForm"></div><div id="anOut"><div class="card">${empty("Excavator", "Isi data di samping lalu tekan <b>Hitung &amp; Analisa</b>.")}</div></div></div>`;
  drawAnForm();
}
function drawAnForm() {
  const eq = S.equipment.find(e => e.id == AN.equipment_id);
  const category = eq ? eq.category : AN.category;
  const k = S.catalog[category] || S.catalog.Lainnya;
  const pv = (key, def) => AN.params[key] !== undefined && AN.params[key] !== "" ? AN.params[key] : def;
  const cap = eq && eq.capacity ? eq.capacity : null;
  const params = k.params.map(p => field(`${p.label}`, num("p_" + p.key, pv(p.key, p.from_cap && cap ? cap : p.default), "", p.unit))).join("");
  $("#anForm").innerHTML = `<form class="form" id="fA" style="grid-template-columns:1fr 1fr">
    ${field("Alat dari armada", `<select name="equipment_id" id="aEq">${eqOpts(AN.equipment_id).replace(/^/, `<option value="">— Alat baru / belum dimiliki —</option>`)}</select>`, "", "full")}
    ${eq ? "" : `<div class="field full"><label>Jenis alat</label><input type="hidden" name="category" value="${esc(category)}"><div class="pick" id="aCat">${ART.categories.filter(c => c !== "Lainnya").map(c => `<button type="button" data-c="${c}" class="${c === category ? "on" : ""}">${ART.svg(c)}<span>${c}</span></button>`).join("")}</div></div>`}
    ${field("Untuk proyek", `<select name="project_id">${prOpts(AN.project_id, "— Tanpa proyek —")}</select>`, "Jika dipilih, hasil dibandingkan dengan sisa anggaran proyek", "full")}
    ${field("Volume pekerjaan", num("volume", AN.volume, "mis. 20000", "m³"), "Atau isi jam alat di bawah")}
    ${field("atau Jam alat", num("hours", AN.hours, "", "jam"))}
    ${field("Batas waktu", num("work_days", AN.work_days, "", "hari"), "Untuk hitung jumlah unit")}
    ${field("Jam kerja / hari", num("hours_per_day", AN.hours_per_day, "8", "jam"))}
    ${field("Jumlah unit", num("units", AN.units, "otomatis", "unit"), "Kosong = dihitung otomatis")}
    ${field("Harga solar", num("solar_price", AN.solar_price, nf(S.settings.harga_solar), "Rp/L"))}
    ${field("Anggaran alat ini", num("budget", AN.budget, "opsional", "Rp"))}
    ${field("Mob/demob per unit", num("mobdemob", AN.mobdemob, "0", "Rp"))}
    ${field("Tarif sewa pasar", num("market_rent", AN.market_rent, "opsional", "Rp/jam"), "Pembanding milik vs sewa", "full")}
    ${k.params.length ? `<details class="more full" open><summary>Parameter produktivitas — ${esc(category)}</summary><div class="form" style="grid-template-columns:1fr 1fr">${params}</div><p class="small muted" style="padding-bottom:10px">Ubah sesuai kondisi lapangan (jenis tanah, jarak, efisiensi).</p></details>` : ""}
    ${eq ? "" : `<details class="more full"><summary>Data alat baru (opsional)</summary><div class="form" style="grid-template-columns:1fr 1fr">
      ${field("Harga alat", num("price", AN.price, nf(k.harga), "Rp"))}${field("Daya mesin", num("hp", AN.hp, k.hp, "HP"))}${field("Umur ekonomis", num("life_years", AN.life_years, k.umur, "th"))}</div></details>`}
    <div class="full form-actions"><button class="btn" style="flex:1">${ico("calc")} Hitung &amp; Analisa</button></div></form>`;
  const f = $("#fA");
  const save = () => {
    const o = Object.fromEntries(new FormData(f));
    Object.keys(AN).forEach(key => { if (key !== "params" && o[key] !== undefined) AN[key] = o[key]; });
    Object.keys(o).forEach(key => { if (key.startsWith("p_")) AN.params[key.slice(2)] = o[key]; });
  };
  f.addEventListener("input", save);
  $("#aEq").onchange = e => { save(); AN.equipment_id = e.target.value; AN.params = {}; const q = S.equipment.find(x => x.id == AN.equipment_id); if (q) AN.category = q.category; drawAnForm(); };
  $$("#aCat button").forEach(b => b.onclick = () => { save(); AN.category = b.dataset.c; AN.params = {}; drawAnForm(); });
  f.onsubmit = async ev => {
    ev.preventDefault(); save();
    const o = { ...AN, category, params: Object.fromEntries(Object.entries(AN.params).filter(([, v]) => v !== "")) };
    $("#anOut").innerHTML = `<div class="loader">Menghitung…</div>`;
    const r = await api("/analyze", "POST", o);
    if (!r) { $("#anOut").innerHTML = `<div class="card">${empty(category, "Perhitungan gagal. Periksa isian lalu coba lagi.")}</div>`; return; }
    renderAnalysis(r);
    if (window.innerWidth < 1100) $("#anOut").scrollIntoView({ behavior: "smooth", block: "start" });
  };
}
function renderAnalysis(r) {
  const k = S.catalog[r.category] || {};
  const title = r.equipment ? `${esc(r.equipment.code)} — ${esc(r.equipment.name)}` : esc(r.category);
  const kpi = (l, v, u = "", hl = "") => `<div class="kpi ${hl}"><div class="lbl">${l}</div><div class="v">${v}</div><div class="u">${u}</div></div>`;
  const br = Object.entries(r.breakdown).map(([label, value]) => ({ label, value }));
  const maxS = Math.max(...r.sensitivity.map(s => s.total));
  const sens = r.sensitivity.map((s, i) => `<div class="r"><span class="t">${esc(s.label)}</span><div class="track"><i class="${i === 0 ? "base" : s.delta_pct > 0 ? "up" : "down"}" style="width:${s.total / maxS * 100}%"></i></div><span class="mono small"><b>${rpS(s.total)}</b>${i ? ` <span class="${s.delta_pct > 0 ? "" : ""} muted">(${s.delta_pct > 0 ? "+" : ""}${nf(s.delta_pct, 1)}%)</span>` : ""}</span></div>`).join("");
  const o = r.own_vs_rent;
  const b = r.budget;
  const paramRows = (k.params || []).map(p => `<tr><td>${esc(p.key)}</td><td>${esc(p.label)}</td><td class="num">${nf(r.params[p.key], 2)} ${esc(p.unit)}</td></tr>`).join("");
  $("#anOut").innerHTML = `
    <div class="card"><div class="card-h"><h3>Hasil Analisa · ${title}</h3><div class="actions no-print"><button class="btn ghost sm" onclick="window.print()">${ico("printer")} Cetak / PDF</button></div></div>
      ${r.project ? `<p class="small muted" style="margin-bottom:10px">Proyek: <b>${esc(r.project.name)}</b> · sisa anggaran alat ${rp(r.project.sisa)}</p>` : ""}
      <div class="kpis">
        ${r.productivity ? kpi("Produktivitas", nf(r.productivity, 1), "m³ per jam") : ""}
        ${kpi("Jam alat total", nf(r.hours, 0), r.volume && r.productivity ? "= " + nf(r.volume) + " m³ ÷ Q" : "jam")}
        ${kpi("Jumlah unit", r.units, r.work_days && r.units_needed ? "butuh " + r.units_needed + " unit" : "")}
        ${kpi("Durasi", nf(r.duration_days, 1), "hari kerja / unit")}
        ${kpi("Total biaya", rpS(r.total), rp(r.total), "hl")}
        ${r.cost_per_m3 ? kpi("Biaya per m³", rp(r.cost_per_m3), "milik sendiri", "hl") : ""}
        ${r.rent_per_m3 ? kpi("Jika sewa /m³", rp(r.rent_per_m3), "tarif + OH&P") : ""}</div></div>

    <div class="card"><h3>Temuan &amp; Saran Konsultasi</h3>${r.recommendations.map(x => alertHtml(x.level, x.title, x.text)).join("")}</div>

    <div class="grid g2"><div class="card"><h3>Rincian Biaya</h3>${donut(br)}</div>
    <div class="card"><h3>${b ? "Terhadap Anggaran" : "Biaya per Jam"}</h3>${b ? `
      <p class="small muted">${esc(b.source)}: <b>${rp(b.budget)}</b></p>
      <div class="bar ${barCls(b.pct)}" style="margin:8px 0"><i style="width:${Math.min(b.pct, 100)}%"></i></div>
      <p><b>${nf(b.pct, 1)}%</b> terpakai · ${b.selisih >= 0 ? "sisa" : "kurang"} <b>${rp(Math.abs(b.selisih))}</b></p>
      <p class="small muted" style="margin-top:8px">Anggaran cukup untuk ±<b>${nf(b.max_hours)}</b> jam alat${b.max_volume ? ` (≈ ${nf(b.max_volume)} m³)` : ""}.</p>`
      : `<div class="kpis" style="grid-template-columns:1fr 1fr">${kpi("Biaya alat", rp(r.hourly.total), "per jam")}${kpi("Tarif sewa", rp(r.hourly.tarif_sewa), "per jam")}</div><p class="small muted">Isi “Anggaran alat ini” atau pilih proyek untuk membandingkan.</p>`}</div></div>

    <div class="card" style="margin-top:16px"><h3>Sensitivitas — jika kondisi berubah</h3><div class="bars">${sens}</div></div>

    <div class="card"><h3>Milik Sendiri vs Sewa</h3><div class="table-wrap"><table><tbody>
      <tr><td>Total biaya jika milik sendiri</td><td class="num"><b>${rp(o.own_total)}</b></td></tr>
      <tr><td>Total biaya jika sewa (tarif ${rp(o.market_rate)}/jam ${o.market_given ? "pasar" : "analisa + OH&amp;P"})</td><td class="num"><b>${rp(o.rent_total)}</b></td></tr>
      <tr><td>Biaya tetap kepemilikan per tahun</td><td class="num">${rp(o.fixed_year)}</td></tr>
      <tr><td>Biaya variabel per jam</td><td class="num">${rp(o.variable_hour)}</td></tr>
      <tr><td>Titik impas milik vs sewa</td><td class="num">${o.breakeven_hours_year ? nf(o.breakeven_hours_year) + " jam/tahun" : "sewa selalu lebih murah"}</td></tr></tbody></table></div></div>

    <details class="card more" open><summary><h3 style="margin:0">Perhitungan Lengkap</h3></summary>
      ${r.productivity ? `<h4 style="margin:6px 0">1. Produktivitas alat</h4><div class="formula">${esc(r.formula)}</div>
      <div class="table-wrap" style="margin-top:8px"><table><thead><tr><th>Simbol</th><th>Parameter</th><th class="num">Nilai</th></tr></thead><tbody>${paramRows}
      ${Object.entries(r.productivity_detail).map(([kk, v]) => `<tr class="sub-row"><td>${kk}</td><td>hasil hitung</td><td class="num">${nf(v, 2)} menit</td></tr>`).join("")}</tbody>
      <tfoot><tr><td>Q</td><td>Produktivitas</td><td class="num">${nf(r.productivity, 2)} m³/jam</td></tr></tfoot></table></div>
      <p class="step" style="margin:8px 0 14px">Jam alat = Volume ÷ Q = ${nf(r.volume)} ÷ ${nf(r.productivity, 2)} = ${nf(r.hours, 1)} jam · Unit = ⌈jam ÷ (hari × jam/hari)⌉ = ${r.units_needed}</p>` : ""}
      <h4 style="margin:6px 0">${r.productivity ? "2" : "1"}. Biaya alat per jam</h4>${costCard(r.hourly, S.settings, r.solar_used)}</details>`;
}

// ---------- LAPORAN ----------
let reportPid = "";
async function pgLaporan(arg) {
  await loadCommon();
  if (arg) reportPid = arg;
  if (!S.projects.find(p => p.id == reportPid)) reportPid = S.projects[0] ? String(S.projects[0].id) : "";
  if (!reportPid) { view.innerHTML = `<div class="page-head"><h2>Laporan Biaya</h2></div><div class="card">${empty("Bulldozer", "Belum ada proyek untuk dilaporkan.", `<a class="btn" href="#/proyek">Tambah Proyek</a>`)}</div>`; return; }
  const r = await api(`/projects/${reportPid}/report`); if (!r) return;
  const p = r.project, pct = r.persentase_terpakai;
  const stat = (l, v, s = "", c = "") => `<div class="stat accent"><div class="lbl">${l}</div><div class="num ${c}">${v}</div><div class="sub">${s}</div></div>`;
  const br = Object.entries(r.breakdown).map(([label, value]) => ({ label, value }));
  const maxM = Math.max(1, ...r.monthly.map(m => m.cost));
  const months = r.monthly.map(m => `<div class="c"><b>${rpS(m.cost).replace("Rp ", "")}</b><i style="height:${m.cost / maxM * 100}%"></i><span>${esc(m.month)}</span></div>`).join("");
  const eqRows = r.per_equipment.map(e => `<tr><td data-l="Alat"><b>${esc(e.code)}</b> <span class="muted small">${esc(e.name)}</span></td><td class="num" data-l="Jam">${nf(e.hours, 1)}</td>
    <td class="num" data-l="Solar (L/jam)">${nf(e.fuel_liters)} <span class="muted small">(${nf(e.l_per_hour, 1)})</span></td><td class="num" data-l="BBM">${rp(e.fuel)}</td><td class="num" data-l="Pelumas">${rp(e.pelumas)}</td>
    <td class="num" data-l="Upah">${rp(e.upah)}</td><td class="num" data-l="Biaya pasti">${rp(e.pasti)}</td><td class="num" data-l="Maintenance">${rp(e.maint)}</td><td class="num" data-l="Total"><b>${rp(e.total)}</b></td>
    <td class="num" data-l="Rp/jam">${rp(e.cost_per_hour)}</td></tr>`).join("");
  const pr = r.projection;
  view.innerHTML = `<div class="page-head no-print"><div><h2>Laporan Biaya Proyek</h2><p>Realisasi biaya operasional alat berat terhadap anggaran</p></div>
      <div class="actions"><select id="rProj" style="width:auto;min-width:200px">${prOpts(reportPid)}</select>
      <button class="btn dark" onclick="window.print()">${ico("printer")} Cetak / PDF</button><a class="btn ghost" href="/api/projects/${reportPid}/export.xlsx" download>${ico("download")} Excel</a></div></div>
    <div class="report-head"><h2>LAPORAN BIAYA OPERASIONAL ALAT BERAT</h2><p><b>${esc(p.name)}</b> — ${esc(p.location || "")}</p><p>Dicetak ${fmtDate(today())}</p></div>
    <div class="stats six">
      ${stat("Realisasi biaya", rpS(r.actual_cost), rp(r.actual_cost))}
      ${stat("Anggaran", rpS(p.budget), rp(p.budget))}
      ${stat(r.sisa_anggaran < 0 ? "Melebihi anggaran" : "Sisa anggaran", rpS(Math.abs(r.sisa_anggaran)), nf(pct, 1) + "% terpakai", r.sisa_anggaran < 0 ? "bad" : "ok")}
      ${stat("Jam alat", nf(r.total_hours) + " HM", nf(r.total_liters) + " L solar")}
      ${stat("Biaya per jam", rpS(r.cost_per_hour), "rata-rata semua alat")}
      ${stat("Biaya per m³", r.cost_per_m3 ? rp(r.cost_per_m3) : "-", r.total_volume ? nf(r.total_volume) + " m³ dikerjakan" : "volume belum dicatat")}</div>
    <div class="card"><h3>Analisa &amp; Catatan</h3>${r.insights.map(i => alertHtml(i.level, "", i.text)).join("")}
      ${pr ? `<p class="small muted" style="margin-top:6px">Proyeksi: ${nf(pr.progress_time_pct, 0)}% waktu berjalan (${pr.elapsed_days}/${pr.total_days} hari) → biaya akhir diperkirakan <b>${rp(pr.projected_cost)}</b>.</p>` : ""}</div>
    <div class="grid g2"><div class="card"><h3>Komposisi Biaya</h3>${donut(br)}</div>
      <div class="card"><h3>Biaya per Bulan</h3>${months ? `<div class="vbars">${months}</div>` : `<p class="muted">Belum ada data.</p>`}</div></div>
    <div class="card" style="margin-top:16px"><h3>Rekap per Alat</h3>${eqRows ? `<div class="table-wrap"><table class="stack"><thead><tr><th>Alat</th><th class="num">Jam</th><th class="num">Solar (L/jam)</th><th class="num">BBM</th><th class="num">Pelumas</th><th class="num">Upah</th><th class="num">Biaya pasti</th><th class="num">Maint.</th><th class="num">Total</th><th class="num">Rp/jam</th></tr></thead><tbody>${eqRows}</tbody></table></div>` : `<p class="muted">Belum ada pemakaian alat pada proyek ini.</p>`}
      <p class="small muted" style="margin-top:10px">Biaya pasti = alokasi modal &amp; asuransi per jam pakai. BBM dari catatan solar aktual; pelumas dan upah dihitung per jam kerja; maintenance dari catatan servis proyek.</p></div>`;
  $("#rProj").onchange = e => { reportPid = e.target.value; location.hash = "#/laporan/" + reportPid; };
}

// ---------- PENGATURAN ----------
async function pgPengaturan() {
  await loadCommon(true);
  const fields = Object.entries(S.labels).map(([k, l]) => field(l.label, num("s_" + k, S.settings[k], "", l.unit))).join("");
  view.innerHTML = `<div class="page-head"><div><h2>Pengaturan Perhitungan</h2><p>Parameter ini dipakai di seluruh rumus biaya alat. Sesuaikan dengan data proyek atau acuan dosen.</p></div></div>
    <div class="card"><form class="form" id="fS">${fields}<div class="full form-actions"><button class="btn">Simpan</button><button type="button" class="btn ghost" id="resetS">Kembalikan bawaan</button></div></form></div>
    <div class="card"><h3>Ringkasan Rumus</h3><div class="formula">Biaya pasti/jam   = (B−C)·D/W + asuransi·B/W      ; D = i(1+i)^A / ((1+i)^A − 1)
Biaya operasi/jam = BBM + pelumas + perawatan + upah   ; BBM = koef × HP × harga solar
Produktivitas Q   = V·Fb·Fa·60 / (Ts·Fk)   (m³/jam)
Jam alat          = Volume / Q       Unit = ⌈jam / (hari × jam/hari)⌉
Biaya per m³      = Total biaya / Volume</div>
      <p class="small muted" style="margin-top:8px">Koefisien bawaan adalah nilai acuan umum. Untuk tugas resmi, samakan dengan tabel/pedoman yang diminta dosen (mis. AHSP SNI / Permen PUPR).</p></div>
    <div class="card"><h3>Data</h3><div class="actions"><button class="btn ghost" id="seed">Muat Data Contoh</button><button class="btn danger" id="wipe">Hapus Semua Data</button></div>
      <p class="small muted" style="margin-top:8px">Database tersimpan di file <code>backend/sipil_app.db</code> pada perangkat tempat server berjalan.</p></div>`;
  $("#fS").onsubmit = async e => {
    e.preventDefault(); const o = {};
    for (const [k, v] of new FormData(e.target)) o[k.slice(2)] = v;
    if (await api("/settings", "PUT", o)) { toast("Pengaturan tersimpan"); await loadCommon(true); }
  };
  $("#resetS").onclick = async () => { if (await api("/settings", "PUT", S.defaults)) { toast("Dikembalikan ke nilai bawaan"); pgPengaturan(); } };
  $("#seed").onclick = async () => { if (await api("/seed", "POST")) { toast("Data contoh dimuat"); location.hash = "#/dashboard"; } };
  $("#wipe").onclick = async () => { if (confirm("Hapus SEMUA proyek, alat, pemakaian, dan maintenance? Tidak bisa dibatalkan.") && await api("/reset", "DELETE")) { toast("Semua data dihapus"); location.hash = "#/dashboard"; pgDashboard(); } };
}

// ====================================================================
//  ROUTER & NAVIGASI
// ====================================================================
const ROUTES = {
  dashboard: ["Beranda", "home", pgDashboard], proyek: ["Proyek", "folder", pgProyek], alat: ["Alat Berat", "truck", pgAlat],
  pemakaian: ["Pemakaian", "clock", pgPemakaian], maintenance: ["Maintenance", "wrench", pgMaintenance],
  analisa: ["Analisa Biaya", "calc", pgAnalisa], laporan: ["Laporan", "report", pgLaporan], pengaturan: ["Pengaturan", "sliders", pgPengaturan],
};
const BOTTOM = ["dashboard", "alat", "pemakaian", "analisa"];
$("#sideNav").innerHTML = Object.entries(ROUTES).map(([k, [t, i]]) => `<a href="#/${k}" data-r="${k}">${ico(i)}<span>${t}</span></a>`).join("");
$("#bottomNav").innerHTML = BOTTOM.map(k => `<a href="#/${k}" data-r="${k}">${ico(ROUTES[k][1])}<span>${ROUTES[k][0].replace("Analisa Biaya", "Analisa").replace("Alat Berat", "Alat")}</span></a>`).join("")
  + `<button id="moreBtn" aria-label="Menu lainnya">${ico("grid")}<span>Lainnya</span></button>`;
$("#brandLogo").innerHTML = LOGO; $("#brandLogoSm").innerHTML = LOGO;
$("#moreBtn").onclick = () => openModal("Menu", `<div class="grid" style="gap:8px">${["proyek", "maintenance", "laporan", "pengaturan"].map(k => `<a class="btn ghost" style="justify-content:flex-start" href="#/${k}" data-close>${ico(ROUTES[k][1])} ${ROUTES[k][0]}</a>`).join("")}</div>`);

async function route() {
  closeModal();
  const [name, arg] = (location.hash.replace(/^#\//, "") || "dashboard").split("/");
  const r = ROUTES[name] || ROUTES.dashboard, key = ROUTES[name] ? name : "dashboard";
  $$("[data-r]").forEach(a => a.classList.toggle("active", a.dataset.r === key));
  $("#pageTitle").textContent = r[0]; document.title = r[0] + " — SIPIL-APP";
  view.innerHTML = `<div class="loader">Memuat…</div>`;
  try { await r[2](arg); } catch (e) { console.error(e); view.innerHTML = `<div class="card">${empty("Lainnya", "Terjadi kesalahan saat menampilkan halaman.")}</div>`; }
  window.scrollTo(0, 0);
}
window.addEventListener("hashchange", route);

// ---------- tema ----------
function setTheme(t) { document.documentElement.dataset.theme = t; try { localStorage.setItem("sipil-theme", t); } catch (e) { } $("#themeBtn").innerHTML = ico("moon"); }
(() => {
  let t = null; try { t = localStorage.getItem("sipil-theme"); } catch (e) { }
  setTheme(t || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"));
  $("#themeBtn").onclick = () => setTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark");
})();
route();
