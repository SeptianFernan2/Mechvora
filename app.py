"""
Entry point SIPIL-APP.
Menjalankan backend Flask yang berada di folder backend/.

Lokal      : python app.py
Production : gunicorn app:app   (Render, Railway, dll.)
"""
import importlib.util
import os
import sys

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")

# Pastikan folder backend dan root bisa di-import
for p in (BACKEND_DIR, ROOT_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

MAIN_PATH = os.path.join(BACKEND_DIR, "main.py")
if not os.path.isfile(MAIN_PATH):
    raise FileNotFoundError(
        f"backend/main.py tidak ditemukan di {BACKEND_DIR}. "
        "Pastikan folder backend/ ikut ter-upload ke GitHub "
        "(cek .gitignore dan nama folder, huruf besar/kecil berpengaruh di Linux)."
    )

# Load backend/main.py langsung lewat path, supaya tidak bentrok
# dengan modul lain bernama 'main' dan tidak bergantung pada sys.path.
spec = importlib.util.spec_from_file_location("sipil_backend_main", MAIN_PATH)
_module = importlib.util.module_from_spec(spec)
sys.modules["sipil_backend_main"] = _module
spec.loader.exec_module(_module)

app = _module.app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    print("\nSIPIL-APP berjalan.")
    print(f"Buka: http://127.0.0.1:{port}")
    print("Untuk akses dari perangkat lain, gunakan IP komputer/HP pada jaringan Wi-Fi yang sama.\n")
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
