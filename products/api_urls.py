from django.urls import path
from core.image_upload_views import ProductImageUploadView
from .api_views import (
    ProductListCreateAPIView,
    ProductRetrieveUpdateDestroyAPIView,
    ProductCategoryListCreateAPIView,
    ProductCategoryRetrieveUpdateDestroyAPIView,
    ProductVariantListCreateAPIView,
    ProductVariantRetrieveUpdateDestroyAPIView,
    ProductImageListCreateAPIView,
    ProductImageRetrieveUpdateDestroyAPIView,
    ProductSearchView,  # ✅ جديد
    FeaturedProductsView,  # ✅ جديد
    BestSellingProductsView,  # ✅ جديد
)

urlpatterns = [
    # Image Upload URLs
    path('upload/image/', ProductImageUploadView.as_view(), name='product-image-upload'),

    # Product URLs
    path('', ProductListCreateAPIView.as_view(), name='product-list-create'),
    path('search/', ProductSearchView.as_view(), name='product-search'),  # ✅ جديد
    path('featured/', FeaturedProductsView.as_view(), name='product-featured'),  # ✅ جديد
    path('best-selling/', BestSellingProductsView.as_view(), name='product-best-selling'),  # ✅ جديد
    path('<int:pk>/', ProductRetrieveUpdateDestroyAPIView.as_view(), name='product-detail'),

    # Product Variant URLs
    path('<int:product_id>/variants/', ProductVariantListCreateAPIView.as_view(), name='product-variant-list-create'),
    path('variants/<int:pk>/', ProductVariantRetrieveUpdateDestroyAPIView.as_view(), name='product-variant-detail'),

    # Product Image URLs
    path('<int:product_id>/images/', ProductImageListCreateAPIView.as_view(), name='product-image-list-create'),
    path('images/<int:pk>/', ProductImageRetrieveUpdateDestroyAPIView.as_view(), name='product-image-detail'),

    # Category URLs
    path('categories/', ProductCategoryListCreateAPIView.as_view(), name='category-list-create'),
    path('categories/<int:pk>/', ProductCategoryRetrieveUpdateDestroyAPIView.as_view(), name='category-detail'),
]