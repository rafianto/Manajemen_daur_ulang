from django.contrib import admin
from .models import Collector, WasteType, WasteTransaction, OperationalCost, FactorySale


@admin.register(Collector)
class CollectorAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'id_card_number', 'join_date', 'is_active']
    list_filter = ['is_active', 'join_date']
    search_fields = ['name', 'phone', 'id_card_number']


@admin.register(WasteType)
class WasteTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'purchase_price_per_kg', 'selling_price_per_kg', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name']


@admin.register(WasteTransaction)
class WasteTransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_type', 'waste_type', 'weight_kg', 'price_per_kg', 'total_price', 'date', 'collector']
    list_filter = ['transaction_type', 'waste_type', 'date']
    search_fields = ['waste_type__name', 'collector__name', 'factory_name']
    date_hierarchy = 'date'


@admin.register(OperationalCost)
class OperationalCostAdmin(admin.ModelAdmin):
    list_display = ['category', 'description', 'amount', 'date']
    list_filter = ['category', 'date']
    date_hierarchy = 'date'


@admin.register(FactorySale)
class FactorySaleAdmin(admin.ModelAdmin):
    list_display = ['factory_name', 'waste_type', 'weight_kg', 'total_price', 'delivery_fee', 'payment_status', 'date']
    list_filter = ['payment_status', 'waste_type', 'date']
    search_fields = ['factory_name']
    date_hierarchy = 'date'
