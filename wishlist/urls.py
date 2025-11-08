# wishlist/urls.py
from django.urls import path
from .views import (
    UserProductFavoriteView,
    UserStoreFavoriteView,
    UserProductFavoriteIdsView,
    UserStoreFavoriteIdsView,
)

app_name = 'wishlist'

urlpatterns = [
    # URLs for Product Wishlist
    path('products/', UserProductFavoriteView.as_view(), name='product-wishlist'),
    path('products/<int:product_id>/', UserProductFavoriteView.as_view(), name='product-wishlist-detail'),
    
    # URLs for Store Wishlist
    path('stores/', UserStoreFavoriteView.as_view(), name='store-wishlist'),
    path('stores/<int:store_id>/', UserStoreFavoriteView.as_view(), name='store-wishlist-detail'),
    
    # ✅ IDs only endpoints (for quick membership checks) - Class-based
    path('products-ids/', UserProductFavoriteIdsView.as_view(), name='wishlist-product-ids'),
    path('stores-ids/', UserStoreFavoriteIdsView.as_view(), name='wishlist-store-ids'),
]