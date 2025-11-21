from django.shortcuts import render, redirect 
from django.http import JsonResponse 
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from .models import Product, Sale, SaleItem, StockBatch, Alert
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum, F
import json
import urllib.request
import urllib.parse
from django.conf import settings

from .models import (
    Product,
    StockBatch,
    Sale,
    SaleItem,
    Alert,
)

# -------------------------------------------------------
# BASIC PAGE VIEWS
# -------------------------------------------------------

def landing_page(request):
    return render(request, 'APP/landing_page.html')

def login_page(request):
    return render(request, 'APP/login.html')

def dashboard(request):
    return render(request, 'APP/dashboard.html')

def finance_tracker(request):
    """
    This page shows 'Today's Profit', 'Revenue vs COGS', and 'Profit Makers'.
    """
    today = timezone.now().date()
    
    sales_today = Sale.objects.filter(sale_timestamp__date=today)
    
    total_revenue_today = sales_today.aggregate(total=Sum('total_amount'))['total'] or 0
    total_cogs_today = 0
    
    for sale in sales_today:
        # NOTE: Assumes a reverse relationship 'items' exists from Sale to SaleItem
        for item in sale.items.all(): 
            total_cogs_today += item.cost_at_sale * item.quantity 
            
    todays_profit = total_revenue_today - total_cogs_today

    revenue_vs_cogs = {
        'revenue': total_revenue_today,
        'cogs': total_cogs_today,
        'profit': todays_profit
    }

    # Query to find top 5 profit makers
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
    It prepares JSON data for the Gemini AI.
    """
    from .models import Product, StockBatch
    from django.db.models import Sum
    
    # 1. Get Waste Alerts (expiring within 7 days)
    seven_days_from_now = timezone.now() + timezone.timedelta(days=7)
    waste_alerts_query = StockBatch.objects.filter(
        expiry_date__lte=seven_days_from_now,
        quantity__gt=0 
    ).order_by('expiry_date')

    waste_list = []
    for item in waste_alerts_query:
        waste_list.append({
            'product': item.product.product_name,
            'stock': item.quantity,
            'expiry_date': item.expiry_date.strftime('%Y-%m-%d')
        })

    # 2. Get Reorder Suggestions (low stock)
    products = Product.objects.all()
    reorder_list = []
    for product in products:
        # Accessing the related StockBatch objects via the 'stock_batches' related_name
        total_stock = product.stock_batches.aggregate(total=Sum('quantity'))['total'] or 0
        if total_stock < product.reorder_level: 
            reorder_list.append({
                'name': product.product_name,
                'current_stock': total_stock,
                'reorder_level': product.reorder_level
            })

    # 3. Trend Alerts (Placeholder)
    trend_alerts = [
        {'product_name': 'Sample Product', 'message': 'Selling 50% faster than average.'}
    ]

    context = {
        'waste_alerts': waste_alerts_query,
        'reorder_suggestions': reorder_list,
        'trend_alerts': trend_alerts,
        
        # FINAL AI DATA FOR JAVASCRIPT
        'waste_alerts_json': json.dumps(waste_list),
        'reorder_suggestions_json': json.dumps(reorder_list),
        'trend_alerts_json': json.dumps(trend_alerts),
        'GROQ_API_KEY': settings.GROQ_API_KEY,
    }
    
    return render(request, 'APP/ai_advisor.html', context)

@csrf_exempt
def generate_ai_summary(request):
    """
    Receives JSON data from the frontend (including Trend Alerts), and 
    returns a dynamic mock response based on the real inventory data.
    """
    if request.method == 'POST':
        try:
            # 1. Get the data prepared by the frontend
            data = json.loads(request.body.decode('utf-8'))
            waste_data = data.get('waste_data', [])
            reorder_data = data.get('reorder_data', [])
            trend_data = data.get('trend_data', []) # GETTING TREND DATA
            
            # --- Determine the focus for the summary ---
            
            # Reorder Priority (Highest): Find the first product needing reorder
            low_stock_summary = next((item['name'] for item in reorder_data), None)

            # Waste Priority (High): Is anything expiring?
            is_expiring = bool(waste_data)
            
            # Trend Priority (Moderate): Find the fastest moving product
            fastest_moving_summary = next((item['product_name'] for item in trend_data), None)
            
            # --- Build the prompt (optional for mock, but good practice) ---
            # ... (Prompt building logic here is unchanged, using all data) ...
            
            # 2. --- START DYNAMIC MOCK RESPONSE LOGIC ---

            ai_summary = ""
            
            if low_stock_summary:
                # SCENARIO 1: Immediate Restock Required
                ai_summary = f"SUCCESS: Your inventory has been analyzed. Recommendation: Immediate focus should be restocking '{low_stock_summary}'. Additionally, check {len(waste_data)} item(s) approaching expiry."
            
            elif fastest_moving_summary:
                 # SCENARIO 2: Trend Alert is the Main Concern (No low stock)
                 ai_summary = f"SUCCESS: Inventory is stable. Recommendation: A strong trend is emerging for '{fastest_moving_summary}'. Proactively increase your next order to capitalize on this demand."
            
            elif is_expiring:
                # SCENARIO 3: Only Waste is a concern (No low stock or trend)
                ai_summary = f"SUCCESS: Inventory is stable. Recommendation: {len(waste_data)} item(s) are approaching expiry. Run a flash sale or promotion to clear this stock immediately."
            
            else:
                # SCENARIO 4: Everything is Perfect
                ai_summary = "SUCCESS: All inventory levels are optimal, and no critical alerts are present. Recommendation: Continue monitoring sales and consider diversifying product offerings."
            
            return JsonResponse({'status': 'success', 'summary': ai_summary})
            
            # --- END DYNAMIC MOCK RESPONSE ---

        except Exception as e:
            # Catch general Python errors during data processing
            print(f"Internal Processing Error: {e}")
            return JsonResponse({'status': 'error', 'message': f'Internal Python Error: {str(e)}'}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


@csrf_exempt
def scan_product_api(request, barcode):
    """
    This is an API endpoint for your phone scanner.
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
    
    return JsonResponse(data)


