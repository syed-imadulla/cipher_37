from django.db import models
from django.contrib.auth.models import User # Using Django's built-in User model
from django.utils import timezone

# 1. Products Table (replaces Products)
class Product(models.Model):
    barcode = models.CharField(max_length=255, unique=True, null=True, blank=True)
    product_name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    # This links to the user who added the product
    added_by_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.product_name

# 2. Inventory / StockBatches Table (replaces StockBatches)
# Tracks stock levels for each product.
class StockBatch(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="batches")
    quantity = models.IntegerField()
    received_date = models.DateField(default=timezone.now)
    expiry_date = models.DateField(null=True, blank=True) # For "Show Waste Alerts"

    def __str__(self):
        return f"{self.product.product_name} - Batch ({self.quantity})"

# 3. Sales Table (replaces Sales)
# A parent table to group items sold in a single transaction.
class Sale(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True) # The cashier
    sale_timestamp = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    total_profit = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Sale #{self.id} - {self.sale_timestamp.strftime('%Y-%m-%d %H:%M')}"

# 4. SaleItems Table (replaces SaleItems)
# Stores the individual products sold in each sale.
class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT) # Protect from deletion if sold
    quantity = models.IntegerField()
    # Store the prices at the time of sale
    price_at_sale = models.DecimalField(max_digits=10, decimal_places=2)
    cost_at_sale = models.DecimalField(max_digits=10, decimal_places=2)

# 5. Alerts Table (replaces Alerts)
# Stores the generated alerts from the "AI Advisor".
class Alert(models.Model):
    ALERT_TYPES = [
        ('reorder', 'Reorder'),
        ('waste', 'Waste'),
        ('trend', 'Trend'),
    ]
    alert_type = models.CharField(max_length=10, choices=ALERT_TYPES)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    message = models.TextField()
    suggestion_details = models.TextField(null=True, blank=True)
    is_viewed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.get_alert_type_display()}] {self.message[:50]}..."

# 6. PurchaseOrders Table (replaces PurchaseOrders)
# For the "Add to Purchase Order" flow.
class PurchaseOrder(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('received', 'Received'),
    ]
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True) # User who created PO
    supplier_info = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True) # For "Send PO via WhatsApp"

    def __str__(self):
        return f"PO #{self.id} - {self.status}"

# 7. PurchaseOrderItems Table (replaces PurchaseOrderItems)
# The specific products and quantities for each Purchase Order.
class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT) # Protect product
    quantity = models.IntegerField()
    agreed_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)


