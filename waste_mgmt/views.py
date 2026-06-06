from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, F, Q, Max # Ditambahkan Max
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal
from collections import defaultdict
import json
import calendar

from django.http import JsonResponse
from django.db import transaction

from .models import Collector, WasteType, WasteTransaction, OperationalCost, FactorySale
from .forms import (
    CollectorForm, WasteTypeForm, WasteTransactionInForm,
    WasteTransactionOutForm, OperationalCostForm, FactorySaleForm
)


# ===================== HELPER =====================

def _get_period_key(date_val, period):
    """Convert a date to a period key string for grouping."""
    if period == 'daily':
        return date_val.strftime('%Y-%m-%d')
    elif period == 'weekly':
        iso = date_val.isocalendar()
        return f"{iso[0]}-W{iso[1]:02d}"
    else:  # monthly
        return date_val.strftime('%Y-%m')


def _format_period_label(key, period):
    """Format a period key for display."""
    if period == 'daily':
        parts = key.split('-')
        return f"{parts[2]}/{parts[1]}"
    elif period == 'weekly':
        parts = key.split('-W')
        return f"W{parts[1]}/{parts[0][2:]}"
    else:
        parts = key.split('-')
        months = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Ags', 'Sep', 'Okt', 'Nov', 'Des']
        return f"{months[int(parts[1])]} {parts[0]}"


def _generate_period_range(start_date, end_date, period):
    """Generate all period keys between start and end date."""
    keys = []
    current = start_date
    while current <= end_date:
        keys.append(_get_period_key(current, period))
        if period == 'daily':
            current += timedelta(days=1)
        elif period == 'weekly':
            current += timedelta(weeks=1)
        else:
            # Move to next month
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)
    return keys


# ===================== DASHBOARD =====================

@login_required
def dashboard(request):
    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    start_of_month = today.replace(day=1)

    # Summary cards
    total_sales_today = FactorySale.objects.filter(date=today).aggregate(
        total=Sum('total_price'))['total'] or Decimal('0')
    total_sales_week = FactorySale.objects.filter(date__gte=start_of_week).aggregate(
        total=Sum('total_price'))['total'] or Decimal('0')
    total_sales_month = FactorySale.objects.filter(date__gte=start_of_month).aggregate(
        total=Sum('total_price'))['total'] or Decimal('0')

    total_purchase_today = WasteTransaction.objects.filter(
        transaction_type='in', date__date=today).aggregate(
        total=Sum('total_price'))['total'] or Decimal('0')
    total_purchase_week = WasteTransaction.objects.filter(
        transaction_type='in', date__date__gte=start_of_week).aggregate(
        total=Sum('total_price'))['total'] or Decimal('0')
    total_purchase_month = WasteTransaction.objects.filter(
        transaction_type='in', date__date__gte=start_of_month).aggregate(
        total=Sum('total_price'))['total'] or Decimal('0')

    total_opex_today = OperationalCost.objects.filter(date=today).aggregate(
        total=Sum('amount'))['total'] or Decimal('0')
    total_opex_week = OperationalCost.objects.filter(date__gte=start_of_week).aggregate(
        total=Sum('amount'))['total'] or Decimal('0')
    total_opex_month = OperationalCost.objects.filter(date__gte=start_of_month).aggregate(
        total=Sum('amount'))['total'] or Decimal('0')

    # Net cashflow
    net_cashflow_today = total_sales_today - total_purchase_today - total_opex_today
    net_cashflow_week = total_sales_week - total_purchase_week - total_opex_week
    net_cashflow_month = total_sales_month - total_purchase_month - total_opex_month

    # Accumulation per waste type
    waste_accumulation = []
    for wt in WasteType.objects.filter(is_active=True):
        total_in = WasteTransaction.objects.filter(
            waste_type=wt, transaction_type='in').aggregate(
            total=Sum('weight_kg'))['total'] or Decimal('0')
        total_out = WasteTransaction.objects.filter(
            waste_type=wt, transaction_type='out').aggregate(
            total=Sum('weight_kg'))['total'] or Decimal('0')
        factory_out = FactorySale.objects.filter(
            waste_type=wt).aggregate(
            total=Sum('weight_kg'))['total'] or Decimal('0')
        stock = total_in - total_out - factory_out
        if stock < 0:
            stock = Decimal('0')
        waste_accumulation.append({
            'waste_type': wt,
            'total_in': total_in,
            'total_out': total_out + factory_out,
            'stock': stock,
        })

    # Sales per waste type
    sales_by_type_daily = FactorySale.objects.filter(
        date=today
    ).values('waste_type__name').annotate(
        total=Sum('total_price'),
        weight=Sum('weight_kg')
    ).order_by('-total')

    sales_by_type_weekly = FactorySale.objects.filter(
        date__gte=start_of_week
    ).values('waste_type__name').annotate(
        total=Sum('total_price'),
        weight=Sum('weight_kg')
    ).order_by('-total')

    sales_by_type_monthly = FactorySale.objects.filter(
        date__gte=start_of_month
    ).values('waste_type__name').annotate(
        total=Sum('total_price'),
        weight=Sum('weight_kg')
    ).order_by('-total')

    # Recent transactions
    recent_transactions = WasteTransaction.objects.all()[:10]
    recent_sales = FactorySale.objects.all()[:5]
    recent_opex = OperationalCost.objects.all()[:5]

    # Active collectors count
    active_collectors = Collector.objects.filter(is_active=True).count()
    active_waste_types = WasteType.objects.filter(is_active=True).count()

    context = {
        'today': today,
        'total_sales_today': total_sales_today,
        'total_sales_week': total_sales_week,
        'total_sales_month': total_sales_month,
        'total_purchase_today': total_purchase_today,
        'total_purchase_week': total_purchase_week,
        'total_purchase_month': total_purchase_month,
        'total_opex_today': total_opex_today,
        'total_opex_week': total_opex_week,
        'total_opex_month': total_opex_month,
        'net_cashflow_today': net_cashflow_today,
        'net_cashflow_week': net_cashflow_week,
        'net_cashflow_month': net_cashflow_month,
        'waste_accumulation': waste_accumulation,
        'sales_by_type_daily': sales_by_type_daily,
        'sales_by_type_weekly': sales_by_type_weekly,
        'sales_by_type_monthly': sales_by_type_monthly,
        'recent_transactions': recent_transactions,
        'recent_sales': recent_sales,
        'recent_opex': recent_opex,
        'active_collectors': active_collectors,
        'active_waste_types': active_waste_types,
    }
    return render(request, 'waste_mgmt/dashboard.html', context)


