"""
Entry point SIPIL-APP (Flask + SQLite).

Boleh dipakai dengan struktur rapi (backend/ + frontend/) ATAU struktur datar
(semua file di folder utama). Struktur datar akan dirapikan otomatis saat start.

  Lokal / Termux : python app.py
  Render/Railway : gunicorn app:app
"""
import os
import shutil
import sys

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")


def _prepare_layout():
    """Kalau file masih datar di folder utama, salin ke backend/ dan frontend/."""
    if not os.path.isfile(os.path.join(BACKEND_DIR, "main.py")):
        for name in ("main.py", "calc.py"):
            src = os.path.join(ROOT_DIR, name)
            if os.path.isfile(src):
                os.makedirs(BACKEND_DIR, exist_ok=True)
                shutil.copyfile(src, os.path.join(BACKEND_DIR, name))
    if not os.path.isfile(os.path.join(FRONTEND_DIR, "index.html")):
        for name in ("index.html", "style.css", "app.js", "art.js"):
            src = os.path.join(ROOT_DIR, name)
            if os.path.isfile(src):
                os.makedirs(FRONTEND_DIR, exist_ok=True)
                shutil.copyfile(src, os.path.join(FRONTEND_DIR, name))


def _running_in_streamlit():
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        return get_script_run_ctx() is not None
    except Exception:
        return False


_prepare_layout()

_missing = [
    p for p in ("backend/main.py", "backend/calc.py", "frontend/index.html",
                "frontend/app.js", "frontend/style.css", "frontend/art.js")
    if not os.path.isfile(os.path.join(ROOT_DIR, p))
    and not os.path.isfile(os.path.join(ROOT_DIR, os.path.basename(p)))
]
if _missing:
    raise FileNotFoundError("File belum ter-upload ke repo: " + ", ".join(_missing))

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from main import app  # noqa: E402  (Flask app dari backend/main.py)

if _running_in_streamlit():
    # Streamlit Cloud hanya menjalankan aplikasi Streamlit, bukan server Flask.
    import streamlit as st

    st.set_page_config(page_title="SIPIL-APP", page_icon="🏗️")
    st.title("SIPIL-APP")
    st.warning("Semua file sudah lengkap, tetapi aplikasi ini berbasis Flask sehingga tidak bisa tampil di Streamlit Cloud.")
    st.markdown(
        """
**Deploy di Render (gratis):**
1. New → Web Service → pilih repo ini
2. Build Command: `pip install -r requirements.txt`
3. Start Command: `gunicorn app:app`

**Atau jalankan di komputer:** `python app.py` lalu buka http://127.0.0.1:8000
"""
    )
elif __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    print("\nSIPIL-APP berjalan.")
    print(f"Buka: http://127.0.0.1:{port}")
    print("Untuk akses dari perangkat lain, gunakan IP komputer/HP pada jaringan Wi-Fi yang sama.\n")
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
