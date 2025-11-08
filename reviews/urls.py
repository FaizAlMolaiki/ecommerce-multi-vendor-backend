from django.urls import path
from .api import StoreReviewViewSet, ProductReviewViewSet

urlpatterns = [
    # Store Reviews: /api/v1/stores/{store_id}/reviews/
    # ⚠️ ضع الـ specific paths قبل dynamic patterns
    path('stores/<int:store_pk>/reviews/stats/', StoreReviewViewSet.as_view({
        'get': 'stats'
    }), name='store-reviews-stats'),
    
    path('stores/<int:store_pk>/reviews/my-review/', StoreReviewViewSet.as_view({
        'get': 'my_review'
    }), name='store-reviews-my-review'),
    
    path('stores/<int:store_pk>/reviews/', StoreReviewViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='store-reviews-list'),
    
    path('stores/<int:store_pk>/reviews/<int:pk>/', StoreReviewViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='store-reviews-detail'),
    
    # Product Reviews: /api/v1/products/{product_id}/reviews/
    path('products/<int:product_pk>/reviews/stats/', ProductReviewViewSet.as_view({
        'get': 'stats'
    }), name='product-reviews-stats'),
    
    path('products/<int:product_pk>/reviews/my-review/', ProductReviewViewSet.as_view({
        'get': 'my_review'
    }), name='product-reviews-my-review'),
    
    path('products/<int:product_pk>/reviews/', ProductReviewViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='product-reviews-list'),
    
    path('products/<int:product_pk>/reviews/<int:pk>/', ProductReviewViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='product-reviews-detail'),
]