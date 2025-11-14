from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from .models import Product, Sale, SaleItem, StockBatch, Alert
from django.utils import timezone
from django.db.models import Sum, F

# Create your views here.

def landing_page(request):
    """
    This is the main homepage (your flowchart's 'Landing Page').
    """
    # Just shows the simple landing_page.html template
    return render(request, 'APP/landing_page.html')

def finance_tracker(request):
    """
    This page shows 'Today's Profit', 'Revenue vs COGS', and 'Profit Makers'.
    """
    today = timezone.now().date()
    
    # 1. Calculate Today's Profit
    # Get all sales from today
    sales_today = Sale.objects.filter(sale_date__date=today)
    
    # Calculate total revenue and total cost of goods sold (COGS) for today
    total_revenue_today = sales_today.aggregate(total=Sum('total_price'))['total'] or 0
    total_cogs_today = 0
    
    for sale in sales_today:
        for item in sale.items.all():
            # Add the cost of this specific batch to the COGS
            total_cogs_today += item.stock_batch.cost_price * item.quantity
            
    todays_profit = total_revenue_today - total_cogs_today

    # 2. Revenue vs COGS (can be expanded for a chart)
    revenue_vs_cogs = {
        'revenue': total_revenue_today,
        'cogs': total_cogs_today,
        'profit': todays_profit
    }

    # 3. Profit Makers (Top 5 profitable products today)
    # This is a more complex query, so we'll do a simple version
    # Get all sale items from today and annotate profit
    profit_makers_query = SaleItem.objects.filter(sale__sale_date__date=today).annotate(
        profit_per_item=(F('price_per_unit') - F('stock_batch__cost_price')) * F('quantity')
    ).values('product__name').annotate(total_profit=Sum('total_profit')).order_by('-total_profit')[:5]

    profit_makers = list(profit_makers_query)
    
    # The 'context' is the data we send to the HTML page
    context = {
        'todays_profit': todays_profit,
        'revenue_vs_cogs': revenue_vs_cogs,
        'profit_makers': profit_makers,
    }
    
    return render(request, 'APP/finance_tracker.html', context)

def ai_advisor(request):
    """
    This page shows 'Reorder Suggestions', 'Waste Alerts', and 'Trend Alerts'.
    """
    
    # 1. Get Waste Alerts (expiring within 7 days)
    seven_days_from_now = timezone.now() + timezone.timedelta(days=7)
    waste_alerts = StockBatch.objects.filter(
        expiry_date__lte=seven_days_from_now,
        current_stock__gt=0
    ).order_by('expiry_date')

    # 2. Get Reorder Suggestions (low stock)
    # We find products where total stock is below its reorder_level
    products = Product.objects.all()
    reorder_suggestions = []
    for product in products:
        total_stock = product.stock_batches.aggregate(total=Sum('current_stock'))['total'] or 0
        if total_stock < product.reorder_level:
            reorder_suggestions.append({
                'name': product.name,
                'current_stock': total_stock,
                'reorder_level': product.reorder_level
            })

    # 3. Trend Alerts (e.g., selling faster than usual)
    # This requires more complex logic (e.g., comparing last 7 days vs 30 days)
    # For now, we'll just show a placeholder
    trend_alerts = [
        {'product_name': 'Placeholder Product', 'message': 'Selling 50% faster than average.'}
    ]

    # You would also create Alert objects here to save them
    # Example: Alert.objects.create(alert_type='WASTE', message='...')

    context = {
        'waste_alerts': waste_alerts,
        'reorder_suggestions': reorder_suggestions,
        'trend_alerts': trend_alerts,
    }
    
    return render(request, 'APP/ai_advisor.html', context)


# --- This is your API Endpoint ---

def scan_product_api(request, barcode):
    """
    This is an API endpoint. It doesn't show a webpage.
    It returns JSON data for your phone scanner.
    """
    data = {}
    try:
        # Find the product by its barcode
        product = Product.objects.get(barcode=barcode)
        
        # Find the most relevant stock batch (e.g., oldest one with stock)
        # This uses FIFO (First-In, First-Out)
        available_stock = StockBatch.objects.filter(
            product=product, 
            current_stock__gt=0
        ).order_by('expiry_date').first() # Sell oldest/soonest-to-expire first

        if available_stock:
            data = {
                'status': 'found',
                'product_id': product.id,
                'name': product.name,
                'description': product.description,
                'selling_price': product.selling_price,
                'stock_batch_id': available_stock.id,
                'available_stock_in_batch': available_stock.current_stock
            }
        else:
            data = {
                'status': 'not_in_stock',
                'name': product.name,
                'message': 'This product is out of stock.'
            }
            
    except Product.DoesNotExist:
        # Product's barcode isn't in our database
        data = {
            'status': 'not_found',
            'message': 'Barcode not found in database.'
        }
    except Exception as e:
        data = {
            'status': 'error',
            'message': str(e)
        }

def login_page(request):
    # This view just shows the login page.
    return render(request, 'APP/login.html')

    
    # Return the data as a JSON object
    return JsonResponse(data)