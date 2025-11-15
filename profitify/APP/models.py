# APP/models.py
from django.db import models
from django.contrib.auth.models import User  # Using Django's built-in User model
from django.utils import timezone
from decimal import Decimal


class Product(models.Model):
    barcode = models.CharField(max_length=255, unique=True, null=True, blank=True)
    product_name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    reorder_level = models.IntegerField(
        default=0, 
        help_text="The minimum stock level before a reorder is triggered."
    )
    # This links to the user who added the product
    added_by_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.product_name


class StockBatch(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_batches')
    quantity = models.IntegerField()
    received_date = models.DateField(default=timezone.now)
    expiry_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.product.product_name} - Batch ({self.quantity})"


class Sale(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    sale_timestamp = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    total_profit = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        ts = self.sale_timestamp.strftime('%Y-%m-%d %H:%M') if self.sale_timestamp else "unspecified"
        return f"Sale #{self.id} - {ts}"


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.IntegerField()
    price_at_sale = models.DecimalField(max_digits=10, decimal_places=2)
    cost_at_sale = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.product_name} x{self.quantity} (Sale #{self.sale_id if self.sale_id else self.sale})"


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


class PurchaseOrder(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('received', 'Received'),
    ]
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    supplier_info = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"PO #{self.id} - {self.status}"


class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.IntegerField()
    agreed_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"PO #{self.purchase_order.id} - {self.product.product_name} x{self.quantity}"
