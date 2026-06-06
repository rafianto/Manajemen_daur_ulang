#!/bin/bash
# =====================================================
# Skrip Menjalankan Server
# Sistem Manajemen Pengelolaan Daur Ulang Sampah
# =====================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Port default
PORT=${1:-8000}

# Aktifkan virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo ""
echo "======================================================="
echo "  SISTEM MANAJEMEN DAUR ULANG SAMPAH"
echo "  Server berjalan di: http://0.0.0.0:$PORT"
echo "  Tekan Ctrl+C untuk menghentikan"
echo "======================================================="
echo ""

python manage.py runserver 0.0.0.0:$PORT
