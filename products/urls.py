from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, ProductCategoryViewSet
from .api_views import (
    ProductCategoryListCreateAPIView, 
    ProductCategoryRetrieveUpdateDestroyAPIView,
    ProductVariantListCreateAPIView,
    ProductVariantRetrieveUpdateDestroyAPIView
)

# استخدام APIView للفئات بدلاً من ViewSet
urlpatterns = [
    # Product Categories API - يدعم GET و POST
    path('categories/', ProductCategoryListCreateAPIView.as_view(), name='category-list-create'),
    # Product Category Detail API - يدعم GET و PUT و PATCH و DELETE
    path('categories/<int:pk>/', ProductCategoryRetrieveUpdateDestroyAPIView.as_view(), name='category-detail'),
    
    # Product Variants API
    path('<int:product_id>/variants/', ProductVariantListCreateAPIView.as_view(), name='product-variants'),
    path('variants/<int:pk>/', ProductVariantRetrieveUpdateDestroyAPIView.as_view(), name='variant-detail'),
]

# Router للمنتجات فقط
router = DefaultRouter()
router.register(r'', ProductViewSet, basename='product')

# إضافة router URLs
urlpatterns += [
    path('', include(router.urls)),
]
