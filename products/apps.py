from django.apps import AppConfig


class ProductsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'products'
    
    def ready(self):
        """تحميل signals عند بدء التطبيق"""
        import products.signals  # ✅ تفعيل إشعارات المنتجات
