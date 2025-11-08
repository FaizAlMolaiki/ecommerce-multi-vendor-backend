from django.apps import AppConfig


class PricingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pricing'
    verbose_name = 'نظام التسعير والخصومات'  # NEW: اسم عربي للإدارة
    
    # NEW: تفعيل الـ signals عند بدء التطبيق
    def ready(self):
        """تفعيل إشارات التطبيق عند البدء"""
        try:
            import pricing.signals  # استيراد ملف الإشارات
        except ImportError:
            pass
