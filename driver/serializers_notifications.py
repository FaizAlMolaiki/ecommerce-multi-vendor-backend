"""
Serializers للإشعارات الخاصة بالموصلين
"""
from rest_framework import serializers
from .models_notifications import DriverNotification, NotificationTemplate 


class DriverNotificationSerializer(serializers.ModelSerializer):
    """
    Serializer لإشعارات الموصل
    """
    
    # حقول إضافية
    icon = serializers.ReadOnlyField()
    color = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = DriverNotification
        fields = [
            'id',
            'title',
            'message',
            'notification_type',
            'priority',
            'data',
            'is_read',
            'created_at',
            'read_at',
            'expires_at',
            'icon',
            'color',
            'is_expired',
            'time_ago'
        ]
        read_only_fields = [
            'id', 
            'created_at', 
            'read_at',
            'icon',
            'color',
            'is_expired',
            'time_ago'
        ]
    
    def get_time_ago(self, obj):
        """حساب الوقت المنقضي منذ إنشاء الإشعار"""
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        diff = now - obj.created_at
        
        if diff < timedelta(minutes=1):
            return 'الآن'
        elif diff < timedelta(hours=1):
            minutes = int(diff.total_seconds() / 60)
            return f'منذ {minutes} دقيقة'
        elif diff < timedelta(days=1):
            hours = int(diff.total_seconds() / 3600)
            return f'منذ {hours} ساعة'
        elif diff < timedelta(days=7):
            days = diff.days
            return f'منذ {days} يوم'
        else:
            return obj.created_at.strftime('%Y-%m-%d')


class NotificationTemplateSerializer(serializers.ModelSerializer):
    """
    Serializer لقوالب الإشعارات
    """
    
    class Meta:
        model = NotificationTemplate
        fields = [
            'id',
            'name',
            'title_template',
            'message_template',
            'notification_type',
            'priority',
            'is_active',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class CreateNotificationSerializer(serializers.Serializer):
    """
    Serializer لإنشاء إشعار جديد
    """
    
    title = serializers.CharField(max_length=200)
    message = serializers.CharField()
    notification_type = serializers.ChoiceField(
        choices=DriverNotification.NOTIFICATION_TYPES,
        default='info'
    )
    priority = serializers.ChoiceField(
        choices=DriverNotification.PRIORITY_LEVELS,
        default='medium'
    )
    data = serializers.JSONField(required=False, default=dict)
    expires_at = serializers.DateTimeField(required=False, allow_null=True)
    
    def validate_title(self, value):
        """التحقق من العنوان"""
        if len(value.strip()) < 3:
            raise serializers.ValidationError('العنوان قصير جداً')
        return value.strip()
    
    def validate_message(self, value):
        """التحقق من الرسالة"""
        if len(value.strip()) < 5:
            raise serializers.ValidationError('الرسالة قصيرة جداً')
        return value.strip()


class NotificationStatsSerializer(serializers.Serializer):
    """
    Serializer لإحصائيات الإشعارات
    """
    
    unread_count = serializers.IntegerField()
    total_count = serializers.IntegerField()
    today_count = serializers.IntegerField(required=False)
    this_week_count = serializers.IntegerField(required=False)
    
    # إحصائيات حسب النوع
    new_orders_count = serializers.IntegerField(required=False)
    assigned_orders_count = serializers.IntegerField(required=False)
    cancelled_orders_count = serializers.IntegerField(required=False)
    system_messages_count = serializers.IntegerField(required=False)