# ===================== CASHFLOW DASHBOARD =====================

@login_required
def cashflow_dashboard(request):
    today = timezone.now().date()
    period = request.GET.get('period', 'daily')

    if period == 'daily':
        start_date = today - timedelta(days=29)
    elif period == 'weekly':
        start_date = today - timedelta(weeks=11)
    else:
        start_date = (today - timedelta(days=365)).replace(day=1)

    # Fetch raw data
    sales_qs = FactorySale.objects.filter(date__gte=start_date, date__lte=today).values('date', 'total_price')
    purchase_qs = WasteTransaction.objects.filter(
        transaction_type='in', date__date__gte=start_date, date__date__lte=today
    ).values('date', 'total_price')
    opex_qs = OperationalCost.objects.filter(date__gte=start_date, date__lte=today).values('date', 'amount')

    # Aggregate by period in Python
    sales_by_period = defaultdict(float)
    for item in sales_qs:
        key = _get_period_key(item['date'], period)
        sales_by_period[key] += float(item['total_price'] or 0)

    purchase_by_period = defaultdict(float)
    for item in purchase_qs:
        key = _get_period_key(item['date'].date() if hasattr(item['date'], 'date') else item['date'], period)
        purchase_by_period[key] += float(item['total_price'] or 0)

    opex_by_period = defaultdict(float)
    for item in opex_qs:
        key = _get_period_key(item['date'], period)
        opex_by_period[key] += float(item['amount'] or 0)

    # Generate all periods in range
    all_period_keys = _generate_period_range(start_date, today, period)

    chart_labels = []
    sales_values = []
    purchase_values = []
    opex_values = []
    net_values = []

    for key in all_period_keys:
        chart_labels.append(_format_period_label(key, period))
        s = sales_by_period.get(key, 0)
        pu = purchase_by_period.get(key, 0)
        op = opex_by_period.get(key, 0)
        net = s - pu - op

        sales_values.append(s)
        purchase_values.append(pu)
        opex_values.append(op)
        net_values.append(net)

    context = {
        'period': period,
        'chart_labels': json.dumps(chart_labels),
        'sales_values': json.dumps(sales_values),
        'purchase_values': json.dumps(purchase_values),
        'opex_values': json.dumps(opex_values),
        'net_values': json.dumps(net_values),
        'total_sales': sum(sales_values),
        'total_purchase': sum(purchase_values),
        'total_opex': sum(opex_values),
        'total_net': sum(net_values),
    }
    return render(request, 'waste_mgmt/cashflow.html', context)


