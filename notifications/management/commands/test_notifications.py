"""
أمر Django لاختبار نظام الإشعارات
الاستخدام: python manage.py test_notifications
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from notifications.services import NotificationService
from notifications.email_service import EmailNotificationService
from notifications.models import NotificationType, NotificationPriority
from orders.models import Order

User = get_user_model()


class Command(BaseCommand):
    help = 'اختبار نظام الإشعارات (FCM + Email + Database)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='البريد الإلكتروني للمستخدم المستهدف'
        )
        parser.add_argument(
            '--channel',
            type=str,
            choices=['all', 'fcm', 'email', 'database'],
            default='all',
            help='القناة المراد اختبارها'
        )

    def handle(self, *args, **options):
        email = options.get('email')
        channel = options.get('channel')
        
        # جلب المستخدم
        if email:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'❌ المستخدم {email} غير موجود'))
                return
        else:
            user = User.objects.first()
            if not user:
                self.stdout.write(self.style.ERROR('❌ لا يوجد مستخدمين في النظام'))
                return
        
        self.stdout.write(self.style.SUCCESS(f'\n🎯 اختبار الإشعارات للمستخدم: {user.email}\n'))
        
        # اختبار قاعدة البيانات
        if channel in ['all', 'database']:
            self.test_database_notification(user)
        
        # اختبار FCM
        if channel in ['all', 'fcm']:
            self.test_fcm_notification(user)
        
        # اختبار البريد الإلكتروني
        if channel in ['all', 'email']:
            self.test_email_notification(user)
        
        self.stdout.write(self.style.SUCCESS('\n✅ انتهى الاختبار!\n'))
    
    def test_database_notification(self, user):
        """اختبار إشعار قاعدة البيانات"""
        self.stdout.write(self.style.WARNING('📊 اختبار: Database Notification'))
        
        notification = NotificationService.send_notification_to_user(
            user=user,
            title='اختبار إشعار قاعدة البيانات',
            body='هذا إشعار تجريبي محفوظ في قاعدة البيانات',
            notification_type=NotificationType.SYSTEM,
            priority=NotificationPriority.NORMAL,
            send_fcm=False,
            send_email=False
        )
        
        self.stdout.write(self.style.SUCCESS(f'   ✅ تم إنشاء الإشعار #{notification.id}'))
        self.stdout.write(f'   📝 العنوان: {notification.title}')
        self.stdout.write(f'   📅 التاريخ: {notification.created_at}\n')
    
    def test_fcm_notification(self, user):
        """اختبار إشعار Firebase"""
        self.stdout.write(self.style.WARNING('🔥 اختبار: Firebase Cloud Messaging'))
        
        from notifications.firebase_config import is_fcm_enabled
        
        if not is_fcm_enabled():
            self.stdout.write(self.style.ERROR('   ⚠️ FCM غير مُفعّل في الإعدادات'))
            self.stdout.write('   💡 فعّله من settings.py: ENABLE_FCM = True\n')
            return
        
        notification = NotificationService.send_notification_to_user(
            user=user,
            title='اختبار Firebase 🔥',
            body='إشعار تجريبي عبر Firebase Cloud Messaging',
            notification_type=NotificationType.SYSTEM,
            priority=NotificationPriority.HIGH,
            send_fcm=True,
            send_email=False,
            data={
                'test': 'true',
                'channel': 'fcm'
            }
        )
        
        self.stdout.write(self.style.SUCCESS('   ✅ تم إرسال إشعار FCM'))
        self.stdout.write('   📱 تحقق من تطبيق الموبايل\n')
    
    def test_email_notification(self, user):
        """اختبار إشعار البريد الإلكتروني"""
        self.stdout.write(self.style.WARNING('📧 اختبار: Email Notification'))
        
        # إرسال رسالة ترحيب
        result = EmailNotificationService.send_welcome_email(user)
        
        if result:
            self.stdout.write(self.style.SUCCESS(f'   ✅ تم إرسال بريد إلكتروني إلى: {user.email}'))
            self.stdout.write('   📬 تحقق من صندوق البريد الوارد')
            self.stdout.write('   💡 قد يستغرق دقيقة أو دقيقتين\n')
        else:
            self.stdout.write(self.style.ERROR('   ❌ فشل إرسال البريد الإلكتروني'))
            self.stdout.write('   💡 تحقق من إعدادات SMTP في settings.py\n')
        
        # اختبار إشعار طلب إذا كان موجود
        order = Order.objects.filter(user=user).first()
        if order:
            self.stdout.write('   📦 اختبار إشعار طلب موجود...')
            EmailNotificationService.send_order_notification_email(user, order)
            self.stdout.write(self.style.SUCCESS(f'   ✅ تم إرسال إشعار الطلب #{order.id}\n'))
