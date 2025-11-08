from rest_framework import serializers
from django.utils import timezone
from .models import Notification, FCMDevice, NotificationTemplate


class NotificationSerializer(serializers.ModelSerializer):
    """سيريالايزر الإشعارات"""
    
    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'body', 'type', 'priority', 'data', 
            'image_url', 'is_read', 'created_at', 'read_at', 'related_id'
        ]
        read_only_fields = ('id', 'created_at', 'read_at')
    
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


class FCMDeviceSerializer(serializers.ModelSerializer):
    """سيريالايزر أجهزة FCM"""
    
    class Meta:
        model = FCMDevice
        fields = ['registration_token', 'device_type', 'device_name']
        


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
    
    class Meta:
        model = Notification
        fields = [
            'title', 'body', 'type', 'priority', 'data', 
            'image_url', 'related_id', 'users'
        ]
        
    def create(self, validated_data):
        """إنشاء إشعارات متعددة"""
        users = validated_data.pop('users', [])
        notifications = []
        
        if users:
            # إرسال لمستخدمين محددين
            for user_id in users:
                notification_data = validated_data.copy()
                notification_data['user_id'] = user_id
                notifications.append(Notification(**notification_data))
        else:
            # إرسال للمستخدم الحالي فقط
            validated_data['user'] = self.context['request'].user
            notifications.append(Notification(**validated_data))
            
        # إنشاء الإشعارات بشكل مجمع
        created_notifications = Notification.objects.bulk_create(notifications)
        
        # إرجاع أول إشعار (للتوافق مع API)
        return created_notifications[0] if created_notifications else None


class NotificationStatsSerializer(serializers.Serializer):
    """سيريالايزر إحصائيات الإشعارات"""
    total_count = serializers.IntegerField(read_only=True)
    unread_count = serializers.IntegerField(read_only=True)
    read_count = serializers.IntegerField(read_only=True)
    by_type = serializers.DictField(read_only=True)
    by_priority = serializers.DictField(read_only=True)
