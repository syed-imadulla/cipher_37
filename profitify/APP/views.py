from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from .models import Product, Sale, SaleItem, StockBatch, Alert
from django.utils import timezone
from django.db.models import Sum, F
import json # We will use this later, it's fine to import now

# Create your views here.

def landing_page(request):
    """
    This is the main homepage.
    """
    return render(request, 'APP/landing_page.html')

def login_page(request):
    """
    This view just shows the login page.
    """
    return render(request, 'APP/login.html')

def dashboard(request):
    """
    This view just shows the dashboard page.
    """
    return render(request, 'APP/dashboard.html')

def finance_tracker(request):
    """
    This page shows 'Today's Profit', 'Revenue vs COGS', and 'Profit Makers'.
    (This function is now 100% corrected)
    """
    today = timezone.now().date()
    
    sales_today = Sale.objects.filter(sale_timestamp__date=today)
    
    total_revenue_today = sales_today.aggregate(total=Sum('total_amount'))['total'] or 0
    total_cogs_today = 0
    
    for sale in sales_today:
        for item in sale.items.all():
            total_cogs_today += item.cost_at_sale * item.quantity 
            
    todays_profit = total_revenue_today - total_cogs_today

    revenue_vs_cogs = {
        'revenue': total_revenue_today,
        'cogs': total_cogs_today,
        'profit': todays_profit
    }

    profit_makers_query = SaleItem.objects.filter(sale__sale_timestamp__date=today).annotate(
        profit_per_item=(F('price_at_sale') - F('cost_at_sale')) * F('quantity')
    ).values('product__product_name').annotate(total_profit=Sum('profit_per_item')).order_by('-total_profit')[:5]

    profit_makers = list(profit_makers_query)
    
    context = {
        'todays_profit': todays_profit,
        'revenue_vs_cogs': revenue_vs_cogs,
        'profit_makers': profit_makers,
    }
    
    return render(request, 'APP/finance_tracker.html', context)

def ai_advisor(request):
    """
    This page shows 'Reorder Suggestions', 'Waste Alerts', and 'Trend Alerts'.
    (This is the simple, corrected version)
    """
    
    # 1. Get Waste Alerts (expiring within 7 days)
    seven_days_from_now = timezone.now() + timezone.timedelta(days=7)
    # FIXED: current_stock to quantity
    waste_alerts_query = StockBatch.objects.filter(
        expiry_date__lte=seven_days_from_now,
        quantity__gt=0 
    ).order_by('expiry_date')

    # 2. Get Reorder Suggestions (low stock)
    products = Product.objects.all()
    reorder_list = []
    for product in products:
        # FIXED: current_stock to quantity
        total_stock = product.stock_batches.aggregate(total=Sum('quantity'))['total'] or 0
        if total_stock < product.reorder_level:
            reorder_list.append({
                # FIXED: product.name to product.product_name
                'name': product.product_name, 
                'current_stock': total_stock,
                'reorder_level': product.reorder_level
            })

    # 3. Trend Alerts (Placeholder)
    trend_alerts = [
        {'product_name': 'Placeholder Product', 'message': 'Selling 50% faster than average.'}
    ]

    context = {
        'waste_alerts': waste_alerts_query, # For the HTML list
        'reorder_suggestions': reorder_list, # For the HTML list
        'trend_alerts': trend_alerts,
    }
    
    return render(request, 'APP/ai_advisor.html', context)


# --- This is your API Endpoint ---

def scan_product_api(request, barcode):
    """
    This is an API endpoint for your phone scanner.
    (This function is now 100% corrected)
    """
    data = {}
    try:
        product = Product.objects.get(barcode=barcode)
        
        # FIXED: current_stock to quantity
        available_stock = StockBatch.objects.filter(
            product=product, 
            quantity__gt=0
        ).order_by('expiry_date').first() 

        if available_stock:
            data = {
                'status': 'found',
                'product_id': product.id,
                'name': product.product_name,
                'description': product.description,
                'selling_price': product.selling_price,
                'stock_batch_id': available_stock.id,
                # FIXED: current_stock to quantity
                'available_stock_in_batch': available_stock.quantity 
            }
        else:
            data = {
                'status': 'not_in_stock',
                'name': product.product_name,
                'message': 'This product is out of stock.'
            }
            
    except Product.DoesNotExist:
        data = {
            'status': 'not_found',
            'message': 'Barcode not found in database.'
        }
    except Exception as e:
        data = {
            'status': 'error',
            'message': str(e)
        }

def settings_page(request):
    # This view just shows the settings page.
    # Later you can add logic to save user settings.
    return render(request, 'APP/settings.html')

    return JsonResponse(data)