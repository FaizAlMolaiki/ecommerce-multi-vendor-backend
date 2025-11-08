# from rest_framework import serializers
# from .models import Promotion, Coupon, Offer, CouponRedemption

# class CouponSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Coupon
#         fields = ['id', 'code', 'active', 'start_at', 'end_at', 'usage_limit', 'limit_per_user']

# class PromotionSerializer(serializers.ModelSerializer):
#     required_coupon = CouponSerializer(read_only=True)
    
#     class Meta:
#         model = Promotion
#         fields = [
#             'id', 'name', 'active', 'start_at', 'end_at', 'min_purchase_amount',
#             'priority', 'stackable', 'required_coupon', 'promotion_type', 'value',
#             'stores', 'categories', 'products', 'variants'
#         ]

# class OfferSerializer(serializers.ModelSerializer):
#     required_coupon = CouponSerializer(read_only=True)
    
#     class Meta:
#         model = Offer
#         fields = [
#             'id', 'name', 'active', 'start_at', 'end_at', 'min_purchase_amount',
#             'priority', 'stackable', 'required_coupon', 'offer_type', 'configuration',
#             'stores', 'categories', 'products', 'variants'
#         ]

# class CouponRedemptionSerializer(serializers.ModelSerializer):
#     coupon = CouponSerializer(read_only=True)
    
#     class Meta:
#         model = CouponRedemption
#         fields = ['id', 'coupon', 'user', 'order', 'redeemed_at']


from rest_framework import serializers

from products.models import Product, ProductCategory, ProductVariant
from .models import Promotion, Coupon, Offer, CouponRedemption


# ✅ =======================Mixin مشترك للصور=======================
class ImageUrlMixin:
    """Mixin لإضافة وظيفة get_image_url لأي Serializer"""
    
    def get_image_url(self, obj):
        """إرجاع الرابط الكامل والصالح للصورة."""
        if obj.image and hasattr(obj.image, 'url'):
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None
# ====================================================================

class CouponSerializer(serializers.ModelSerializer):
    # ✅ FIXED: استخدام الحقول الصحيحة من موديل Coupon
    is_active = serializers.BooleanField(source='active')
    valid_from = serializers.DateTimeField(source='start_at', allow_null=True)
    valid_to = serializers.DateTimeField(source='end_at', allow_null=True)
    usage_count = serializers.SerializerMethodField()
    
    # NEW: نظام الموافقة
    approval_status = serializers.CharField(read_only=True)
    reviewed_at = serializers.DateTimeField(read_only=True)
    rejection_reason = serializers.CharField(read_only=True)
    
    def get_usage_count(self, obj):
        return obj.redemptions.count() if hasattr(obj, 'redemptions') else 0
    
    class Meta:
        model = Coupon
        fields = [
            'id', 
            'code', 
            'is_active',
            'valid_from', 
            'valid_to', 
            'usage_limit', 
            'limit_per_user',
            'usage_count',
            'stores',  # ✅ أضفنا هذا
            'created_at', 
            'updated_at',
            # NEW: حقول الموافقة
            'approval_status',
            'reviewed_at',
            'rejection_reason',
        ]


