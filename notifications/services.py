from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
from .models import Notification, FCMDevice, NotificationTemplate, NotificationType, NotificationPriority
from .email_service import EmailNotificationService
import logging
import json

# إعداد Firebase Admin
try:
    from firebase_admin import messaging
    from .firebase_config import initialize_firebase, is_fcm_enabled
    FIREBASE_AVAILABLE = initialize_firebase()
except ImportError:
    FIREBASE_AVAILABLE = False
    messaging = None
    is_fcm_enabled = lambda: False

logger = logging.getLogger(__name__)
User = get_user_model()


class NotificationService:
    """خدمة إدارة الإشعارات"""
    
    @staticmethod
    def send_notification_to_user(
        user, 
        title, 
        body, 
        notification_type=NotificationType.SYSTEM,
        priority=NotificationPriority.NORMAL,
        data=None, 
        image_url=None, 
        related_id=None,
        send_fcm=True,
        send_email=False
    ):
        """إرسال إشعار لمستخدم محدد"""
        
        # حفظ الإشعار في قاعدة البيانات
        notification = Notification.objects.create(
            user=user,
            title=title,
            body=body,
            type=notification_type,
            priority=priority,
            data=data or {},
            image_url=image_url,
            related_id=related_id
        )
        
        # إرسال إشعار Firebase إذا كان مطلوباً
        if send_fcm and is_fcm_enabled():
            NotificationService._send_fcm_to_user(user, title, body, data, image_url)
        
        # إرسال بريد إلكتروني للإشعارات ذات الأولوية العالية
        if send_email or priority in [NotificationPriority.HIGH, NotificationPriority.URGENT]:
            EmailNotificationService.send_notification_email(
                user=user,
                subject=title,
                message=body,
                priority=priority
            )
            
        logger.info(f"Notification sent to user {user.email}: {title}")
        return notification
    
    @staticmethod
    def send_notification_to_users(
        user_ids, 
        title, 
        body, 
        notification_type=NotificationType.SYSTEM,
        priority=NotificationPriority.NORMAL,
        data=None, 
        image_url=None, 
        related_id=None,
        send_fcm=True
    ):
        """إرسال إشعار لعدة مستخدمين"""
        
        users = User.objects.filter(id__in=user_ids)
        notifications = []
        
        for user in users:
            notifications.append(Notification(
                user=user,
                title=title,
                body=body,
                type=notification_type,
                priority=priority,
                data=data or {},
                image_url=image_url,
                related_id=related_id
            ))
        
        # إنشاء الإشعارات بشكل مجمع
        created_notifications = Notification.objects.bulk_create(notifications)
        
        # إرسال FCM للمستخدمين
        if send_fcm:
            for user in users:
                NotificationService._send_fcm_to_user(user, title, body, data, image_url)
        
        logger.info(f"Notification sent to {len(users)} users: {title}")
        return created_notifications
    
    @staticmethod
    def send_broadcast_notification(
        title, 
        body, 
        notification_type=NotificationType.SYSTEM,
        priority=NotificationPriority.NORMAL,
        data=None, 
        image_url=None,
        user_filter=None,
        send_fcm=True
    ):
        """إرسال إشعار عام لجميع المستخدمين أو مجموعة محددة"""
        
        users_query = User.objects.filter(is_active=True)
        
        # تطبيق فلتر إضافي إذا كان موجوداً
        if user_filter:
            users_query = users_query.filter(user_filter)
        
        users = list(users_query)
        notifications = []
        
        for user in users:
            notifications.append(Notification(
                user=user,
                title=title,
                body=body,
                type=notification_type,
                priority=priority,
                data=data or {},
                image_url=image_url
            ))
        
        # إنشاء الإشعارات بشكل مجمع
        created_notifications = Notification.objects.bulk_create(notifications, batch_size=1000)
        
        # إرسال FCM
        if send_fcm and users:
            NotificationService._send_fcm_broadcast(users, title, body, data, image_url)
        
        logger.info(f"Broadcast notification sent to {len(users)} users: {title}")
        return created_notifications
    
    @staticmethod
    def _send_fcm_to_user(user, title, body, data=None, image_url=None):
        """إرسال إشعار FCM لمستخدم واحد"""
        if not FIREBASE_AVAILABLE:
            logger.warning("Firebase Admin SDK not available")
            return
            
        devices = FCMDevice.objects.filter(user=user, is_active=True)
        if not devices.exists():
            logger.info(f"No active FCM devices for user {user.email}")
            return
            
        tokens = [device.registration_token for device in devices]
        NotificationService._send_fcm_notification(tokens, title, body, data, image_url)
    
    @staticmethod
    def _send_fcm_broadcast(users, title, body, data=None, image_url=None):
        """إرسال إشعار FCM لعدة مستخدمين"""
        if not FIREBASE_AVAILABLE:
            logger.warning("Firebase Admin SDK not available")
            return
            
        # جمع جميع الرموز النشطة
        user_ids = [user.id for user in users]
        devices = FCMDevice.objects.filter(user_id__in=user_ids, is_active=True)
        tokens = [device.registration_token for device in devices]
        
        if tokens:
            # تقسيم الرموز إلى مجموعات (FCM يدعم حتى 1000 رمز في المرة الواحدة)
            batch_size = 1000
            for i in range(0, len(tokens), batch_size):
                batch_tokens = tokens[i:i + batch_size]
                NotificationService._send_fcm_notification(batch_tokens, title, body, data, image_url)
    
    @staticmethod
    def _send_fcm_notification(tokens, title, body, data=None, image_url=None):
        """إرسال إشعار FCM"""
        if not FIREBASE_AVAILABLE or not messaging:
            logger.warning("Firebase messaging not available")
            return
            
        try:
            # إعداد رسالة FCM
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                    image=image_url
                ),
                data={str(k): str(v) for k, v in (data or {}).items()},  # تحويل جميع القيم إلى strings
                tokens=tokens,
                android=messaging.AndroidConfig(
                    notification=messaging.AndroidNotification(
                        channel_id='high_importance_channel',
                        priority='high',
                        default_sound=True,
                        default_vibrate_timings=True,
                        default_light_settings=True
                    )
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            alert=messaging.ApsAlert(title=title, body=body),
                            sound='default',
                            badge=1
                        )
                    )
                )
            )
            
            # إرسال الرسالة
            response = messaging.send_multicast(message)
            
            logger.info(f'Successfully sent {response.success_count} FCM notifications')
            
            # معالجة الرموز الفاشلة
            if response.failure_count > 0:
                failed_tokens = []
                for idx, resp in enumerate(response.responses):
                    if not resp.success:
                        failed_tokens.append(tokens[idx])
                        logger.error(f'FCM error: {resp.exception}')
                
                # إلغاء تفعيل الرموز الفاشلة
                if failed_tokens:
                    FCMDevice.objects.filter(
                        registration_token__in=failed_tokens
                    ).update(is_active=False)
                    
        except Exception as e:
            logger.error(f'Error sending FCM notification: {e}')
    
    @staticmethod
    def send_order_notification(user, order):
        """إرسال إشعار طلب جديد"""
        return NotificationService.send_notification_to_user(
            user=user,
            title='طلب جديد',
            body=f'تم استلام طلبك رقم {order.id} بقيمة {order.grand_total} ريال',
            notification_type=NotificationType.ORDER,
            priority=NotificationPriority.HIGH,
            related_id=order.id,
            data={
                'order_id': str(order.id),
                'grand_total': str(order.grand_total),
                'fulfillment_status': getattr(order, 'fulfillment_status', '')
            }
        )
    
    @staticmethod
    def send_order_status_notification(user, order, new_status):
        """إرسال إشعار تحديث حالة الطلب"""
        status_messages = {
            'pending': 'في انتظار التأكيد',
            'confirmed': 'تم تأكيد الطلب',
            'preparing': 'جاري تحضير الطلب',
            'ready': 'الطلب جاهز للاستلام',
            'picked_up': 'تم استلام الطلب من المتجر',
            'on_the_way': 'الطلب في الطريق إليك',
            'delivered': 'تم توصيل الطلب',
            'cancelled': 'تم إلغاء الطلب'
        }
        
        status_text = status_messages.get(new_status, new_status)
        
        return NotificationService.send_notification_to_user(
            user=user,
            title='تحديث حالة الطلب',
            body=f'طلبك رقم {order.id} أصبح في حالة: {status_text}',
            notification_type=NotificationType.SHIPPING,
            priority=NotificationPriority.HIGH,
            related_id=order.id,
            data={
                'order_id': str(order.id),
                'status': new_status,
                'status_text': status_text
            }
        )
    
    @staticmethod
    def send_product_notification(user, product):
        """إرسال إشعار منتج جديد"""
        return NotificationService.send_notification_to_user(
            user=user,
            title='منتج جديد',
            body=f'تم إضافة منتج جديد: {product.name}',
            notification_type=NotificationType.PRODUCT,
            priority=NotificationPriority.NORMAL,
            related_id=product.id,
            image_url=product.cover_image_url,
            data={
                'product_id': str(product.id),
                'store_id': str(product.store.id)
            }
        )
    
    @staticmethod
    def send_promotion_notification(users, promotion):
        """إرسال إشعار عرض جديد"""
        user_ids = [user.id for user in users] if hasattr(users, '__iter__') else users
        
        return NotificationService.send_notification_to_users(
            user_ids=user_ids,
            title='عرض جديد!',
            body=f'{promotion.title} - خصم {promotion.discount_percentage}%',
            notification_type=NotificationType.PROMOTION,
            priority=NotificationPriority.NORMAL,
            related_id=promotion.id,
            image_url=getattr(promotion, 'image_url', None),
            data={
                'promotion_id': str(promotion.id),
                'discount': str(promotion.discount_percentage)
            }
        )
    
    @staticmethod
    def get_user_notification_stats(user):
        """الحصول على إحصائيات إشعارات المستخدم"""
        notifications = user.notifications.all()
        
        total_count = notifications.count()
        unread_count = notifications.filter(is_read=False).count()
        read_count = total_count - unread_count
        
        # إحصائيات حسب النوع
        by_type = {}
        for choice in NotificationType.choices:
            type_count = notifications.filter(type=choice[0]).count()
            if type_count > 0:
                by_type[choice[0]] = {
                    'count': type_count,
                    'label': choice[1]
                }
        
        # إحصائيات حسب الأولوية
        by_priority = {}
        for choice in NotificationPriority.choices:
            priority_count = notifications.filter(priority=choice[0]).count()
            if priority_count > 0:
                by_priority[choice[0]] = {
                    'count': priority_count,
                    'label': choice[1]
                }
        
        return {
            'total_count': total_count,
            'unread_count': unread_count,
            'read_count': read_count,
            'by_type': by_type,
            'by_priority': by_priority
        }
    
    @staticmethod
    def mark_all_as_read(user):
        """تعليم جميع إشعارات المستخدم كمقروءة"""
        updated_count = user.notifications.filter(is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        
        logger.info(f"Marked {updated_count} notifications as read for user {user.email}")
        return updated_count
    
    @staticmethod
    def cleanup_old_notifications(days=30):
        """حذف الإشعارات القديمة"""
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        deleted_count = Notification.objects.filter(
            created_at__lt=cutoff_date,
            is_read=True
        ).delete()[0]
        
        logger.info(f"Cleaned up {deleted_count} old notifications")
        return deleted_count
    
    @staticmethod
    def send_template_notification(
        template_name_or_id,
        user_ids=None,
        context_data=None,
        send_fcm=True,
        send_email=False
    ):
        """
        إرسال إشعار باستخدام قالب
        
        Args:
            template_name_or_id: اسم القالب أو معرفه
            user_ids: قائمة معرفات المستخدمين (None = إرسال للجميع)
            context_data: البيانات الديناميكية للقالب (مثل {user_name: 'أحمد', order_id: 123})
            send_fcm: إرسال عبر FCM
            send_email: إرسال عبر البريد الإلكتروني
        """
        # الحصول على القالب
        try:
            if isinstance(template_name_or_id, int):
                template = NotificationTemplate.objects.get(id=template_name_or_id, is_active=True)
            else:
                template = NotificationTemplate.objects.get(name=template_name_or_id, is_active=True)
        except NotificationTemplate.DoesNotExist:
            logger.error(f"Template not found: {template_name_or_id}")
            return []
        
        # معالجة البيانات الديناميكية
        context = context_data or {}
        
        # تحديد المستخدمين
        if user_ids:
            users = User.objects.filter(id__in=user_ids, is_active=True)
        else:
            users = User.objects.filter(is_active=True)
        
        # إنشاء الإشعارات
        notifications = []
        for user in users:
            # استبدال المتغيرات الخاصة بالمستخدم
            user_context = context.copy()
            user_context.update({
                'user_name': user.name or user.email,
                'user_email': user.email,
            })
            
            user_title = template.title_template.format(**user_context)
            user_body = template.body_template.format(**user_context)
            
            notifications.append(Notification(
                user=user,
                title=user_title,
                body=user_body,
                type=template.type,
                priority=template.priority,
                data=context
            ))
        
        # حفظ الإشعارات
        created_notifications = Notification.objects.bulk_create(notifications, batch_size=1000)
        
        # إرسال FCM
        if send_fcm:
            for user in users:
                user_context = context.copy()
                user_context.update({
                    'user_name': user.name or user.email,
                    'user_email': user.email,
                })
                user_title = template.title_template.format(**user_context)
                user_body = template.body_template.format(**user_context)
                
                NotificationService._send_fcm_to_user(user, user_title, user_body, context)
        
        # إرسال بريد إلكتروني
        if send_email:
            for user in users:
                user_context = context.copy()
                user_context.update({
                    'user_name': user.name or user.email,
                    'user_email': user.email,
                })
                user_title = template.title_template.format(**user_context)
                user_body = template.body_template.format(**user_context)
                
                EmailNotificationService.send_notification_email(
                    user=user,
                    subject=user_title,
                    message=user_body,
                    priority=template.priority
                )
        
        logger.info(f"Sent {len(created_notifications)} notifications using template '{template.name}'")
        return created_notifications
