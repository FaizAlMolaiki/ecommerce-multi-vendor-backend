from rest_framework import serializers
from django.utils import timezone
from django.contrib.auth import get_user_model
from urllib.parse import urlparse
from .models import Notification, FCMDevice, NotificationTemplate
from .utils import serialize_content_object

User = get_user_model()


class NotificationSerializer(serializers.ModelSerializer):
    """سيريالايزر الإشعارات"""
    content_object = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'body', 'type', 'priority', 'data', 
            'image_url', 'is_read', 'created_at', 'read_at',
            'content_type', 'object_id', 'content_object', 'user'
        ]
        read_only_fields = ('id', 'created_at', 'read_at', 'content_object')
    
    def get_content_object(self, obj):
        """استدعاء دالة serialize من utils"""
        return serialize_content_object(obj)
    
    def to_representation(self, instance):
        """تخصيص عرض البيانات"""
        data = super().to_representation(instance)
        
        # إضافة تسميات النوع والأولوية
        data['type_display'] = instance.get_type_display()
        data['priority_display'] = instance.get_priority_display()
        
        # تنسيق التواريخ
        if instance.created_at:
            data['created_at_formatted'] = instance.created_at.strftime('%Y-%m-%d %H:%M')
        
        if instance.read_at:
            data['read_at_formatted'] = instance.read_at.strftime('%Y-%m-%d %H:%M')
            
        return data
    
    def validate_data(self, value):
        """التحقق من صحة JSONField"""
        if value is None:
            return value
            
        if not isinstance(value, dict):
            raise serializers.ValidationError("البيانات يجب أن تكون JSON object")
        
        # التحقق من حجم البيانات (5KB max)
        if len(str(value)) > 5000:
            raise serializers.ValidationError("البيانات كبيرة جداً (الحد الأقصى 5KB)")
        
        return value
    
    def validate_image_url(self, value):
        """التحقق من صحة رابط الصورة"""
        if not value:
            return value
        
        # التحقق من صيغة URL
        try:
            parsed = urlparse(value)
            if not all([parsed.scheme, parsed.netloc]):
                raise serializers.ValidationError("رابط غير صحيح")
        except Exception:
            raise serializers.ValidationError("رابط غير صحيح")
        
        # التحقق من امتدادات الصور
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']
        if not any(value.lower().endswith(ext) for ext in valid_extensions):
            raise serializers.ValidationError(
                "صيغة الصورة غير مدعومة. الصيغ المدعومة: jpg, jpeg, png, gif, webp, svg"
            )
        
        return value
    
    def validate_object_id(self, value):
        """التحقق من object_id"""
        if value is not None and value < 1:
            raise serializers.ValidationError("معرف العنصر يجب أن يكون موجباً")
        return value
    
    def validate(self, attrs):
        """Validation شامل للـ GenericForeignKey"""
        content_type = attrs.get('content_type')
        object_id = attrs.get('object_id')
        notification_type = attrs.get('type')
        
        # التحقق من توافق content_type مع object_id
        if content_type and not object_id:
            raise serializers.ValidationError({
                'object_id': 'يجب تحديد معرف العنصر عند تحديد نوع المحتوى'
            })
        
        if object_id and not content_type:
            raise serializers.ValidationError({
                'content_type': 'يجب تحديد نوع المحتوى عند تحديد معرف العنصر'
            })
        
        # التحقق من وجود العنصر المرتبط (optional - Django handles this)
        if content_type and object_id:
            try:
                from django.contrib.contenttypes.models import ContentType
                ct = ContentType.objects.get_for_id(content_type.id if hasattr(content_type, 'id') else content_type)
                model_class = ct.model_class()
                
                if model_class and not model_class.objects.filter(id=object_id).exists():
                    raise serializers.ValidationError({
                        'object_id': f'{ct.model} غير موجود'
                    })
            except Exception:
                # إذا حدث خطأ، نتجاهل التحقق (Django سيتعامل معه)
                pass
        
        return attrs


