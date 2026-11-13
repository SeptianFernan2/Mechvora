"""
calc.py — Modul perhitungan biaya & produktivitas alat berat (Teknik Sipil)

Acuan metode: analisa biaya sewa alat per jam (biaya pasti + biaya operasi)
sebagaimana lazim dipakai dalam Analisa Harga Satuan Pekerjaan (pedoman PUPR/SNI),
serta rumus produktivitas alat (excavator, loader, dump truck, bulldozer, roller).

Semua koefisien dapat diubah dari halaman Pengaturan. Nilai bawaan adalah nilai
acuan umum, bukan ketentuan mutlak — sesuaikan dengan data proyek/dosen.
"""
import math

# ------------------------------------------------------------------ pengaturan
DEFAULT_SETTINGS = {
    "harga_solar":     13500,   # Rp / liter
    "harga_pelumas":   45000,   # Rp / liter
    "upah_operator":   30000,   # Rp / jam
    "upah_pembantu":   20000,   # Rp / jam
    "bunga":           10.0,    # % per tahun (suku bunga modal)
    "asuransi":        0.2,     # % dari harga alat per tahun (asuransi dll)
    "jam_per_tahun":   2000,    # W — jam kerja alat per tahun
    "nilai_sisa":      10.0,    # % dari harga alat (nilai sisa / salvage)
    "koef_bbm":        12.5,    # % x HP = liter BBM per jam
    "koef_pelumas":    1.0,     # % x HP = liter pelumas per jam (dapat diubah sesuai acuan dosen/AHSP)
    "koef_perawatan":  12.5,    # % x B / W  (perawatan & perbaikan)
    "overhead_profit": 10.0,    # % overhead & profit untuk tarif sewa
}

SETTING_LABELS = {
    "harga_solar":    ("Harga solar", "Rp/liter"),
    "harga_pelumas":  ("Harga pelumas", "Rp/liter"),
    "upah_operator":  ("Upah operator", "Rp/jam"),
    "upah_pembantu":  ("Upah pembantu operator", "Rp/jam"),
    "bunga":          ("Suku bunga modal (i)", "% / tahun"),
    "asuransi":       ("Asuransi & pajak", "% harga alat / tahun"),
    "jam_per_tahun":  ("Jam kerja alat per tahun (W)", "jam"),
    "nilai_sisa":     ("Nilai sisa alat (C)", "% harga alat"),
    "koef_bbm":       ("Koefisien BBM", "% x HP = L/jam"),
    "koef_pelumas":   ("Koefisien pelumas", "% x HP = L/jam"),
    "koef_perawatan": ("Koefisien perawatan & perbaikan", "% x B / W"),
    "overhead_profit": ("Overhead & profit tarif sewa", "%"),
}

