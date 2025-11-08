# هذا السطر يضمن أن التطبيق يتم تحميله دائمًا عند بدء تشغيل جانغو
# حتى يمكن لـ shared_task استخدام هذا التطبيق.
from .celery import app as celery_app

__all__ = ('celery_app',)