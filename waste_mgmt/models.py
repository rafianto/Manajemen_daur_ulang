from django.db import models
from django.core.validators import MinValueValidator


class Collector(models.Model):
    """Model untuk data anggota pengupul barang bekas"""
    name = models.CharField('Nama Pengupul', max_length=200)
    phone = models.CharField('No. Telepon', max_length=20, blank=True)
    address = models.TextField('Alamat', blank=True)
    id_card_number = models.CharField('No. KTP', max_length=30, blank=True)
    join_date = models.DateField('Tanggal Bergabung', auto_now_add=True)
    is_active = models.BooleanField('Aktif', default=True)
    notes = models.TextField('Catatan', blank=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Pengupul'
        verbose_name_plural = 'Data Pengupul'

    def __str__(self):
        return self.name

    def total_supplied_kg(self):
        """Total sampah yang disuplai oleh pengupul ini (dalam kg)"""
        return self.transactions.filter(transaction_type='in').aggregate(
            total=models.Sum('weight_kg')
        )['total'] or 0

    def total_payment(self):
        """Total pembayaran ke pengupul ini"""
        return self.transactions.filter(transaction_type='in').aggregate(
            total=models.Sum('total_price')
        )['total'] or 0


class WasteType(models.Model):
    """Model untuk jenis sampah daur ulang"""
    CATEGORY_CHOICES = [
        ('plastik', 'Plastik'),
        ('logam', 'Logam'),
        ('kertas', 'Kertas'),
        ('kaca', 'Kaca'),
        ('elektronik', 'Elektronik'),
        ('tekstil', 'Tekstil'),
        ('organik', 'Organik'),
        ('lainnya', 'Lainnya'),
    ]

    name = models.CharField('Nama Jenis Sampah', max_length=200)
    category = models.CharField('Kategori', max_length=20, choices=CATEGORY_CHOICES, default='lainnya')
    purchase_price_per_kg = models.DecimalField(
        'Harga Beli per Kg (Rp)',
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    selling_price_per_kg = models.DecimalField(
        'Harga Jual per Kg (Rp)',
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    unit = models.CharField('Satuan', max_length=20, default='kg')
    description = models.TextField('Deskripsi', blank=True)
    is_active = models.BooleanField('Aktif', default=True)

    class Meta:
        ordering = ['category', 'name']
        verbose_name = 'Jenis Sampah'
        verbose_name_plural = 'Data Jenis Sampah'

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"

    def margin_per_kg(self):
        return self.selling_price_per_kg - self.purchase_price_per_kg


class WasteTransaction(models.Model):
    """Model untuk transaksi masuk/keluar sampah"""
    TRANSACTION_TYPE_CHOICES = [
        ('in', 'Pembelian (Masuk)'),
        ('out', 'Penjualan (Keluar)'),
    ]

    transaction_type = models.CharField('Jenis Transaksi', max_length=3, choices=TRANSACTION_TYPE_CHOICES)
    collector = models.ForeignKey(
        Collector, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='transactions', verbose_name='Pengupul'
    )
    waste_type = models.ForeignKey(
        WasteType, on_delete=models.PROTECT,
        related_name='transactions', verbose_name='Jenis Sampah'
    )
    weight_kg = models.DecimalField(
        'Berat (Kg)', max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    price_per_kg = models.DecimalField(
        'Harga per Kg (Rp)', max_digits=12, decimal_places=2
    )
    total_price = models.DecimalField(
        'Total Harga (Rp)', max_digits=14, decimal_places=2
    )
    date = models.DateTimeField('Tanggal Transaksi')
    factory_name = models.CharField('Nama Pabrik/Pembeli', max_length=200, blank=True)
    notes = models.TextField('Catatan', blank=True)
    created_at = models.DateTimeField('Dibuat', auto_now_add=True)
    created_by = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True,
        verbose_name='Dibuat Oleh'
    )

    class Meta:
        ordering = ['-date']
        verbose_name = 'Transaksi Sampah'
        verbose_name_plural = 'Data Transaksi Sampah'

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.waste_type.name} - {self.weight_kg} kg"

    def save(self, *args, **kwargs):
        self.total_price = self.weight_kg * self.price_per_kg
        super().save(*args, **kwargs)


class OperationalCost(models.Model):
    """Model untuk biaya operasional"""
    CATEGORY_CHOICES = [
        ('transport', 'Transportasi'),
        ('rent', 'Sewa Tempat'),
        ('salary', 'Gaji Karyawan'),
        ('equipment', 'Peralatan'),
        ('utility', 'Utilitas (Listrik/Air)'),
        ('maintenance', 'Perawatan'),
        ('other', 'Lainnya'),
    ]

    category = models.CharField('Kategori', max_length=20, choices=CATEGORY_CHOICES)
    description = models.CharField('Deskripsi', max_length=300)
    amount = models.DecimalField(
        'Jumlah (Rp)', max_digits=14, decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    date = models.DateField('Tanggal')
    receipt_number = models.CharField('No. Kwitansi', max_length=100, blank=True)
    notes = models.TextField('Catatan', blank=True)
    created_at = models.DateTimeField('Dibuat', auto_now_add=True)
    created_by = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True,
        verbose_name='Dibuat Oleh'
    )

    class Meta:
        ordering = ['-date']
        verbose_name = 'Biaya Operasional'
        verbose_name_plural = 'Data Biaya Operasional'

    def __str__(self):
        return f"{self.get_category_display()} - Rp {self.amount:,.0f} - {self.date}"


class FactorySale(models.Model):
    """Model untuk penjualan ke pabrik"""
    waste_type = models.ForeignKey(
        WasteType, on_delete=models.PROTECT,
        related_name='factory_sales', verbose_name='Jenis Sampah'
    )
    factory_name = models.CharField('Nama Pabrik', max_length=200)
    weight_kg = models.DecimalField(
        'Berat Dijual (Kg)', max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    price_per_kg = models.DecimalField(
        'Harga Jual per Kg (Rp)', max_digits=12, decimal_places=2
    )
    total_price = models.DecimalField(
        'Total Penjualan (Rp)', max_digits=14, decimal_places=2
    )
    date = models.DateField('Tanggal Penjualan')
    delivery_fee = models.DecimalField(
        'Biaya Pengiriman (Rp)', max_digits=12, decimal_places=2, default=0
    )
    payment_status = models.CharField(
        'Status Pembayaran', max_length=20,
        choices=[('pending', 'Belum Dibayar'), ('paid', 'Sudah Dibayar'), ('partial', 'Sebagian')],
        default='pending'
    )
    notes = models.TextField('Catatan', blank=True)
    created_at = models.DateTimeField('Dibuat', auto_now_add=True)
    created_by = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True,
        verbose_name='Dibuat Oleh'
    )

    class Meta:
        ordering = ['-date']
        verbose_name = 'Penjualan ke Pabrik'
        verbose_name_plural = 'Data Penjualan ke Pabrik'

    def __str__(self):
        return f"{self.factory_name} - {self.waste_type.name} - {self.weight_kg} kg"

    def save(self, *args, **kwargs):
        self.total_price = self.weight_kg * self.price_per_kg
        super().save(*args, **kwargs)

    def net_revenue(self):
        return self.total_price - self.delivery_fee
