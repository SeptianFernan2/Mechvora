"""
Entry point SIPIL-APP (Flask + SQLite).

Letakkan file ini di folder utama repo, sejajar dengan folder backend/ dan frontend/.

  Lokal / Termux : python app.py
  Render/Railway : gunicorn app:app
"""
import os
import sys

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")

# main.py melakukan "import calc", jadi folder backend harus ada di sys.path
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

if not os.path.isfile(os.path.join(BACKEND_DIR, "main.py")):
    raise FileNotFoundError(
        "backend/main.py tidak ditemukan. Struktur repo harus: "
        "app.py, requirements.txt, backend/, frontend/ (semua di folder utama)."
    )

from main import app  # noqa: E402  (Flask app dari backend/main.py)


def _running_in_streamlit():
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        return get_script_run_ctx() is not None
    except Exception:
        return False


if _running_in_streamlit():
    # Streamlit Cloud hanya bisa menjalankan aplikasi Streamlit, bukan server Flask.
    import streamlit as st

    st.set_page_config(page_title="SIPIL-APP", page_icon="🏗️")
    st.title("SIPIL-APP")
    st.error("Aplikasi ini berbasis Flask, jadi tidak bisa tampil di Streamlit Cloud.")
    st.markdown(
        """
**Deploy di Render (gratis):**
1. New → Web Service → pilih repo ini
2. Build Command: `pip install -r requirements.txt`
3. Start Command: `gunicorn app:app`

**Atau jalankan lokal / Termux:** `python app.py` lalu buka http://127.0.0.1:8000
"""
    )
elif __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    print("\nSIPIL-APP berjalan.")
    print(f"Buka: http://127.0.0.1:{port}")
    print("Untuk akses dari perangkat lain, gunakan IP komputer/HP pada jaringan Wi-Fi yang sama.\n")
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