# ===================== SALES DASHBOARD =====================

@login_required
def sales_dashboard(request):
    today = timezone.now().date()
    period = request.GET.get('period', 'daily')

    if period == 'daily':
        start_date = today - timedelta(days=29)
    elif period == 'weekly':
        start_date = today - timedelta(weeks=11)
    else:
        start_date = (today - timedelta(days=365)).replace(day=1)

    # Sales by waste type
    sales_by_type = FactorySale.objects.filter(
        date__gte=start_date
    ).values(
        'waste_type__name', 'waste_type__category'
    ).annotate(
        total_price=Sum('total_price'),
        total_weight=Sum('weight_kg'),
        total_delivery=Sum('delivery_fee'),
        count=Count('id')
    ).order_by('-total_price')

    # Sales over time - Python aggregation
    sales_qs = FactorySale.objects.filter(date__gte=start_date, date__lte=today).values('date', 'total_price', 'weight_kg')

    sales_by_period = defaultdict(lambda: {'total': 0, 'weight': 0})
    for item in sales_qs:
        key = _get_period_key(item['date'], period)
        sales_by_period[key]['total'] += float(item['total_price'] or 0)
        sales_by_period[key]['weight'] += float(item['weight_kg'] or 0)

    all_period_keys = _generate_period_range(start_date, today, period)

    chart_labels = []
    chart_values = []
    chart_weights = []
    for key in all_period_keys:
        chart_labels.append(_format_period_label(key, period))
        data = sales_by_period.get(key, {'total': 0, 'weight': 0})
        chart_values.append(data['total'])
        chart_weights.append(data['weight'])

    # Top factories
    top_factories = FactorySale.objects.filter(
        date__gte=start_date
    ).values('factory_name').annotate(
        total_price=Sum('total_price'),
        total_weight=Sum('weight_kg'),
        count=Count('id')
    ).order_by('-total_price')[:10]

    # Pending payments
    pending_payments = FactorySale.objects.filter(
        payment_status='pending', date__gte=start_date
    ).aggregate(total=Sum('total_price'))['total'] or Decimal('0')

    context = {
        'period': period,
        'sales_by_type': sales_by_type,
        'chart_labels': json.dumps(chart_labels),
        'chart_values': json.dumps(chart_values),
        'chart_weights': json.dumps(chart_weights),
        'top_factories': top_factories,
        'pending_payments': pending_payments,
        'total_sales': sum(chart_values),
        'total_weight': sum(chart_weights),
    }
    return render(request, 'waste_mgmt/sales_dashboard.html', context)


# ===================== COLLECTOR VIEWS =====================

@login_required
def collector_list(request):
    collectors = Collector.objects.all()
    search = request.GET.get('search', '')
    if search:
        collectors = collectors.filter(
            Q(name__icontains=search) | Q(phone__icontains=search) | Q(id_card_number__icontains=search)
        )
    status = request.GET.get('status', '')
    if status == 'active':
        collectors = collectors.filter(is_active=True)
    elif status == 'inactive':
        collectors = collectors.filter(is_active=False)
    return render(request, 'waste_mgmt/collector_list.html', {
        'collectors': collectors, 'search': search, 'status': status
    })


@login_required
def collector_create(request):
    if request.method == 'POST':
        form = CollectorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Data pengupul berhasil ditambahkan!')
            return redirect('waste:collector_list')
    else:
        form = CollectorForm()
    return render(request, 'waste_mgmt/collector_form.html', {'form': form, 'title': 'Tambah Pengupul'})