class FCMDeviceSerializer(serializers.ModelSerializer):
    """سيريالايزر أجهزة FCM"""
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    
    class Meta:
        model = FCMDevice
        fields = ['registration_token', 'device_type', 'device_name', 'user']
        read_only_fields = ('user',)
    
    def validate_registration_token(self, value):
        """التحقق من صحة التوكن وعدم تكراره"""
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("التوكن مطلوب")
        
        # التحقق من طول التوكن (FCM tokens usually 152-200+ chars)
        if len(value) < 100:
            raise serializers.ValidationError("التوكن غير صحيح (قصير جداً)")
        
        return value.strip()
    
    def validate(self, attrs):
        """التحقق من عدد الأجهزة للمستخدم"""
        user = attrs.get('user')
        
        if user:
            # حد أقصى 5 أجهزة نشطة لكل مستخدم
            active_devices_count = FCMDevice.objects.filter(
                user=user, 
                is_active=True
            ).count()
            
            if active_devices_count >= 5:
                raise serializers.ValidationError(
                    "وصلت للحد الأقصى من الأجهزة المسجلة (5 أجهزة). "
                    "يرجى حذف جهاز قديم أولاً."
                )
        
        return attrs
    
    def create(self, validated_data):
        """تعطيل الأجهزة القديمة بنفس التوكن قبل الإنشاء"""
        token = validated_data['registration_token']
        
        # تعطيل أي أجهزة أخرى بنفس التوكن (للمستخدمين الآخرين)
        FCMDevice.objects.filter(registration_token=token).update(is_active=False)
        
        # إنشاء الجهاز الجديد
        return super().create(validated_data)
        


class NotificationTemplateSerializer(serializers.ModelSerializer):
    """سيريالايزر قوالب الإشعارات"""
    
    class Meta:
        model = NotificationTemplate
        fields = '__all__'
        read_only_fields = ('id', 'created_at')


class NotificationCreateSerializer(serializers.ModelSerializer):
    """سيريالايزر إنشاء إشعار جديد"""
    users = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="قائمة معرفات المستخدمين لإرسال الإشعار إليهم"
    )
    sender = serializers.HiddenField(default=serializers.CurrentUserDefault())
    
    class Meta:
        model = Notification
        fields = [
            'title', 'body', 'type', 'priority', 'data', 
            'image_url', 'content_type', 'object_id', 'users', 'sender'
        ]
    
    def validate_users(self, value):
        """التحقق من وجود المستخدمين وصلاحيات الإرسال"""
        if not value:
            return value
        
        # التحقق من صلاحيات المستخدم الحالي
        request = self.context.get('request')
        if request and request.user:
            # فقط الـ staff يمكنهم الإرسال الجماعي
            if not request.user.is_staff:
                raise serializers.ValidationError(
                    "لا تملك صلاحية إرسال إشعارات جماعية. "
                    "هذه الميزة متاحة للمشرفين فقط."
                )
        
        # حد أقصى 100 مستخدم في المرة الواحدة
        if len(value) > 100:
            raise serializers.ValidationError(
                f"الحد الأقصى 100 مستخدم في المرة الواحدة. "
                f"تم تحديد {len(value)} مستخدم."
            )
        
        # التحقق من عدم وجود تكرار
        if len(value) != len(set(value)):
            raise serializers.ValidationError("يوجد تكرار في قائمة المستخدمين")
        
        # التحقق من وجود المستخدمين
        existing_users_count = User.objects.filter(id__in=value, is_active=True).count()
        if existing_users_count != len(value):
            raise serializers.ValidationError(
                f"بعض المستخدمين غير موجودين أو غير نشطين. "
                f"تم العثور على {existing_users_count} من {len(value)} مستخدم."
            )
        
        return value
        
    def create(self, validated_data):
        """إنشاء إشعارات متعددة بشكل آمن"""
        users = validated_data.pop('users', [])
        sender = validated_data.pop('sender', None)
        notifications = []
        
        if users:
            # إضافة معلومات المرسل في data
            if 'data' not in validated_data:
                validated_data['data'] = {}
            
            if sender:
                validated_data['data']['sender_id'] = sender.id
                validated_data['data']['sender_name'] = sender.get_full_name() or sender.email
            
            # إرسال لمستخدمين محددين
            for user_id in users:
                notification_data = validated_data.copy()
                notification_data['user_id'] = user_id
                notifications.append(Notification(**notification_data))
        else:
            # إرسال للمستخدم الحالي فقط
            validated_data['user'] = self.context['request'].user
            notifications.append(Notification(**validated_data))
            
        # إنشاء الإشعارات بشكل مجمع (batch size 100)
        created_notifications = Notification.objects.bulk_create(
            notifications,
            batch_size=100
        )
        
        # إرجاع أول إشعار (للتوافق مع API)
        return created_notifications[0] if created_notifications else None


class NotificationStatsSerializer(serializers.Serializer):
    """سيريالايزر إحصائيات الإشعارات"""
    total_count = serializers.IntegerField(read_only=True)
    unread_count = serializers.IntegerField(read_only=True)
    read_count = serializers.IntegerField(read_only=True)
    by_type = serializers.DictField(read_only=True)
    by_priority = serializers.DictField(read_only=True)
