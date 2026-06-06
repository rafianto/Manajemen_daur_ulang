from django import forms
from django.db.models import Sum # Tambahkan import ini
from .models import Collector, WasteType, WasteTransaction, OperationalCost, FactorySale # Pastikan WasteTransaction ada



class CollectorForm(forms.ModelForm):
    class Meta:
        model = Collector
        fields = ['name', 'phone', 'address', 'id_card_number', 'is_active', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama lengkap pengupul'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '08xxxxxxxxxx'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Alamat lengkap'}),
            'id_card_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nomor KTP'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Catatan tambahan'}),
        }


class WasteTypeForm(forms.ModelForm):
    class Meta:
        model = WasteType
        fields = ['name', 'category', 'purchase_price_per_kg', 'selling_price_per_kg', 'unit', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contoh: Botol PET'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'purchase_price_per_kg': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Harga beli per kg'}),
            'selling_price_per_kg': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Harga jual per kg'}),
            'unit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'kg'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class WasteTransactionInForm(forms.ModelForm):
    """Form untuk transaksi pembelian (sampah masuk dari pengupul)"""
    class Meta:
        model = WasteTransaction
        fields = ['collector', 'waste_type', 'weight_kg', 'price_per_kg', 'date', 'notes']
        widgets = {
            'collector': forms.Select(attrs={'class': 'form-select'}),
            'waste_type': forms.Select(attrs={'class': 'form-select'}),
            'weight_kg': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Berat dalam kg'}),
            'price_per_kg': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Harga beli per kg'}),
            # PERBAIKAN: Tambahkan format='%Y-%m-%dT%H:%M' agar datetime-local muncul nilainya
            'date': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'}, 
                format='%Y-%m-%dT%H:%M'
            ),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['collector'].queryset = Collector.objects.filter(is_active=True)
        self.fields['waste_type'].queryset = WasteType.objects.filter(is_active=True)
        # PERBAIKAN: Tambahkan input_formats agar Django bisa mem-parsing format dari browser
        self.fields['date'].input_formats = ['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M']


class WasteTransactionOutForm(forms.ModelForm):
    """Form untuk transaksi pengeluaran (sampah keluar)"""
    class Meta:
        model = WasteTransaction
        fields = ['waste_type', 'weight_kg', 'price_per_kg', 'date', 'factory_name', 'notes']
        widgets = {
            'waste_type': forms.Select(attrs={'class': 'form-select'}),
            'weight_kg': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Berat dalam kg'}),
            'price_per_kg': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Harga per kg'}),
            # PERBAIKAN: Tambahkan format='%Y-%m-%dT%H:%M'
            'date': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'}, 
                format='%Y-%m-%dT%H:%M'
            ),
            'factory_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama pabrik tujuan'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['waste_type'].queryset = WasteType.objects.filter(is_active=True)
        # PERBAIKAN: Tambahkan input_formats
        self.fields['date'].input_formats = ['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M']


class OperationalCostForm(forms.ModelForm):
    class Meta:
        model = OperationalCost
        fields = ['category', 'description', 'amount', 'date', 'receipt_number', 'notes']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Deskripsi biaya'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Jumlah dalam Rupiah'}),
            # PERBAIKAN: Tambahkan format='%Y-%m-%d' agar input type="date" muncul nilainya
            'date': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'}, 
                format='%Y-%m-%d'
            ),
            'receipt_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nomor kwitansi'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class FactorySaleForm(forms.ModelForm):
    class Meta:
        model = FactorySale
        fields = ['waste_type', 'factory_name', 'weight_kg', 'price_per_kg', 'date', 'delivery_fee', 'payment_status', 'notes']
        widgets = {
            'waste_type': forms.Select(attrs={'class': 'form-select'}),
            'factory_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama pabrik pembeli'}),
            'weight_kg': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Berat dalam kg'}),
            'price_per_kg': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Harga jual per kg'}),
            # PERBAIKAN: Tambahkan format='%Y-%m-%d' agar tanggal muncul saat edit
            'date': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'}, 
                format='%Y-%m-%d'
            ),
            'delivery_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Biaya pengiriman', 'value': '0'}),
            'payment_status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['waste_type'].queryset = WasteType.objects.filter(is_active=True)

    # TAMBAHAN: Validasi Stok Akumulasi di Backend
    def clean(self):
        cleaned_data = super().clean()
        waste_type = cleaned_data.get('waste_type')
        weight_kg = cleaned_data.get('weight_kg')

        if waste_type and weight_kg:
            # 1. Hitung total stok masuk (sampah yang dibeli dari pengupul)
            stock_in = WasteTransaction.objects.filter(
                waste_type=waste_type, 
                transaction_type='in'
            ).aggregate(total=Sum('weight_kg'))['total'] or 0
            
            # 2. Hitung total stok keluar (sampah yang sudah dijual ke pabrik)
            stock_out = FactorySale.objects.filter(
                waste_type=waste_type
            ).aggregate(total=Sum('weight_kg'))['total'] or 0

            # 3. Jika ini proses EDIT (update data), jangan hitung berat lama sebagai pengurang stok
            if self.instance and self.instance.pk:
                stock_out -= self.instance.weight_kg or 0

            # 4. Hitung sisa stok yang tersedia saat ini
            available_stock = stock_in - stock_out

            # 5. Jika berat yang ingin dijual melebihi stok, tolak dan tampilkan error
            if weight_kg > available_stock:
                raise forms.ValidationError(
                    f"Stok tidak mencukupi! Sisa stok {waste_type.name} saat ini adalah "
                    f"{available_stock:.2f} kg, sedangkan Anda mencoba menjual {weight_kg} kg."
                )

        return cleaned_data