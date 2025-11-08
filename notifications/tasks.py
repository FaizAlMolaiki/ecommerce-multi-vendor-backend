# notifications/tasks.py

from celery import shared_task
from django.contrib.auth import get_user_model
from .services import NotificationService
from .models import NotificationType, NotificationPriority
from pricing.models import Promotion, Offer # استيراد النماذج من تطبيق التسعير

import logging
logger = logging.getLogger(__name__)

User = get_user_model()


@shared_task(bind=True, max_retries=3)
def send_promotion_notification_task(self, promotion_id):
    """
    مهمة خلفية لإرسال إشعارات الخصم الجديد.
    """
    try:
        promo = Promotion.objects.get(id=promotion_id)
        
        logger.info(f"Executing task for promotion: {promo.name}")
        
        # جلب جميع المستخدمين النشطين (ليسوا staff أو vendors)
        active_users_ids = list(User.objects.filter(
            is_active=True,
            is_staff=False,
            is_vendor=False
        ).values_list('id', flat=True))
        
        if not active_users_ids:
            logger.warning("No active users found to send promotion notifications.")
            return

        # --- نفس منطق بناء الرسالة من الكود الأصلي ---
        if promo.promotion_type == Promotion.PromotionType.CART_PERCENTAGE:
            title = f'🎉 خصم {promo.value}% على جميع مشترياتك!'
            body = f'{promo.name} - وفّر الآن'
        elif promo.promotion_type == Promotion.PromotionType.CART_FIXED_AMOUNT:
            title = f'🎁 خصم {promo.value} ريال على طلبك!'
            body = f'{promo.name} - عرض محدود'
        else:
            title = f'💰 خصم {promo.value}% على منتجات مختارة!'
            body = f'{promo.name} - اكتشف العروض'
            
        data = {
            'type': 'promotion',
            'promotion_id': str(promo.id),
        }

        NotificationService.send_notification_to_users(
            user_ids=active_users_ids,
            title=title,
            body=body,
            notification_type=NotificationType.PROMOTION,
            priority=NotificationPriority.HIGH,
            related_id=promo.id,
            data=data,
            send_fcm=True
        )
        
        logger.info(f"Promotion notification successfully sent to {len(active_users_ids)} users.")

    except Promotion.DoesNotExist:
        logger.warning(f"Promotion with ID {promotion_id} does not exist. Task will not run.")
    except Exception as e:
        logger.error(f"Error in send_promotion_notification_task: {e}", exc_info=True)
        # إعادة محاولة المهمة في حالة حدوث خطأ غير متوقع
        raise self.retry(exc=e, countdown=60)


@shared_task(bind=True, max_retries=3)
def send_offer_notification_task(self, offer_id):
    """
    مهمة خلفية لإرسال إشعارات العرض الجديد.
    """
    try:
        offer = Offer.objects.get(id=offer_id)

        logger.info(f"Executing task for offer: {offer.name}")

        active_users_ids = list(User.objects.filter(
            is_active=True,
            is_staff=False,
            is_vendor=False
        ).values_list('id', flat=True))
        
        if not active_users_ids:
            logger.warning("No active users found to send offer notifications.")
            return

        # --- نفس منطق بناء الرسالة من الكود الأصلي ---
        if offer.offer_type == Offer.OfferType.BUY_X_GET_Y:
            title = '🛍️ اشتر واحصل على هدية مجاناً!'
            body = f'{offer.name} - عرض خاص'
        elif offer.offer_type == Offer.OfferType.THRESHOLD_FREE_SHIPPING:
            title = '🚚 شحن مجاني!'
            body = f'{offer.name} - وفّر على الشحن'
        else:
            title = '✨ عرض جديد!'
            body = f'{offer.name} - لا تفوته'

        data = {
            'type': 'offer',
            'offer_id': str(offer.id),
        }
        
        NotificationService.send_notification_to_users(
            user_ids=active_users_ids,
            title=title,
            body=body,
            notification_type=NotificationType.PROMOTION,
            priority=NotificationPriority.HIGH,
            related_id=offer.id,
            data=data,
            send_fcm=True
        )

        logger.info(f"Offer notification successfully sent to {len(active_users_ids)} users.")

    except Offer.DoesNotExist:
        logger.warning(f"Offer with ID {offer_id} does not exist. Task will not run.")
    except Exception as e:
        logger.error(f"Error in send_offer_notification_task: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=60)