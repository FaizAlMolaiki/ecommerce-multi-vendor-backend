from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    CartItemViewSet,
    CreateOrderView,
    MyOrdersListView,
    OrderDetailView,
    MarkOrderPaidView,
    OrderStatusView,  # ✅ New
    OrderRatingView,  # ✅ New
)
from .api_views import grouped_cart_view

router = DefaultRouter()
router.register(r'cart', CartItemViewSet, basename='cart')

urlpatterns = [
 
    # ✅ Cart grouped by store
    path('cart/grouped/', grouped_cart_view, name='cart-grouped'),
    path('', include(router.urls)),
    # Orders
    path('create/', CreateOrderView.as_view(), name='orders-create'),
    path('my/', MyOrdersListView.as_view(), name='orders-my'),
    path('<int:order_id>/', OrderDetailView.as_view(), name='orders-detail'),
    path('<int:order_id>/mark-paid/', MarkOrderPaidView.as_view(), name='orders-mark-paid'),
    # ✅ New endpoints for Flutter improvements
    path('<int:order_id>/status/', OrderStatusView.as_view(), name='orders-status'),
    path('<int:order_id>/rate/', OrderRatingView.as_view(), name='orders-rate'),
]
