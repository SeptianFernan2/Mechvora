"""
Entry point SIPIL-APP.
Menjalankan backend Flask yang berada di folder backend/.
Jalankan dari folder utama proyek: python app.py
"""
import os
import sys

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from main import app  # noqa: E402

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    print("\nSIPIL-APP berjalan.")
    print(f"Buka: http://127.0.0.1:{port}")
    print("Untuk akses dari perangkat lain, gunakan IP komputer/HP pada jaringan Wi-Fi yang sama.\n")
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
