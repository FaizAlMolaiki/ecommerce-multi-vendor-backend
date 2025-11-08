# ===================================================================
# ✅ Serializers محسّن - يجمع أفضل ما في المشروعين
# - من مجلد one: ProductListSerializer منفصل + حساب ديناميكي للتقييمات  
# - من المشروع الرئيسي: دعم الصور المتعددة في create/update
# ===================================================================

from rest_framework import serializers
from .models import ProductCategory, Product, ProductVariant, ProductImage
from django.db.models import Avg  # ✅ للحساب الديناميكي

# ===================================================================
#  Serializer للصور
# ===================================================================
class ProductImageSerializer(serializers.ModelSerializer):
    """
    Serializer for the ProductImage model.
    Accepts image data for creating/updating images.
    """
    # أصبح هذا الحقل قابلاً للكتابة لاستقبال الروابط من التطبيق
    image_url = serializers.URLField(max_length=500)

    class Meta:
        model = ProductImage
        fields = ['id', 'image_url', 'display_order']
        # 'id' للقراءة فقط لأنه يُنشأ تلقائيًا
        read_only_fields = ['id']


# ===================================================================
#  Serializer للمتغيرات
# ===================================================================
class ProductVariantSerializer(serializers.ModelSerializer):
    """Serializer for product variants with nested images"""
    images = ProductImageSerializer(many=True, required=False)

    # NEW: حقول السعر مع الخصم
    original_price = serializers.DecimalField(
        source='price', max_digits=10, decimal_places=2, read_only=True
    )
    discounted_price = serializers.SerializerMethodField()
    has_discount = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = [
            'id', 'product', 
            'price',  # OLD: السعر الأصلي (للتوافق)
            'original_price',  # NEW: نفس السعر بتسمية واضحة
            'discounted_price',  # NEW: السعر بعد الخصم
            'has_discount',  # NEW: هل يوجد خصم؟
            'sku', 'options', 'cover_image_url', 'images'
        ]
        extra_kwargs = {
            'product': {'write_only': True, 'required': False}
        }
    
    def create(self, validated_data):
        """إنشاء متغير جديد مع صوره"""
        images_data = validated_data.pop('images', [])
        variant = ProductVariant.objects.create(**validated_data)
        
        for img_data in images_data:
            ProductImage.objects.create(
                variant=variant,
                product=variant.product,
                image_url=img_data.get('image_url'),
                display_order=img_data.get('display_order', 1)
            )
        
        return variant
    
    def update(self, instance, validated_data):
        """تحديث متغير موجود مع صوره"""
        images_data = validated_data.pop('images', None)
        
        # تحديث بيانات المتغير
        instance.price = validated_data.get('price', instance.price)
        instance.sku = validated_data.get('sku', instance.sku)
        instance.options = validated_data.get('options', instance.options)
        instance.cover_image_url = validated_data.get('cover_image_url', instance.cover_image_url)
        instance.save()
        
        # تحديث الصور إذا تم إرسالها
        if images_data is not None:
            instance.images.all().delete()
            for img_data in images_data:
                ProductImage.objects.create(
                    variant=instance,
                    product=instance.product,
                    image_url=img_data.get('image_url'),
                    display_order=img_data.get('display_order', 1)
                )
        
        return instance
    # NEW: methods للخصومات
    def get_has_discount(self, obj):
        """
        هل المتغير عليه خصم؟
        يتحقق من وجود promotion نشط يستهدف هذا المتغير
        """
        from pricing.models import Promotion
        from django.utils import timezone
        
        try:
            # البحث عن promotions نشطة تستهدف هذا المتغير
            now = timezone.now()
            active_promotions = Promotion.objects.filter(
                variants=obj,
                active=True,
                start_at__lte=now,
                end_at__gte=now
            ).exists()
            
            return active_promotions
        except Exception as e:
            # Fallback: تحقق من has_discount على مستوى المنتج
            return obj.product.has_discount if hasattr(obj.product, 'has_discount') else False
    
    def get_discounted_price(self, obj):
        """
        السعر بعد الخصم (إن وجد)
        يحسب السعر الفعلي بعد تطبيق جميع الخصومات النشطة
        """
        from pricing.models import Promotion
        from django.utils import timezone
        from decimal import Decimal
        
        try:
            # البحث عن أفضل promotion نشط
            now = timezone.now()
            promotions = Promotion.objects.filter(
                variants=obj,
                active=True,
                start_at__lte=now,
                end_at__gte=now
            ).order_by('-value')  # أعلى خصم أولاً
            
            if promotions.exists():
                promotion = promotions.first()
                price = Decimal(str(obj.price))
                
                # حساب الخصم حسب النوع
                if promotion.promotion_type == 'PRODUCT_PERCENTAGE_DISCOUNT':
                    discount = price * (promotion.value / Decimal('100'))
                    final_price = price - discount
                elif promotion.promotion_type == 'PRODUCT_FIXED_AMOUNT':
                    final_price = price - promotion.value
                else:
                    final_price = price
                
                # تأكد من أن السعر لا يصبح سالباً
                final_price = max(final_price, Decimal('0'))
                return str(final_price)
            
            return None
        except Exception as e:
            # Fallback: استخدام الطريقة القديمة
            if hasattr(obj.product, 'has_discount') and obj.product.has_discount:
                if hasattr(obj.product, 'get_price_after_discount'):
                    return str(obj.product.get_price_after_discount(obj.price))
            return None


