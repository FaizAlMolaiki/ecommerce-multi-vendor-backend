import os
from celery import Celery

# قم بتعيين متغير بيئة إعدادات جانغو الافتراضي لبرنامج 'celery'.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

# أنشئ نسخة من التطبيق وقم بتسميتها 'project'
app = Celery('project')

# باستخدام سلسلة نصية هنا يعني أن العامل لن يضطر إلى
# عمل serialization لكائن الإعدادات عند إرساله عبر الشبكة.
# namespace='CELERY' يعني أن جميع إعدادات Celery يجب أن تبدأ بـ CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# قم بتحميل وحدات المهام تلقائيًا من جميع تطبيقات جانغو المسجلة.
app.autodiscover_tasks()