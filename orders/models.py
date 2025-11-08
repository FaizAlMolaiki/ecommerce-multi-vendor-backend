from django.db import models
from django.conf import settings
from products.models import ProductVariant 
from stores.models import Store 

class CartItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart_items')
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'variant')

    def __str__(self):
        # Safe string to avoid relying on username which may not exist on custom user model
        user_label = getattr(self.user, 'email', None) or str(self.user_id)
        product_name = None
        try:
            product_name = self.variant.product.name
        except Exception:
            product_name = 'product'
        return f"{self.quantity} x {product_name} in {user_label}'s cart"
    
    

class Order(models.Model):
    class PaymentStatus(models.TextChoices):
        PENDING_PAYMENT = 'PENDING_PAYMENT', 'Pending Payment'
        PAID = 'PAID', 'Paid'
        CANCELLED = 'CANCELLED', 'Cancelled'
        REFUNDED = 'REFUNDED', 'Refunded'

    class FulfillmentStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending Review'
        ACCEPTED = 'ACCEPTED', 'Accepted'
        PREPARING = 'PREPARING', 'Preparing'
        SHIPPED = 'SHIPPED', 'Shipped'
        DELIVERED = 'DELIVERED', 'Delivered'
        REJECTED = 'REJECTED', 'Rejected'

    # Each order belongs to exactly one store
    store = models.ForeignKey(Store, on_delete=models.PROTECT, related_name='orders', null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='orders')
    # Optional delivery agent (courier) assigned later by admin from dashboard
    delivery_agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_orders_as_delivery',
        help_text='Assigned delivery person (can be set later)'
    )
    grand_total = models.DecimalField(max_digits=12, decimal_places=2)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_address_snapshot = models.JSONField()
    payment_status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING_PAYMENT)
    fulfillment_status = models.CharField(max_length=20, choices=FulfillmentStatus.choices, default=FulfillmentStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

   
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        # Use email if available; fallback to 'guest' or user_id
        user_label = None
        if self.user_id:
            user_label = getattr(self.user, 'email', None) or str(self.user_id)
        else:
            user_label = 'guest'
        store_name = getattr(self.store, 'name', None) or f"Store {self.store_id}"
        return f"Order #{self.id} for {store_name} by {user_label}"

## StoreOrder model removed: unified into Order
        
class OrderItem(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        CANCELLED = 'CANCELLED', 'Cancelled'

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', null=True, blank=True)
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField()
    
    # Snapshot fields
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)
    product_name_snapshot = models.CharField(max_length=255)
    variant_options_snapshot = models.JSONField()
    
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    cancellation_reason = models.TextField(blank=True, null=True)



