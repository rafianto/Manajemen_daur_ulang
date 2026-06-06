from django.urls import path
from . import views

app_name = 'waste'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    path('cashflow/', views.cashflow_dashboard, name='cashflow_dashboard'),
    path('sales-dashboard/', views.sales_dashboard, name='sales_dashboard'),
    path('stock/', views.stock_view, name='stock_view'),

    # Collectors (Pengupul)
    path('collectors/', views.collector_list, name='collector_list'),
    path('collectors/create/', views.collector_create, name='collector_create'),
    path('collectors/<int:pk>/edit/', views.collector_update, name='collector_update'),
    path('collectors/<int:pk>/', views.collector_detail, name='collector_detail'),

    # Waste Types (Jenis Sampah)
    path('waste-types/', views.waste_type_list, name='waste_type_list'),
    path('waste-types/create/', views.waste_type_create, name='waste_type_create'),
    path('waste-types/<int:pk>/edit/', views.waste_type_update, name='waste_type_update'),

    # Transactions (Transaksi)
    path('transactions/', views.transaction_list, name='transaction_list'),
    path('transactions/in/create/', views.transaction_in_create, name='transaction_in_create'),
    path('transactions/out/create/', views.transaction_out_create, name='transaction_out_create'),

    # Operational Costs (Biaya Operasional)
    path('operational-costs/', views.operational_cost_list, name='operational_cost_list'),
    path('operational-costs/create/', views.operational_cost_create, name='operational_cost_create'),

    # Factory Sales (Penjualan ke Pabrik)
    path('factory-sales/', views.factory_sale_list, name='factory_sale_list'),
    path('factory-sales/create/', views.factory_sale_create, name='factory_sale_create'),
    path('factory-sales/<int:pk>/edit/', views.factory_sale_update, name='factory_sale_update'),

    path('api/waste-stock/<int:pk>/', views.get_waste_stock_api, name='waste_stock_api'),
    path('api/waste-info/<int:pk>/', views.get_waste_info_api, name='waste_info_api'),
]
