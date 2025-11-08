from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Coupon, Promotion, Offer, CouponRedemption


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'active', 'usage_stats', 'validity_period', 'linked_rules_count']
    list_filter = ['active', 'start_at', 'end_at']
    search_fields = ['code']
    readonly_fields = ['usage_stats_detail', 'linked_rules_detail']
    
    fieldsets = (
        ('معلومات الكوبون', {
            'fields': ('code', 'active')
        }),
        ('فترة الصلاحية', {
            'fields': ('start_at', 'end_at'),
            'classes': ('collapse',)
        }),
        ('حدود الاستخدام', {
            'fields': ('usage_limit', 'limit_per_user'),
            'classes': ('collapse',)
        }),
        ('إحصائيات', {
            'fields': ('usage_stats_detail', 'linked_rules_detail'),
            'classes': ('collapse',)
        }),
    )
    
    def usage_stats(self, obj):
        used = obj.redemptions.count()
        if obj.usage_limit:
            return format_html(
                '<span style="color: {};">{}/{}</span>',
                'red' if used >= obj.usage_limit else 'green',
                used, obj.usage_limit
            )
        return format_html('<span style="color: green;">{} (غير محدود)</span>', used)
    usage_stats.short_description = 'الاستخدام'
    
    def validity_period(self, obj):
        now = timezone.now()
        if not obj.start_at and not obj.end_at:
            return format_html('<span style="color: green;">دائم</span>')
        
        status = 'green'
        if obj.start_at and now < obj.start_at:
            status = 'orange'
        elif obj.end_at and now > obj.end_at:
            status = 'red'
            
        return format_html(
            '<span style="color: {};">{} - {}</span>',
            status,
            obj.start_at.strftime('%Y-%m-%d') if obj.start_at else 'بلا بداية',
            obj.end_at.strftime('%Y-%m-%d') if obj.end_at else 'بلا نهاية'
        )
    validity_period.short_description = 'فترة الصلاحية'
    
    def linked_rules_count(self, obj):
        promotion_count = obj.promotion_rules.count()
        offer_count = obj.offer_rules.count()
        total = promotion_count + offer_count
        
        if total == 0:
            return format_html('<span style="color: gray;">غير مرتبط</span>')
        
        return format_html(
            '<span style="color: blue;">{} قاعدة ({} خصم، {} عرض)</span>',
            total, promotion_count, offer_count
        )
    linked_rules_count.short_description = 'القواعد المرتبطة'
    
    def usage_stats_detail(self, obj):
        used = obj.redemptions.count()
        recent = obj.redemptions.order_by('-redeemed_at')[:5]
        
        html = f'<p><strong>إجمالي الاستخدام:</strong> {used}</p>'
        if obj.usage_limit:
            remaining = max(0, obj.usage_limit - used)
            html += f'<p><strong>المتبقي:</strong> {remaining}</p>'
        
        
        if recent:
            html += '<p><strong>آخر 5 استخدامات:</strong></p><ul>'
            for redemption in recent:
                html += f'<li>{redemption.user.email} - {redemption.redeemed_at.strftime("%Y-%m-%d %H:%M")}</li>'
            html += '</ul>'
        
        return format_html(html)
    usage_stats_detail.short_description = 'تفاصيل الاستخدام'
    
    def linked_rules_detail(self, obj):
        html = ''
        
        promotions = obj.promotion_rules.all()
        if promotions:
            html += '<p><strong>الخصومات المرتبطة:</strong></p><ul>'
            for promo in promotions:
                status = '✅' if promo.active else '❌'
                html += f'<li>{status} {promo.name} ({promo.get_promotion_type_display()})</li>'
            html += '</ul>'
        
        offers = obj.offer_rules.all()
        if offers:
            html += '<p><strong>العروض المرتبطة:</strong></p><ul>'
            for offer in offers:
                status = '✅' if offer.active else '❌'
                html += f'<li>{status} {offer.name} ({offer.get_offer_type_display()})</li>'
            html += '</ul>'
        
        return format_html(html) if html else 'لا توجد قواعد مرتبطة'
    linked_rules_detail.short_description = 'تفاصيل القواعد المرتبطة'


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ['name', 'promotion_type', 'value_display', 'active', 'required_coupon', 'priority', 'validity_status']
    list_filter = ['active', 'promotion_type', 'stackable', 'start_at', 'end_at', 'required_coupon']
    search_fields = ['name', 'required_coupon__code']
    filter_horizontal = ['stores', 'categories', 'products', 'variants']
    
    fieldsets = (
        ('المعلومات الأساسية', {
            'fields': ('name', 'active', 'required_coupon')
        }),
        ('إعدادات الخصم', {
            'fields': ('promotion_type', 'value', 'min_purchase_amount')
        }),
        ('التحكم في التطبيق', {
            'fields': ('priority', 'stackable'),
            'classes': ('collapse',)
        }),
        ('فترة الصلاحية', {
            'fields': ('start_at', 'end_at'),
            'classes': ('collapse',)
        }),
        ('نطاق التطبيق', {
            'fields': ('stores', 'categories', 'products', 'variants'),
            'classes': ('collapse',)
        }),
    )
    
    def value_display(self, obj):
        if 'PERCENTAGE' in obj.promotion_type:
            return format_html('<span style="color: blue;">{}%</span>', obj.value)
        else:
            return format_html('<span style="color: green;">{} ر.س</span>', obj.value)
    value_display.short_description = 'القيمة'
    
    def validity_status(self, obj):
        now = timezone.now()
        if not obj.start_at and not obj.end_at:
            return format_html('<span style="color: green;">دائم</span>')
        
        if obj.start_at and now < obj.start_at:
            return format_html('<span style="color: orange;">لم يبدأ</span>')
        elif obj.end_at and now > obj.end_at:
            return format_html('<span style="color: red;">منتهي</span>')
        else:
            return format_html('<span style="color: green;">ساري</span>')
    validity_status.short_description = 'حالة الصلاحية'


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ['name', 'offer_type', 'active', 'required_coupon', 'priority', 'validity_status', 'configuration_summary']
    list_filter = ['active', 'offer_type', 'stackable', 'start_at', 'end_at', 'required_coupon']
    search_fields = ['name', 'required_coupon__code']
    filter_horizontal = ['stores', 'categories', 'products', 'variants']
    
    fieldsets = (
        ('المعلومات الأساسية', {
            'fields': ('name', 'active', 'required_coupon')
        }),
        ('إعدادات العرض', {
            'fields': ('offer_type', 'configuration', 'min_purchase_amount')
        }),
        ('التحكم في التطبيق', {
            'fields': ('priority', 'stackable'),
            'classes': ('collapse',)
        }),
        ('فترة الصلاحية', {
            'fields': ('start_at', 'end_at'),
            'classes': ('collapse',)
        }),
        ('نطاق التطبيق', {
            'fields': ('stores', 'categories', 'products', 'variants'),
            'classes': ('collapse',)
        }),
    )
    
    def configuration_summary(self, obj):
        if not obj.configuration:
            return format_html('<span style="color: gray;">لا توجد إعدادات</span>')
        
        summary = []
        for key, value in obj.configuration.items():
            summary.append(f'{key}: {value}')
        
        return format_html('<small>{}</small>', ', '.join(summary[:3]))
    configuration_summary.short_description = 'ملخص الإعدادات'
    
    def validity_status(self, obj):
        now = timezone.now()
        if not obj.start_at and not obj.end_at:
            return format_html('<span style="color: green;">دائم</span>')
        
        if obj.start_at and now < obj.start_at:
            return format_html('<span style="color: orange;">لم يبدأ</span>')
        elif obj.end_at and now > obj.end_at:
            return format_html('<span style="color: red;">منتهي</span>')
        else:
            return format_html('<span style="color: green;">ساري</span>')
    validity_status.short_description = 'حالة الصلاحية'


@admin.register(CouponRedemption)
class CouponRedemptionAdmin(admin.ModelAdmin):
    list_display = ['coupon', 'user', 'order_link', 'redeemed_at']
    list_filter = ['redeemed_at', 'coupon__code']
    search_fields = ['coupon__code', 'user__email', 'order__id']
    readonly_fields = ['coupon', 'user', 'order', 'redeemed_at']
    
    def order_link(self, obj):
        if obj.order:
            return format_html(
                '<a href="/admin/orders/order/{}/change/">طلب #{}</a>',
                obj.order.id, obj.order.id
            )
        return '-'
    order_link.short_description = 'الطلب'
    
    def has_add_permission(self, request):
        return False  # منع الإضافة اليدوية
    
    def has_change_permission(self, request, obj=None):
        return False  # منع التعديل
