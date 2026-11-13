"""
SIPIL-APP v1.0 — Manajemen Maintenance Alat Berat & Analisa Biaya Operasional Proyek
Backend: Flask + SQLite (ringan, mudah dipasang di Termux / Android)

Jalankan:
    cd backend
    python main.py
Buka http://127.0.0.1:8000  (dari HP)  atau  http://<IP-HP>:8000  (dari laptop, satu WiFi)
"""
import io
import math
import os
import random
import socket
import sqlite3
from datetime import date, datetime, timedelta
from types import SimpleNamespace

from flask import Flask, jsonify, request, send_file, send_from_directory

import calc

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "sipil_app.db")
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend"))

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
app.json.ensure_ascii = False
app.json.sort_keys = False


# ============================================================ DATABASE
def get_db():
    con = sqlite3.connect(DB_FILE)
    con.row_factory = sqlite3.Row
    return con


SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL, location TEXT DEFAULT '',
    start_date TEXT, end_date TEXT,
    budget REAL DEFAULT 0, status TEXT DEFAULT 'Aktif',
    volume_target REAL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS equipment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE, name TEXT NOT NULL,
    category TEXT DEFAULT '', brand TEXT DEFAULT '', year INTEGER,
    purchase_price REAL DEFAULT 0, status TEXT DEFAULT 'Ready',
    engine_hp REAL, life_years REAL, salvage_pct REAL,
    capacity REAL, initial_hm REAL DEFAULT 0, service_interval REAL DEFAULT 250
);
CREATE TABLE IF NOT EXISTS maintenance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id INTEGER NOT NULL, project_id INTEGER,
    date TEXT, mtype TEXT DEFAULT 'Preventif', description TEXT DEFAULT '',
    sparepart_cost REAL DEFAULT 0, labor_cost REAL DEFAULT 0, other_cost REAL DEFAULT 0,
    next_due_hours REAL, hm_at_service REAL
);
CREATE TABLE IF NOT EXISTS usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id INTEGER NOT NULL, project_id INTEGER NOT NULL,
    date TEXT, work_hours REAL DEFAULT 0, fuel_liters REAL DEFAULT 0,
    fuel_price REAL DEFAULT 0, operator_name TEXT DEFAULT '',
    volume_m3 REAL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value REAL);
