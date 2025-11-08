# ===================================================================
# ✅ API Views محسّن - من مجلد one
# - استخدام Generics بدلاً من APIView  
# - إضافة البحث والمنتجات المميزة
# - تحسينات الأمان والأداء
# ===================================================================

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.db.models import Q, Case, When, Value
from django.shortcuts import get_object_or_404

from .models import Product, ProductCategory, ProductVariant, ProductImage
from .serializers import (
    ProductListSerializer, 
    ProductDetailSerializer,
    ProductCategorySerializer,
    ProductVariantSerializer,
    ProductImageSerializer
)
from stores.models import Store


class ProductListCreateAPIView(generics.ListCreateAPIView):
    """
    List all products or create a new product
    GET /api/v1/products/
    POST /api/v1/products/
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        # عرض المنتجات من المتاجر النشطة فقط
        queryset = Product.objects.filter(
            store__status=Store.StoreStatus.ACTIVE,
            is_active=True
        ).select_related('store', 'store__platform_category')

        # ✅ فلترة حسب فئة المنصة (platform_category)
        platform_category = self.request.query_params.get('platform_category')
        if platform_category:
            queryset = queryset.filter(store__platform_category_id=platform_category)

        # فلترة حسب المتجر
        store_id = self.request.query_params.get('store_id')
        if store_id:
            queryset = queryset.filter(store_id=store_id)

        # فلترة حسب الفئة
        category_id = self.request.query_params.get('category_id')
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        # البحث
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(description__icontains=search) |
                Q(specifications__icontains=search)
            )

        # ✅ الترتيب حسب sort-by (للتوافق مع Flutter)
        sort_by = self.request.query_params.get('sort-by')
        if sort_by == 'top-rated':
            queryset = queryset.order_by('-average_rating', '-id')
        elif sort_by == 'top-sale':
            queryset = queryset.order_by('-selling_count', '-id')
        else:
            # الترتيب الافتراضي أو المخصص
            ordering = self.request.query_params.get('ordering')
            if ordering:
                queryset = queryset.order_by(ordering)
            else:
                queryset = queryset.order_by('-id')  # الأحدث أولاً

        return queryset
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ProductListSerializer
        return ProductDetailSerializer
    
    def perform_create(self, serializer):
        # Ensure the user owns the store
        store_id = self.request.data.get('store')
        if store_id:
            store = get_object_or_404(Store, id=store_id, owner=self.request.user)
            serializer.save(store=store)
        else:
            serializer.save()


class ProductRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a product
    GET /api/v1/products/{id}/
    PUT /api/v1/products/{id}/
    PATCH /api/v1/products/{id}/
    DELETE /api/v1/products/{id}/
    """
    queryset = Product.objects.all()
    serializer_class = ProductDetailSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]
    
    def perform_update(self, serializer):
        product = self.get_object()
        if product.store.owner != self.request.user:
            raise permissions.PermissionDenied("You can only modify your own store's products")
        serializer.save()
    
    def perform_destroy(self, instance):
        if instance.store.owner != self.request.user:
            raise permissions.PermissionDenied("You can only delete your own store's products")
        instance.delete()


class ProductCategoryListCreateAPIView(generics.ListCreateAPIView):
    """
    List all product categories or create a new category
    GET /api/v1/products/categories/
    POST /api/v1/products/categories/
    """
    queryset = ProductCategory.objects.all()
    serializer_class = ProductCategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        queryset = ProductCategory.objects.all()
        store_id = self.request.query_params.get('store', None)
        if store_id:
            try:
                store_id = int(store_id)
                queryset = queryset.filter(store_id=store_id)
            except (ValueError, TypeError):
                pass
        return queryset
    
    def perform_create(self, serializer):
        store_id = self.request.data.get('store')
        if store_id:
            store = get_object_or_404(Store, id=store_id, owner=self.request.user)
            serializer.save(store=store)
        else:
            serializer.save()


class ProductCategoryRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a product category
    GET /api/v1/products/categories/{id}/
    PUT /api/v1/products/categories/{id}/
    PATCH /api/v1/products/categories/{id}/
    DELETE /api/v1/products/categories/{id}/
    """
    queryset = ProductCategory.objects.all()
    serializer_class = ProductCategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]


class ProductVariantListCreateAPIView(generics.ListCreateAPIView):
    """
    List all variants for a product or create a new variant
    GET /api/v1/products/{product_id}/variants/
    POST /api/v1/products/{product_id}/variants/
    """
    serializer_class = ProductVariantSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        product_id = self.kwargs['product_id']
        return ProductVariant.objects.filter(product_id=product_id)
    
    def perform_create(self, serializer):
        product_id = self.kwargs['product_id']
        product = get_object_or_404(Product, id=product_id)
        
        if product.store.owner != self.request.user:
            raise permissions.PermissionDenied("You can only add variants to your own store's products")
        
        serializer.save(product=product)


class ProductVariantRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a product variant
    GET /api/v1/products/variants/{id}/
    PUT /api/v1/products/variants/{id}/
    PATCH /api/v1/products/variants/{id}/
    DELETE /api/v1/products/variants/{id}/
    """
    queryset = ProductVariant.objects.all()
    serializer_class = ProductVariantSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]