# ===================================================================
#  ✅ Serializer للقوائم (من مجلد one)
# ===================================================================

class ProductListSerializer(serializers.ModelSerializer):
    """Serializer مبسط لقائمة المنتجات"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    store_name = serializers.CharField(source='store.name', read_only=True)
    store_id = serializers.IntegerField(source='store.id', read_only=True)
    min_price = serializers.SerializerMethodField()
    
    # ✅ حساب ديناميكي
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()

    # 🆕 الحقول الجديدة للتعامل الذكي مع المتغيرات
    has_single_variant = serializers.SerializerMethodField()
    default_variant_id = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'cover_image_url', 'average_rating',
            'review_count', 'selling_count', 'category_name', 'store_name', 'store_id', 'min_price',
            'has_single_variant',  # 🆕
            'default_variant_id',  # 🆕
        ]

    def get_min_price(self, obj):
        """الحصول على أقل سعر من المتغيرات"""
        variants = obj.variants.all()
        if variants:
            return min(variant.price for variant in variants)
        return None
    
    def get_average_rating(self, obj):
        """حساب متوسط التقييمات"""
        try:
            from reviews.models import ProductReview
            result = ProductReview.objects.filter(product=obj).aggregate(Avg('rating'))
            return round(result['rating__avg'], 1) if result['rating__avg'] else 0.0
        except:
            return 0.0
    
    def get_review_count(self, obj):
        """حساب عدد التقييمات"""
        try:
            from reviews.models import ProductReview
            return ProductReview.objects.filter(product=obj).count()
        except:
            return 0
        

    # 🆕 دالة جديدة: التحقق من وجود متغير واحد بدون خيارات
    def get_has_single_variant(self, obj):
        """
        تحقق إذا كان المنتج له متغير واحد فقط بدون خيارات حقيقية
        
        Returns:
            bool: True إذا كان متغير واحد بدون options حقيقية
        """
        # عدد المتغيرات
        variants = obj.variants.all()
        
        if variants.count() != 1:
            return False
        
        # جلب المتغير الوحيد
        variant = variants.first()
        
        if not variant or not variant.options:
            return True
        
        # تصفية الخيارات: استثناء الحقول التقنية
        technical_keys = ['stock', 'is_active', 'additional_images']
        real_options = {
            k: v for k, v in variant.options.items() 
            if k not in technical_keys and v is not None and v != ''
        }
        
        # إذا لم يتبق أي خيار حقيقي
        return len(real_options) == 0
    
    # 🆕 دالة جديدة: ID المتغير الافتراضي
    def get_default_variant_id(self, obj):
        """
        ID المتغير الافتراضي (فقط إذا كان متغير واحد بدون خيارات)
        
        Returns:
            int|None: ID المتغير أو None
        """
        if self.get_has_single_variant(obj):
            variant = obj.variants.first()
            return variant.id if variant else None
        return None

# ===================================================================
#  ✅ Serializer للتفاصيل (من مجلد one + دعم الصور المتعددة)
# ===================================================================
class ProductDetailSerializer(serializers.ModelSerializer):
    """Serializer مفصل للمنتج مع دعم الصور المتعددة"""
    variants = ProductVariantSerializer(many=True, required=False)
    images = ProductImageSerializer(many=True, required=False)  # ✅ قابل للكتابة
    category_name = serializers.CharField(source='category.name', read_only=True)
    store_name = serializers.CharField(source='store.name', read_only=True)
    store_id = serializers.IntegerField(source='store.id', read_only=True)
    
    # ✅ حساب ديناميكي
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'store', 'store_id', 'category', 'category_name', 'store_name', 'name', 'description',
            'specifications', 'cover_image_url', 'average_rating',
            'review_count', 'selling_count', 'variants', 'images', 'is_active'
        ]
        read_only_fields = ['selling_count']
    
    def get_average_rating(self, obj):
        """حساب متوسط التقييمات"""
        try:
            from reviews.models import ProductReview
            result = ProductReview.objects.filter(product=obj).aggregate(Avg('rating'))
            return round(result['rating__avg'], 1) if result['rating__avg'] else 0.0
        except:
            return 0.0

    def get_review_count(self, obj):
        """حساب عدد التقييمات"""
        try:
            from reviews.models import ProductReview
            return ProductReview.objects.filter(product=obj).count()
        except:
            return 0

    # ✅ دعم الصور المتعددة (من المشروع الرئيسي)
    def create(self, validated_data):
        """إنشاء منتج جديد مع صوره المتعددة"""
        images_data = validated_data.pop('images', [])
        product = Product.objects.create(**validated_data)
        for image_data in images_data:
            ProductImage.objects.create(product=product, **image_data)
        return product

    def update(self, instance, validated_data):
        """تحديث منتج موجود مع تحديث قائمة صوره والمتغيرات"""
        images_data = validated_data.pop('images', None)
        variants_data = validated_data.pop('variants', None)
        
        # تحديث بيانات المنتج الأساسية
        instance = super().update(instance, validated_data)
        
        # تحديث صور المنتج (ليس المتغيرات)
        if images_data is not None:
            instance.images.filter(variant__isnull=True).delete()
            for image_data in images_data:
                ProductImage.objects.create(product=instance, **image_data)
        
        # تحديث المتغيرات مع صورها
        if variants_data is not None:
            existing_variants = {v.id: v for v in instance.variants.all()}
            updated_variant_ids = []
            
            for variant_data in variants_data:
                variant_id = variant_data.get('id')
                
                # إزالة حقول غير مدعومة
                variant_data.pop('stockQuantity', None)
                variant_data.pop('cart_quantity', None)
                
                if variant_id and variant_id in existing_variants:
                    # تحديث متغير موجود
                    variant_serializer = ProductVariantSerializer()
                    variant_serializer.update(existing_variants[variant_id], variant_data)
                    updated_variant_ids.append(variant_id)
                elif not variant_id or variant_id < 0:
                    # إنشاء متغير جديد (ID سالب أو غير موجود)
                    variant_data['product'] = instance
                    variant_data.pop('id', None)  # إزالة ID السالب
                    variant_serializer = ProductVariantSerializer()
                    new_variant = variant_serializer.create(variant_data)
                    updated_variant_ids.append(new_variant.id)
            
            # ✅ حذف المتغيرات القديمة التي لم تعد موجودة
            instance.variants.exclude(id__in=updated_variant_ids).delete()
        
        return instance


# ===================================================================
#  Serializer عام للمنتج (backward compatibility)
# ===================================================================
class ProductSerializer(ProductDetailSerializer):
    """Serializer عام - يستخدم ProductDetailSerializer"""
    pass


# ===================================================================
#  ✅ Serializer لفئات المنتجات (مع دعم الهيكل الشجري من Two)
# ===================================================================
class ProductCategorySerializer(serializers.ModelSerializer):
    """
    Serializer for the ProductCategory model with hierarchical support.
    """
    children = serializers.SerializerMethodField()
    level = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductCategory
        fields = ['id', 'store', 'name', 'parent', 'children', 'level']
    
    def get_children(self, obj):
        """إرجاع الفئات الفرعية"""
        if obj.get_children().exists():
            return ProductCategorySerializer(obj.get_children(), many=True).data
        return []
    
    def get_level(self, obj):
        """إرجاع مستوى الفئة في الشجرة"""
        return obj.level
