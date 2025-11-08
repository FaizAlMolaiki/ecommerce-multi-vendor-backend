from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Notification, FCMDevice, NotificationTemplate


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """إدارة الإشعارات في لوحة الإدارة"""
    list_display = [
        'title', 'user_email', 'type', 'priority', 'is_read', 
        'created_at', 'read_status_badge'
    ]
    list_filter = [
        'type', 'priority', 'is_read', 'created_at'
    ]
    search_fields = [
        'title', 'body', 'user__email', 'user__name'
    ]
    readonly_fields = [
        'created_at', 'read_at', 'read_status_badge'
    ]
    list_per_page = 25
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('user', 'title', 'body', 'type', 'priority')
        }),
        ('بيانات إضافية', {
            'fields': ('data', 'image_url', 'related_id'),
            'classes': ('collapse',)
        }),
        ('حالة القراءة', {
            'fields': ('is_read', 'read_at', 'read_status_badge'),
            'classes': ('collapse',)
        }),
        ('معلومات النظام', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def user_email(self, obj):
        """عرض بريد المستخدم"""
        if obj.user:
            return obj.user.email
        return "Anonymous"
    user_email.short_description = 'البريد الإلكتروني'
    user_email.admin_order_field = 'user__email'
    
    def read_status_badge(self, obj):
        """عرض حالة القراءة كشارة ملونة"""
        if obj.is_read:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ مقروء</span>'
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">✗ غير مقروء</span>'
            )
    read_status_badge.short_description = 'حالة القراءة'
    
    def get_queryset(self, request):
        """تحسين الاستعلامات"""
        return super().get_queryset(request).select_related('user')
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        """تعليم الإشعارات المحددة كمقروءة"""
        updated = queryset.update(is_read=True)
        self.message_user(request, f'تم تعليم {updated} إشعار كمقروء')
    mark_as_read.short_description = 'تعليم كمقروء'
    
    def mark_as_unread(self, request, queryset):
        """تعليم الإشعارات المحددة كغير مقروءة"""
        updated = queryset.update(is_read=False, read_at=None)
        self.message_user(request, f'تم تعليم {updated} إشعار كغير مقروء')
    mark_as_unread.short_description = 'تعليم كغير مقروء'


@admin.register(FCMDevice)
class FCMDeviceAdmin(admin.ModelAdmin):
    """إدارة أجهزة FCM في لوحة الإدارة"""
    list_display = [
        'user_email', 'device_type', 'device_name', 'is_active', 
        'created_at', 'last_used_at', 'status_badge'
    ]
    list_filter = [
        'device_type', 'is_active', 'created_at', 'last_used_at'
    ]
    search_fields = [
        'user__email', 'user__name', 'device_name', 'registration_token'
    ]
    readonly_fields = [
        'registration_token', 'created_at', 'updated_at', 'status_badge'
    ]
    list_per_page = 25
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('معلومات المستخدم', {
            'fields': ('user',)
        }),
        ('معلومات الجهاز', {
            'fields': ('device_type', 'device_name', 'is_active')
        }),
        ('رمز التسجيل', {
            'fields': ('registration_token',),
            'classes': ('collapse',)
        }),
        ('معلومات النظام', {
            'fields': ('created_at', 'updated_at', 'last_used_at', 'status_badge'),
            'classes': ('collapse',)
        }),
    )
    
    def user_email(self, obj):
        """عرض بريد المستخدم"""
        if obj.user:
            return obj.user.email
        return "Anonymous"
    user_email.short_description = 'البريد الإلكتروني'
    user_email.admin_order_field = 'user__email'
    
    def status_badge(self, obj):
        """عرض حالة الجهاز كشارة ملونة"""
        if obj.is_active:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ نشط</span>'
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">✗ غير نشط</span>'
            )
    status_badge.short_description = 'الحالة'
    
    def get_queryset(self, request):
        """تحسين الاستعلامات"""
        return super().get_queryset(request).select_related('user')
    
    actions = ['activate_devices', 'deactivate_devices']
    
    def activate_devices(self, request, queryset):
        """تفعيل الأجهزة المحددة"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'تم تفعيل {updated} جهاز')
    activate_devices.short_description = 'تفعيل الأجهزة'
    
    def deactivate_devices(self, request, queryset):
        """إلغاء تفعيل الأجهزة المحددة"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'تم إلغاء تفعيل {updated} جهاز')
    deactivate_devices.short_description = 'إلغاء تفعيل الأجهزة'


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    """إدارة قوالب الإشعارات في لوحة الإدارة"""
    list_display = [
        'name', 'type', 'priority', 'is_active', 'created_at', 'status_badge'
    ]
    list_filter = [
        'type', 'priority', 'is_active', 'created_at'
    ]
    search_fields = [
        'name', 'title_template', 'body_template'
    ]
    readonly_fields = [
        'created_at', 'status_badge'
    ]
    list_per_page = 25
    date_hierarchy = 'created_at'
    ordering = ['name']
    
    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('name', 'type', 'priority', 'is_active')
        }),
        ('قوالب النصوص', {
            'fields': ('title_template', 'body_template'),
            'description': 'يمكن استخدام متغيرات مثل {user_name}, {order_id}, {product_name}'
        }),
        ('معلومات النظام', {
            'fields': ('created_at', 'status_badge'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        """عرض حالة القالب كشارة ملونة"""
        if obj.is_active:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ نشط</span>'
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">✗ غير نشط</span>'
            )
    status_badge.short_description = 'الحالة'
    
    actions = ['activate_templates', 'deactivate_templates']
    
    def activate_templates(self, request, queryset):
        """تفعيل القوالب المحددة"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'تم تفعيل {updated} قالب')
    activate_templates.short_description = 'تفعيل القوالب'
    
    def deactivate_templates(self, request, queryset):
        """إلغاء تفعيل القوالب المحددة"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'تم إلغاء تفعيل {updated} قالب')
    deactivate_templates.short_description = 'إلغاء تفعيل القوالب'