@login_required
def collector_update(request, pk):
    collector = get_object_or_404(Collector, pk=pk)
    if request.method == 'POST':
        form = CollectorForm(request.POST, instance=collector)
        if form.is_valid():
            form.save()
            messages.success(request, 'Data pengupul berhasil diperbarui!')
            return redirect('waste:collector_list')
    else:
        form = CollectorForm(instance=collector)
    return render(request, 'waste_mgmt/collector_form.html', {
        'form': form, 'title': 'Edit Pengupul', 'collector': collector
    })


@login_required
def collector_detail(request, pk):
    collector = get_object_or_404(Collector, pk=pk)
    transactions = collector.transactions.all()[:20]
    return render(request, 'waste_mgmt/collector_detail.html', {
        'collector': collector, 'transactions': transactions
    })


# ===================== WASTE TYPE VIEWS =====================

@login_required
def waste_type_list(request):
    waste_types = WasteType.objects.all()
    category = request.GET.get('category', '')
    if category:
        waste_types = waste_types.filter(category=category)
    return render(request, 'waste_mgmt/waste_type_list.html', {
        'waste_types': waste_types, 'category': category
    })


@login_required
def waste_type_create(request):
    if request.method == 'POST':
        form = WasteTypeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Jenis sampah berhasil ditambahkan!')
            return redirect('waste:waste_type_list')
    else:
        form = WasteTypeForm()
    return render(request, 'waste_mgmt/waste_type_form.html', {'form': form, 'title': 'Tambah Jenis Sampah'})


@login_required
def waste_type_update(request, pk):
    waste_type = get_object_or_404(WasteType, pk=pk)
    if request.method == 'POST':
        form = WasteTypeForm(request.POST, instance=waste_type)
        if form.is_valid():
            form.save()
            messages.success(request, 'Jenis sampah berhasil diperbarui!')
            return redirect('waste:waste_type_list')
    else:
        form = WasteTypeForm(instance=waste_type)
    return render(request, 'waste_mgmt/waste_type_form.html', {
        'form': form, 'title': 'Edit Jenis Sampah', 'waste_type': waste_type
    })


# ===================== TRANSACTION VIEWS =====================

@login_required
def transaction_list(request):
    transactions = WasteTransaction.objects.select_related('waste_type', 'collector')
    trans_type = request.GET.get('type', '')
    if trans_type:
        transactions = transactions.filter(transaction_type=trans_type)
    waste_type_id = request.GET.get('waste_type', '')
    if waste_type_id:
        transactions = transactions.filter(waste_type_id=waste_type_id)
    date_from = request.GET.get('date_from', '')
    if date_from:
        transactions = transactions.filter(date__date__gte=date_from)
    date_to = request.GET.get('date_to', '')
    if date_to:
        transactions = transactions.filter(date__date__lte=date_to)
    transactions = transactions[:100]
    return render(request, 'waste_mgmt/transaction_list.html', {
        'transactions': transactions, 'trans_type': trans_type,
        'waste_type_id': waste_type_id, 'date_from': date_from, 'date_to': date_to,
        'waste_types': WasteType.objects.filter(is_active=True),
    })


@login_required
def transaction_in_create(request):
    if request.method == 'POST':
        form = WasteTransactionInForm(request.POST)
        if form.is_valid():
            transaksi = form.save(commit=False)
            transaksi.transaction_type = 'in'
            transaksi.created_by = request.user
            transaksi.total_price = transaksi.weight_kg * transaksi.price_per_kg
            transaksi.save()
            messages.success(request, 'Transaksi pembelian sampah berhasil dicatat!')
            return redirect('waste:transaction_list')
    else:
        form = WasteTransactionInForm()
    return render(request, 'waste_mgmt/transaction_form.html', {
        'form': form, 'title': 'Catat Pembelian Sampah (Masuk)'
    })


