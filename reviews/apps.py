from django.apps import AppConfig


class ReviewsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reviews'
    
    def ready(self):
        """
        ✅ تحميل الـ Signals تلقائياً عند بدء التطبيق
        يضمن تفعيل التحديث التلقائي لتقييمات المنتجات والمتاجر
        """
        import reviews.signals