"""

# kolom baru untuk database lama (v0.1) -> migrasi otomatis
MIGRATIONS = {
    "projects": {"volume_target": "REAL DEFAULT 0"},
    "equipment": {"engine_hp": "REAL", "life_years": "REAL", "salvage_pct": "REAL",
                  "capacity": "REAL", "initial_hm": "REAL DEFAULT 0",
                  "service_interval": "REAL DEFAULT 250"},
    "maintenance": {"hm_at_service": "REAL"},
    "usage": {"volume_m3": "REAL DEFAULT 0"},
}


def init_db():
    con = get_db()
    con.executescript(SCHEMA)
    for table, cols in MIGRATIONS.items():
        have = {r["name"] for r in con.execute(f"PRAGMA table_info({table})")}
        for col, ddl in cols.items():
            if col not in have:
                con.execute(f"ALTER TABLE {table} ADD COLUMN {col} {ddl}")
    con.commit()
    con.close()


init_db()


def get_settings(con=None):
    own = con is None
    con = con or get_db()
    s = dict(calc.DEFAULT_SETTINGS)
    for r in con.execute("SELECT key, value FROM settings"):
        if r["key"] in s:
            s[r["key"]] = r["value"]
    if own:
        con.close()
    return s


# ============================================================ VALIDASI INPUT
class ApiError(Exception):
    def __init__(self, status, msg):
        self.status, self.msg = status, msg


@app.errorhandler(ApiError)
def _api_error(e):
    return jsonify({"detail": e.msg}), e.status


@app.errorhandler(404)
def _nf(e):
    return jsonify({"detail": "Tidak ditemukan"}), 404


@app.errorhandler(Exception)
def _any(e):
    if hasattr(e, "code") and isinstance(e.code, int):  # HTTPException
        return jsonify({"detail": getattr(e, "description", str(e))}), e.code
    app.logger.exception(e)
    return jsonify({"detail": f"Kesalahan server: {e}"}), 500


def _blank(v):
    return v is None or (isinstance(v, str) and v.strip() == "")


def parse(data, spec):
    """spec: {field: (tipe, default)} tipe: str|float|int|date|bool|dict, 'opt' di awal = boleh kosong."""
    data = data or {}
    out = {}
    for k, (t, dflt) in spec.items():
        v = data.get(k)
        opt = t.startswith("opt_")
        t = t.replace("opt_", "")
        if _blank(v):
            if dflt == "REQUIRED":
                raise ApiError(400, f"Kolom '{k}' wajib diisi")
            out[k] = dflt
            continue
        try:
            if t == "str":
                out[k] = str(v).strip()
            elif t == "float":
                out[k] = float(v)
            elif t == "int":
                out[k] = int(float(v))
            elif t == "bool":
                out[k] = bool(v) if not isinstance(v, str) else v.lower() in ("1", "true", "ya", "on")
            elif t == "date":
                out[k] = datetime.strptime(str(v)[:10], "%Y-%m-%d").date().isoformat()
            elif t == "dict":
                out[k] = v if isinstance(v, dict) else {}
        except (ValueError, TypeError):
            raise ApiError(400, f"Nilai kolom '{k}' tidak valid")
    return out


PROJECT_SPEC = {"name": ("str", "REQUIRED"), "location": ("str", ""), "start_date": ("opt_date", None),
                "end_date": ("opt_date", None), "budget": ("float", 0.0), "status": ("str", "Aktif"),
                "volume_target": ("float", 0.0)}
EQUIP_SPEC = {"code": ("str", "REQUIRED"), "name": ("str", "REQUIRED"), "category": ("str", ""), "brand": ("str", ""),
              "year": ("opt_int", None), "purchase_price": ("float", 0.0), "status": ("str", "Ready"),
              "engine_hp": ("opt_float", None), "life_years": ("opt_float", None), "salvage_pct": ("opt_float", None),
              "capacity": ("opt_float", None), "initial_hm": ("float", 0.0), "service_interval": ("float", 250.0)}
MAINT_SPEC = {"equipment_id": ("int", "REQUIRED"), "project_id": ("opt_int", None), "date": ("opt_date", None),
              "mtype": ("str", "Preventif"), "description": ("str", ""), "sparepart_cost": ("float", 0.0),
              "labor_cost": ("float", 0.0), "other_cost": ("float", 0.0), "next_due_hours": ("opt_float", None),
              "hm_at_service": ("opt_float", None), "set_ready": ("bool", False)}
USAGE_SPEC = {"equipment_id": ("int", "REQUIRED"), "project_id": ("int", "REQUIRED"), "date": ("opt_date", None),
              "work_hours": ("float", 0.0), "fuel_liters": ("float", 0.0), "fuel_price": ("float", 0.0),
              "operator_name": ("str", ""), "volume_m3": ("float", 0.0)}
ANALYZE_SPEC = {"category": ("str", "Excavator"), "equipment_id": ("opt_int", None), "project_id": ("opt_int", None),
                "params": ("dict", {}), "volume": ("opt_float", None), "hours": ("opt_float", None),
                "work_days": ("opt_float", None), "hours_per_day": ("float", 8.0), "units": ("opt_int", None),
                "solar_price": ("opt_float", None), "mobdemob": ("float", 0.0), "budget": ("opt_float", None),
                "market_rent": ("opt_float", None), "price": ("opt_float", None), "hp": ("opt_float", None),
                "life_years": ("opt_float", None)}


def body():
    return request.get_json(silent=True) or {}


def row(con, table, rid):
    r = con.execute(f"SELECT * FROM {table} WHERE id=?", (rid,)).fetchone()
    return dict(r) if r else None


def num(v):
    return calc.num(v)


# ============================================================ HELPER HITUNG
def equipment_hm(con, eid, initial=None):
    if initial is None:
        r = con.execute("SELECT initial_hm FROM equipment WHERE id=?", (eid,)).fetchone()
        initial = (r["initial_hm"] if r else 0) or 0
    t = con.execute("SELECT COALESCE(SUM(work_hours),0) h FROM usage WHERE equipment_id=?", (eid,)).fetchone()["h"]
    return initial + t


def service_of(con, e, hm):
    cat = calc.category_of(e["category"])
    last = con.execute(
        "SELECT hm_at_service, next_due_hours FROM maintenance WHERE equipment_id=? ORDER BY date DESC, id DESC LIMIT 1",
        (e["id"],)).fetchone()
    return calc.service_status(hm, last["hm_at_service"] if last else None,
                               last["next_due_hours"] if last else None,
                               e.get("service_interval") or cat["interval"])


def equipment_view(con, e, s):
    e = dict(e)
    hm = equipment_hm(con, e["id"], e.get("initial_hm") or 0)
    hc = calc.hourly_cost(e, s)
    e.update({"hm_total": hm, "service": service_of(con, e, hm),
              "cost_hour": hc["total"], "rent_hour": hc["tarif_sewa"],
              "hp_eff": hc["HP"], "life_eff": hc["A"], "price_eff": hc["B"]})
    return e


def project_calc(con, pid, s):
    """Hitung seluruh biaya realisasi sebuah proyek."""
    project = row(con, "projects", pid)
    usages = [dict(r) for r in con.execute("SELECT * FROM usage WHERE project_id=? ORDER BY date, id", (pid,))]
    maints = [dict(r) for r in con.execute("SELECT * FROM maintenance WHERE project_id=? ORDER BY date, id", (pid,))]
    eqs = {r["id"]: dict(r) for r in con.execute("SELECT * FROM equipment")}
    hcache = {}

    def hc_of(eid):
        if eid not in hcache:
            hcache[eid] = calc.hourly_cost(eqs.get(eid, {"category": "Lainnya"}), s)
        return hcache[eid]

    def new_eq(eid):
        e = eqs.get(eid, {})
        return {"equipment_id": eid, "code": e.get("code", "?"), "name": e.get("name", "?"),
                "category": e.get("category", ""), "hours": 0.0, "fuel_liters": 0.0, "volume": 0.0,
                "fuel": 0.0, "pelumas": 0.0, "upah": 0.0, "pasti": 0.0, "maint": 0.0}

    tot = {"fuel": 0.0, "pelumas": 0.0, "upah": 0.0, "pasti": 0.0, "maint": 0.0,
           "hours": 0.0, "liters": 0.0, "volume": 0.0}
    per_eq, monthly = {}, {}
    for u in usages:
        hc = hc_of(u["equipment_id"])
        h = u["work_hours"] or 0
        fuel = (u["fuel_liters"] or 0) * (u["fuel_price"] or 0)
        pel = h * hc["I_pelumas"]
        upah = h * (hc["L_operator"] + hc["M_pembantu"])
        pasti = h * hc["biaya_pasti"]
        tot["fuel"] += fuel; tot["pelumas"] += pel; tot["upah"] += upah; tot["pasti"] += pasti
        tot["hours"] += h; tot["liters"] += u["fuel_liters"] or 0; tot["volume"] += u["volume_m3"] or 0
        r = per_eq.setdefault(u["equipment_id"], new_eq(u["equipment_id"]))
        r["hours"] += h; r["fuel_liters"] += u["fuel_liters"] or 0; r["volume"] += u["volume_m3"] or 0
        r["fuel"] += fuel; r["pelumas"] += pel; r["upah"] += upah; r["pasti"] += pasti
        mk = (u["date"] or "")[:7]
        monthly[mk] = monthly.get(mk, 0.0) + fuel + pel + upah + pasti
    for m in maints:
        c = (m["sparepart_cost"] or 0) + (m["labor_cost"] or 0) + (m["other_cost"] or 0)
        tot["maint"] += c
        r = per_eq.setdefault(m["equipment_id"], new_eq(m["equipment_id"]))
        r["maint"] += c
        mk = (m["date"] or "")[:7]
        monthly[mk] = monthly.get(mk, 0.0) + c

    actual = tot["fuel"] + tot["pelumas"] + tot["upah"] + tot["pasti"] + tot["maint"]
    budget = project["budget"] or 0
    for r in per_eq.values():
        r["total"] = r["fuel"] + r["pelumas"] + r["upah"] + r["pasti"] + r["maint"]
        r["cost_per_hour"] = r["total"] / r["hours"] if r["hours"] else 0
        r["l_per_hour"] = r["fuel_liters"] / r["hours"] if r["hours"] else 0
        r["cost_per_m3"] = r["total"] / r["volume"] if r["volume"] else 0

    proj = None
    try:
        if project["start_date"] and project["end_date"] and usages:
            sd = datetime.strptime(project["start_date"][:10], "%Y-%m-%d").date()
            ed = datetime.strptime(project["end_date"][:10], "%Y-%m-%d").date()
            last = max(datetime.strptime(u["date"][:10], "%Y-%m-%d").date() for u in usages if u["date"])
            elapsed = max((last - sd).days + 1, 1)
            total_days = max((ed - sd).days + 1, elapsed)
            proj = {"elapsed_days": elapsed, "total_days": total_days,
                    "projected_cost": actual / elapsed * total_days,
                    "progress_time_pct": min(elapsed / total_days * 100, 100)}
    except Exception:
        proj = None

    return {
        "project": project,
        "total_hours": tot["hours"], "total_liters": tot["liters"], "total_volume": tot["volume"],
        "breakdown": {"BBM (Solar)": tot["fuel"], "Pelumas": tot["pelumas"], "Upah Operator": tot["upah"],
                      "Biaya Pasti (Modal & Asuransi)": tot["pasti"], "Maintenance": tot["maint"]},
        "fuel_cost": tot["fuel"], "maintenance_cost": tot["maint"],
        "actual_cost": actual, "sisa_anggaran": budget - actual,
        "persentase_terpakai": (actual / budget * 100) if budget else 0,
        "cost_per_hour": actual / tot["hours"] if tot["hours"] else 0,
        "cost_per_m3": actual / tot["volume"] if tot["volume"] else 0,
        "per_equipment": sorted(per_eq.values(), key=lambda x: -x["total"]),
        "monthly": [{"month": k, "cost": v} for k, v in sorted(monthly.items()) if k],
        "projection": proj,
        "usages": usages, "maintenances": maints, "eq_map": eqs,
    }


def project_insights(c):
    out = []
    p = c["project"]
    pct = c["persentase_terpakai"]
    tot = c["actual_cost"]
    if p["budget"] and tot:
        if pct > 100:
            out.append(("bad", f"Realisasi biaya alat melebihi anggaran sebesar {calc.rupiah(-c['sisa_anggaran'])} ({pct:.1f}% dari anggaran)."))
        elif pct > 85:
            out.append(("warn", f"Anggaran alat sudah terpakai {pct:.1f}%. Sisa {calc.rupiah(c['sisa_anggaran'])} — kendalikan pemakaian."))
        else:
            out.append(("ok", f"Anggaran alat terkendali: terpakai {pct:.1f}%, sisa {calc.rupiah(c['sisa_anggaran'])}."))
    pr = c.get("projection")
    if pr and p["budget"]:
        if pr["projected_cost"] > p["budget"]:
            out.append(("warn", f"Dengan laju biaya saat ini, proyeksi biaya akhir {calc.rupiah(pr['projected_cost'])} "
                                f"melebihi anggaran sebesar {calc.rupiah(pr['projected_cost'] - p['budget'])}."))
        else:
            out.append(("ok", f"Proyeksi biaya akhir {calc.rupiah(pr['projected_cost'])} masih di bawah anggaran."))
    if tot:
        bbm = c["breakdown"]["BBM (Solar)"] / tot * 100
        if bbm > 45:
            out.append(("warn", f"BBM menyumbang {bbm:.0f}% biaya. Periksa idle time, kondisi mesin, dan kemungkinan kebocoran solar."))
    for e in c["per_equipment"]:
        if e["hours"] and e["l_per_hour"]:
            hp = (c["eq_map"].get(e["equipment_id"]) or {}).get("engine_hp") or calc.category_of(e["category"])["hp"]
            exp = hp * 0.125
            if e["l_per_hour"] > exp * 1.3:
                out.append(("warn", f"{e['code']}: konsumsi solar {e['l_per_hour']:.1f} L/jam, "
                                    f"±{(e['l_per_hour'] / exp - 1) * 100:.0f}% di atas acuan {exp:.1f} L/jam. Cek kondisi mesin."))
    if not out:
        out.append(("ok", "Belum ada data pemakaian untuk dianalisa."))
    return [{"level": l, "text": t} for l, t in out]


# ============================================================ API: PENGATURAN
@app.get("/api/settings")
def api_settings():
    return jsonify({"values": get_settings(),
                    "labels": {k: {"label": v[0], "unit": v[1]} for k, v in calc.SETTING_LABELS.items()},
                    "defaults": calc.DEFAULT_SETTINGS})


@app.put("/api/settings")
def api_settings_put():
    data = body()
    con = get_db()
    for k, v in data.items():
        if k in calc.DEFAULT_SETTINGS:
            try:
                fv = float(v)
            except (TypeError, ValueError):
                continue
            con.execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (k, fv))
    con.commit()
    s = get_settings(con)
    con.close()
    return jsonify(s)


@app.get("/api/catalog")
def api_catalog():
    return jsonify(calc.CATEGORIES)


# ============================================================ API: PROYEK
@app.get("/api/projects")
def list_projects():
    con = get_db()
    s = get_settings(con)
    out = []
    for r in con.execute("SELECT * FROM projects ORDER BY id DESC").fetchall():
        p = dict(r)
        c = project_calc(con, p["id"], s)
        p["actual_cost"] = c["actual_cost"]
        p["persentase_terpakai"] = c["persentase_terpakai"]
        out.append(p)
    con.close()
    return jsonify(out)


@app.post("/api/projects")
def create_project():
    d = parse(body(), PROJECT_SPEC)
    con = get_db()
    cur = con.execute(
        "INSERT INTO projects (name,location,start_date,end_date,budget,status,volume_target) VALUES (?,?,?,?,?,?,?)",
        (d["name"], d["location"], d["start_date"], d["end_date"], d["budget"], d["status"], d["volume_target"]))
    con.commit()
    r = row(con, "projects", cur.lastrowid)
    con.close()
    return jsonify(r)


@app.put("/api/projects/<int:pid>")
def update_project(pid):
    d = parse(body(), PROJECT_SPEC)
    con = get_db()
    if not row(con, "projects", pid):
        con.close(); raise ApiError(404, "Proyek tidak ditemukan")
    con.execute("UPDATE projects SET name=?,location=?,start_date=?,end_date=?,budget=?,status=?,volume_target=? WHERE id=?",
                (d["name"], d["location"], d["start_date"], d["end_date"], d["budget"], d["status"], d["volume_target"], pid))
    con.commit()
    r = row(con, "projects", pid)
    con.close()
    return jsonify(r)


@app.delete("/api/projects/<int:pid>")
def delete_project(pid):
    con = get_db()
    if not row(con, "projects", pid):
        con.close(); raise ApiError(404, "Proyek tidak ditemukan")
    con.execute("DELETE FROM usage WHERE project_id=?", (pid,))
    con.execute("UPDATE maintenance SET project_id=NULL WHERE project_id=?", (pid,))
    con.execute("DELETE FROM projects WHERE id=?", (pid,))
    con.commit(); con.close()
    return jsonify({"ok": True})


# ============================================================ API: ALAT BERAT
@app.get("/api/equipment")
def list_equipment():
    con = get_db()
    s = get_settings(con)
    rows = [equipment_view(con, r, s) for r in con.execute("SELECT * FROM equipment ORDER BY code").fetchall()]
    con.close()
    return jsonify(rows)


def eq_values(d):
    return (d["code"], d["name"], d["category"], d["brand"], d["year"], d["purchase_price"], d["status"],
            d["engine_hp"], d["life_years"], d["salvage_pct"], d["capacity"], d["initial_hm"], d["service_interval"])


@app.post("/api/equipment")
def create_equipment():
    d = parse(body(), EQUIP_SPEC)
    con = get_db()
    try:
        cur = con.execute(
            """INSERT INTO equipment (code,name,category,brand,year,purchase_price,status,
               engine_hp,life_years,salvage_pct,capacity,initial_hm,service_interval) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            eq_values(d))
    except sqlite3.IntegrityError:
        con.close(); raise ApiError(400, "Kode alat sudah dipakai")
    con.commit()
    r = equipment_view(con, row(con, "equipment", cur.lastrowid), get_settings(con))
    con.close()
    return jsonify(r)