class PromotionSerializer(ImageUrlMixin, serializers.ModelSerializer):
    # ===================================================================
    #   القسم الأول: حقول القراءة (ما يراه Flutter)
    # ===================================================================

    # حقول متوافقة مع الأسماء القديمة إذا لزم الأمر
    discount_type = serializers.CharField(source='promotion_type', read_only=True)
    discount_value = serializers.DecimalField(source='value', max_digits=10, decimal_places=2, read_only=True)
    start_date = serializers.DateTimeField(source='start_at', read_only=True)
    end_date = serializers.DateTimeField(source='end_at', read_only=True)
    is_active = serializers.BooleanField(source='active', read_only=True)

    # حقل image_url للقراءة فقط، يعرض الرابط الكامل
    image_url = serializers.SerializerMethodField()
    # get_image_url() موجودة في ImageUrlMixin ✅

    # ===================================================================
    #   القسم الثاني: حقول الكتابة (ما يرسله Flutter)
    # ===================================================================

    # حقل 'image' للكتابة فقط، يتوقع نصاً (رابط كامل أو مسار نسبي)
    image = serializers.CharField(write_only=True, required=False, allow_blank=True, allow_null=True)

    # تعريف الحقول بأسماءها الصحيحة في الموديل للسماح بالكتابة
    # promotion_type, value, start_at, end_at, active
    # سيتم التعامل معها تلقائياً بواسطة DRF إذا كانت في fields

    # IDs للكتابة في علاقات ManyToMany
    products = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), many=True, required=False
    )
    categories = serializers.PrimaryKeyRelatedField(
        queryset=ProductCategory.objects.all(), many=True, required=False
    )
    variants = serializers.PrimaryKeyRelatedField(
        queryset=ProductVariant.objects.all(), many=True, required=False
    )

    class Meta:
        model = Promotion
        fields = [
            # --- المفتاح الأساسي (للقراءة دائماً) ---
            'id', 
            
            # --- الحقول الأساسية (للقراءة والكتابة) ---
            'name',
            'description',
            'priority',
            'stackable',
            'min_purchase_amount',

            # --- حقول القراءة فقط (ما يراه Flutter) ---
            # هذه الحقول محسوبة أو لها أسماء مخصصة للعرض فقط
            'image_url', 
            'discount_type', 
            'discount_value',
            'start_date', 
            'end_date', 
            'is_active',
            'created_at',
            'updated_at',
            
            # NEW: حقول نظام الموافقة (للقراءة فقط)
            'approval_status',
            'reviewed_at',
            'rejection_reason',

            # --- حقول الكتابة فقط (ما يرسله Flutter) ---
            # هذه الحقول تستخدم لتحديث الموديل
            'image',            # حقل النص لتحديث الصورة
            'promotion_type',   # الاسم الحقيقي في الموديل
            'value',            # الاسم الحقيقي في الموديل
            'start_at',         # الاسم الحقيقي في الموديل
            'end_at',           # الاسم الحقيقي في الموديل
            'active',           # الاسم الحقيقي في الموديل
            'products',         # لتحديث المنتجات المرتبطة
            'categories',       # لتحديث الفئات المرتبطة
            'variants',         # لتحديث المتغيرات المرتبطة
        ]
    
    # --- إعدادات إضافية للحقول ---
    # هذا الجزء مهم جداً لتحديد سلوك الحقول عند الكتابة
    extra_kwargs = {
        # نجعل الحقول التي لها نظير للقراءة فقط (read-only counterpart)
        # متاحة للكتابة فقط (write-only) لتجنب التكرار في الاستجابة
        'promotion_type': {'write_only': True, 'required': True},
        'value': {'write_only': True, 'required': True},
        'start_at': {'write_only': True, 'required': False, 'allow_null': True},
        'end_at': {'write_only': True, 'required': False, 'allow_null': True},
        'active': {'write_only': True, 'required': False},
        
        # حقل الصورة للكتابة فقط
        'image': {'write_only': True, 'required': False},

        # حقول العلاقات ليست إجبارية عند التحديث
        'products': {'write_only': True, 'required': False},
        'categories': {'write_only': True, 'required': False},
        'variants': {'write_only': True, 'required': False},
    }

    # في PromotionSerializer داخل ملف serializers.py

    def validate_image(self, value):
        """
        التحقق من صحة رابط الصورة المدخل وتنظيفه.
        تضمن هذه الدالة أن ما يتم حفظه في قاعدة البيانات هو المسار النسبي
        بدون MEDIA_URL ليعمل Django بشكل صحيح.
        """
        if not value:  # يسمح بالقيم الفارغة (null أو '') لحذف الصورة
            return value

        path = value

        # الخطوة 1: إذا كان رابطاً كاملاً، استخرج المسار بعد '/media/'
        if path.startswith('http'):
            if '/media/' in path:
                # هذا يستخرج "promotions/2025/image.jpg"
                path = path.split('/media/', 1)[-1]
            else:
                raise serializers.ValidationError("رابط الصورة غير صالح. يجب أن يكون من نفس الخادم.")
        
        # الخطوة 2: إذا كان المسار لا يزال يحتوي على '/media/' في بدايته، قم بإزالته
        # هذا يعالج حالة إرسال مسار نسبي مثل '/media/promotions/image.jpg'
        if path.startswith('/media/'):
            # استبدال أول ظهور فقط
            path = path.replace('/media/', '', 1)

        # الخطوة 3: إزالة أي شرطة مائلة "/" في البداية
        if path.startswith('/'):
            path = path[1:]
            
        # النتيجة النهائية التي يتم حفظها في قاعدة البيانات ستكون مثل:
        # "promotions/2025/11/05/3b1c4b89b89a40b280941bdc2296da21.jpg"
        return path

    def to_internal_value(self, data):
        """
        تعديل البيانات القادمة قبل التحقق منها.
        هذا يسمح لـ Flutter بإرسال 'discount_type' بدلاً من 'promotion_type' إذا لزم الأمر.
        """
        # إذا كان Flutter يرسل أسماء الحقول المتوافقة (discount_type)،
        # نقوم بنسخها إلى الأسماء الصحيحة التي يتوقعها DRF للكتابة.
        if 'discount_type' in data:
            data['promotion_type'] = data['discount_type']
        if 'discount_value' in data:
            data['value'] = data['discount_value']
        if 'start_date' in data:
            data['start_at'] = data['start_date']
            
        if 'end_date' in data:
            data['end_at'] = data['end_date']

        if 'is_active' in data:
            data['active'] = data['is_active']
        
        return super().to_internal_value(data)

