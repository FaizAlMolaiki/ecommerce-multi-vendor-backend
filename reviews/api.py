from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from django.db.models import Avg
from .models import StoreReview, ProductReview
from .serializers import StoreReviewSerializer, ProductReviewSerializer


class StoreReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Store Reviews
    - GET /stores/{store_id}/reviews/ - List all reviews for a store
    - POST /stores/{store_id}/reviews/ - Create/Update review
    - GET /stores/{store_id}/reviews/{id}/ - Get specific review
    - DELETE /stores/{store_id}/reviews/{id}/ - Delete review
    """
    serializer_class = StoreReviewSerializer
    
    def get_permissions(self):
        """
        Allow anyone to read reviews, but require authentication for write operations
        """
        if self.action in ['list', 'retrieve', 'stats']:
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        store_id = self.kwargs.get('store_pk')
        if store_id:
            return StoreReview.objects.filter(store_id=store_id).select_related('user', 'store')
        return StoreReview.objects.all().select_related('user', 'store')
    
    def perform_create(self, serializer):
        """Auto-assign the logged-in user"""
        serializer.save(user=self.request.user)
    
    def perform_destroy(self, instance):
        """Only allow users to delete their own reviews"""
        if instance.user != self.request.user:
            return Response(
                {'error': 'You can only delete your own reviews.'},
                status=status.HTTP_403_FORBIDDEN
            )
        instance.delete()
    
    @action(detail=False, methods=['get'], url_path='my-review')
    def my_review(self, request, store_pk=None):
        """Get current user's review for this store"""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            review = StoreReview.objects.get(
                user=request.user,
                store_id=store_pk
            )
            serializer = self.get_serializer(review)
            return Response(serializer.data)
        except StoreReview.DoesNotExist:
            return Response(
                {'detail': 'No review found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request, store_pk=None):
        """Get review statistics for a store"""
        reviews = self.get_queryset()
        
        stats = {
            'average_rating': reviews.aggregate(Avg('rating'))['rating__avg'] or 0,
            'total_reviews': reviews.count(),
            'rating_distribution': {
                'five': reviews.filter(rating=5).count(),
                'four': reviews.filter(rating=4).count(),
                'three': reviews.filter(rating=3).count(),
                'two': reviews.filter(rating=2).count(),
                'one': reviews.filter(rating=1).count(),
            }
        }
        return Response(stats)


class ProductReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Product Reviews
    - GET /products/{product_id}/reviews/ - List all reviews for a product
    - POST /products/{product_id}/reviews/ - Create/Update review
    """
    serializer_class = ProductReviewSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'stats']:
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        product_id = self.kwargs.get('product_pk')
        if product_id:
            return ProductReview.objects.filter(product_id=product_id).select_related('user', 'product')
        return ProductReview.objects.all().select_related('user', 'product')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def perform_destroy(self, instance):
        if instance.user != self.request.user:
            return Response(
                {'error': 'You can only delete your own reviews.'},
                status=status.HTTP_403_FORBIDDEN
            )
        instance.delete()
    
    @action(detail=False, methods=['get'], url_path='my-review')
    def my_review(self, request, product_pk=None):
        """Get current user's review for this product"""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            review = ProductReview.objects.get(
                user=request.user,
                product_id=product_pk
            )
            serializer = self.get_serializer(review)
            return Response(serializer.data)
        except ProductReview.DoesNotExist:
            return Response(
                {'detail': 'No review found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request, product_pk=None):
        """Get review statistics for a product"""
        reviews = self.get_queryset()
        
        avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']
        
        stats = {
            'average_rating': float(avg_rating) if avg_rating else 0.0,
            'total_reviews': reviews.count(),
            'rating_distribution': {
                'five': reviews.filter(rating=5).count(),
                'four': reviews.filter(rating=4).count(),
                'three': reviews.filter(rating=3).count(),
                'two': reviews.filter(rating=2).count(),  # ✅ صحيح
                'one': reviews.filter(rating=1).count(),
            }
        }
        
        return Response(stats)