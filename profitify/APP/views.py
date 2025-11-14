from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from .models import Product, Sale, SaleItem, StockBatch, Alert
from django.utils import timezone
from django.db.models import Sum, F
import json # We will use this later, it's fine to import now
from django.urls import reverse

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

def scan_barcode_api(request):
    """
    Receives a barcode via AJAX/Fetch, checks the database, 
    and returns a JSON response with the correct redirect URL.
    """
    if request.method == 'POST':
        try:
            # Load the JSON body sent by the JavaScript scanner
            data = json.loads(request.body.decode('utf-8'))
            barcode = data.get('barcode')
            
            if not barcode:
                return JsonResponse({'status': 'error', 'message': 'No barcode provided'}, status=400)
            
            # 1. Try to find the product
            # FIXED: using correct 'quantity' field
            product = Product.objects.get(barcode=barcode)
            
            # 2. FOUND! Return the Sell Product URL
            # We use 'reverse' to dynamically get the URL based on the name
            sell_url = reverse('sell-product-page', kwargs={'product_id': product.id})
            
            return JsonResponse({
                'status': 'found',
                'redirect_url': sell_url
            })
            
        except Product.DoesNotExist:
            # 3. NOT FOUND! Return the Add Product URL
            add_url = reverse('add-product-page')
            return JsonResponse({
                'status': 'not_found',
                'redirect_url': add_url
            })
        
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def add_product(request):
    """
    Handles both showing the 'add product' form and saving the new product.
    """
    context = {} # <-- FIXED: Define context for the GET request
    
    if request.method == 'POST':
        # --- (The rest of your POST saving logic would go here) ---
        print("Form submitted!")
        return redirect('dashboard-page')
    else:
        # This is the GET request to show the form
        return render(request, 'APP/add_product.html', context)

def sell_product(request, product_id):
    """
    Handles showing the 'sell product' page (pre-filled) and saving the sale.
    This function is now 100% complete and saves data.
    """
    from .models import Product, Sale, SaleItem, StockBatch
    from django.db import transaction # Needed for reliable saving
    
    # Get the product the user is trying to sell
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        # If product ID is invalid, send them back to the dashboard
        return redirect('dashboard-page')
        
    # Get the best batch to sell from (First-In, First-Out/Soonest Expiry)
    available_batch = StockBatch.objects.filter(
        product=product,
        quantity__gt=0
    ).order_by('expiry_date').first()

    context = {
        'product': product,
        'batch': available_batch,
        'error_message': None,
        'success_message': None,
    }

    if request.method == 'POST':
        try:
            quantity_sold = int(request.POST.get('quantity_sold'))
        except (ValueError, TypeError):
            context['error_message'] = "Invalid quantity entered."
            return render(request, 'APP/sell-product.html', context)
            
        if quantity_sold <= 0:
            context['error_message'] = "Quantity must be greater than zero."
            return render(request, 'APP/sell-product.html', context)

        if not available_batch or available_batch.quantity < quantity_sold:
            context['error_message'] = f"Not enough stock. Available: {available_batch.quantity if available_batch else 0}"
            return render(request, 'APP/sell-product.html', context)

        # --- DATA SAVING LOGIC ---
        with transaction.atomic():
            # 1. Create the Sale record
            cost = available_batch.cost_price
            revenue = product.selling_price
            
            total_amount = revenue * quantity_sold
            total_profit = (revenue - cost) * quantity_sold
            
            sale = Sale.objects.create(
                total_amount=total_amount,
                total_profit=total_profit,
                # In a real app, user_id would be pulled from request.user
                user_id="manual_sale_user" 
            )

            # 2. Create the SaleItem record
            SaleItem.objects.create(
                sale=sale,
                product=product,
                stock_batch=available_batch,
                quantity=quantity_sold,
                price_at_sale=revenue,
                cost_at_sale=cost
            )

            # 3. Update the Stock Batch (inventory reduction)
            available_batch.quantity -= quantity_sold
            available_batch.save()
        
        # Success! Redirect to the dashboard
        return redirect('dashboard-page') 

    # This is a GET request to show the form
    return render(request, 'APP/sell-product.html', context)
    
    return JsonResponse(data)