@login_required
def transaction_out_create(request):
    if request.method == 'POST':
        form = WasteTransactionOutForm(request.POST)
        if form.is_valid():
            with transaction.atomic(): # Keamanan database jika ada proses kalkulasi
                transaksi = form.save(commit=False)
                transaksi.transaction_type = 'out'
                transaksi.created_by = request.user
                
                # Hitung total harga (gunakan Decimal untuk keamanan angka finansial)
                transaksi.total_price = transaksi.weight_kg * transaksi.price_per_kg
                
                transaksi.save()
                
            messages.success(request, f'Transaksi pengeluaran sampah ({transaksi.waste_type.name}) berhasil dicatat!')
            return redirect('waste:transaction_list')
        else:
            # Jika gagal validasi (misal: stok tidak cukup), tampilkan pesan error
            messages.error(request, 'Gagal menyimpan transaksi. Periksa kembali isian form dan ketersediaan stok.')
    else:
        form = WasteTransactionOutForm()

    return render(request, 'waste_mgmt/transaction_form.html', {
        'form': form, 
        'title': 'Catat Pengeluaran Sampah (Keluar)'
    })


# ===================== OPERATIONAL COST VIEWS =====================

@login_required
def operational_cost_list(request):
    costs = OperationalCost.objects.all()
    category = request.GET.get('category', '')
    if category:
        costs = costs.filter(category=category)
    date_from = request.GET.get('date_from', '')
    if date_from:
        costs = costs.filter(date__gte=date_from)
    date_to = request.GET.get('date_to', '')
    if date_to:
        costs = costs.filter(date__lte=date_to)
    return render(request, 'waste_mgmt/operational_cost_list.html', {
        'costs': costs, 'category': category, 'date_from': date_from, 'date_to': date_to,
    })


@login_required
def operational_cost_create(request):
    if request.method == 'POST':
        form = OperationalCostForm(request.POST)
        if form.is_valid():
            cost = form.save(commit=False)
            cost.created_by = request.user
            cost.save()
            messages.success(request, 'Biaya operasional berhasil dicatat!')
            return redirect('waste:operational_cost_list')
    else:
        form = OperationalCostForm()
    return render(request, 'waste_mgmt/operational_cost_form.html', {
        'form': form, 'title': 'Catat Biaya Operasional'
    })


# ===================== FACTORY SALE VIEWS =====================

@login_required
def factory_sale_list(request):
    sales = FactorySale.objects.select_related('waste_type')
    payment_status = request.GET.get('payment_status', '')
    if payment_status:
        sales = sales.filter(payment_status=payment_status)
    date_from = request.GET.get('date_from', '')
    if date_from:
        sales = sales.filter(date__gte=date_from)
    date_to = request.GET.get('date_to', '')
    if date_to:
        sales = sales.filter(date__lte=date_to)
    return render(request, 'waste_mgmt/factory_sale_list.html', {
        'sales': sales, 'payment_status': payment_status,
        'date_from': date_from, 'date_to': date_to,
    })


@login_required
def factory_sale_create(request):
    if request.method == 'POST':
        form = FactorySaleForm(request.POST)
        if form.is_valid():
            sale = form.save(commit=False)
            sale.created_by = request.user
            sale.total_price = sale.weight_kg * sale.price_per_kg
            sale.save()
            messages.success(request, 'Penjualan ke pabrik berhasil dicatat!')
            return redirect('waste:factory_sale_list')
    else:
        form = FactorySaleForm()
    return render(request, 'waste_mgmt/factory_sale_form.html', {
        'form': form, 'title': 'Catat Penjualan ke Pabrik'
    })


@login_required
def factory_sale_update(request, pk):
    sale = get_object_or_404(FactorySale, pk=pk)
    if request.method == 'POST':
        form = FactorySaleForm(request.POST, instance=sale)
        if form.is_valid():
            sale = form.save(commit=False)
            sale.total_price = sale.weight_kg * sale.price_per_kg
            sale.save()
            messages.success(request, 'Data penjualan berhasil diperbarui!')
            return redirect('waste:factory_sale_list')
    else:
        form = FactorySaleForm(instance=sale)
    return render(request, 'waste_mgmt/factory_sale_form.html', {
        'form': form, 'title': 'Edit Penjualan ke Pabrik', 'sale': sale
    })


# ===================== STOCK / ACCUMULATION =====================

