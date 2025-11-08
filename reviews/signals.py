from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Avg
from reviews.models import ProductReview, StoreReview

@receiver([post_save, post_delete], sender=ProductReview)
def update_product_rating(sender, instance, **kwargs):
    """تحديث تقييم المنتج تلقائياً"""
    product = instance.product
    reviews = ProductReview.objects.filter(product=product)
    product.average_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0.0
    product.review_count = reviews.count()
    product.save(update_fields=['average_rating', 'review_count'])

@receiver([post_save, post_delete], sender=StoreReview)
def update_store_rating(sender, instance, **kwargs):
    """تحديث تقييم المتجر تلقائياً"""
    store = instance.store
    reviews = StoreReview.objects.filter(store=store)
    store.average_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0.0
    store.review_count = reviews.count()
    store.save(update_fields=['average_rating', 'review_count'])