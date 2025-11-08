from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from notifications.services import NotificationService
from notifications.models import Notification, FCMDevice
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'تنظيف الإشعارات القديمة والأجهزة غير النشطة'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='عدد الأيام للاحتفاظ بالإشعارات المقروءة (افتراضي: 30)'
        )
        parser.add_argument(
            '--inactive-devices-days',
            type=int,
            default=90,
            help='عدد الأيام لحذف الأجهزة غير النشطة (افتراضي: 90)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='عرض ما سيتم حذفه بدون تنفيذ الحذف فعلياً'
        )

    def handle(self, *args, **options):
        days = options['days']
        inactive_days = options['inactive_devices_days']
        dry_run = options['dry_run']

        self.stdout.write(
            self.style.SUCCESS(f'بدء تنظيف الإشعارات (dry_run={dry_run})')
        )

        # تنظيف الإشعارات القديمة المقروءة
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        old_notifications = Notification.objects.filter(
            created_at__lt=cutoff_date,
            is_read=True
        )
        
        old_count = old_notifications.count()
        self.stdout.write(f'الإشعارات المقروءة القديمة: {old_count}')
        
        if not dry_run and old_count > 0:
            deleted_count = old_notifications.delete()[0]
            self.stdout.write(
                self.style.SUCCESS(f'تم حذف {deleted_count} إشعار قديم')
            )
            logger.info(f"Deleted {deleted_count} old read notifications")

        # تنظيف الأجهزة غير النشطة
        inactive_cutoff = timezone.now() - timezone.timedelta(days=inactive_days)
        inactive_devices = FCMDevice.objects.filter(
            last_used_at__lt=inactive_cutoff,
            is_active=False
        )
        
        inactive_count = inactive_devices.count()
        self.stdout.write(f'الأجهزة غير النشطة: {inactive_count}')
        
        if not dry_run and inactive_count > 0:
            deleted_devices = inactive_devices.delete()[0]
            self.stdout.write(
                self.style.SUCCESS(f'تم حذف {deleted_devices} جهاز غير نشط')
            )
            logger.info(f"Deleted {deleted_devices} inactive devices")

        # إحصائيات عامة
        total_notifications = Notification.objects.count()
        total_devices = FCMDevice.objects.count()
        active_devices = FCMDevice.objects.filter(is_active=True).count()
        
        self.stdout.write('\n--- إحصائيات عامة ---')
        self.stdout.write(f'إجمالي الإشعارات: {total_notifications}')
        self.stdout.write(f'إجمالي الأجهزة: {total_devices}')
        self.stdout.write(f'الأجهزة النشطة: {active_devices}')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('تم تشغيل الأمر في وضع المعاينة - لم يتم حذف أي شيء')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('تم الانتهاء من تنظيف الإشعارات')
            )
