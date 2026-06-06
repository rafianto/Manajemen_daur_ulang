#!/bin/bash
# =====================================================
# Skrip Instalasi Otomatis
# Sistem Manajemen Pengelolaan Daur Ulang Sampah
# =====================================================

set -e

# Warna
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo ""
echo -e "${CYAN}=====================================================${NC}"
echo -e "${CYAN}   SISTEM MANAJEMEN PENGELOLAAN DAUR ULANG SAMPAH    ${NC}"
echo -e "${CYAN}   Skrip Instalasi Otomatis                          ${NC}"
echo -e "${CYAN}=====================================================${NC}"
echo ""

# Deteksi direktori proyek
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${YELLOW}[1/7] Memeriksa Python...${NC}"
if command -v python3 &>/dev/null; then
    PYTHON=python3
    PYVER=$($PYTHON --version 2>&1)
    echo -e "   ${GREEN}Ditemukan: $PYVER${NC}"
else
    echo -e "   ${RED}ERROR: Python 3 tidak ditemukan!${NC}"
    echo -e "   Silakan install Python 3.10+ dari https://python.org"
    exit 1
fi

echo ""
echo -e "${YELLOW}[2/7] Membuat virtual environment...${NC}"
if [ ! -d "venv" ]; then
    $PYTHON -m venv venv
    echo -e "   ${GREEN}Virtual environment berhasil dibuat${NC}"
else
    echo -e "   ${GREEN}Virtual environment sudah ada${NC}"
fi

echo ""
echo -e "${YELLOW}[3/7] Menginstall dependensi...${NC}"
source venv/bin/activate
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
echo -e "   ${GREEN}Dependensi berhasil diinstall${NC}"

echo ""
echo -e "${YELLOW}[4/7] Menjalankan migrasi database...${NC}"
python manage.py makemigrations --noinput 2>/dev/null || true
python manage.py migrate --noinput
echo -e "   ${GREEN}Migrasi database berhasil${NC}"

echo ""
echo -e "${YELLOW}[5/7] Mengumpulkan file static...${NC}"
python manage.py collectstatic --noinput 2>/dev/null || true
echo -e "   ${GREEN}File static berhasil dikumpulkan${NC}"

echo ""
echo -e "${YELLOW}[6/7] Membuat akun administrator...${NC}"
# Cek apakah superuser sudah ada
if python -c "
import os, django
os.environ['DJANGO_SETTINGS_MODULE']='daur_ulang.settings'
django.setup()
from django.contrib.auth.models import User
exit(0 if User.objects.filter(is_superuser=True).exists() else 1)
" 2>/dev/null; then
    echo -e "   ${GREEN}Akun administrator sudah ada${NC}"
else
    echo ""
    echo -e "   ${CYAN}Buat akun administrator:${NC}"
    read -p "   Username [admin]: " USERNAME
    USERNAME=${USERNAME:-admin}
    read -p "   Email [admin@daurulang.com]: " EMAIL
    EMAIL=${EMAIL:-admin@daurulang.com}
    read -s -p "   Password [admin123]: " PASSWORD
    echo ""
    PASSWORD=${PASSWORD:-admin123}

    DJANGO_SUPERUSER_PASSWORD="$PASSWORD" python manage.py createsuperuser \
        --username "$USERNAME" --email "$EMAIL" --noinput 2>/dev/null
    echo -e "   ${GREEN}Akun administrator berhasil dibuat${NC}"
fi

echo ""
echo -e "${YELLOW}[7/7] Mengisi data demo (opsional)...${NC}"
read -p "   Isi data demo untuk testing? [y/N]: " SEED
if [[ "$SEED" =~ ^[Yy]$ ]]; then
    python seed_data.py
    echo -e "   ${GREEN}Data demo berhasil diisi${NC}"
else
    echo -e "   ${CYAN}Data demo dilewati${NC}"
fi

echo ""
echo -e "${GREEN}=====================================================${NC}"
echo -e "${GREEN}   INSTALASI BERHASIL!                               ${NC}"
echo -e "${GREEN}=====================================================${NC}"
echo ""
echo -e "   Untuk menjalankan server:"
echo -e "   ${CYAN}cd $SCRIPT_DIR${NC}"
echo -e "   ${CYAN}source venv/bin/activate${NC}"
echo -e "   ${CYAN}python manage.py runserver 0.0.0.0:8000${NC}"
echo ""
echo -e "   Atau gunakan script:"
echo -e "   ${CYAN}./start.sh${NC}"
echo ""
echo -e "   Buka browser: ${CYAN}http://localhost:8000${NC}"
echo ""
