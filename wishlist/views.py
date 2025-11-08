from rest_framework import generics, mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import UserProductFavorite, UserStoreFavorite
from .serializers import (
    UserProductFavoriteListSerializer, UserProductFavoriteCreateSerializer,
    UserStoreFavoriteListSerializer, UserStoreFavoriteCreateSerializer
)
from core.pagination import CustomCursorPagination

class UserProductFavoriteView(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    generics.GenericAPIView
):

    permission_classes = [IsAuthenticated]
    pagination_class = CustomCursorPagination

    
    lookup_field = 'product_id' 
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserProductFavoriteCreateSerializer
        return UserProductFavoriteListSerializer

    def get_queryset(self):
        return UserProductFavorite.objects.filter(
            user=self.request.user
        ).select_related('product__store')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

    def get_object(self):
        queryset = self.get_queryset()
        
        product_id = self.kwargs[self.lookup_field]
    
        obj = generics.get_object_or_404(queryset, product__id=product_id)
        self.check_object_permissions(self.request, obj)
        return obj



class UserStoreFavoriteView(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    generics.GenericAPIView
):
    permission_classes = [IsAuthenticated]
    pagination_class = CustomCursorPagination
    lookup_field = 'store_id'

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserStoreFavoriteCreateSerializer
        return UserStoreFavoriteListSerializer

    def get_queryset(self):
        return UserStoreFavorite.objects.filter(
            user=self.request.user
        ).select_related('store')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

    def get_object(self):
        queryset = self.get_queryset()
        store_id = self.kwargs[self.lookup_field]
        obj = generics.get_object_or_404(queryset, store__id=store_id)
        self.check_object_permissions(self.request, obj)
        return obj


# ===================================================================
# ✅ Lightweight Class-based Views for IDs (faster client-side checks)
# ===================================================================

class UserProductFavoriteIdsView(generics.GenericAPIView):
    """
    إرجاع قائمة بـ IDs المنتجات في wishlist المستخدم
    Lightweight endpoint for quick membership checks
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        ids = list(
            UserProductFavorite.objects.filter(user=request.user)
            .values_list('product_id', flat=True)
        )
        # ✅ إرجاع object للتوافق مع Flutter
        return Response({
            'success': True,
            'product_ids': ids,
            'count': len(ids)
        })


class UserStoreFavoriteIdsView(generics.GenericAPIView):
    """
    إرجاع قائمة بـ IDs المتاجر في wishlist المستخدم
    Lightweight endpoint for quick membership checks
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        ids = list(
            UserStoreFavorite.objects.filter(user=request.user)
            .values_list('store_id', flat=True)
        )
        # ✅ إرجاع object للتوافق مع Flutter
        return Response({
            'success': True,
            'store_ids': ids,
            'count': len(ids)
        })