from rest_framework import serializers
from stores.serializers import StoreListSerializer as StoreSerializer
from products.serializers import ProductListSerializer
from .models import UserProductFavorite, UserStoreFavorite

class UserProductFavoriteListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing favorite products (Read-only).
    Includes nested product details.
    """
    product = ProductListSerializer(read_only=True)

    class Meta:
        model = UserProductFavorite
        fields = ['id', 'product', 'created_at']


class UserProductFavoriteCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for adding a product to favorites (Write-only).
    """
    class Meta:
        model = UserProductFavorite
        fields = ['product']

    def validate_product(self, value):
        """
        Check if the product is already in the user's favorites.
        """
        user = self.context['request'].user
        if UserProductFavorite.objects.filter(user=user, product=value).exists():
            raise serializers.ValidationError("This product is already in your wishlist.")
        return value



class UserStoreFavoriteListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing favorite stores (Read-only).
    Includes nested store details.
    """
    store = StoreSerializer(read_only=True)

    class Meta:
        model = UserStoreFavorite
        fields = ['id', 'store', 'created_at']


class UserStoreFavoriteCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for adding a store to favorites (Write-only).
    """
    class Meta:
        model = UserStoreFavorite
        fields = ['store']

    def validate_store(self, value):

        user = self.context['request'].user
        if UserStoreFavorite.objects.filter(user=user, store=value).exists():
            raise serializers.ValidationError("This store is already in your favorites.")
        return value