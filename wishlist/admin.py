# wishlist/admin.py

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import UserProductFavorite, UserStoreFavorite

@admin.register(UserProductFavorite)
class UserProductFavoriteAdmin(admin.ModelAdmin):
    list_display = ('user_link', 'product_link', 'created_at')
    search_fields = ('user__email', 'product__name')
    autocomplete_fields = ['user', 'product'] # لتحسين الأداء عند الإضافة اليدوية

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'product')
        
    def user_link(self, obj):
        link = reverse("admin:accounts_user_change", args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', link, obj.user.email)
    user_link.short_description = 'User'

    def product_link(self, obj):
        link = reverse("admin:products_product_change", args=[obj.product.id])
        return format_html('<a href="{}">{}</a>', link, obj.product.name)
    product_link.short_description = 'Product'


@admin.register(UserStoreFavorite)
class UserStoreFavoriteAdmin(admin.ModelAdmin):
    list_display = ('user_link', 'store_link', 'created_at')
    search_fields = ('user__email', 'store__name')
    autocomplete_fields = ['user', 'store']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'store')
        
    def user_link(self, obj):
        link = reverse("admin:accounts_user_change", args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', link, obj.user.email)
    user_link.short_description = 'User'

    def store_link(self, obj):
        link = reverse("admin:stores_store_change", args=[obj.store.id])
        return format_html('<a href="{}">{}</a>', link, obj.store.name)
    store_link.short_description = 'Store'