def settings_page(request):
    return render(request, 'APP/settings.html')

@csrf_exempt
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
    Handles both showing the 'add product' form and saving the new product 
    and its initial stock batch.
    """
    context = {}
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # 1. Create the new Product record
                new_product = Product.objects.create(
                    product_name=request.POST.get('product_name'),
                    barcode=request.POST.get('barcode'),
                    selling_price=float(request.POST.get('selling_price')),
                    cost_price=float(request.POST.get('cost_price')),
                    reorder_level=int(request.POST.get('reorder_level')),
                    # Add any other Product fields here
                )
                
                # 2. Create the initial Stock Batch for the product
                initial_quantity = int(request.POST.get('initial_stock_quantity', 0))
                
                if initial_quantity > 0:
                    StockBatch.objects.create(
                        product=new_product,
                        quantity=initial_quantity,
                        cost_price=new_product.cost_price, # Use the product's cost price
                        expiry_date=request.POST.get('expiry_date'), # Assuming this field is in the form
                        date_added=timezone.now().date(),
                    )
                
                # Success! Redirect to the dashboard after adding
                return redirect('dashboard-page')
        
        except ValueError:
            context['error_message'] = "Invalid number format for price, level, or quantity."
        except Exception as e:
            context['error_message'] = f"Database error during creation: {str(e)}"
        
        # If any error occurred, re-render the form with the error message
        return render(request, 'APP/add_product.html', context)
        
    else:
        # This is the GET request to show the form
        return render(request, 'APP/add_product.html', context)
        
# Replace the existing sell_product view with this exact block
def sell_product(request, product_id):
    """
    Handles showing the 'sell product' page (pre-filled) and saving the sale.
    """
    from .models import Product, Sale, SaleItem, StockBatch
    from django.db import transaction

    # Try to find the product, otherwise redirect to dashboard
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return redirect('dashboard-page')

    # Get the best batch to sell from (FIFO / nearest expiry)
    available_batch = StockBatch.objects.filter(
        product=product,
        quantity__gt=0
    ).order_by('expiry_date').first()

    # Use the template that actually exists in your project
    template_name = 'APP/sell_product.html'   # <-- corrected underscore

    context = {
        'product': product,
        'batch': available_batch,
        'error_message': None,
    }

    if request.method == 'POST':
        try:
            quantity_sold = int(request.POST.get('quantity_sold'))
        except (ValueError, TypeError):
            context['error_message'] = "Invalid quantity entered."
            return render(request, template_name, context)

        if quantity_sold <= 0:
            context['error_message'] = "Quantity must be greater than zero."
            return render(request, template_name, context)

        if not available_batch or available_batch.quantity < quantity_sold:
            context['error_message'] = f"Not enough stock. Available: {available_batch.quantity if available_batch else 0}"
            return render(request, template_name, context)

        try:
            with transaction.atomic():
                cost = available_batch.cost_price
                revenue = product.selling_price

                total_amount = revenue * quantity_sold
                total_profit = (revenue - cost) * quantity_sold

                sale = Sale.objects.create(
                    total_amount=total_amount,
                    total_profit=total_profit,
                    user_id="scanner_user"
                )

                SaleItem.objects.create(
                    sale=sale,
                    product=product,
                    quantity=quantity_sold,
                    price_at_sale=revenue,
                    cost_at_sale=cost
                )

                available_batch.quantity -= quantity_sold
                available_batch.save()

            return redirect('dashboard-page')
        except Exception as e:
            context['error_message'] = f"Transaction failed: {str(e)}"
            return render(request, template_name, context)

    return render(request, template_name, context)

# Replace or add this function in APP/views.py
def sell_product_list(request):
    # Render the generic sell page (list/search) using the APP template folder
    return render(request, 'APP/sell_product.html')

