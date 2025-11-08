from django.contrib import admin
from .models import ProductReview, OrderReview, StoreReview


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'product', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('user__email', 'product__name', 'comment')
    readonly_fields = ('created_at',)


@admin.register(StoreReview)
class StoreReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'store', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('user__email', 'store__name', 'comment')
    readonly_fields = ('created_at',)


@admin.register(OrderReview)
class OrderReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'order', 'delivery_speed_rating', 'service_quality_rating', 'created_at')
    list_filter = ('delivery_speed_rating', 'service_quality_rating', 'created_at')
    search_fields = ('user__email', 'order__id')
    readonly_fields = ('created_at',)