@login_required
def stock_view(request):
    stocks = []
    for wt in WasteType.objects.filter(is_active=True):
        total_in = WasteTransaction.objects.filter(
            waste_type=wt, transaction_type='in').aggregate(
            total=Sum('weight_kg'))['total'] or Decimal('0')
        total_out_transaction = WasteTransaction.objects.filter(
            waste_type=wt, transaction_type='out').aggregate(
            total=Sum('weight_kg'))['total'] or Decimal('0')
        total_out_factory = FactorySale.objects.filter(
            waste_type=wt).aggregate(
            total=Sum('weight_kg'))['total'] or Decimal('0')
        total_out = total_out_transaction + total_out_factory
        stock = total_in - total_out
        if stock < 0:
            stock = Decimal('0')
        stock_value = stock * wt.purchase_price_per_kg
        stocks.append({
            'waste_type': wt,
            'total_in': total_in,
            'total_out': total_out,
            'stock': stock,
            'stock_value': stock_value,
            'margin_per_kg': wt.margin_per_kg(),
        })
    return render(request, 'waste_mgmt/stock.html', {'stocks': stocks})


# ===================== API ENDPOINTS =====================

@login_required
def get_waste_stock_api(request, pk):
    """API untuk cek stok dan harga tertinggi untuk transaksi keluar"""
    try:
        waste_type = WasteType.objects.get(pk=pk)
        
        # 1. Hitung Stok Akumulasi
        stock_in = WasteTransaction.objects.filter(
            waste_type=waste_type, transaction_type='in'
        ).aggregate(total=Sum('weight_kg'))['total'] or 0
        
        stock_out_trans = WasteTransaction.objects.filter(
            waste_type=waste_type, transaction_type='out'
        ).aggregate(total=Sum('weight_kg'))['total'] or 0
        
        stock_out_factory = FactorySale.objects.filter(
            waste_type=waste_type
        ).aggregate(total=Sum('weight_kg'))['total'] or 0
        
        available_stock = stock_in - stock_out_trans - stock_out_factory
        
        # Pastikan stok tidak min
        if available_stock < 0:
            available_stock = 0

        # 2. Ambil Harga Jual Tertinggi dari Histori Transaksi Keluar
        highest_price_data = WasteTransaction.objects.filter(
            waste_type=waste_type, 
            transaction_type='out'
        ).aggregate(max_price=Max('price_per_kg'))
        
        # Jika belum ada histori keluar, gunakan harga jual default (selling_price)
        highest_price = highest_price_data['max_price'] if highest_price_data['max_price'] else waste_type.selling_price_per_kg

        return JsonResponse({
            'available_stock': float(available_stock),
            'highest_price': float(highest_price),
            'default_selling_price': float(waste_type.selling_price_per_kg),
        })
    except WasteType.DoesNotExist:
        return JsonResponse({'error': 'Jenis sampah tidak ditemukan'}, status=404)


@login_required
def get_waste_info_api(request, pk):
    """API untuk mendapatkan stok dan harga jual TERTINGGI ke pabrik"""
    try:
        waste_type = WasteType.objects.get(pk=pk)
        
        # 1. Hitung Stok Akumulasi (Total Masuk - Keluar Transaksi - Keluar Pabrik)
        stock_in = WasteTransaction.objects.filter(
            waste_type=waste_type, transaction_type='in'
        ).aggregate(total=Sum('weight_kg'))['total'] or 0
        
        stock_out_trans = WasteTransaction.objects.filter(
            waste_type=waste_type, transaction_type='out'
        ).aggregate(total=Sum('weight_kg'))['total'] or 0
        
        stock_out_factory = FactorySale.objects.filter(
            waste_type=waste_type
        ).aggregate(total=Sum('weight_kg'))['total'] or 0
        
        available_stock = stock_in - stock_out_trans - stock_out_factory
        if available_stock < 0:
            available_stock = 0

        # 2. Ambil Harga Jual TERTINGGI dari Riwayat Penjualan ke Pabrik
        highest_price_data = FactorySale.objects.filter(
            waste_type=waste_type
        ).aggregate(max_price=Max('price_per_kg'))
        
        # Jika belum ada riwayat jual ke pabrik, gunakan harga jual default
        highest_price = highest_price_data['max_price'] if highest_price_data['max_price'] else waste_type.selling_price_per_kg

        return JsonResponse({
            'available_stock': float(available_stock),
            'highest_price': float(highest_price),
            'default_price': float(waste_type.selling_price_per_kg)
        })
    except WasteType.DoesNotExist:
        return JsonResponse({'error': 'Jenis sampah tidak ditemukan'}, status=404)