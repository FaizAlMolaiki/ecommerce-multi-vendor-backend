from django.db import models
from django.conf import settings
from mptt.models import MPTTModel, TreeForeignKey

from stores.models import Store # Assuming stores app is at the same level

class ProductCategory(MPTTModel):
    """
    Tree structure for product categories within a store using django-mptt.
    """
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=200)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')

    class MPTTMeta:
        order_insertion_by = ['name']

    class Meta:
        verbose_name_plural = "Product Categories"
        unique_together = ('store', 'name', 'parent')

    def __str__(self):
        return self.name

class Product(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(ProductCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    specifications = models.JSONField(default=dict, blank=True, help_text="e.g., {'Screen': '6.1 inch', 'RAM': '8GB'}")
    # ✅ إضافة حقل التفعيل
    is_active = models.BooleanField(default=True, help_text="هل المنتج متاح للعرض؟")
    
    # Denormalized fields
    cover_image_url = models.URLField(max_length=500, blank=True)
    average_rating = models.FloatField(default=0.0)
    review_count = models.PositiveIntegerField(default=0)
    selling_count = models.PositiveIntegerField(default=0)
    

    def __str__(self):
        return self.name
    # NEW: Properties للخصومات النشطة
    @property
    def active_promotions(self):
        """الخصومات النشطة على هذا المنتج"""
        from pricing.models import Promotion
        from django.utils import timezone
        from django.db import models as django_models
        
        now = timezone.now()
        return Promotion.objects.filter(
            active=True,
            products=self
        ).filter(
            django_models.Q(start_at__isnull=True) | django_models.Q(start_at__lte=now)
        ).filter(
            django_models.Q(end_at__isnull=True) | django_models.Q(end_at__gte=now)
        )
    
    @property
    def has_discount(self):
        """هل يوجد خصم نشط على هذا المنتج؟"""
        return self.active_promotions.exists()
    
    @property
    def discount_percentage(self):
        """أعلى نسبة خصم متاحة على المنتج"""
        from pricing.models import Promotion
        
        promo = self.active_promotions.filter(
            promotion_type__in=[
                Promotion.PromotionType.PRODUCT_PERCENTAGE,
                Promotion.PromotionType.CART_PERCENTAGE
            ]
        ).order_by('-value').first()
        
        return float(promo.value) if promo else None
    
    def get_price_after_discount(self, base_price):
        """حساب السعر بعد تطبيق الخصم"""
        from decimal import Decimal
        
        if not self.has_discount:
            return base_price
        
        discount_pct = self.discount_percentage
        if discount_pct:
            discount_amount = (base_price * Decimal(str(discount_pct))) / Decimal('100')
            return base_price - discount_amount
        
        return base_price


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    sku = models.CharField(max_length=100, unique=True, blank=True, null=True)
    options = models.JSONField(default=dict, blank=True, help_text="e.g., {'color': 'Black', 'storage': '256GB'}")

    # Denormalized field
    cover_image_url = models.URLField(max_length=500, blank=True)

    def __str__(self):
        options_str = ', '.join([f'{k}: {v}' for k, v in self.options.items()])
        return f"{self.product.name} ({options_str})"

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='images', null=True, blank=True)
    image_url = models.URLField(max_length=500)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['display_order']

    def __str__(self):
        return f"Image for {self.product.name}"

