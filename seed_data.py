"""
Seed script untuk mengisi data demo Sistem Manajemen Pengelolaan Daur Ulang Sampah
"""
import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'daur_ulang.settings')
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)
django.setup()

from django.db import transaction
from django.utils import timezone
from django.contrib.auth.models import User
from waste_mgmt.models import Collector, WasteType, WasteTransaction, OperationalCost, FactorySale

# Reproducible demo data
RANDOM_SEED = 42


def seed():
    random.seed(RANDOM_SEED)

    with transaction.atomic():
        # ── Bersihkan data lama ──────────────────────────────────
        print("Menghapus data demo lama...")
        WasteTransaction.objects.all().delete()
        FactorySale.objects.all().delete()
        OperationalCost.objects.all().delete()
        Collector.objects.all().delete()
        WasteType.objects.all().delete()

        # ── Buat / pastikan admin user ───────────────────────────
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'is_superuser': True,
                'is_staff': True,
                'email': 'admin@example.com',
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            print("  Membuat user admin (password: admin123)")

        # ── Waste Types ──────────────────────────────────────────
        waste_types_data = [
            {'name': 'Botol PET', 'category': 'plastik',
             'purchase_price_per_kg': 1500, 'selling_price_per_kg': 3000},
            {'name': 'Botol HDPE', 'category': 'plastik',
             'purchase_price_per_kg': 2000, 'selling_price_per_kg': 4000},
            {'name': 'Plastik Campuran', 'category': 'plastik',
             'purchase_price_per_kg': 800, 'selling_price_per_kg': 1800},
            {'name': 'Kertas Koran', 'category': 'kertas',
             'purchase_price_per_kg': 1500, 'selling_price_per_kg': 2800},
            {'name': 'Kardus', 'category': 'kertas',
             'purchase_price_per_kg': 1200, 'selling_price_per_kg': 2500},
            {'name': 'Kertas HVS', 'category': 'kertas',
             'purchase_price_per_kg': 2000, 'selling_price_per_kg': 3500},
            {'name': 'Besi Tua', 'category': 'logam',
             'purchase_price_per_kg': 3000, 'selling_price_per_kg': 5500},
            {'name': 'Aluminium Kaleng', 'category': 'logam',
             'purchase_price_per_kg': 5000, 'selling_price_per_kg': 9000},
            {'name': 'Tembaga', 'category': 'logam',
             'purchase_price_per_kg': 25000, 'selling_price_per_kg': 45000},
            {'name': 'Botol Kaca', 'category': 'kaca',
             'purchase_price_per_kg': 1000, 'selling_price_per_kg': 2200},
            {'name': 'Kaca Campuran', 'category': 'kaca',
             'purchase_price_per_kg': 600, 'selling_price_per_kg': 1500},
            {'name': 'Kabel Elektronik', 'category': 'elektronik',
             'purchase_price_per_kg': 8000, 'selling_price_per_kg': 15000},
            {'name': 'PCB Board', 'category': 'elektronik',
             'purchase_price_per_kg': 15000, 'selling_price_per_kg': 28000},
            {'name': 'Kain Perca', 'category': 'tekstil',
             'purchase_price_per_kg': 500, 'selling_price_per_kg': 1200},
        ]

        waste_types = []
        for wtd in waste_types_data:
            wt = WasteType.objects.create(
                name=wtd['name'],
                category=wtd['category'],
                purchase_price_per_kg=Decimal(str(wtd['purchase_price_per_kg'])),
                selling_price_per_kg=Decimal(str(wtd['selling_price_per_kg'])),
                unit='kg',
                is_active=True,
            )
            waste_types.append(wt)
        print(f"Membuat {len(waste_types)} jenis sampah")

        # ── Collectors ───────────────────────────────────────────
        collectors_data = [
            {'name': 'Budi Santoso', 'phone': '081234567890',
             'id_card_number': '3201234567890001',
             'address': 'Jl. Merdeka No. 10, Jakarta Selatan'},
            {'name': 'Siti Aminah', 'phone': '082345678901',
             'id_card_number': '3201234567890002',
             'address': 'Jl. Sudirman No. 25, Jakarta Pusat'},
            {'name': 'Ahmad Ridwan', 'phone': '083456789012',
             'id_card_number': '3201234567890003',
             'address': 'Jl. Gatot Subroto No. 5, Jakarta Timur'},
            {'name': 'Dewi Lestari', 'phone': '084567890123',
             'id_card_number': '3201234567890004',
             'address': 'Jl. Asia Afrika No. 15, Bandung'},
            {'name': 'Eko Prasetyo', 'phone': '085678901234',
             'id_card_number': '3201234567890005',
             'address': 'Jl. Pahlawan No. 30, Surabaya'},
            {'name': 'Ratna Sari', 'phone': '086789012345',
             'id_card_number': '3201234567890006',
             'address': 'Jl. Diponegoro No. 8, Semarang'},
            {'name': 'Hendra Gunawan', 'phone': '087890123456',
             'id_card_number': '3201234567890007',
             'address': 'Jl. Ahmad Yani No. 20, Medan'},
            {'name': 'Yuni Astuti', 'phone': '088901234567',
             'id_card_number': '3201234567890008',
             'address': 'Jl. Veteran No. 12, Yogyakarta'},
        ]

        collectors = []
        for cd in collectors_data:
            c = Collector.objects.create(**cd)
            collectors.append(c)
        print(f"Membuat {len(collectors)} pengupul")

        # ── Waste Transactions (30 hari) ─────────────────────────
        today = timezone.now().date()
        transaction_count = 0

        for days_ago in range(30):
            date = today - timedelta(days=days_ago)
            num_transactions = random.randint(3, 8)

            for _ in range(num_transactions):
                wt = random.choice(waste_types)
                collector = random.choice(collectors)
                weight = Decimal(str(round(random.uniform(5, 150), 2)))
                price = wt.purchase_price_per_kg + Decimal(
                    str(random.randint(-100, 200))
                )
                price = max(Decimal('100'), price)

                trans_dt = timezone.make_aware(datetime.combine(
                    date,
                    datetime.min.time().replace(
                        hour=random.randint(7, 17),
                        minute=random.randint(0, 59),
                    )
                ))

                WasteTransaction.objects.create(
                    transaction_type='in',
                    collector=collector,
                    waste_type=wt,
                    weight_kg=weight,
                    price_per_kg=price,
                    total_price=weight * price,
                    date=trans_dt,
                    created_by=admin_user,
                )
                transaction_count += 1

            if days_ago % 10 == 0:
                print(f"  Transaksi: hari {30 - days_ago}/30...")

        print(f"Membuat {transaction_count} transaksi pembelian")

        # ── Factory Sales (30 hari) ──────────────────────────────
        sale_count = 0
        factories = [
            'PT Daur Plastik Jaya',
            'PT Kertas Recycle Indonesia',
            'PT Logam Mulia Sejahtera',
            'PT Kaca Bangun Nusantara',
            'PT E-Waste Processing',
            'CV Plastik Mandiri',
        ]

        for days_ago in range(30):
            date = today - timedelta(days=days_ago)
            num_sales = random.randint(1, 3)

            for _ in range(num_sales):
                wt = random.choice(waste_types)
                weight = Decimal(str(round(random.uniform(50, 500), 2)))
                price = wt.selling_price_per_kg + Decimal(
                    str(random.randint(-200, 500))
                )
                price = max(Decimal('200'), price)
                delivery = Decimal(str(random.randint(20000, 150000)))

                FactorySale.objects.create(
                    waste_type=wt,
                    factory_name=random.choice(factories),
                    weight_kg=weight,
                    price_per_kg=price,
                    total_price=weight * price,
                    date=date,
                    delivery_fee=delivery,
                    payment_status=random.choice(
                        ['paid', 'paid', 'paid', 'pending', 'partial']
                    ),
                    created_by=admin_user,
                )
                sale_count += 1

        print(f"Membuat {sale_count} penjualan ke pabrik")

        # ── Operational Costs (30 hari) ──────────────────────────
        opex_count = 0
        opex_data = [
            ('transport', 'Biaya bensin pickup sampah', 75000),
            ('transport', 'Sewa truk pengiriman', 200000),
            ('rent', 'Sewa gudang bulanan', 3000000),
            ('salary', 'Gaji karyawan harian', 150000),
            ('salary', 'Gaji helper', 100000),
            ('utility', 'Listrik gudang', 350000),
            ('utility', 'Air bersih', 100000),
            ('equipment', 'Timbangan digital', 500000),
            ('equipment', 'Karung plastik (50 pcs)', 250000),
            ('maintenance', 'Perbaikan atap gudang', 450000),
            ('other', 'Biaya telepon & internet', 200000),
            ('other', 'Konsumsi karyawan', 75000),
        ]

        for days_ago in range(30):
            date = today - timedelta(days=days_ago)
            num_costs = random.randint(2, 4)

            for _ in range(num_costs):
                cat, desc, amount = random.choice(opex_data)
                amount = max(
                    Decimal('10000'),
                    Decimal(str(amount + random.randint(-20000, 30000)))
                )

                OperationalCost.objects.create(
                    category=cat,
                    description=desc,
                    amount=amount,
                    date=date,
                    created_by=admin_user,
                )
                opex_count += 1

        print(f"Membuat {opex_count} biaya operasional")

    # ── Selesai ──────────────────────────────────────────────────
    print("\n=== SEED DATA SELESAI ===")


if __name__ == '__main__':
    seed()