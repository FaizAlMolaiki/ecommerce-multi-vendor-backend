# stores/serializers.py

from rest_framework import serializers

from products.models import Product, ProductCategory, ProductImage, ProductVariant
from stores.models import PlatformCategory, Store


class PlatformCategorySerializer(serializers.ModelSerializer):
    """
    Serializer for platform categories.
    """
    class Meta:
        model = PlatformCategory
        fields = ['id', 'name', 'image_url']

class StoreSerializer(serializers.ModelSerializer):
    """
    An efficient and informative serializer for the Store model.
    """
    # 1. استخدام serializer متداخل لعرض تفاصيل الفئة بدلاً من ID
    platform_category = PlatformCategorySerializer(read_only=True)

    # 2. حقول مخصصة (SerializerMethodField) لعرض بيانات محسوبة أو منسقة
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)

    # 3. مثال لحقل مخصص آخر إذا احتجته في المستقبل
    # is_favorited = serializers.SerializerMethodField()

    class Meta:
        model = Store
        fields = [
            'id',
            'name',
            'description',
            'logo_url',
            'is_active',
            'platform_category',
            'owner', # نعرض ID المالك
            'owner_name', # ونعرض اسم المالك لسهولة الاستخدام

            # الحقول المحسوبة (Denormalized) التي تأتي مباشرة من الموديل
            'product_count',
            'average_rating',
            'review_count',
            'favorites_count',
        ]
        read_only_fields = [
            'owner', 
            'product_count', 
            'average_rating', 
            'review_count', 
            'favorites_count'
        ]

  
    
    


# --- Serializers مساعدة ---

class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ['id', 'name']

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image_url', 'display_order']

class ProductVariantSerializer(serializers.ModelSerializer):
    # عرض الصور الخاصة بهذا المتغير فقط
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = ProductVariant
        fields = [
            'id', 
            'price', 
            'sku', 
            'options', # e.g., {'color': 'Black', 'storage': '256GB'}
            'cover_image_url',
            'images',
        ]

# --- Serializers الرئيسية ---

class ProductListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing products. Shows essential info for display in a grid or list.
    (عرض مختصر)
    """
    # عرض اسم المتجر فقط في القائمة
    store_name = serializers.CharField(source='store.name', read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'store', # ID المتجر
            'store_name',
            'cover_image_url',
            'average_rating',
            'selling_count',
            # قد نضيف أقل سعر من المتغيرات هنا إذا لزم الأمر
            # 'base_price', 
        ]

class ProductDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for the product detail view. Shows all related information.
    (عرض تفصيلي)
    """
    # استخدام serializers متداخلة لعرض التفاصيل الكاملة
    store = StoreSerializer(read_only=True)
    category = ProductCategorySerializer(read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    
    # جلب الصور التي لا ترتبط بمتغير معين (صور المنتج العامة)
    images = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'description',
            'specifications',
            'store',
            'category',
            'variants',
            'images', # الصور العامة
            'average_rating',
            'review_count',
            'selling_count',
        ]
    
    def get_images(self, obj):
        # جلب الصور المرتبطة بالمنتج نفسه فقط (variant is null)
        general_images = obj.images.filter(variant__isnull=True)
        return ProductImageSerializer(general_images, many=True).data