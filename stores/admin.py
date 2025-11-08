from django.contrib import admin
from django.utils.html import format_html
from .models import Store, PlatformCategory


@admin.register(PlatformCategory)
class PlatformCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_featured', 'stores_count']
    list_filter = ['is_featured']
    search_fields = ['name']
    
    def stores_count(self, obj):
        return obj.stores.count()
    stores_count.short_description = 'عدد المتاجر'


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'owner', 'colored_status', 'platform_category', 
        'created_at', 'reviewed_at', 'product_count', 'average_rating'
    ]
    list_filter = ['status', 'platform_category', 'created_at', 'city']
    search_fields = ['name', 'description', 'owner__email']
    readonly_fields = [
        'created_at', 'updated_at', 'reviewed_at', 'approved_at',
        'product_count', 'average_rating', 'review_count', 'favorites_count'
    ]
    
    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('name', 'description', 'owner', 'platform_category', 'status')
        }),
        ('بيانات الاتصال', {
            'fields': ('phone_number', 'email', 'address', 'website', 'logo_url', 'cover_image_url', 'city'),
            'classes': ('collapse',)
        }),
        ('أوقات العمل', {
            'fields': ('opening_time', 'closing_time'),
            'classes': ('collapse',)
        }),
        ('بيانات الطلب', {
            'fields': ('business_license', 'admin_notes'),
            'classes': ('collapse',)
        }),
        ('التواريخ', {
            'fields': ('created_at', 'updated_at', 'reviewed_at', 'approved_at'),
            'classes': ('collapse',)
        }),
        ('الإحصائيات (محدثة بـ Signals)', {
            'fields': ('product_count', 'average_rating', 'review_count', 'favorites_count'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_stores', 'reject_stores', 'activate_stores', 'suspend_stores']
    
    def approve_stores(self, request, queryset):
        approved_count = 0
        for store in queryset:
            if store.is_request:
                try:
                    store.approve(admin_user=request.user)
                    approved_count += 1
                except ValueError:
                    pass
        self.message_user(request, f'تمت الموافقة على {approved_count} متجر')
    approve_stores.short_description = 'الموافقة على المتاجر المحددة'
    
    def reject_stores(self, request, queryset):
        rejected_count = 0
        for store in queryset:
            if store.is_request:
                try:
                    store.reject(reason="تم الرفض من لوحة الإدارة", admin_user=request.user)
                    rejected_count += 1
                except ValueError:
                    pass
        self.message_user(request, f'تم رفض {rejected_count} متجر')
    reject_stores.short_description = 'رفض المتاجر المحددة'
    
    def activate_stores(self, request, queryset):
        activated_count = 0
        for store in queryset:
            if store.status == Store.StoreStatus.APPROVED:
                try:
                    store.activate()
                    activated_count += 1
                except ValueError:
                    pass
        self.message_user(request, f'تم تفعيل {activated_count} متجر')
    activate_stores.short_description = 'تفعيل المتاجر المحددة'
    
    def suspend_stores(self, request, queryset):
        suspended_count = 0
        for store in queryset:
            if store.is_active_store:
                try:
                    store.suspend(reason="تم الإيقاف من لوحة الإدارة")
                    suspended_count += 1
                except ValueError:
                    pass
        self.message_user(request, f'تم إيقاف {suspended_count} متجر')
    suspend_stores.short_description = 'إيقاف المتاجر المحددة'
    
    def colored_status(self, obj):
        colors = {
            'pending': 'orange', 'under_review': 'blue', 'approved': 'green',
            'active': 'darkgreen', 'rejected': 'red', 'suspended': 'purple', 'closed': 'gray'
        }
        color = colors.get(obj.status, 'black')
        return format_html('<span style="color: {};">{}</span>', color, obj.get_status_display())
    colored_status.short_description = 'الحالة'