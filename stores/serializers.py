from rest_framework import serializers
from .models import Store, PlatformCategory

# يستخدم هذا السيريالايزر لتحويل بيانات المتجر إلى JSON والعكس
class PlatformCategorySerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = PlatformCategory
        fields = ['id', 'name', 'image_url', 'is_featured']
    
    def get_image_url(self, obj):
        """إرجاع URL صالح للصورة أو None"""
        if obj.image_url and obj.image_url.strip():
            return obj.image_url
        return None

# ✅ محدث: يستخدم هذا الكلاس لعرض معلومات مختصرة في القائمة
class StoreListSerializer(serializers.ModelSerializer):
    platform_category = PlatformCategorySerializer(read_only=True)
    platform_category_name = serializers.CharField(source='platform_category.name', read_only=True)
    owner_name = serializers.CharField(source='owner.name', read_only=True)
    is_favorite = serializers.BooleanField(read_only=True, default=False)
    logo_url = serializers.SerializerMethodField()
    cover_image_url = serializers.SerializerMethodField()
    
    # ✅ الإحصائيات من Model (محدثة بـ Signals)
    # product_count, average_rating, review_count, favorites_count
    # يتم قراءتها مباشرة من Model
    
    # خصائص مساعدة للنموذج الجديد
    is_request = serializers.ReadOnlyField()
    is_active_store = serializers.ReadOnlyField()
    can_sell = serializers.ReadOnlyField()
    is_open_now = serializers.ReadOnlyField()
    
    def get_logo_url(self, obj):
        """إرجاع URL صالح للشعار مع الـ base URL الحالي"""
        if obj.logo_url and obj.logo_url.strip():
            request = self.context.get('request')
            if request and not obj.logo_url.startswith('http'):
                return request.build_absolute_uri(obj.logo_url)
            return obj.logo_url
        return None
    
    def get_cover_image_url(self, obj):
        """إرجاع URL صالح لصورة الغلاف مع الـ base URL الحالي"""
        if obj.cover_image_url and obj.cover_image_url.strip():
            request = self.context.get('request')
            if request and not obj.cover_image_url.startswith('http'):
                return request.build_absolute_uri(obj.cover_image_url)
            return obj.cover_image_url
        return None
    
    class Meta:
        model = Store
        fields = [
            'id', 'name', 'description', 'logo_url', 'cover_image_url', 'city', 'status',
            'platform_category', 'platform_category_name', 'owner_name',
            'opening_time', 'closing_time',
            'average_rating', 'review_count', 'product_count', 'favorites_count',
            'created_at', 'is_favorite', 'is_request', 'is_active_store', 'can_sell', 'is_open_now'
        ]

# ✅ محدث: يستخدم هذا السيريالايزر لعرض كل تفاصيل المتجر
class StoreDetailSerializer(serializers.ModelSerializer):
    platform_category = PlatformCategorySerializer(read_only=True)
    platform_category_name = serializers.CharField(source='platform_category.name', read_only=True)
    platform_category_id = serializers.IntegerField(write_only=True, required=False)
    owner_name = serializers.CharField(source='owner.name', read_only=True)
    owner_email = serializers.CharField(source='owner.email', read_only=True)
    is_favorite = serializers.BooleanField(read_only=True, default=False)
    logo_url = serializers.CharField(max_length=500, allow_blank=True, required=False)
    cover_image_url = serializers.CharField(max_length=500, allow_blank=True, required=False)
    
    # ✅ الإحصائيات من Model (محدثة بـ Signals)
    # product_count, average_rating, review_count, favorites_count
    
    # خصائص مساعدة للنموذج الجديد
    is_request = serializers.ReadOnlyField()
    is_active_store = serializers.ReadOnlyField()
    can_sell = serializers.ReadOnlyField()
    is_open_now = serializers.ReadOnlyField()
    
    def to_representation(self, instance):
        """تحويل البيانات للعرض - إضافة الـ base URL للصور"""
        data = super().to_representation(instance)
        request = self.context.get('request')
        
        if request and data.get('logo_url'):
            if not data['logo_url'].startswith('http'):
                data['logo_url'] = request.build_absolute_uri(data['logo_url'])
        
        if request and data.get('cover_image_url'):
            if not data['cover_image_url'].startswith('http'):
                data['cover_image_url'] = request.build_absolute_uri(data['cover_image_url'])
        
        return data
    
    def validate_logo_url(self, value):
        """التحقق من صحة URL الشعار"""
        if not value:
            return value
        
        # إذا كان URL كامل، استخراج المسار النسبي
        if value.startswith('http'):
            if '/media/' in value:
                return '/media/' + value.split('/media/')[-1]
            else:
                raise serializers.ValidationError("URL غير صالح - يجب أن يحتوي على /media/")
        
        # إذا كان مسار نسبي، التأكد من أنه يبدأ بـ /media/
        if not value.startswith('/media/'):
            raise serializers.ValidationError("المسار يجب أن يبدأ بـ /media/")
        
        return value
    
    def validate_cover_image_url(self, value):
        """التحقق من صحة URL صورة الغلاف"""
        if not value:
            return value
        
        # إذا كان URL كامل، استخراج المسار النسبي
        if value.startswith('http'):
            if '/media/' in value:
                return '/media/' + value.split('/media/')[-1]
            else:
                raise serializers.ValidationError("URL غير صالح - يجب أن يحتوي على /media/")
        
        # إذا كان مسار نسبي، التأكد من أنه يبدأ بـ /media/
        if not value.startswith('/media/'):
            raise serializers.ValidationError("المسار يجب أن يبدأ بـ /media/")
        
        return value
    
    class Meta:
        model = Store
        fields = [
            'id', 'name', 'description', 'logo_url', 'cover_image_url', 'status',
            'platform_category', 'platform_category_name', 'platform_category_id',
            'phone_number', 'address',
            'city', 'opening_time', 'closing_time',
            'owner_name', 'owner_email',
            'created_at', 'updated_at', 'reviewed_at', 'approved_at',
            'product_count', 'average_rating', 'review_count', 'favorites_count',
            'is_favorite', 'is_request', 'is_active_store', 'can_sell', 'is_open_now'
        ]
        read_only_fields = [
            'id', 'owner_name', 'owner_email', 'status',
            'created_at', 'updated_at', 'reviewed_at', 'approved_at',
            'product_count', 'average_rating', 'review_count', 'favorites_count'
        ]