# ------------------------------------------------------------------ katalog kategori
# params: parameter produktivitas yang dapat diubah user pada halaman Analisa.
CATEGORIES = {
    "Excavator": {
        "hp": 148, "umur": 5, "harga": 1_750_000_000, "kapasitas": 0.8, "kap_label": "Kapasitas bucket (m³)",
        "interval": 250, "produktif": True,
        "rumus": "Q = (V × Fb × Fa × 60) / (Ts × Fk)",
        "params": [
            {"key": "V",  "label": "Kapasitas bucket V", "unit": "m³", "default": 0.8, "from_cap": True},
            {"key": "Fb", "label": "Faktor bucket Fb", "unit": "", "default": 0.9},
            {"key": "Fa", "label": "Efisiensi kerja Fa", "unit": "", "default": 0.75},
            {"key": "Ts", "label": "Waktu siklus Ts", "unit": "menit", "default": 0.5},
            {"key": "Fk", "label": "Faktor konversi material Fk", "unit": "", "default": 1.2},
        ],
    },
    "Bulldozer": {
        "hp": 200, "umur": 5, "harga": 2_600_000_000, "kapasitas": 4.0, "kap_label": "Kapasitas blade (m³)",
        "interval": 250, "produktif": True,
        "rumus": "Q = (q × Fb × Fa × 60) / (Ts × Fk);  Ts = J/F + J/R + Z",
        "params": [
            {"key": "q",  "label": "Kapasitas blade q", "unit": "m³", "default": 4.0, "from_cap": True},
            {"key": "Fb", "label": "Faktor blade Fb", "unit": "", "default": 0.8},
            {"key": "Fa", "label": "Efisiensi kerja Fa", "unit": "", "default": 0.75},
            {"key": "J",  "label": "Jarak dorong J", "unit": "m", "default": 30},
            {"key": "F",  "label": "Kecepatan maju F", "unit": "km/jam", "default": 4},
            {"key": "R",  "label": "Kecepatan mundur R", "unit": "km/jam", "default": 6},
            {"key": "Z",  "label": "Waktu ganti persneling Z", "unit": "menit", "default": 0.15},
            {"key": "Fk", "label": "Faktor konversi material Fk", "unit": "", "default": 1.2},
        ],
    },
    "Dump Truck": {
        "hp": 130, "umur": 5, "harga": 700_000_000, "kapasitas": 8.0, "kap_label": "Kapasitas bak (m³)",
        "interval": 250, "produktif": True,
        "rumus": "Q = (V × Fa × 60) / (Ts × Fk);  Ts = T1 + L/v1 + L/v2 + T2",
        "params": [
            {"key": "V",  "label": "Kapasitas bak V", "unit": "m³", "default": 8.0, "from_cap": True},
            {"key": "Fa", "label": "Efisiensi kerja Fa", "unit": "", "default": 0.8},
            {"key": "L",  "label": "Jarak angkut L (sekali jalan)", "unit": "km", "default": 5},
            {"key": "v1", "label": "Kecepatan bermuatan v1", "unit": "km/jam", "default": 30},
            {"key": "v2", "label": "Kecepatan kosong v2", "unit": "km/jam", "default": 40},
            {"key": "T1", "label": "Waktu muat T1", "unit": "menit", "default": 2.0},
            {"key": "T2", "label": "Waktu bongkar & manuver T2", "unit": "menit", "default": 2.0},
            {"key": "Fk", "label": "Faktor konversi material Fk", "unit": "", "default": 1.2},
        ],
    },
    "Wheel Loader": {
        "hp": 150, "umur": 5, "harga": 1_400_000_000, "kapasitas": 2.0, "kap_label": "Kapasitas bucket (m³)",
        "interval": 250, "produktif": True,
        "rumus": "Q = (V × Fb × Fa × 60) / (Ts × Fk)",
        "params": [
            {"key": "V",  "label": "Kapasitas bucket V", "unit": "m³", "default": 2.0, "from_cap": True},
            {"key": "Fb", "label": "Faktor bucket Fb", "unit": "", "default": 0.85},
            {"key": "Fa", "label": "Efisiensi kerja Fa", "unit": "", "default": 0.8},
            {"key": "Ts", "label": "Waktu siklus Ts", "unit": "menit", "default": 0.7},
            {"key": "Fk", "label": "Faktor konversi material Fk", "unit": "", "default": 1.2},
        ],
    },
    "Vibrator Roller": {
        "hp": 100, "umur": 5, "harga": 900_000_000, "kapasitas": 2.0, "kap_label": "Lebar drum (m)",
        "interval": 250, "produktif": True,
        "rumus": "Q = ((W − b₀) × v × 1000 × t × Fa) / n",
        "params": [
            {"key": "W",  "label": "Lebar efektif drum W", "unit": "m", "default": 2.0, "from_cap": True},
            {"key": "b0", "label": "Lebar overlap b₀", "unit": "m", "default": 0.2},
            {"key": "v",  "label": "Kecepatan v", "unit": "km/jam", "default": 4},
            {"key": "t",  "label": "Tebal lapisan padat t", "unit": "m", "default": 0.15},
            {"key": "n",  "label": "Jumlah lintasan n", "unit": "kali", "default": 8},
            {"key": "Fa", "label": "Efisiensi kerja Fa", "unit": "", "default": 0.83},
        ],
    },
    "Crane": {
        "hp": 250, "umur": 8, "harga": 4_500_000_000, "kapasitas": 50, "kap_label": "Kapasitas angkat (ton)",
        "interval": 250, "produktif": False,
        "rumus": "Dihitung per jam pakai (tidak ada rumus m³/jam)",
        "params": [],
    },
    "Lainnya": {
        "hp": 100, "umur": 5, "harga": 500_000_000, "kapasitas": 0, "kap_label": "Kapasitas",
        "interval": 250, "produktif": False,
        "rumus": "Dihitung per jam pakai",
        "params": [],
    },
}


def category_of(name):
    return CATEGORIES.get(name) or CATEGORIES["Lainnya"]


def num(v, default=0.0):
    try:
        if v is None or v == "":
            return default
        return float(v)
    except (TypeError, ValueError):
        return default


