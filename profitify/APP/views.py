from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum, F
from .models import Product, Sale, SaleItem, StockBatch, Alert
from datetime import timedelta

# Create your views here.

def landing_page(request):
    """
    This will be the main home page for the user.
    """
    # Just renders the main landing page template
    return render(request, 'APP/landing_page.html')

def finance_tracker(request):
    """
    This view provides all the data for the "Finance Tracker" page.
    """
    # 1. Calculate Today's Profit
    today = timezone.now().date()
    sales_today = Sale.objects.filter(sale_timestamp__date=today)
    
    todays_profit = sales_today.aggregate(
        total_profit=Sum('total_profit')
    )['total_profit'] or 0.00

    # 2. Calculate Revenue vs COGS (Cost of Goods Sold)
    # Revenue is the total amount from sales
    todays_revenue = sales_today.aggregate(
        total_revenue=Sum('total_amount')
    )['total_revenue'] or 0.00
    
    # COGS is the cost of the items sold
    todays_cogs = sales_today.aggregate(
        total_cogs=Sum('saleitem__cost_at_sale') * F('saleitem__quantity')
    ).get('total_cogs', 0.00) or 0.00

    # 3. Calculate Profit Metrics (e.g., Gross Margin)
    gross_margin = 0
    if todays_revenue > 0:
        gross_margin = (todays_profit / todays_revenue) * 100

    context = {
        'todays_profit': todays_profit,
        'todays_revenue': todays_revenue,
        'todays_cogs': todays_cogs,
        'gross_margin': round(gross_margin, 2),
    }
    
    return render(request, 'APP/finance_tracker.html', context)

def ai_advisor(request):
    """
    This view finds and displays all alerts for the "AI Advisor" page.
    """
    
    # --- This logic should be run regularly (e.g., daily) ---
    # For the hackathon, we can just run it when the page is visited.
    
    # 1. Find Reorder Alerts
    products_to_reorder = Product.objects.filter(current_stock__lt=F('reorder_level'))
    for product in products_to_reorder:
        Alert.objects.get_or_create(
            product=product,
            alert_type='REORDER',
            defaults={'message': f"Stock low ({product.current_stock}). Reorder level is {product.reorder_level}."}
        )
        
    # 2. Find Waste Alerts (Expiry)
    two_weeks_from_now = today + timedelta(days=14)
    expiring_batches = StockBatch.objects.filter(
        expiry_date__lte=two_weeks_from_now,
        quantity__gt=0
    )
    for batch in expiring_batches:
        Alert.objects.get_or_create(
            product=batch.product,
            alert_type='WASTE',
            defaults={'message': f"{batch.quantity} units expiring on {batch.expiry_date.strftime('%Y-%m-%d')}."}
        )

    # --- End of alert generation ---

    # Get all unread alerts to display on the page
    all_alerts = Alert.objects.filter(is_viewed=False).order_by('-created_at')
    
    reorder_alerts = all_alerts.filter(alert_type='REORDER')
    waste_alerts = all_alerts.filter(alert_type='WASTE')
    trend_alerts = all_alerts.filter(alert_type='TREND') # You can add logic for this later

    context = {
        'reorder_alerts': reorder_alerts,
        'waste_alerts': waste_alerts,
        'trend_alerts': trend_alerts,
    }
    return render(request, 'APP/ai_advisor.html', context)


def scan_product_api(request, barcode):
    """
    This is an API endpoint for your scanner.
    It takes a barcode and returns product details as JSON.
    This is what the "Product Found?" box in your flowchart does.
    """
    try:
        product = Product.objects.get(barcode=barcode)
        # "Yes" path: Product Found
        data = {
            'status': 'found',
            'product_id': product.id,
            'product_name': product.product_name,
            'selling_price': product.selling_price,
            'stock': product.current_stock,
        }
    except Product.DoesNotExist:
        # "No" path: Product Not Found
        data = {
            'status': 'not_found',
            'message': 'Product not found. Would you like to add it?'
        }
    
    return JsonResponse(data)

#
# --- You will also need functions for ---
#
# def add_product_page(request):
#   # Show a form to add a new product (your "Show Add Product Page")
#   pass
#
# def finish_sale(request):
#   # This will be a complex view that takes the final cart (as JSON from the frontend)
#   # and creates the Sale and SaleItem objects in the database.
#   # (This matches your "Finish Sale" box)
#   pass
#