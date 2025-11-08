from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "notifications"
    verbose_name = 'نظام الإشعارات'
    
    def ready(self):
        """تحميل الإشارات عند بدء التطبيق"""
        import notifications.signals
