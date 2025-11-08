from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from products.models import Product
from stores.models import Store

class UserStoreFavorite(models.Model):
    """
    Tracks stores that a user has favorited.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorite_stores')
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)
    
   

    class Meta:
        # Ensures a user cannot favorite the same store more than once
        unique_together = ('user', 'store')
        verbose_name = "User's Favorite Store"
        verbose_name_plural = "User's Favorite Stores"

    def __str__(self):
        user_label = getattr(self.user, 'email', None) or getattr(self.user, 'username', None) or 'guest'
        return f"{user_label} favorited {self.store.name}"
    
    
class UserProductFavorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorite_products')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)
    
   

    class Meta:
        unique_together = ('user', 'product')
        verbose_name = "User's Favorite Product"
        verbose_name_plural = "User's Favorite Products"
    
    def __str__(self):
        user_label = getattr(self.user, 'email', None) or getattr(self.user, 'username', None) or 'guest'
        return f"{user_label} favorited {self.product.name}"