class OfferSerializer(ImageUrlMixin, serializers.ModelSerializer):
    # ✅ Matches Flutter OfferModel field naming
    is_active = serializers.BooleanField(source='active')
    
    # ===================== ✅ التعديل الجديد والأبسط هنا =====================
    image = serializers.CharField(write_only=True, required=False, allow_null=True)
    image_url = serializers.SerializerMethodField()
    # get_image_url() موجودة في ImageUrlMixin ✅

    # ✅ IDs للعناصر المرتبطة (matches Flutter List<int>)
    store_ids = serializers.PrimaryKeyRelatedField(
        source='stores',
        many=True,
        read_only=True
    )
    
    # ✅ Backward compatibility: return first store_id
    store_id = serializers.SerializerMethodField()
    
    product_ids = serializers.PrimaryKeyRelatedField(
        source='products',
        many=True,
        read_only=True
    )
    category_ids = serializers.PrimaryKeyRelatedField(
        source='categories',
        many=True,
        read_only=True
    )
    variant_ids = serializers.PrimaryKeyRelatedField(
        source='variants',
        many=True,
        read_only=True
    )
    
    # ✅ كوبون مرتبط (إن وجد)
    required_coupon = CouponSerializer(read_only=True)
    
    def get_store_id(self, obj):
        """استخراج store_id من stores المرتبطة بالـ Offer"""
        if obj.stores.exists():
            return obj.stores.first().id
        return None
    
    class Meta:
        model = Offer
        fields = [
            'id', 
            'name', 
            'description',  # ✅ NEW - matches Flutter
            'image',  # ✅ NEW - matches Flutter
            'image_url',
            'offer_type',
            'configuration',
            'store_id',  # ✅ Backward compatibility (single store)
            'store_ids',  # ✅ All associated stores
            'product_ids',  # ✅ renamed from products
            'category_ids',  # ✅ renamed from categories
            'variant_ids',  # ✅ renamed from variants
            'start_at', 
            'end_at', 
            'is_active',  # ✅ renamed from active
            'priority', 
            'stackable',
            'min_purchase_amount',
            'required_coupon',  # ✅ ForeignKey to Coupon
            'created_at', 
            'updated_at',
            # NEW: حقول نظام الموافقة
            'approval_status',
            'reviewed_at',
            'rejection_reason',
        ]

    # ===================== ✅ وأضف هذه الدالة =====================
    def update(self, instance, validated_data):
        """
        تعديل مخصص لدالة التحديث.
        """
        return super().update(instance, validated_data)
    # =============================================================

class CouponRedemptionSerializer(serializers.ModelSerializer):
    coupon = CouponSerializer(read_only=True)
    
    class Meta:
        model = CouponRedemption
        fields = ['id', 'coupon', 'user', 'order', 'redeemed_at']
