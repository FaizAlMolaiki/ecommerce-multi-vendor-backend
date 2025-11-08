from rest_framework import serializers
from .models import CartItem, Order, OrderItem
from products.models import ProductVariant


class CartItemSerializer(serializers.ModelSerializer):
    variant_id = serializers.PrimaryKeyRelatedField(
        source='variant', queryset=ProductVariant.objects.all(), write_only=True
    )
    product_name = serializers.SerializerMethodField(read_only=True)
    store_name = serializers.SerializerMethodField(read_only=True)
    unit_price = serializers.SerializerMethodField(read_only=True)
    line_total = serializers.SerializerMethodField(read_only=True)
    image_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CartItem
        fields = [
            'id', 'variant_id', 'quantity', 'added_at',
            'product_name', 'store_name', 'unit_price', 'line_total', 'image_url'
        ]
        read_only_fields = ['id', 'added_at', 'product_name', 'store_name', 'unit_price', 'line_total', 'image_url']

    def get_product_name(self, obj):
        try:
            return obj.variant.product.name
        except Exception:
            return None

    def get_store_name(self, obj):
        try:
            return obj.variant.product.store.name
        except Exception:
            return None

    def get_unit_price(self, obj):
        try:
            return str(obj.variant.price)
        except Exception:
            return None

    def get_line_total(self, obj):
        try:
            return str(obj.variant.price * obj.quantity)
        except Exception:
            return None

    def get_image_url(self, obj):
        """إرجاع URL صالح لصورة المنتج في السلة"""
        try:
            request = self.context.get('request')
            # استخدم صورة الـ variant أو صورة المنتج
            if obj.variant.cover_image_url:
                return request.build_absolute_uri(obj.variant.cover_image_url) if request else obj.variant.cover_image_url
            elif obj.variant.product.cover_image_url:
                return request.build_absolute_uri(obj.variant.product.cover_image_url) if request else obj.variant.product.cover_image_url
            return None
        except Exception:
            return None

    def create(self, validated_data):
        user = self.context['request'].user
        variant = validated_data['variant']
        quantity = validated_data['quantity']
        
        # استخدم get_or_create لتجنب خطأ UNIQUE constraint
        cart_item, created = CartItem.objects.get_or_create(
            user=user,
            variant=variant,
            defaults={'quantity': quantity}
        )
        
        # إذا كان موجوداً بالفعل، زِد الكمية
        if not created:
            cart_item.quantity += quantity
            cart_item.save(update_fields=['quantity'])
        
        return cart_item

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError('Quantity must be at least 1.')
        return value


class OrderItemReadSerializer(serializers.ModelSerializer):
    line_total = serializers.SerializerMethodField()  # ✅ إضافة line_total
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'quantity', 'price_at_purchase',
            'product_name_snapshot', 'variant_options_snapshot',
            'line_total',  # ✅ إضافة
            'status', 'cancellation_reason'
        ]
        read_only_fields = fields
    
    def get_line_total(self, obj):
        """حساب إجمالي السطر (price * quantity)"""
        return obj.price_at_purchase * obj.quantity


class OrderReadSerializer(serializers.ModelSerializer):
    items = OrderItemReadSerializer(many=True, read_only=True)
    store_id = serializers.IntegerField(source='store.id', read_only=True)
    store_name = serializers.CharField(source='store.name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)  # ✅ إضافة user_email

    class Meta:
        model = Order
        fields = [
            'id', 'store_id', 'store_name',
            'user_email',  # ✅ إضافة
            'grand_total', 'delivery_fee', 'shipping_address_snapshot',
            'payment_status', 'fulfillment_status', 'created_at',
            'items'
        ]
        read_only_fields = fields


class CreateOrderSerializer(serializers.Serializer):
    """
    Serializer محسّن لإنشاء طلب جديد
    يدعم: address_id, payment_method, note
    """
    # ✅ دعم address_id من UserAddress
    address_id = serializers.IntegerField(required=False, allow_null=True)
    # ✅ أو استخدام shipping_address مباشرة (للتوافق مع الكود القديم)
    shipping_address = serializers.JSONField(required=False)
    
    # ✅ طرق الدفع المتاحة
    payment_method = serializers.ChoiceField(
        choices=[
            ('cod', 'Cash on Delivery'),
            ('card', 'Credit/Debit Card'),
            ('wallet', 'Wallet'),
        ],
        default='cod'
    )
    
    # ✅ ملاحظة اختيارية
    note = serializers.CharField(required=False, allow_blank=True, max_length=500)

    def validate(self, data):
        """التحقق من وجود address_id أو shipping_address"""
        address_id = data.get('address_id')
        shipping_address = data.get('shipping_address')
        
        # يجب توفير أحدهما على الأقل
        if not address_id and not shipping_address:
            raise serializers.ValidationError(
                'يجب توفير address_id أو shipping_address'
            )
        
        return data
    
    def validate_address_id(self, value):
        """التحقق من أن العنوان ينتمي للمستخدم الحالي"""
        if value:
            user = self.context['request'].user
            try:
                from accounts.models import UserAddress
                address = UserAddress.objects.get(id=value, user=user)
                # حفظ العنوان في context للاستخدام لاحقاً
                self.context['address'] = address
                return value
            except UserAddress.DoesNotExist:
                raise serializers.ValidationError("العنوان غير موجود أو لا ينتمي لك")
        return value
    
    def validate_shipping_address(self, value):
        """التحقق من صحة shipping_address إذا تم إرساله مباشرة"""
        if value and (not isinstance(value, dict) or not value):
            raise serializers.ValidationError('shipping_address must be a non-empty JSON object')
        return value
