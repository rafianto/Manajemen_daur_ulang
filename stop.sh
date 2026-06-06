#!/bin/bash
# Skrip Menghentikan Server

echo "Menghentikan server..."
pkill -f "manage.py runserver" 2>/dev/null && echo "Server berhasil dihentikan." || echo "Tidak ada server yang berjalan."