@app.put("/api/equipment/<int:eid>")
def update_equipment(eid):
    d = parse(body(), EQUIP_SPEC)
    con = get_db()
    if not row(con, "equipment", eid):
        con.close(); raise ApiError(404, "Alat tidak ditemukan")
    try:
        con.execute(
            """UPDATE equipment SET code=?,name=?,category=?,brand=?,year=?,purchase_price=?,status=?,
               engine_hp=?,life_years=?,salvage_pct=?,capacity=?,initial_hm=?,service_interval=? WHERE id=?""",
            eq_values(d) + (eid,))
    except sqlite3.IntegrityError:
        con.close(); raise ApiError(400, "Kode alat sudah dipakai")
    con.commit()
    r = equipment_view(con, row(con, "equipment", eid), get_settings(con))
    con.close()
    return jsonify(r)


@app.put("/api/equipment/<int:eid>/status")
def set_equipment_status(eid):
    status = str(body().get("status", "")).strip()
    if status not in ("Ready", "Dipakai", "Maintenance", "Rusak"):
        raise ApiError(400, "Status tidak valid")
    con = get_db()
    if not row(con, "equipment", eid):
        con.close(); raise ApiError(404, "Alat tidak ditemukan")
    con.execute("UPDATE equipment SET status=? WHERE id=?", (status, eid))
    con.commit(); con.close()
    return jsonify({"ok": True})