class ProductImageListCreateAPIView(generics.ListCreateAPIView):
    """
    List all images for a product or create a new image
    GET /api/v1/products/{product_id}/images/
    POST /api/v1/products/{product_id}/images/
    """
    serializer_class = ProductImageSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        product_id = self.kwargs['product_id']
        return ProductImage.objects.filter(product_id=product_id)
    
    def perform_create(self, serializer):
        product_id = self.kwargs['product_id']
        product = get_object_or_404(Product, id=product_id)
        
        if product.store.owner != self.request.user:
            raise permissions.PermissionDenied("You can only add images to your own store's products")
        
        serializer.save(product=product)


class ProductImageRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a product image
    GET /api/v1/products/images/{id}/
    PUT /api/v1/products/images/{id}/
    PATCH /api/v1/products/images/{id}/
    DELETE /api/v1/products/images/{id}/
    """
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]


# ✅ إضافة جديدة: البحث في المنتجات
class ProductSearchView(generics.ListAPIView):
    """
    Search products by name or description
    GET /api/v1/products/search/?search={query}&store={store_id}&category={category_id}
    """
    serializer_class = ProductListSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        search_term = self.request.query_params.get('search', '').strip()
        store_id = self.request.query_params.get('store', None)
        category_id = self.request.query_params.get('category', None)
        
        queryset = Product.objects.all()
        
        if search_term:
            queryset = queryset.filter(
                Q(name__icontains=search_term) | 
                Q(description__icontains=search_term) |
                Q(specifications__icontains=search_term)
            )
        else:
            return Product.objects.none()
        
        if store_id:
            try:
                store_id = int(store_id)
                queryset = queryset.filter(store_id=store_id)
            except (ValueError, TypeError):
                pass
        
        if category_id:
            try:
                category_id = int(category_id)
                queryset = queryset.filter(category_id=category_id)
            except (ValueError, TypeError):
                pass
        
        queryset = queryset.annotate(
            relevance=Case(
                When(name__icontains=search_term, then=Value(1)),
                When(description__icontains=search_term, then=Value(2)),
                default=Value(3),
            )
        ).order_by('relevance', '-id')
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """✅ Override to add search metadata to response (من Two)"""
        queryset = self.get_queryset()
        search_term = request.query_params.get('search', '').strip()
        
        if not search_term:
            return Response({
                'error': 'Search term is required',
                'message': 'Please provide a search query using ?search=your_query'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Paginate results
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            # Add search metadata
            response.data['search_metadata'] = {
                'query': search_term,
                'total_results': queryset.count(),
                'store_filter': request.query_params.get('store'),
                'category_filter': request.query_params.get('category'),
            }
            return response
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'results': serializer.data,
            'search_metadata': {
                'query': search_term,
                'total_results': queryset.count(),
                'store_filter': request.query_params.get('store'),
                'category_filter': request.query_params.get('category'),
            }
        })
# ✅ إضافة جديدة: المنتجات المميزة (محدَّث)
class FeaturedProductsView(generics.ListAPIView):
    """
    Get featured products (products with high ratings or sales)
    GET /api/v1/products/featured/
    يدعم الفلترة حسب platform_category والترتيب حسب sort-by
    """
    serializer_class = ProductListSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        # المنتجات المميزة: تقييم عالي أو مبيعات جيدة
        queryset = Product.objects.filter(
            Q(average_rating__gte=4.0) | Q(selling_count__gte=10),
            store__status=Store.StoreStatus.ACTIVE,
            is_active=True
        ).select_related('store', 'store__platform_category')
        
        # ✅ فلترة حسب فئة المنصة
        platform_category = self.request.query_params.get('platform_category')
        if platform_category:
            queryset = queryset.filter(store__platform_category_id=platform_category)
        
        # ✅ الترتيب حسب sort-by
        sort_by = self.request.query_params.get('sort-by')
        if sort_by == 'top-rated':
            queryset = queryset.order_by('-average_rating', '-id')
        elif sort_by == 'top-sale':
            queryset = queryset.order_by('-selling_count', '-id')
        else:
            # الترتيب الافتراضي
            queryset = queryset.order_by('-average_rating', '-selling_count', '-id')
        
        return queryset[:20]  # أفضل 20 منتج


# ✅ إضافة جديدة: المنتجات الأكثر مبيعاً (محدَّث)
class BestSellingProductsView(generics.ListAPIView):
    """
    Get best selling products
    GET /api/v1/products/best-selling/
    يدعم الفلترة حسب platform_category
    """
    serializer_class = ProductListSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = Product.objects.filter(
            selling_count__gt=0,
            store__status=Store.StoreStatus.ACTIVE,
            is_active=True
        ).select_related('store', 'store__platform_category')
        
        # ✅ فلترة حسب فئة المنصة
        platform_category = self.request.query_params.get('platform_category')
        if platform_category:
            queryset = queryset.filter(store__platform_category_id=platform_category)
        
        return queryset.order_by('-selling_count', '-id')[:20]