# notifications/tasks.py

from celery import shared_task
from django.contrib.auth import get_user_model
from .services import NotificationService
from .models import NotificationType, NotificationPriority

import logging
logger = logging.getLogger(__name__)

User = get_user_model()


# ============================================================================
# Tasks للـ Signals - تحويل المعالجة المتزامنة إلى غير متزامنة
# ============================================================================
# هذه المهام تُستدعى من signals.py بدلاً من الاستدعاء المباشر
# الفائدة: API response سريع + معالجة في الخلفية
# ============================================================================


@shared_task(bind=True, max_retries=3)
def send_promotion_notification_task(self, promotion_id):
    """
    مهمة خلفية لإرسال إشعارات الخصم الجديد.
    """
    try:
        from pricing.models import Promotion
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
            content_object=promo,  # ✅ GenericForeignKey
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
        from pricing.models import Offer
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
            content_object=offer,  # ✅ GenericForeignKey
            data=data,
            send_fcm=True
        )

        logger.info(f"Offer notification successfully sent to {len(active_users_ids)} users.")

    except Offer.DoesNotExist:
        logger.warning(f"Offer with ID {offer_id} does not exist. Task will not run.")
    except Exception as e:
        logger.error(f"Error in send_offer_notification_task: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=60)


# ============================================================================
# Tasks للـ Signals الجديدة
# ============================================================================

@shared_task(bind=True, max_retries=3)
def send_order_notification_async(self, user_id, order_id):
    """مهمة خلفية لإرسال إشعار طلب جديد"""
    try:
        from orders.models import Order
        
        user = User.objects.get(id=user_id)
        order = Order.objects.get(id=order_id)
        
        NotificationService.send_order_notification(user, order)
        logger.info(f"Order notification sent for order {order_id}")
        
    except (User.DoesNotExist, Order.DoesNotExist) as e:
        logger.warning(f"User or Order not found: {e}")
    except Exception as e:
        logger.error(f"Error in send_order_notification_async: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=60)


@shared_task(bind=True, max_retries=3)
def send_order_status_notification_async(self, user_id, order_id, status):
    """مهمة خلفية لإرسال إشعار تغيير حالة الطلب"""
    try:
        from orders.models import Order
        
        user = User.objects.get(id=user_id)
        order = Order.objects.get(id=order_id)
        
        NotificationService.send_order_status_notification(user, order, status)
        logger.info(f"Order status notification sent for order {order_id}, status: {status}")
        
    except (User.DoesNotExist, Order.DoesNotExist) as e:
        logger.warning(f"User or Order not found: {e}")
    except Exception as e:
        logger.error(f"Error in send_order_status_notification_async: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=60)


@shared_task(bind=True, max_retries=3)
def send_product_notification_async(self, user_id, product_id):
    """مهمة خلفية لإرسال إشعار منتج جديد"""
    try:
        from products.models import Product
        
        user = User.objects.get(id=user_id)
        product = Product.objects.get(id=product_id)
        
        NotificationService.send_product_notification(user, product)
        logger.info(f"Product notification sent for product {product_id}")
        
    except (User.DoesNotExist, Product.DoesNotExist) as e:
        logger.warning(f"User or Product not found: {e}")
    except Exception as e:
        logger.error(f"Error in send_product_notification_async: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=60)


@shared_task(bind=True, max_retries=3)
def send_welcome_notification_async(self, user_id, user_full_name):
    """مهمة خلفية لإرسال إشعار ترحيب"""
    try:
        user = User.objects.get(id=user_id)
        
        NotificationService.send_notification_to_user(
            user=user,
            title='مرحباً بك!',
            body=f'أهلاً وسهلاً بك {user_full_name} في منصتنا. نتمنى لك تجربة رائعة!',
            notification_type='system',
            priority='normal',
            send_fcm=False
        )
        logger.info(f"Welcome notification sent to user {user_id}")
        
    except User.DoesNotExist:
        logger.warning(f"User {user_id} not found")
    except Exception as e:
        logger.error(f"Error in send_welcome_notification_async: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=60)


@shared_task(bind=True, max_retries=3)
def send_store_notification_async(self, owner_id, store_id, store_name):
    """مهمة خلفية لإرسال إشعار متجر جديد"""
    try:
        from stores.models import Store
        
        owner = User.objects.get(id=owner_id)
        store = Store.objects.get(id=store_id)
        
        NotificationService.send_notification_to_user(
            user=owner,
            title='تم إنشاء متجرك بنجاح!',
            body=f'تم إنشاء متجر "{store_name}" بنجاح. يمكنك الآن البدء في إضافة المنتجات.',
            notification_type='store',
            priority='high',
            content_object=store,  # ✅ GenericForeignKey
            data={'store_id': str(store_id)}
        )
        logger.info(f"Store notification sent for store {store_id}")
        
    except User.DoesNotExist:
        logger.warning(f"Store owner {owner_id} not found")
    except Exception as e:
        logger.error(f"Error in send_store_notification_async: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=60)


@shared_task(bind=True, max_retries=3)
def send_review_notification_async(self, user_id, review_type, review_id, rating, item_name):
    """مهمة خلفية لإرسال إشعار تقييم جديد"""
    try:
        user = User.objects.get(id=user_id)
        
        # الحصول على review object
        review_object = None
        if review_type == 'product':
            from reviews.models import ProductReview
            title = 'تقييم جديد لمنتجك'
            body = f'تم إضافة تقييم جديد ({rating}★) لمنتج {item_name}'
            try:
                review_object = ProductReview.objects.get(id=review_id)
            except ProductReview.DoesNotExist:
                logger.warning(f"ProductReview {review_id} not found")
        else:  # store
            from reviews.models import StoreReview
            title = 'تقييم جديد لمتجرك'
            body = f'تم إضافة تقييم جديد ({rating}★) لمتجر {item_name}'
            try:
                review_object = StoreReview.objects.get(id=review_id)
            except StoreReview.DoesNotExist:
                logger.warning(f"StoreReview {review_id} not found")
        
        NotificationService.send_notification_to_user(
            user=user,
            title=title,
            body=body,
            notification_type='review',
            priority='normal',
            content_object=review_object,  # ✅ GenericForeignKey
            data={
                'review_id': str(review_id),
                'rating': str(rating),
                'type': review_type
            }
        )
        logger.info(f"Review notification sent for {review_type} review {review_id}")
        
    except User.DoesNotExist:
        logger.warning(f"User {user_id} not found")
    except Exception as e:
        logger.error(f"Error in send_review_notification_async: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=60)


# ============================================================================
# مهمة عامة لإرسال إشعارات مخصصة
# ============================================================================

@shared_task(bind=True, max_retries=3)
def send_custom_notification_async(self, user_id, title, body, notification_type, priority, 
                                   content_type_model=None, object_id=None, data=None):
    """
    مهمة خلفية عامة لإرسال أي إشعار مخصص
    تُستخدم من التطبيقات الأخرى (orders, stores, etc.)
    
    Parameters:
        content_type_model: اسم النموذج (مثل: 'products.product', 'orders.order', 'stores.store')
        object_id: معرف الكائن
    """
    try:
        from django.contrib.contenttypes.models import ContentType
        
        user = User.objects.get(id=user_id)
        
        # تحديد content_object للـ GenericForeignKey
        content_object = None
        if content_type_model and object_id:
            try:
                # الحصول على ContentType من اسم النموذج
                app_label, model = content_type_model.split('.')
                ct = ContentType.objects.get(app_label=app_label, model=model.lower())
                model_class = ct.model_class()
                content_object = model_class.objects.get(pk=object_id)
            except Exception as e:
                logger.warning(f"Could not get content_object for {content_type_model}:{object_id}: {e}")
        
        NotificationService.send_notification_to_user(
            user=user,
            title=title,
            body=body,
            notification_type=notification_type,
            priority=priority,
            content_object=content_object,  # ✅ GenericForeignKey فقط
            data=data or {}
        )
        logger.info(f"Custom notification sent to user {user_id}: {title}")
        
    except User.DoesNotExist:
        logger.warning(f"User {user_id} not found for custom notification")
    except Exception as e:
        logger.error(f"Error in send_custom_notification_async: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=60)