@app.delete("/api/equipment/<int:eid>")
def delete_equipment(eid):
    con = get_db()
    if not row(con, "equipment", eid):
        con.close(); raise ApiError(404, "Alat tidak ditemukan")
    con.execute("DELETE FROM usage WHERE equipment_id=?", (eid,))
    con.execute("DELETE FROM maintenance WHERE equipment_id=?", (eid,))
    con.execute("DELETE FROM equipment WHERE id=?", (eid,))
    con.commit(); con.close()
    return jsonify({"ok": True})


@app.get("/api/equipment/<int:eid>/costcard")
def equipment_costcard(eid):
    """Rincian perhitungan biaya per jam (kartu biaya alat)."""
    con = get_db()
    e = row(con, "equipment", eid)
    if not e:
        con.close(); raise ApiError(404, "Alat tidak ditemukan")
    s = get_settings(con)
    hc = calc.hourly_cost(e, s)
    con.close()
    return jsonify({"equipment": e, "settings": s, "cost": hc})


# ============================================================ API: MAINTENANCE
@app.get("/api/maintenance")
def list_maintenance():
    eid = request.args.get("equipment_id", type=int)
    con = get_db()
    if eid:
        rows = con.execute("SELECT * FROM maintenance WHERE equipment_id=? ORDER BY date DESC, id DESC", (eid,)).fetchall()
    else:
        rows = con.execute("SELECT * FROM maintenance ORDER BY date DESC, id DESC").fetchall()
    con.close()
    return jsonify([dict(r) for r in rows])


