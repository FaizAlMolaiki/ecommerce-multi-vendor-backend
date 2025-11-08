"""
خدمة إرسال الإشعارات عبر البريد الإلكتروني
"""
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)


class EmailNotificationService:
    """خدمة إرسال إشعارات البريد الإلكتروني"""
    
    @staticmethod
    def send_notification_email(
        user,
        subject,
        message,
        html_template=None,
        context=None,
        priority='normal'
    ):
        """
        إرسال إشعار عبر البريد الإلكتروني
        
        Args:
            user: المستخدم المستلم
            subject: عنوان الإيميل
            message: نص الرسالة
            html_template: قالب HTML (اختياري)
            context: بيانات القالب
            priority: أولوية الإرسال
        """
        try:
            # التحقق من تفعيل البريد الإلكتروني
            config = getattr(settings, 'NOTIFICATIONS_CONFIG', {})
            if not config.get('ENABLE_EMAIL_NOTIFICATIONS', False):
                logger.debug("Email notifications are disabled")
                return False
            
            # إعداد البريد الإلكتروني
            recipient_email = user.email
            from_email = settings.DEFAULT_FROM_EMAIL
            
            # إذا كان هناك قالب HTML
            if html_template and context:
                html_content = render_to_string(html_template, context)
                text_content = strip_tags(html_content)
                
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=text_content,
                    from_email=from_email,
                    to=[recipient_email]
                )
                email.attach_alternative(html_content, "text/html")
                email.send(fail_silently=False)
            else:
                # إرسال نص بسيط
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=from_email,
                    recipient_list=[recipient_email],
                    fail_silently=False
                )
            
            logger.info(f"Email notification sent to {recipient_email}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
            return False
    
    @staticmethod
    def send_order_notification_email(user, order):
        """إرسال إشعار طلب جديد عبر البريد"""
        subject = f'طلب جديد #{order.id}'
        context = {
            'user': user,
            'order': order,
            'site_name': 'منصتنا',
        }
        
        return EmailNotificationService.send_notification_email(
            user=user,
            subject=subject,
            message=f'تم استلام طلبك رقم {order.id} بنجاح',
            html_template='notifications/email/order_created.html',
            context=context,
            priority='high'
        )
    
    @staticmethod
    def send_order_status_email(user, order, new_status):
        """إرسال إشعار تحديث حالة الطلب"""
        status_messages = {
            'PENDING': 'في انتظار المراجعة',
            'ACCEPTED': 'تم قبول الطلب',
            'PREPARING': 'جاري تحضير الطلب',
            'SHIPPED': 'تم شحن الطلب',
            'DELIVERED': 'تم توصيل الطلب',
            'REJECTED': 'تم رفض الطلب'
        }
        
        status_text = status_messages.get(new_status, new_status)
        subject = f'تحديث الطلب #{order.id}'
        
        context = {
            'user': user,
            'order': order,
            'status_text': status_text,
            'site_name': 'منصتنا',
        }
        
        return EmailNotificationService.send_notification_email(
            user=user,
            subject=subject,
            message=f'طلبك رقم {order.id} أصبح في حالة: {status_text}',
            html_template='notifications/email/order_status_update.html',
            context=context,
            priority='high'
        )
    
    @staticmethod
    def send_welcome_email(user):
        """إرسال رسالة ترحيب"""
        subject = 'مرحباً بك في منصتنا!'
        context = {
            'user': user,
            'site_name': 'منصتنا',
        }
        
        return EmailNotificationService.send_notification_email(
            user=user,
            subject=subject,
            message=f'أهلاً وسهلاً بك {user.get_full_name()}!',
            html_template='notifications/email/welcome.html',
            context=context,
            priority='normal'
        )
