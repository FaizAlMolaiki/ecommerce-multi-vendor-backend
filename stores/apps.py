from django.apps import AppConfig


class StoresConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'stores'
    
    def ready(self):
        """تحميل signals عند بدء التطبيق"""
        import stores.signals  # ✅ تفعيل إشعارات المتاجر
