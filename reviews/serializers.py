from rest_framework import serializers
from .models import StoreReview, ProductReview, OrderReview
from django.contrib.auth import get_user_model

User = get_user_model()


class StoreReviewSerializer(serializers.ModelSerializer):
    """Serializer for Store Reviews"""
    user_name = serializers.SerializerMethodField(read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = StoreReview
        fields = [
            'id',
            'user',
            'user_name',
            'user_email',
            'store',
            'rating',
            'comment',
            'created_at',
        ]
        read_only_fields = ['id', 'user', 'created_at', 'user_name', 'user_email']
    
    def get_user_name(self, obj):
        """Get user's full name or email"""
        if obj.user:
            return obj.user.get_full_name() or obj.user.email
        return 'Anonymous'
    
    def validate_rating(self, value):
        """Validate rating is between 1 and 5"""
        if value < 1 or value > 5:
            raise serializers.ValidationError('Rating must be between 1 and 5.')
        return value
    
    def create(self, validated_data):
        """Create or update review"""
        user = self.context['request'].user
        store = validated_data['store']
        
        # Check if user already reviewed this store
        review, created = StoreReview.objects.update_or_create(
            user=user,
            store=store,
            defaults={
                'rating': validated_data['rating'],
                'comment': validated_data.get('comment', ''),
            }
        )
        return review


class ProductReviewSerializer(serializers.ModelSerializer):
    """Serializer for Product Reviews"""
    user_name = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = ProductReview
        fields = [
            'id',
            'user',
            'user_name',
            'product',
            'rating',
            'comment',
            'created_at',
        ]
        read_only_fields = ['id', 'user', 'created_at', 'user_name']
    
    def get_user_name(self, obj):
        if obj.user:
            return obj.user.get_full_name() or obj.user.email
        return 'Anonymous'
    
    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError('Rating must be between 1 and 5.')
        return value
    
    def create(self, validated_data):
        user = self.context['request'].user
        product = validated_data['product']
        
        review, created = ProductReview.objects.update_or_create(
            user=user,
            product=product,
            defaults={
                'rating': validated_data['rating'],
                'comment': validated_data.get('comment', ''),
            }
        )
        return review


class OrderReviewSerializer(serializers.ModelSerializer):
    """Serializer for Order Reviews"""
    user_name = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = OrderReview
        fields = [
            'id',
            'user',
            'user_name',
            'order',
            'delivery_speed_rating',
            'service_quality_rating',
            'created_at',
        ]
        read_only_fields = ['id', 'user', 'created_at', 'user_name']
    
    def get_user_name(self, obj):
        if obj.user:
            return obj.user.get_full_name() or obj.user.email
        return 'Anonymous'
    
    def validate_delivery_speed_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError('Delivery speed rating must be between 1 and 5.')
        return value
    
    def validate_service_quality_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError('Service quality rating must be between 1 and 5.')
        return value
    
    def create(self, validated_data):
        user = self.context['request'].user
        order = validated_data['order']
        
        review, created = OrderReview.objects.update_or_create(
            user=user,
            order=order,
            defaults={
                'delivery_speed_rating': validated_data['delivery_speed_rating'],
                'service_quality_rating': validated_data['service_quality_rating'],
            }
        )
        return review
