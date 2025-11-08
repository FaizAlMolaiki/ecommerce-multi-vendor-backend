from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class NotificationType(models.TextChoices):
    """أنواع الإشعارات المختلفة"""
    ORDER = 'order', _('طلب')
    PRODUCT = 'product', _('منتج')
    STORE = 'store', _('متجر')
    PROMOTION = 'promotion', _('عرض')
    PAYMENT = 'payment', _('دفع')
    SHIPPING = 'shipping', _('شحن')
    REVIEW = 'review', _('تقييم')
    SYSTEM = 'system', _('نظام')


class NotificationPriority(models.TextChoices):
    """أولويات الإشعارات"""
    LOW = 'low', _('منخفضة')
    NORMAL = 'normal', _('عادية')
    HIGH = 'high', _('عالية')
    URGENT = 'urgent', _('عاجلة')


class Notification(models.Model):
    """نموذج الإشعارات"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='notifications',
        verbose_name=_('المستخدم')
    )
    title = models.CharField(
        max_length=255, 
        verbose_name=_('العنوان')
    )
    body = models.TextField(
        verbose_name=_('المحتوى')
    )
    type = models.CharField(
        max_length=20, 
        choices=NotificationType.choices, 
        default=NotificationType.SYSTEM,
        verbose_name=_('النوع')
    )
    priority = models.CharField(
        max_length=10, 
        choices=NotificationPriority.choices, 
        default=NotificationPriority.NORMAL,
        verbose_name=_('الأولوية')
    )
    data = models.JSONField(
        default=dict, 
        blank=True,
        verbose_name=_('البيانات الإضافية'),
        help_text=_('بيانات إضافية بصيغة JSON')
    )
    image_url = models.URLField(
        blank=True, 
        null=True,
        verbose_name=_('رابط الصورة')
    )
    is_read = models.BooleanField(
        default=False,
        verbose_name=_('مقروء')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('تاريخ الإنشاء')
    )
    read_at = models.DateTimeField(
        blank=True, 
        null=True,
        verbose_name=_('تاريخ القراءة')
    )
    related_id = models.PositiveIntegerField(
        blank=True, 
        null=True,
        verbose_name=_('معرف العنصر المرتبط'),
        help_text=_('معرف الطلب أو المنتج أو المتجر المرتبط بالإشعار')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = _('إشعار')
        verbose_name_plural = _('الإشعارات')
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['type']),
        ]
        
    def __str__(self):
        return f"{self.title} - {self.user.email}"
    
    def mark_as_read(self):
        """تعليم الإشعار كمقروء"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


class FCMDevice(models.Model):
    """نموذج أجهزة Firebase Cloud Messaging"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='fcm_devices',
        verbose_name=_('المستخدم'),
        null=True,  # السماح بقيمة null
        blank=True  # السماح بترك الحقل فارغاً
    )
    registration_token = models.TextField(
        unique=True,
        verbose_name=_('رمز التسجيل'),
        help_text=_('رمز FCM الخاص بالجهاز')
    )
    device_type = models.CharField(
        max_length=10, 
        choices=[
            ('android', _('أندرويد')), 
            ('ios', _('آيفون'))
        ],
        verbose_name=_('نوع الجهاز')
    )
    device_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('اسم الجهاز')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('نشط')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('تاريخ الإنشاء')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('تاريخ التحديث')
    )
    last_used_at = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name=_('آخر استخدام')
    )

    class Meta:
        verbose_name = _('جهاز FCM')
        verbose_name_plural = _('أجهزة FCM')
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['registration_token']),
        ]
        
    def __str__(self):
        user_email = self.user.email if self.user else "Anonymous"
        return f"{user_email} - {self.device_type} ({self.device_name})"


class NotificationTemplate(models.Model):
    """قوالب الإشعارات"""
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('اسم القالب')
    )
    type = models.CharField(
        max_length=20, 
        choices=NotificationType.choices,
        verbose_name=_('نوع الإشعار')
    )
    title_template = models.CharField(
        max_length=255,
        verbose_name=_('قالب العنوان'),
        help_text=_('يمكن استخدام متغيرات مثل {user_name}, {order_id}')
    )
    body_template = models.TextField(
        verbose_name=_('قالب المحتوى'),
        help_text=_('يمكن استخدام متغيرات مثل {user_name}, {order_id}')
    )
    priority = models.CharField(
        max_length=10, 
        choices=NotificationPriority.choices, 
        default=NotificationPriority.NORMAL,
        verbose_name=_('الأولوية الافتراضية')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('نشط')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('تاريخ الإنشاء')
    )

    class Meta:
        verbose_name = _('قالب إشعار')
        verbose_name_plural = _('قوالب الإشعارات')
        
    def __str__(self):
        return self.name
