from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from notifications.services import NotificationService
from notifications.models import NotificationType, NotificationPriority

User = get_user_model()


class Command(BaseCommand):
    help = 'إرسال إشعار تجريبي لاختبار النظام'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-email',
            type=str,
            help='البريد الإلكتروني للمستخدم المستهدف'
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='معرف المستخدم المستهدف'
        )
        parser.add_argument(
            '--all-users',
            action='store_true',
            help='إرسال لجميع المستخدمين النشطين'
        )
        parser.add_argument(
            '--title',
            type=str,
            default='إشعار تجريبي',
            help='عنوان الإشعار'
        )
        parser.add_argument(
            '--body',
            type=str,
            default='هذا إشعار تجريبي لاختبار النظام',
            help='محتوى الإشعار'
        )
        parser.add_argument(
            '--type',
            type=str,
            choices=[choice[0] for choice in NotificationType.choices],
            default='system',
            help='نوع الإشعار'
        )
        parser.add_argument(
            '--priority',
            type=str,
            choices=[choice[0] for choice in NotificationPriority.choices],
            default='normal',
            help='أولوية الإشعار'
        )

    def handle(self, *args, **options):
        title = options['title']
        body = options['body']
        notification_type = options['type']
        priority = options['priority']

        self.stdout.write(
            self.style.SUCCESS('بدء إرسال الإشعار التجريبي...')
        )

        if options['all_users']:
            # إرسال لجميع المستخدمين النشطين
            users = User.objects.filter(is_active=True)[:10]  # حد أقصى 10 مستخدمين للاختبار
            
            if not users.exists():
                self.stdout.write(
                    self.style.ERROR('لا يوجد مستخدمين نشطين في النظام')
                )
                return
            
            user_ids = [user.id for user in users]
            notifications = NotificationService.send_notification_to_users(
                user_ids=user_ids,
                title=title,
                body=body,
                notification_type=notification_type,
                priority=priority,
                send_fcm=False  # تعطيل FCM للاختبار
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'تم إرسال {len(notifications)} إشعار لـ {len(users)} مستخدم')
            )
            
        elif options['user_email']:
            # إرسال لمستخدم محدد بالبريد الإلكتروني
            try:
                user = User.objects.get(email=options['user_email'])
                notification = NotificationService.send_notification_to_user(
                    user=user,
                    title=title,
                    body=body,
                    notification_type=notification_type,
                    priority=priority,
                    send_fcm=False  # تعطيل FCM للاختبار
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f'تم إرسال إشعار للمستخدم: {user.email}')
                )
                
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'المستخدم غير موجود: {options["user_email"]}')
                )
                
        elif options['user_id']:
            # إرسال لمستخدم محدد بالمعرف
            try:
                user = User.objects.get(id=options['user_id'])
                notification = NotificationService.send_notification_to_user(
                    user=user,
                    title=title,
                    body=body,
                    notification_type=notification_type,
                    priority=priority,
                    send_fcm=False  # تعطيل FCM للاختبار
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f'تم إرسال إشعار للمستخدم: {user.email}')
                )
                
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'المستخدم غير موجود: {options["user_id"]}')
                )
                
        else:
            # إرسال لأول مستخدم نشط
            user = User.objects.filter(is_active=True).first()
            
            if not user:
                self.stdout.write(
                    self.style.ERROR('لا يوجد مستخدمين نشطين في النظام')
                )
                return
            
            notification = NotificationService.send_notification_to_user(
                user=user,
                title=title,
                body=body,
                notification_type=notification_type,
                priority=priority,
                send_fcm=False  # تعطيل FCM للاختبار
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'تم إرسال إشعار للمستخدم: {user.email}')
            )

        self.stdout.write(
            self.style.SUCCESS('تم الانتهاء من إرسال الإشعار التجريبي')
        )
