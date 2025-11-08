"""
إشارات نظام التسعير
--------------------
تم تعديل هذا الملف لضمان الأداء العالي والأمان:
- يتم إرسال الإشعارات بشكل غير متزامن (Asynchronous) في الخلفية باستخدام مهام Celery.
- يتم جدولة المهام فقط بعد نجاح عملية الحفظ في قاعدة البيانات (transaction.on_commit).
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from .models import Promotion, Offer, Coupon

import logging
logger = logging.getLogger(__name__)


@receiver(post_save, sender=Promotion)
def promotion_post_save_receiver(sender, instance, created, **kwargs):
    """
    إشارة عند إضافة خصم جديد.
    تقوم بجدولة مهمة في الخلفية لإرسال إشعارات للمستخدمين.
    """
    # فقط عند الإنشاء وإذا كان الخصم نشط ومعتمد
    if not created or not instance.active or instance.approval_status != 'APPROVED':
        return
    
    try:
        # استيراد المهمة الخلفية
        from notifications.tasks import send_promotion_notification_task
        
        # جدولة المهمة لتنفذ فقط بعد نجاح الحفظ في قاعدة البيانات
        transaction.on_commit(
            lambda: send_promotion_notification_task.delay(instance.id)
        )
        
        logger.info(f"Task scheduled to notify users about new promotion ID: {instance.id}")
    
    except ImportError:
        logger.error("Could not import 'send_promotion_notification_task'. Is Celery configured correctly?")
    except Exception as e:
        logger.error(f"Error scheduling promotion notification task: {e}", exc_info=True)


@receiver(post_save, sender=Offer)
def offer_post_save_receiver(sender, instance, created, **kwargs):
    """
    إشارة عند إضافة عرض جديد.
    تقوم بجدولة مهمة في الخلفية لإرسال إشعارات للمستخدمين.
    """
    # فقط عند الإنشاء وإذا كان العرض نشط ومعتمد
    if not created or not instance.active or instance.approval_status != 'APPROVED':
        return
        
    try:
        # استيراد المهمة الخلفية
        from notifications.tasks import send_offer_notification_task

        # جدولة المهمة لتنفذ فقط بعد نجاح الحفظ في قاعدة البيانات
        transaction.on_commit(
            lambda: send_offer_notification_task.delay(instance.id)
        )
        
        logger.info(f"Task scheduled to notify users about new offer ID: {instance.id}")

    except ImportError:
        logger.error("Could not import 'send_offer_notification_task'. Is Celery configured correctly?")
    except Exception as e:
        logger.error(f"Error scheduling offer notification task: {e}", exc_info=True)


@receiver(post_save, sender=Coupon)
def log_new_coupon(sender, instance, created, **kwargs):
    """
    تسجيل إضافة كوبون جديد (بدون إشعارات).
    هذه العملية سريعة ولا تحتاج إلى مهمة خلفية.
    """
    if created and instance.active:
        logger.info(f"New coupon created: {instance.code}")
        # الكوبونات لا تُرسل إشعارات تلقائية


# ✅ ===================== NEW: Approval Signals =====================
@receiver(post_save, sender=Promotion)
def promotion_approval_notification(sender, instance, created, update_fields, **kwargs):
    """
    إرسال إشعارات عند الموافقة على عرض ترويجي.
    يتم إرسال الإشعار فقط عند تغيير حالة الموافقة إلى APPROVED.
    """
    # تجاهل العروض المُنشأة حديثاً (يتم التعامل معها في signal آخر)
    if created:
        return
    
    # التحقق من أن حالة الموافقة تغيرت إلى APPROVED
    if update_fields and 'approval_status' in update_fields:
        if instance.approval_status == 'APPROVED' and instance.active:
            try:
                from notifications.tasks import send_promotion_notification_task
                transaction.on_commit(
                    lambda: send_promotion_notification_task.delay(instance.id)
                )
                logger.info(f"Approval notification scheduled for promotion ID: {instance.id}")
            except ImportError:
                logger.error("Could not import 'send_promotion_notification_task'.")
            except Exception as e:
                logger.error(f"Error scheduling approval notification: {e}", exc_info=True)


@receiver(post_save, sender=Offer)
def offer_approval_notification(sender, instance, created, update_fields, **kwargs):
    """
    إرسال إشعارات عند الموافقة على عرض خاص.
    يتم إرسال الإشعار فقط عند تغيير حالة الموافقة إلى APPROVED.
    """
    # تجاهل العروض المُنشأة حديثاً
    if created:
        return
    
    # التحقق من أن حالة الموافقة تغيرت إلى APPROVED
    if update_fields and 'approval_status' in update_fields:
        if instance.approval_status == 'APPROVED' and instance.active:
            try:
                from notifications.tasks import send_offer_notification_task
                transaction.on_commit(
                    lambda: send_offer_notification_task.delay(instance.id)
                )
                logger.info(f"Approval notification scheduled for offer ID: {instance.id}")
            except ImportError:
                logger.error("Could not import 'send_offer_notification_task'.")
            except Exception as e:
                logger.error(f"Error scheduling approval notification: {e}", exc_info=True)
# ====================================================================