# ------------------------------------------------------------------ biaya per jam
def hourly_cost(eq, s, solar_price=None):
    """
    Biaya alat per jam (Rp/jam) = Biaya Pasti + Biaya Operasi.

    Biaya pasti:
        C  = nilai_sisa% × B
        D  = i(1+i)^A / ((1+i)^A − 1)          faktor angsuran modal
        E  = (B − C) × D / W                    pengembalian modal / jam
        F  = asuransi% × B / W                  asuransi, pajak / jam
        G  = E + F
    Biaya operasi:
        H  = koef_bbm × HP × harga_solar
        I  = koef_pelumas × HP × harga_pelumas
        K  = koef_perawatan × B / W
        L  = upah operator, M = upah pembantu
    """
    cat = category_of(eq.get("category"))
    B = num(eq.get("purchase_price")) or cat["harga"]
    HP = num(eq.get("engine_hp")) or cat["hp"]
    A = num(eq.get("life_years")) or cat["umur"]
    W = num(s["jam_per_tahun"]) or 2000
    i = num(s["bunga"]) / 100.0
    salv = num(eq.get("salvage_pct"), None)
    if salv is None or salv == 0:
        salv = num(s["nilai_sisa"])
    C = B * salv / 100.0

    if i > 0:
        D = i * (1 + i) ** A / ((1 + i) ** A - 1)
    else:
        D = 1.0 / A
    E = (B - C) * D / W
    F = num(s["asuransi"]) / 100.0 * B / W
    G = E + F

    ms = num(solar_price) if solar_price else num(s["harga_solar"])
    liter_bbm = num(s["koef_bbm"]) / 100.0 * HP
    liter_oli = num(s["koef_pelumas"]) / 100.0 * HP
    H = liter_bbm * ms
    I = liter_oli * num(s["harga_pelumas"])
    K = num(s["koef_perawatan"]) / 100.0 * B / W
    L = num(s["upah_operator"])
    M = num(s["upah_pembantu"])
    operasi = H + I + K + L + M
    total = G + operasi
    sewa = total * (1 + num(s["overhead_profit"]) / 100.0)

    return {
        "B": B, "C": C, "HP": HP, "A": A, "W": W, "i": i, "D": D,
        "E": E, "F": F, "biaya_pasti": G,
        "H_bbm": H, "I_pelumas": I, "K_perawatan": K, "L_operator": L, "M_pembantu": M,
        "biaya_operasi": operasi,
        "total": total,
        "tarif_sewa": sewa,
        "liter_bbm_jam": liter_bbm,
        "liter_pelumas_jam": liter_oli,
        "pasti_per_tahun": (B - C) * D + num(s["asuransi"]) / 100.0 * B,
    }


# ------------------------------------------------------------------ produktivitas
def default_params(category, capacity=None):
    cat = category_of(category)
    out = {}
    for p in cat["params"]:
        v = p["default"]
        if p.get("from_cap") and capacity:
            v = capacity
        out[p["key"]] = v
    return out


def productivity(category, params):
    """Produktivitas (m³/jam) berdasarkan kategori. Mengembalikan (Q, detail)."""
    p = {k: num(v) for k, v in params.items()}
    detail = {}
    if category == "Excavator" or category == "Wheel Loader":
        Q = p["V"] * p["Fb"] * p["Fa"] * 60 / (p["Ts"] * p["Fk"])
    elif category == "Bulldozer":
        Ts = p["J"] / (p["F"] * 1000 / 60) + p["J"] / (p["R"] * 1000 / 60) + p["Z"]
        detail["Ts"] = Ts
        Q = p["q"] * p["Fb"] * p["Fa"] * 60 / (Ts * p["Fk"])
    elif category == "Dump Truck":
        t_isi = p["L"] / p["v1"] * 60
        t_kosong = p["L"] / p["v2"] * 60
        Ts = p["T1"] + t_isi + t_kosong + p["T2"]
        detail.update({"Ts": Ts, "t_isi": t_isi, "t_kosong": t_kosong})
        Q = p["V"] * p["Fa"] * 60 / (Ts * p["Fk"])
    elif category == "Vibrator Roller":
        Q = (p["W"] - p["b0"]) * p["v"] * 1000 * p["t"] * p["Fa"] / p["n"]
    else:
        return None, detail
    return Q, detail


def safe_productivity(category, params):
    try:
        return productivity(category, params)
    except (ZeroDivisionError, KeyError):
        return None, {}


# ------------------------------------------------------------------ jadwal servis
def service_status(current_hm, last_service_hm, next_due_hm, interval):
    """Status servis berkala berdasarkan HM (hour meter)."""
    interval = interval or 250
    estimated = False
    if next_due_hm:
        due = next_due_hm
    elif last_service_hm is not None:
        due = last_service_hm + interval
    else:
        # belum ada riwayat servis: perkirakan kelipatan interval berikutnya
        due = (math.floor(current_hm / interval) + 1) * interval
        estimated = True
    sisa = due - current_hm
    if sisa <= 0:
        st = "Terlambat"
    elif sisa <= max(25, interval * 0.1):
        st = "Segera"
    else:
        st = "Aman"
    return {"next_due_hm": due, "sisa_hm": sisa, "status": st, "estimated": estimated}


def rupiah(n):
    return "Rp " + f"{n:,.0f}".replace(",", ".")
