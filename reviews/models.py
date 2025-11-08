from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from orders.models import Order
from stores.models import Store


class ProductReview(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField() # Consider adding validators.MinValueValidator(1), MaxValueValidator(5)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'product')


class OrderReview(models.Model):
    """
    Stores user feedback specifically about the delivery and service quality
    for a particular sub-order (StoreOrder).
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='order_reviews')
    order= models.OneToOneField(Order, on_delete=models.CASCADE, related_name='review')
    
    delivery_speed_rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating for the delivery speed (1-5)"
    )
    service_quality_rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating for the service quality (1-5)"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Ensures one review per sub-order
        unique_together = ('user', 'order')
        verbose_name = "Order Review"
        verbose_name_plural = "Order Reviews"
        ordering = ['-created_at']

    def __str__(self):
        user_label = getattr(self.user, 'email', None) or getattr(self.user, 'username', None) or 'guest'
        return f"Review for Order #{self.order.id} by {user_label}"


class StoreReview(models.Model):
    """
    Stores user feedback about a specific store, potentially linked to a purchase.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='store_reviews')
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='reviews')

    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Overall rating for the store (1-5)"
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # A user might review a store multiple times over a long period,
        # but you might want to prevent multiple reviews for the same order.
        # This constraint is a good middle ground.
        unique_together = ('user', 'store')
        verbose_name = "Store Review"
        verbose_name_plural = "Store Reviews"
        ordering = ['-created_at']

    def __str__(self):
        user_label = getattr(self.user, 'email', None) or getattr(self.user, 'username', None) or 'guest'
        return f"Review for {self.store.name} by {user_label}"