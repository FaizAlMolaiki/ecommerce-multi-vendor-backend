from rest_framework import serializers
from .models import CartItem
from stores.models import Store


class GroupedCartItemSerializer(serializers.ModelSerializer):
    """Serializer for individual cart items within a store group"""
    product_name = serializers.CharField(source='variant.product.name', read_only=True)
    unit_price = serializers.DecimalField(source='variant.price', max_digits=10, decimal_places=2, read_only=True)
    line_total = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    variant_id = serializers.IntegerField(source='variant.id', read_only=True)
    product_id = serializers.IntegerField(source='variant.product.id', read_only=True)
    store_id = serializers.IntegerField(source='variant.product.store.id', read_only=True)
    store_name = serializers.CharField(source='variant.product.store.name', read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'variant_id', 'product_id', 'product_name', 'quantity', 
                  'unit_price', 'line_total', 'image_url', 'added_at', 'store_id', 'store_name']

    def get_line_total(self, obj):
        return obj.variant.price * obj.quantity

    def get_image_url(self, obj):
        try:
            request = self.context.get('request')
            if obj.variant.cover_image_url:
                url = obj.variant.cover_image_url
            elif obj.variant.product.cover_image_url:
                url = obj.variant.product.cover_image_url
            else:
                return None
            
            # إذا كان URL نسبي، حوله لمطلق
            if request and url and not url.startswith('http'):
                return request.build_absolute_uri(url)
            return url
        except Exception:
            return None


class GroupedCartByStoreSerializer(serializers.Serializer):
    """Serializer for cart items grouped by store"""
    id = serializers.IntegerField()
    name = serializers.CharField()
    logo = serializers.CharField(allow_null=True)
    cover_image = serializers.CharField(allow_null=True)
    store_sub_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    items = GroupedCartItemSerializer(many=True)

    def to_representation(self, instance):
        # instance is a dict with store info and items
        request = self.context.get('request')
        
        # معالجة URLs النسبية للصور
        logo = instance['logo']
        cover_image = instance['cover_image']
        
        if request:
            if logo and not logo.startswith('http'):
                logo = request.build_absolute_uri(logo)
            if cover_image and not cover_image.startswith('http'):
                cover_image = request.build_absolute_uri(cover_image)
        
        return {
            'id': instance['id'],
            'name': instance['name'],
            'logo': logo,
            'cover_image': cover_image,
            'store_sub_total': instance['store_sub_total'],
            'items': GroupedCartItemSerializer(instance['items'], many=True, context=self.context).data
        }