@app.post("/api/maintenance")
def create_maintenance():
    d = parse(body(), MAINT_SPEC)
    con = get_db()
    e = row(con, "equipment", d["equipment_id"])
    if not e:
        con.close(); raise ApiError(404, "Alat tidak ditemukan")
    hm = d["hm_at_service"] if d["hm_at_service"] is not None else equipment_hm(con, e["id"], e.get("initial_hm") or 0)
    nxt = d["next_due_hours"] or (hm + (e.get("service_interval") or calc.category_of(e["category"])["interval"]))
    cur = con.execute(
        """INSERT INTO maintenance (equipment_id,project_id,date,mtype,description,
           sparepart_cost,labor_cost,other_cost,next_due_hours,hm_at_service) VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (d["equipment_id"], d["project_id"], d["date"] or str(date.today()), d["mtype"], d["description"],
         d["sparepart_cost"], d["labor_cost"], d["other_cost"], nxt, hm))
    con.execute("UPDATE equipment SET status=? WHERE id=?", ("Ready" if d["set_ready"] else "Maintenance", d["equipment_id"]))
    con.commit()
    r = row(con, "maintenance", cur.lastrowid)
    con.close()
    return jsonify(r)


@app.delete("/api/maintenance/<int:mid>")
def delete_maintenance(mid):
    con = get_db()
    con.execute("DELETE FROM maintenance WHERE id=?", (mid,))
    con.commit(); con.close()
    return jsonify({"ok": True})


# ============================================================ API: PEMAKAIAN
@app.get("/api/usage")
def list_usage():
    pid = request.args.get("project_id", type=int)
    con = get_db()
    if pid:
        rows = con.execute("SELECT * FROM usage WHERE project_id=? ORDER BY date DESC, id DESC", (pid,)).fetchall()
    else:
        rows = con.execute("SELECT * FROM usage ORDER BY date DESC, id DESC LIMIT 300").fetchall()
    con.close()
    return jsonify([dict(r) for r in rows])


@app.post("/api/usage")
def create_usage():
    d = parse(body(), USAGE_SPEC)
    con = get_db()
    if not row(con, "equipment", d["equipment_id"]) or not row(con, "projects", d["project_id"]):
        con.close(); raise ApiError(404, "Alat atau proyek tidak ditemukan")
    cur = con.execute(
        """INSERT INTO usage (equipment_id,project_id,date,work_hours,fuel_liters,fuel_price,operator_name,volume_m3)
           VALUES (?,?,?,?,?,?,?,?)""",
        (d["equipment_id"], d["project_id"], d["date"] or str(date.today()),
         d["work_hours"], d["fuel_liters"], d["fuel_price"], d["operator_name"], d["volume_m3"]))
    con.execute("UPDATE equipment SET status='Dipakai' WHERE id=? AND status='Ready'", (d["equipment_id"],))
    con.commit()
    r = row(con, "usage", cur.lastrowid)
    con.close()
    return jsonify(r)


@app.delete("/api/usage/<int:uid>")
def delete_usage(uid):
    con = get_db()
    con.execute("DELETE FROM usage WHERE id=?", (uid,))
    con.commit(); con.close()
    return jsonify({"ok": True})


# ============================================================ API: LAPORAN & DASHBOARD
@app.get("/api/projects/<int:pid>/report")
def project_report(pid):
    con = get_db()
    if not row(con, "projects", pid):
        con.close(); raise ApiError(404, "Proyek tidak ditemukan")
    s = get_settings(con)
    c = project_calc(con, pid, s)
    con.close()
    c["insights"] = project_insights(c)
    c.pop("eq_map", None)
    c["settings"] = s
    return jsonify(c)


@app.get("/api/dashboard")
def dashboard():
    con = get_db()
    s = get_settings(con)
    eqs = [equipment_view(con, r, s) for r in con.execute("SELECT * FROM equipment ORDER BY code")]
    projects = [dict(r) for r in con.execute("SELECT * FROM projects ORDER BY id DESC")]
    comp = {"BBM (Solar)": 0.0, "Pelumas": 0.0, "Upah Operator": 0.0,
            "Biaya Pasti (Modal & Asuransi)": 0.0, "Maintenance": 0.0}
    proj_rows = []
    total_budget = total_actual = 0.0
    for p in projects:
        c = project_calc(con, p["id"], s)
        for k, v in c["breakdown"].items():
            comp[k] += v
        proj_rows.append({"id": p["id"], "name": p["name"], "status": p["status"], "budget": p["budget"] or 0,
                          "actual": c["actual_cost"], "pct": c["persentase_terpakai"]})
        if p["status"] == "Aktif":
            total_budget += p["budget"] or 0
            total_actual += c["actual_cost"]
    status = {}
    for e in eqs:
        status[e["status"]] = status.get(e["status"], 0) + 1
    alerts = []
    for e in eqs:
        sv = e["service"]
        est = " (perkiraan, belum ada riwayat servis)" if sv.get("estimated") else ""
        if sv["status"] == "Terlambat":
            alerts.append({"level": "bad", "equipment": e["code"], "name": e["name"],
                           "text": f"Servis terlambat {abs(sv['sisa_hm']):.0f} HM — jatuh tempo {sv['next_due_hm']:.0f} HM, HM sekarang {e['hm_total']:.0f}.{est}"})
        elif sv["status"] == "Segera":
            alerts.append({"level": "warn", "equipment": e["code"], "name": e["name"],
                           "text": f"Servis berikutnya {sv['sisa_hm']:.0f} HM lagi (jatuh tempo {sv['next_due_hm']:.0f} HM).{est}"})
    alerts.sort(key=lambda a: 0 if a["level"] == "bad" else 1)
    maint_total = con.execute("SELECT COALESCE(SUM(sparepart_cost+labor_cost+other_cost),0) t FROM maintenance").fetchone()["t"]
    con.close()
    return jsonify({
        "total_projects": len(projects), "active_projects": sum(1 for p in projects if p["status"] == "Aktif"),
        "total_equipment": len(eqs), "equipment_maintenance": status.get("Maintenance", 0),
        "equipment_status": status, "composition": comp, "projects": proj_rows, "alerts": alerts,
        "total_budget_active": total_budget, "total_actual_active": total_actual, "maintenance_total": maint_total,
        "equipment": [{"id": e["id"], "code": e["code"], "name": e["name"], "category": e["category"],
                       "status": e["status"], "hm": e["hm_total"], "service": e["service"],
                       "cost_hour": e["cost_hour"]} for e in eqs],
    })


# ============================================================ API: ANALISA / KONSULTASI
@app.post("/api/analyze")
def analyze():
    a = SimpleNamespace(**parse(body(), ANALYZE_SPEC))
    con = get_db()
    s = get_settings(con)
    eq = None
    if a.equipment_id:
        eq = row(con, "equipment", a.equipment_id)
        if not eq:
            con.close(); raise ApiError(404, "Alat tidak ditemukan")
        category = eq["category"] or a.category
    else:
        category = a.category
    cat = calc.category_of(category)
    eqd = dict(eq) if eq else {"category": category}
    if a.price: eqd["purchase_price"] = a.price
    if a.hp: eqd["engine_hp"] = a.hp
    if a.life_years: eqd["life_years"] = a.life_years

    proj_info = None
    if a.project_id:
        pj = row(con, "projects", a.project_id)
        if pj:
            c = project_calc(con, a.project_id, s)
            proj_info = {"id": pj["id"], "name": pj["name"], "budget": pj["budget"] or 0,
                         "actual": c["actual_cost"], "sisa": (pj["budget"] or 0) - c["actual_cost"]}
    sv = None
    hm_now = None
    if eq:
        hm_now = equipment_hm(con, eq["id"], eq.get("initial_hm") or 0)
        sv = service_of(con, eq, hm_now)
    con.close()

    hc = calc.hourly_cost(eqd, s, a.solar_price)

    # --- produktivitas
    params = calc.default_params(category, eqd.get("capacity"))
    params.update({k: v for k, v in a.params.items() if v not in (None, "")})
    Q, qdetail = None, {}
    if cat["produktif"]:
        Q, qdetail = calc.safe_productivity(category, params)
        if Q is not None and Q <= 0:
            Q = None

    volume, hours = a.volume, a.hours
    if volume and Q:
        hours = volume / Q
    elif hours and Q and not volume:
        volume = hours * Q
    elif volume and not Q:
        raise ApiError(400, "Kategori ini tidak punya rumus produktivitas — isi 'Jam Alat' langsung.")
    if not hours:
        raise ApiError(400, "Isi volume pekerjaan (m³) atau jam alat.")

    # --- jumlah unit & durasi
    window = (a.work_days or 0) * a.hours_per_day
    units_needed = math.ceil(hours / window) if window > 0 else 1
    units = a.units or units_needed
    hours_per_unit = hours / units
    duration_days = hours_per_unit / a.hours_per_day if a.hours_per_day else 0

    # --- biaya
    mob = a.mobdemob * units if a.mobdemob else 0
    breakdown = {
        "BBM (Solar)": hc["H_bbm"] * hours,
        "Pelumas": hc["I_pelumas"] * hours,
        "Perawatan & Perbaikan": hc["K_perawatan"] * hours,
        "Upah Operator & Pembantu": (hc["L_operator"] + hc["M_pembantu"]) * hours,
        "Biaya Pasti (Modal & Asuransi)": hc["biaya_pasti"] * hours,
    }
    if mob:
        breakdown["Mobilisasi/Demobilisasi"] = mob
    total = sum(breakdown.values())
    rent_total = hc["tarif_sewa"] * hours + mob
    per_m3 = total / volume if volume else None
    rent_per_m3 = rent_total / volume if volume else None

    # --- anggaran
    budget, budget_src = a.budget, "anggaran alat"
    if not budget and proj_info and proj_info["sisa"] > 0:
        budget, budget_src = proj_info["sisa"], "sisa anggaran proyek"
    budget_res = None
    if budget:
        max_hours = max((budget - mob) / hc["total"], 0)
        budget_res = {"budget": budget, "source": budget_src, "selisih": budget - total,
                      "pct": total / budget * 100, "max_hours": max_hours,
                      "max_volume": max_hours * Q if Q else None}

    # --- sensitivitas
    def scen(label, solar_f=1.0, prod_f=1.0):
        h2 = calc.hourly_cost(eqd, s, (a.solar_price or s["harga_solar"]) * solar_f)
        t = h2["total"] * (hours / prod_f) + mob
        return {"label": label, "total": t, "delta_pct": (t / total - 1) * 100 if total else 0}
    sens = [scen("Kondisi dasar"), scen("Harga solar +20%", solar_f=1.2), scen("Harga solar −20%", solar_f=0.8)]
    if volume and Q:
        sens += [scen("Produktivitas turun 20%", prod_f=0.8), scen("Produktivitas naik 20%", prod_f=1.2)]

    # --- sewa vs milik
    market = a.market_rent or hc["tarif_sewa"]
    var_hr = hc["biaya_operasi"]
    be = hc["pasti_per_tahun"] / (market - var_hr) if market > var_hr else None
    own_vs_rent = {"market_rate": market, "market_given": bool(a.market_rent), "own_cost_hour": hc["total"],
                   "fixed_year": hc["pasti_per_tahun"], "variable_hour": var_hr,
                   "breakeven_hours_year": be, "planned_hours": hours, "own_total": total, "rent_total": rent_total}

    # --- rekomendasi konsultatif
    rec = []
    def add(level, title, text):
        rec.append({"level": level, "title": title, "text": text})
    def idn(x, d=0):
        return f"{x:,.{d}f}".replace(",", "§").replace(".", ",").replace("§", ".")

    if budget_res:
        if budget_res["selisih"] < 0:
            t = (f"Biaya operasional {calc.rupiah(total)} melebihi anggaran {calc.rupiah(budget)} "
                 f"sebesar {calc.rupiah(-budget_res['selisih'])}. Dengan anggaran tersebut alat hanya mampu bekerja ±{idn(budget_res['max_hours'])} jam")
            t += f" (≈ {idn(budget_res['max_volume'])} m³)." if budget_res["max_volume"] else "."
            add("bad", "Melebihi anggaran", t)
        elif budget_res["pct"] > 90:
            add("warn", "Anggaran sangat ketat", f"Biaya sudah {budget_res['pct']:.0f}% dari anggaran; tidak ada ruang untuk kenaikan harga solar atau penurunan produktivitas.")
        else:
            add("ok", "Anggaran mencukupi", f"Biaya {budget_res['pct']:.0f}% dari anggaran, tersisa {calc.rupiah(budget_res['selisih'])}.")
    bbm_share = breakdown["BBM (Solar)"] / total * 100 if total else 0
    if bbm_share > 40:
        add("warn", "Biaya BBM dominan", f"BBM {bbm_share:.0f}% dari total. Kurangi waktu idle (mesin menyala tanpa bekerja), perhatikan kondisi front kerja, dan pantau konsumsi solar per jam.")
    if "Fa" in params and num(params["Fa"]) < 0.7:
        add("warn", "Efisiensi kerja rendah", f"Fa = {num(params['Fa']):.2f}. Di bawah 0,70 berarti banyak waktu hilang (menunggu truk, antrian, cuaca). Perbaiki manajemen lapangan sebelum menambah unit.")
    if a.work_days and not a.units and units > 1:
        add("info", "Jumlah unit disesuaikan jadwal", f"Untuk menyelesaikan ±{idn(hours)} jam kerja alat dalam {a.work_days:g} hari ({a.hours_per_day:g} jam/hari) dibutuhkan ±{units} unit.")
    if a.units and window > 0 and hours_per_unit > window:
        add("bad", "Unit tidak cukup untuk jadwal", f"Dengan {a.units} unit, pekerjaan butuh ±{duration_days:.1f} hari, sedangkan target {a.work_days:g} hari. Tambah unit atau jam kerja.")
    if be and hours < be:
        add("info", "Pertimbangkan sewa", f"Pemakaian rencana {idn(hours)} jam lebih kecil dari titik impas kepemilikan ±{idn(be)} jam/tahun terhadap tarif {calc.rupiah(market)}/jam. Untuk pemakaian sesedikit ini, sewa cenderung lebih hemat daripada memiliki alat.")
    elif be:
        add("ok", "Kepemilikan layak", f"Pemakaian rencana {idn(hours)} jam ≥ titik impas ±{idn(be)} jam/tahun terhadap tarif sewa {calc.rupiah(market)}/jam.")
    worst = max(sens, key=lambda x: x["total"])
    if worst["delta_pct"] > 15:
        add("warn", "Risiko biaya terbesar", f"Skenario '{worst['label']}' menaikkan biaya {worst['delta_pct']:.0f}% menjadi {calc.rupiah(worst['total'])}. Sediakan cadangan (contingency) minimal {math.ceil(worst['delta_pct'])}%.")
    if eq and sv and sv["sisa_hm"] < hours_per_unit:
        add("warn", "Servis berkala akan jatuh tempo",
            f"HM alat {hm_now:.0f}, servis berikutnya {sv['next_due_hm']:.0f} HM. Selama pekerjaan (±{hours_per_unit:.0f} jam per unit) alat melewati jadwal servis — rencanakan downtime dan biaya perawatannya.")
    if not rec:
        add("ok", "Tidak ada peringatan", "Parameter yang dimasukkan tidak menunjukkan risiko besar.")

    return jsonify({
        "category": category, "equipment": eq, "project": proj_info,
        "formula": cat["rumus"], "params": params, "productivity": Q, "productivity_detail": qdetail,
        "volume": volume, "hours": hours, "units": units, "units_needed": units_needed,
        "hours_per_unit": hours_per_unit, "duration_days": duration_days, "work_days": a.work_days,
        "hourly": hc, "breakdown": breakdown, "total": total, "cost_per_m3": per_m3,
        "rent_total": rent_total, "rent_per_m3": rent_per_m3,
        "budget": budget_res, "sensitivity": sens, "own_vs_rent": own_vs_rent,
        "recommendations": rec, "solar_used": a.solar_price or s["harga_solar"],
    })


# ============================================================ EXPORT EXCEL
@app.get("/api/projects/<int:pid>/export.xlsx")
def export_xlsx(pid):
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
        from openpyxl.utils import get_column_letter
    except ImportError:
        raise ApiError(501, "Modul openpyxl belum terpasang. Jalankan: pip install openpyxl")

    con = get_db()
    if not row(con, "projects", pid):
        con.close(); raise ApiError(404, "Proyek tidak ditemukan")
    s = get_settings(con)
    c = project_calc(con, pid, s)
    con.close()
    p, eqs = c["project"], c["eq_map"]

    wb = Workbook()
    head_fill = PatternFill("solid", fgColor="1F3A5F")
    head_font = Font(bold=True, color="FFFFFF")
    thin = Side(style="thin", color="CCCCCC")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    RP = "#,##0"

    def header(ws, r, cols):
        for i, t in enumerate(cols, 1):
            cell = ws.cell(r, i, t)
            cell.fill, cell.font, cell.border = head_fill, head_font, border
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    def widths(ws, ws_w):
        for i, w in enumerate(ws_w, 1):
            ws.column_dimensions[get_column_letter(i)].width = w

    ws = wb.active; ws.title = "Ringkasan"
    ws["A1"] = "LAPORAN BIAYA OPERASIONAL ALAT BERAT"; ws["A1"].font = Font(bold=True, size=14)
    ws["A2"] = f"Proyek: {p['name']}"; ws["A3"] = f"Lokasi: {p['location'] or '-'}"
    ws["A4"] = f"Dicetak: {date.today().strftime('%d-%m-%Y')}"
    header(ws, 6, ["Komponen Biaya", "Rupiah", "% Total"])
    n = len(c["breakdown"])
    first = 7
    tot_row = first + n
    r = first
    for k, v in c["breakdown"].items():
        ws.cell(r, 1, k); ws.cell(r, 2, v).number_format = RP
        ws.cell(r, 3, f"=IF($B${tot_row}=0,0,B{r}/$B${tot_row})").number_format = "0.0%"
        r += 1
    ws.cell(tot_row, 1, "TOTAL REALISASI").font = Font(bold=True)
    ws.cell(tot_row, 2, f"=SUM(B{first}:B{tot_row - 1})").number_format = RP
    ws.cell(tot_row, 2).font = Font(bold=True)
    r = tot_row + 2
    ws.cell(r, 1, "Anggaran"); ws.cell(r, 2, p["budget"] or 0).number_format = RP; b_row = r; r += 1
    ws.cell(r, 1, "Sisa anggaran"); ws.cell(r, 2, f"=B{b_row}-B{tot_row}").number_format = RP; r += 1
    ws.cell(r, 1, "% anggaran terpakai"); ws.cell(r, 2, f"=IF(B{b_row}=0,0,B{tot_row}/B{b_row})").number_format = "0.0%"; r += 1
    ws.cell(r, 1, "Total jam alat (HM)"); ws.cell(r, 2, c["total_hours"]).number_format = "#,##0.0"; r += 1
    ws.cell(r, 1, "Total volume hasil (m³)"); ws.cell(r, 2, c["total_volume"]).number_format = "#,##0"; r += 1
    ws.cell(r, 1, "Biaya per jam alat"); ws.cell(r, 2, c["cost_per_hour"]).number_format = RP; r += 1
    ws.cell(r, 1, "Biaya per m³"); ws.cell(r, 2, c["cost_per_m3"]).number_format = RP
    widths(ws, [34, 20, 12])

    ws2 = wb.create_sheet("Per Alat")
    header(ws2, 1, ["Kode", "Nama", "Jam (HM)", "Solar (L)", "L/jam", "BBM", "Pelumas", "Upah", "Biaya Pasti",
                    "Maintenance", "Total", "Rp/jam", "Volume (m³)", "Rp/m³"])
    for i, e in enumerate(c["per_equipment"], 2):
        vals = [e["code"], e["name"], e["hours"], e["fuel_liters"], f"=IF(C{i}=0,0,D{i}/C{i})", e["fuel"], e["pelumas"],
                e["upah"], e["pasti"], e["maint"], f"=SUM(F{i}:J{i})", f"=IF(C{i}=0,0,K{i}/C{i})", e["volume"], f"=IF(M{i}=0,0,K{i}/M{i})"]
        for j, v in enumerate(vals, 1):
            cell = ws2.cell(i, j, v); cell.border = border
            if j >= 3: cell.number_format = "#,##0.0" if j in (3, 4, 5) else RP
    widths(ws2, [10, 30, 10, 10, 8, 14, 14, 14, 14, 14, 16, 12, 12, 12])

    ws3 = wb.create_sheet("Pemakaian")
    header(ws3, 1, ["Tanggal", "Alat", "HM", "Solar (L)", "Harga Solar", "Biaya Solar", "Volume (m³)", "Operator"])
    for i, u in enumerate(c["usages"], 2):
        e = eqs.get(u["equipment_id"], {})
        vals = [u["date"], e.get("code", "?"), u["work_hours"], u["fuel_liters"], u["fuel_price"], f"=D{i}*E{i}", u["volume_m3"], u["operator_name"]]
        for j, v in enumerate(vals, 1):
            cell = ws3.cell(i, j, v); cell.border = border
            if j in (5, 6): cell.number_format = RP
    widths(ws3, [12, 10, 8, 10, 12, 14, 12, 18])

    ws4 = wb.create_sheet("Maintenance")
    header(ws4, 1, ["Tanggal", "Alat", "Jenis", "Deskripsi", "Sparepart", "Jasa", "Lain", "Total"])
    for i, m in enumerate(c["maintenances"], 2):
        e = eqs.get(m["equipment_id"], {})
        vals = [m["date"], e.get("code", "?"), m["mtype"], m["description"], m["sparepart_cost"], m["labor_cost"], m["other_cost"], f"=SUM(E{i}:G{i})"]
        for j, v in enumerate(vals, 1):
            cell = ws4.cell(i, j, v); cell.border = border
            if j >= 5: cell.number_format = RP
    widths(ws4, [12, 10, 12, 40, 14, 14, 14, 16])

    buf = io.BytesIO()
    wb.save(buf); buf.seek(0)
    fname = "Laporan_" + "".join(ch if ch.isalnum() else "_" for ch in p["name"])[:40] + ".xlsx"
    return send_file(buf, as_attachment=True, download_name=fname,
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


# ============================================================ DATA CONTOH
@app.post("/api/seed")
def seed_demo():
    con = get_db()
    if con.execute("SELECT COUNT(*) c FROM equipment").fetchone()["c"] or con.execute("SELECT COUNT(*) c FROM projects").fetchone()["c"]:
        con.close(); raise ApiError(400, "Data sudah ada. Hapus data lama terlebih dahulu.")
    rnd = random.Random(7)
    today = date.today()
    projs = [
        ("Pembangunan Jalan Lingkar Utara STA 0+000–5+500", "Kab. Banyuasin, Sumsel", today - timedelta(days=62), today + timedelta(days=118), 2_400_000_000, "Aktif", 90000),
        ("Normalisasi Saluran Primer Sungai Kramat", "Kota Palembang", today - timedelta(days=40), today + timedelta(days=80), 850_000_000, "Aktif", 30000),
        ("Pematangan Lahan Kawasan Industri Tahap I", "Kab. Ogan Ilir", today - timedelta(days=200), today - timedelta(days=20), 3_100_000_000, "Selesai", 140000),
    ]
    for p in projs:
        con.execute("INSERT INTO projects (name,location,start_date,end_date,budget,status,volume_target) VALUES (?,?,?,?,?,?,?)",
                    (p[0], p[1], str(p[2]), str(p[3]), p[4], p[5], p[6]))
    eqs = [  # kode, nama, kategori, merek, tahun, harga, status, hp, umur, sisa%, kapasitas, HM awal, interval
        ("EXC-01", "PC200-8M0", "Excavator", "Komatsu", 2021, 1_850_000_000, "Ready", 148, 5, 10, 0.9, 3200, 250),
        ("EXC-02", "ZX210-5G", "Excavator", "Hitachi", 2019, 1_650_000_000, "Ready", 158, 5, 10, 0.9, 5400, 250),
        ("BD-01", "D65PX-18", "Bulldozer", "Komatsu", 2020, 2_900_000_000, "Ready", 205, 5, 10, 4.3, 4100, 250),
        ("DT-01", "Hino FM260JD", "Dump Truck", "Hino", 2022, 780_000_000, "Ready", 260, 5, 10, 10, 1800, 250),
        ("DT-02", "Mitsubishi FN527", "Dump Truck", "Mitsubishi", 2022, 720_000_000, "Ready", 220, 5, 10, 8, 2100, 250),
        ("WL-01", "WA320-7", "Wheel Loader", "Komatsu", 2021, 1_450_000_000, "Ready", 150, 5, 10, 2.5, 2600, 250),
        ("VR-01", "Sakai SV512D", "Vibrator Roller", "Sakai", 2020, 950_000_000, "Ready", 100, 5, 10, 2.1, 3500, 250),
    ]
    for e in eqs:
        con.execute("""INSERT INTO equipment (code,name,category,brand,year,purchase_price,status,engine_hp,life_years,salvage_pct,capacity,initial_hm,service_interval)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""", e)
    ops = ["Budi", "Agus", "Rahmat", "Joko", "Dedi", "Hendra"]
    plan = [(1, ["EXC-01", "DT-01", "DT-02", "BD-01", "VR-01"], 62), (2, ["EXC-02", "WL-01"], 40)]
    rows_eq = list(con.execute("SELECT id, code, category, engine_hp FROM equipment"))
    ids = {r["code"]: r["id"] for r in rows_eq}
    cats = {r["code"]: r["category"] for r in rows_eq}
    hps = {r["code"]: r["engine_hp"] for r in rows_eq}
    q_ref = {"Excavator": 75, "Bulldozer": 110, "Dump Truck": 30, "Wheel Loader": 120, "Vibrator Roller": 160}
    for pid, codes, days in plan:
        for d in range(days):
            day = today - timedelta(days=days - d)
            if day.weekday() == 6:
                continue
            for code in codes:
                if rnd.random() < 0.12:
                    continue
                h = round(rnd.uniform(5.5, 8.5) * 2) / 2
                lit = round(h * hps[code] * 0.125 * rnd.uniform(0.85, 1.25), 1)
                vol = round(h * q_ref.get(cats[code], 60) * rnd.uniform(0.8, 1.05))
                con.execute("INSERT INTO usage (equipment_id,project_id,date,work_hours,fuel_liters,fuel_price,operator_name,volume_m3) VALUES (?,?,?,?,?,?,?,?)",
                            (ids[code], pid, str(day), h, lit, rnd.choice([13500, 13500, 13600]), rnd.choice(ops), vol))

    def hm_of(code):
        init = next(e[11] for e in eqs if e[0] == code)
        return init + con.execute("SELECT COALESCE(SUM(work_hours),0) h FROM usage WHERE equipment_id=?", (ids[code],)).fetchone()["h"]

    # kode, hari lalu, jenis, deskripsi, sparepart, jasa, lain, HM sejak servis terakhir, proyek
    ms = [
        ("EXC-01", 30, "Preventif", "Ganti oli mesin, filter oli, filter solar, grease", 6_500_000, 1_500_000, 500_000, 230, 1),
        ("EXC-02", 12, "Preventif", "Servis 500 HM: oli hidrolik, filter", 9_800_000, 2_000_000, 400_000, 290, 2),
        ("DT-01", 20, "Korektif", "Perbaikan sistem rem dan kampas", 4_800_000, 1_200_000, 300_000, 120, 1),
        ("BD-01", 45, "Preventif", "Servis 250 HM + cek undercarriage", 7_500_000, 2_000_000, 500_000, 230, 1),
        ("VR-01", 10, "Inspeksi", "Inspeksi drum & vibrator", 0, 750_000, 100_000, 40, 1),
    ]
    for code, ago, mt, desc, sp, lab, oth, since, pid in ms:
        hm_s = hm_of(code) - since
        con.execute("""INSERT INTO maintenance (equipment_id,project_id,date,mtype,description,sparepart_cost,labor_cost,other_cost,next_due_hours,hm_at_service)
                       VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (ids[code], pid, str(today - timedelta(days=ago)), mt, desc, sp, lab, oth, hm_s + 250, hm_s))
    con.execute("UPDATE equipment SET status='Maintenance' WHERE code='DT-01'")
    con.execute("UPDATE equipment SET status='Dipakai' WHERE code IN ('EXC-01','EXC-02','BD-01','DT-02','WL-01')")
    con.commit(); con.close()
    return jsonify({"ok": True})


@app.delete("/api/reset")
def reset_all():
    con = get_db()
    for t in ("usage", "maintenance", "equipment", "projects"):
        con.execute(f"DELETE FROM {t}")
    con.execute("DELETE FROM sqlite_sequence")
    con.commit(); con.close()
    return jsonify({"ok": True})


# ============================================================ FRONTEND
@app.get("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


def lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return None


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    ip = lan_ip()
    print("\n  SIPIL-APP berjalan.")
    print(f"  Di HP ini      : http://127.0.0.1:{port}")
    if ip:
        print(f"  Dari laptop/PC : http://{ip}:{port}   (harus satu WiFi/hotspot)")
    print("  Hentikan dengan Ctrl+C\n")
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
