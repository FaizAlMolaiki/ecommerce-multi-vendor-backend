from django.contrib import admin
from .models import CartItem, Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = (
        'variant',
        'quantity',
        'price_at_purchase',
        'status',
        'cancellation_reason',
    )
    readonly_fields = ('price_at_purchase',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'store', 'user', 'grand_total', 'payment_status', 'fulfillment_status', 'created_at')
    list_filter = ('store', 'payment_status', 'fulfillment_status', 'created_at')
    search_fields = ('user__email', 'store__name')
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'variant', 'quantity', 'price_at_purchase', 'status')
    list_filter = ('status',)
    search_fields = ('order__id', 'variant__sku', 'product_name_snapshot')


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'variant', 'quantity', 'added_at')
    list_filter = ('added_at',)
    search_fields = ('user__username', 'user__email', 'variant__sku')
