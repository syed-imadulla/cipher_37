from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum, F
from django.urls import reverse
import json

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

def settings_page(request):
    return render(request, 'APP/settings.html')

def add_product(request):
    if request.method == "POST":
        # You will add saving logic later
        return redirect('dashboard-page')

    return render(request, 'APP/add_product.html')


# -------------------------------------------------------
# FINANCE TRACKER
# -------------------------------------------------------

def finance_tracker(request):
    today = timezone.now().date()

    sales_today = Sale.objects.filter(sale_timestamp__date=today)

    # Revenue
    revenue = sales_today.aggregate(total=Sum('total_amount'))['total'] or 0

    # COGS
    total_cogs = 0
    for sale in sales_today:
        for item in sale.items.all():
            total_cogs += item.cost_at_sale * item.quantity

    profit = revenue - total_cogs

    # Profit makers
    profit_makers_query = (
        SaleItem.objects.filter(sale__sale_timestamp__date=today)
        .annotate(
            profit_item=(F('price_at_sale') - F('cost_at_sale')) * F('quantity')
        )
        .values('product__product_name')
        .annotate(total_profit=Sum('profit_item'))
        .order_by('-total_profit')[:5]
    )

    context = {
        "todays_profit": profit,
        "revenue_vs_cogs": {
            "revenue": revenue,
            "cogs": total_cogs,
            "profit": profit,
        },
        "profit_makers": list(profit_makers_query),
    }

    return render(request, "APP/finance_tracker.html", context)


# -------------------------------------------------------
# AI ADVISOR
# -------------------------------------------------------

def ai_advisor(request):
    seven_days_from_now = timezone.now().date() + timezone.timedelta(days=7)

    waste_alerts = StockBatch.objects.filter(
        expiry_date__lte=seven_days_from_now,
        quantity__gt=0
    ).order_by("expiry_date")

    # No reorder logic yet because your Product model has no reorder_level.
    reorder_suggestions = []

    trend_alerts = [
        {"product_name": "Sample product", "message": "Selling 50% faster than usual."}
    ]

    return render(request, "APP/ai_advisor.html", {
        "waste_alerts": waste_alerts,
        "reorder_suggestions": reorder_suggestions,
        "trend_alerts": trend_alerts,
    })


# -------------------------------------------------------
# BARCODE SCAN APIs
# -------------------------------------------------------

def scan_product_api(request, barcode):
    try:
        product = Product.objects.get(barcode=barcode)

        batch = StockBatch.objects.filter(
            product=product,
            quantity__gt=0
        ).order_by('expiry_date').first()

        if batch:
            return JsonResponse({
                "status": "found",
                "product_id": product.id,
                "name": product.product_name,
                "description": product.description,
                "selling_price": product.selling_price,
                "batch_id": batch.id,
                "available_stock": batch.quantity,
            })
        else:
            return JsonResponse({
                "status": "out_of_stock",
                "name": product.product_name,
                "message": "This product exists but has 0 stock."
            })

    except Product.DoesNotExist:
        return JsonResponse({
            "status": "not_found",
            "message": "Barcode not found."
        })


def scan_barcode_api(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "POST only"}, status=405)

    data = json.loads(request.body.decode("utf-8"))
    barcode = data.get("barcode")

    if not barcode:
        return JsonResponse({"status": "error", "message": "No barcode"}, status=400)

    try:
        product = Product.objects.get(barcode=barcode)
        url = reverse("sell-product-page", kwargs={"product_id": product.id})
        return JsonResponse({"status": "found", "redirect_url": url})
    except Product.DoesNotExist:
        url = reverse("add-product-page")
        return JsonResponse({"status": "not_found", "redirect_url": url})


# -------------------------------------------------------
# SELL PRODUCT (PAGE VERSION)
# -------------------------------------------------------

def sell_product(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return redirect("dashboard-page")

    batch = StockBatch.objects.filter(
        product=product,
        quantity__gt=0
    ).order_by("expiry_date").first()

    if request.method == "POST":
        qty = int(request.POST.get("quantity_sold", 0))

        if qty <= 0:
            return render(request, "APP/sell-product.html", {
                "product": product,
                "batch": batch,
                "error_message": "Invalid quantity."
            })

        if not batch or batch.quantity < qty:
            return render(request, "APP/sell-product.html", {
                "product": product,
                "batch": batch,
                "error_message": f"Not enough stock. Available: {batch.quantity if batch else 0}"
            })

        with transaction.atomic():
            total_amount = product.selling_price * qty
            total_profit = (product.selling_price - product.cost_price) * qty

            sale = Sale.objects.create(
                user=request.user if request.user.is_authenticated else None,
                total_amount=total_amount,
                total_profit=total_profit
            )

            SaleItem.objects.create(
                sale=sale,
                product=product,
                quantity=qty,
                price_at_sale=product.selling_price,
                cost_at_sale=product.cost_price
            )

            batch.quantity -= qty
            batch.save()

        return redirect("dashboard-page")

    return render(request, "APP/sell-product.html", {
        "product": product,
        "batch": batch
    })


# -------------------------------------------------------
# SELL PRODUCT (API VERSION for frontend fetch)
# -------------------------------------------------------

def sell_product_api(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    qty = int(data.get("quantity", 0))
    barcode = data.get("barcode")
    product_id = data.get("product_id")

    if qty <= 0:
        return JsonResponse({"error": "Quantity must be > 0"}, status=400)

    # Get product by barcode or id
    try:
        if barcode:
            product = Product.objects.get(barcode=barcode)
        else:
            product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return JsonResponse({"error": "Product not found"}, status=404)

    batch = StockBatch.objects.filter(
        product=product,
        quantity__gt=0
    ).order_by("expiry_date").first()

    if not batch or batch.quantity < qty:
        return JsonResponse({
            "error": "Not enough stock",
            "available": batch.quantity if batch else 0
        }, status=400)

    with transaction.atomic():
        total_amount = product.selling_price * qty
        total_profit = (product.selling_price - product.cost_price) * qty

        sale = Sale.objects.create(
            user=request.user if request.user.is_authenticated else None,
            total_amount=total_amount,
            total_profit=total_profit
        )

        SaleItem.objects.create(
            sale=sale,
            product=product,
            quantity=qty,
            price_at_sale=product.selling_price,
            cost_at_sale=product.cost_price
        )

        batch.quantity -= qty
        batch.save()

    return JsonResponse({
        "ok": True,
        "sale_id": sale.id,
        "product_id": product.id,
        "barcode": product.barcode,
        "quantity": qty,
        "remaining_stock": batch.quantity,
        "total": str(total_amount),
        "profit": str(total_profit)
    })


# -------------------------------------------------------
# GENERIC TEST API
# -------------------------------------------------------

def update_item(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        payload = json.loads(request.body.decode("utf-8"))
        return JsonResponse({"ok": True, "received": payload})
    except Exception as e:
        return HttpResponseBadRequest("Invalid JSON: " + str(e))