# ✅ جديد: Serializer لإنشاء طلب متجر جديد
class StoreRequestCreateSerializer(serializers.ModelSerializer):
    """Serializer لإنشاء طلب متجر جديد"""
    
    platform_category_id = serializers.IntegerField(required=False)
    
    class Meta:
        model = Store
        fields = [
            'name', 'description', 'platform_category_id', 'logo_url', 'cover_image_url',
            'phone_number', 'address',
            'city', 'opening_time', 'closing_time'
        ]
    
    def validate_platform_category_id(self, value):
        """التحقق من وجود الفئة"""
        if value:
            try:
                PlatformCategory.objects.get(id=value)
                return value
            except PlatformCategory.DoesNotExist:
                raise serializers.ValidationError("فئة المتجر غير موجودة")
        return value
    
    def validate_city(self, value):
        """التحقق من صحة المدينة - حقل مفتوح"""
        # المدن يتم التحقق منها في Frontend (Flutter)
        if value and len(value) > 50:
            raise serializers.ValidationError("اسم المدينة طويل جداً")
        return value
    
    def validate(self, data):
        """التحقق من أوقات العمل"""
        opening_time = data.get('opening_time')
        closing_time = data.get('closing_time')
        
        # إذا تم إدخال أحد الأوقات، يجب إدخال الآخر
        if (opening_time and not closing_time) or (closing_time and not opening_time):
            raise serializers.ValidationError({
                'opening_time': 'يجب إدخال وقت الفتح والإغلاق معاً',
                'closing_time': 'يجب إدخال وقت الفتح والإغلاق معاً'
            })
        
        return data
    
    def create(self, validated_data):
        """إنشاء طلب متجر جديد"""
        platform_category_id = validated_data.pop('platform_category_id', None)
        platform_category = None
        if platform_category_id:
            platform_category = PlatformCategory.objects.get(id=platform_category_id)
        
        logo_url = validated_data.pop('logo_url', '')
        cover_image_url = validated_data.pop('cover_image_url', '')
        
        store = Store.objects.create(
            platform_category=platform_category,
            status=Store.StoreStatus.PENDING,
            logo_url=logo_url,
            cover_image_url=cover_image_url,
            **validated_data
        )
        return store

# ✅ جديد: Serializer لإجراءات الإدارة
class StoreActionSerializer(serializers.Serializer):
    """Serializer لإجراءات الإدارة على المتاجر"""
    
    ACTION_CHOICES = [
        ('approve', 'موافقة'),
        ('reject', 'رفض'),
        ('activate', 'تفعيل'),
        ('suspend', 'إيقاف'),
        ('close', 'إغلاق'),
    ]
    
    action = serializers.ChoiceField(choices=ACTION_CHOICES)
    reason = serializers.CharField(max_length=500, required=False, allow_blank=True)
    
    def validate(self, data):
        """التحقق من صحة الإجراء"""
        action = data['action']
        store = self.context['store']
        
        if action == 'approve' and not store.is_request:
            raise serializers.ValidationError("يمكن الموافقة على الطلبات فقط")
        
        if action == 'reject' and not store.is_request:
            raise serializers.ValidationError("يمكن رفض الطلبات فقط")
        
        if action == 'activate' and store.status != Store.StoreStatus.APPROVED:
            raise serializers.ValidationError("يمكن تفعيل المتاجر المعتمدة فقط")
        
        return data