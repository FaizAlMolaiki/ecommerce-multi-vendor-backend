from django.contrib import admin
from .models import Product, ProductCategory, ProductVariant


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'store', 'category')
    search_fields = ('name', 'store__name')
    list_filter = ('store', 'category')


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'store')
    search_fields = ('name', 'store__name')
    list_filter = ('store',)


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('product', 'sku', 'price')
    search_fields = ('product__name', 'sku')
    list_filter = ('product__store',)