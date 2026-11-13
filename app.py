"""
Entry point SIPIL-APP (Flask).

- Lokal            : python app.py
- Render/Railway   : gunicorn app:app
- Streamlit Cloud  : tidak crash/hang; menampilkan halaman utama Flask
                     (mode terbatas, lihat catatan di bawah)
"""
import importlib.util
import os
import sys

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")

for p in (BACKEND_DIR, ROOT_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)


def _find_main():
    candidates = [BACKEND_DIR, ROOT_DIR]
    try:
        for name in os.listdir(ROOT_DIR):
            full = os.path.join(ROOT_DIR, name)
            if os.path.isdir(full) and name.lower() == "backend":
                candidates.insert(0, full)
    except OSError:
        pass
    for folder in candidates:
        path = os.path.join(folder, "main.py")
        if os.path.isfile(path):
            return path
    return None


def _load_app():
    main_path = _find_main()
    if main_path is None:
        return None
    folder = os.path.dirname(main_path)
    if folder not in sys.path:
        sys.path.insert(0, folder)
    spec = importlib.util.spec_from_file_location("sipil_backend_main", main_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["sipil_backend_main"] = module
    spec.loader.exec_module(module)
    return module.app


def _diagnostic_app():
    from flask import Flask

    diag = Flask(__name__)

    @diag.route("/")
    def index():
        lines = []
        for root, dirs, files in os.walk(ROOT_DIR):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]
            for f in files:
                lines.append(os.path.relpath(os.path.join(root, f), ROOT_DIR))
        listing = "\n".join(sorted(lines))
        return (
            "<h2>backend/main.py tidak ditemukan</h2>"
            "<p>Upload folder <b>backend/</b> (berisi main.py) ke repo GitHub, lalu deploy ulang.</p>"
            f"<p>File yang terdeploy:</p><pre>{listing}</pre>"
        )

    return diag


def _running_in_streamlit():
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx

        return get_script_run_ctx() is not None
    except Exception:
        return False


app = _load_app() or _diagnostic_app()


def _streamlit_view():
    """Tampilan untuk Streamlit Cloud. Flask tidak dijalankan sebagai server
    (itu yang bikin layar hitam loading terus), hanya halaman utamanya
    di-render lewat test client lalu ditampilkan."""
    import streamlit as st
    import streamlit.components.v1 as components

    st.set_page_config(page_title="SIPIL-APP", layout="wide")
    try:
        html = app.test_client().get("/").get_data(as_text=True)
        st.warning(
            "Mode Streamlit: halaman tampil, tetapi fitur yang memanggil server Flask "
            "(simpan/hitung/unduh Excel, dll.) tidak akan berfungsi. "
            "Untuk fungsi penuh, deploy ke Render/Railway/PythonAnywhere dengan `gunicorn app:app`."
        )
        components.html(html, height=900, scrolling=True)
    except Exception as e:  # tampilkan error apa adanya, jangan blank
        st.error("Gagal memuat halaman utama Flask.")
        st.exception(e)


if _running_in_streamlit():
    _streamlit_view()
elif __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    print("\nSIPIL-APP berjalan.")
    print(f"Buka: http://127.0.0.1:{port}")
    print("Untuk akses dari perangkat lain, gunakan IP komputer/HP pada jaringan Wi-Fi yang sama.\n")
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
