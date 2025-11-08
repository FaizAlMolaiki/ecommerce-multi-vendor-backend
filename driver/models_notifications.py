"""
نماذج الإشعارات للموصلين
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class DriverNotification(models.Model):
    """
    نموذج إشعارات الموصل
    """
    
    NOTIFICATION_TYPES = [
        ('new_order', 'طلب جديد متاح'),
        ('order_assigned', 'تم تعيين طلب'),
        ('order_cancelled', 'تم إلغاء طلب'),
        ('order_completed', 'تم إكمال طلب'),
        ('system_message', 'رسالة من النظام'),
        ('promotion', 'عرض ترويجي'),
        ('warning', 'تحذير'),
        ('info', 'معلومة عامة'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'منخفض'),
        ('medium', 'متوسط'),
        ('high', 'عالي'),
        ('urgent', 'عاجل'),
    ]
    
    # معلومات أساسية
    driver = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='driver_notifications',
        verbose_name='الموصل'
    )
    
    # محتوى الإشعار
    title = models.CharField(max_length=200, verbose_name='العنوان')
    message = models.TextField(verbose_name='الرسالة')
    notification_type = models.CharField(
        max_length=20, 
        choices=NOTIFICATION_TYPES,
        default='info',
        verbose_name='نوع الإشعار'
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_LEVELS,
        default='medium',
        verbose_name='الأولوية'
    )
    
    # بيانات إضافية (JSON)
    data = models.JSONField(
        default=dict, 
        blank=True,
        verbose_name='بيانات إضافية',
        help_text='بيانات JSON إضافية مثل معرف الطلب، الروابط، إلخ'
    )
    
    # حالة الإشعار
    is_read = models.BooleanField(default=False, verbose_name='تم القراءة')
    is_sent = models.BooleanField(default=False, verbose_name='تم الإرسال')
    
    # أوقات مهمة
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    read_at = models.DateTimeField(null=True, blank=True, verbose_name='تاريخ القراءة')
    expires_at = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name='تاريخ الانتهاء',
        help_text='الإشعارات المنتهية الصلاحية لن تظهر'
    )
    
    class Meta:
        verbose_name = 'إشعار موصل'
        verbose_name_plural = 'إشعارات الموصلين'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['driver', '-created_at']),
            models.Index(fields=['driver', 'is_read']),
            models.Index(fields=['notification_type']),
        ]
    
    def __str__(self):
        return f'{self.driver.email} - {self.title}'
    
    def mark_as_read(self):
        """تمييز الإشعار كمقروء"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    def is_expired(self):
        """التحقق من انتهاء صلاحية الإشعار"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    @property
    def icon(self):
        """أيقونة الإشعار حسب النوع"""
        icons = {
            'new_order': '🔔',
            'order_assigned': '✅',
            'order_cancelled': '❌',
            'order_completed': '🎉',
            'system_message': '📢',
            'promotion': '🎁',
            'warning': '⚠️',
            'info': 'ℹ️',
        }
        return icons.get(self.notification_type, 'ℹ️')
    
    @property
    def color(self):
        """لون الإشعار حسب النوع"""
        colors = {
            'new_order': 'green',
            'order_assigned': 'blue',
            'order_cancelled': 'orange',
            'order_completed': 'purple',
            'system_message': 'gray',
            'promotion': 'gold',
            'warning': 'red',
            'info': 'blue',
        }
        return colors.get(self.notification_type, 'blue')


class NotificationTemplate(models.Model):
    """
    قوالب الإشعارات لسهولة الإدارة
    """
    
    name = models.CharField(max_length=100, unique=True, verbose_name='اسم القالب')
    title_template = models.CharField(max_length=200, verbose_name='قالب العنوان')
    message_template = models.TextField(verbose_name='قالب الرسالة')
    notification_type = models.CharField(
        max_length=20, 
        choices=DriverNotification.NOTIFICATION_TYPES,
        verbose_name='نوع الإشعار'
    )
    priority = models.CharField(
        max_length=10,
        choices=DriverNotification.PRIORITY_LEVELS,
        default='medium',
        verbose_name='الأولوية'
    )
    
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    
    class Meta:
        verbose_name = 'قالب إشعار'
        verbose_name_plural = 'قوالب الإشعارات'
    
    def __str__(self):
        return self.name
    
    def create_notification(self, driver, **context):
        """إنشاء إشعار من القالب"""
        title = self.title_template.format(**context)
        message = self.message_template.format(**context)
        
        return DriverNotification.objects.create(
            driver=driver,
            title=title,
            message=message,
            notification_type=self.notification_type,
            priority=self.priority,
            data=context
        )
