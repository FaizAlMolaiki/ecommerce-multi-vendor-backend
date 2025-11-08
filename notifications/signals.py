from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .services import NotificationService
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

# إشارات الطلبات
try:
    from orders.models import Order
    
    @receiver(post_save, sender=Order)
    def send_order_notification(sender, instance, created, **kwargs):
        """إرسال إشعار عند إنشاء طلب جديد"""
        if created:
            try:
                NotificationService.send_order_notification(instance.user, instance)
                logger.info(f"Order notification sent for order {instance.id}")
            except Exception as e:
                logger.error(f"Failed to send order notification: {e}")
    
    @receiver(pre_save, sender=Order)
    def send_order_status_notification(sender, instance, **kwargs):
        """إرسال إشعار عند تغيير حالة الطلب (الدفع/التنفيذ)"""
        if instance.pk:  # التأكد من أن الطلب موجود مسبقاً
            try:
                old_instance = Order.objects.get(pk=instance.pk)

                # إشعار عند تغيير حالة الدفع
                try:
                    if getattr(old_instance, 'payment_status', None) != getattr(instance, 'payment_status', None):
                        NotificationService.send_order_status_notification(
                            instance.user, instance, getattr(instance, 'payment_status', None)
                        )
                        logger.info(f"Payment status notification sent for order {instance.id}")
                except Exception as e:
                    logger.error(f"Failed to send payment status notification: {e}")

                # إشعار عند تغيير حالة التنفيذ/التجهيز
                try:
                    if getattr(old_instance, 'fulfillment_status', None) != getattr(instance, 'fulfillment_status', None):
                        NotificationService.send_order_status_notification(
                            instance.user, instance, getattr(instance, 'fulfillment_status', None)
                        )
                        logger.info(f"Fulfillment status notification sent for order {instance.id}")
                except Exception as e:
                    logger.error(f"Failed to send fulfillment status notification: {e}")

            except Order.DoesNotExist:
                pass
            except Exception as e:
                logger.error(f"Failed to send order status notification: {e}")

except ImportError:
    logger.warning("Orders app not found, order notifications disabled")

# إشارات المنتجات
try:
    from products.models import Product
    
    @receiver(post_save, sender=Product)
    def send_product_notification(sender, instance, created, **kwargs):
        """إرسال إشعار عند إضافة منتج جديد"""
        if created:
            try:
                # إرسال للمتابعين أو العملاء المهتمين (يمكن تخصيص المنطق)
                # للآن سنرسل لصاحب المتجر فقط كتأكيد
                if hasattr(instance.store, 'owner'):
                    NotificationService.send_product_notification(
                        instance.store.owner, instance
                    )
                    logger.info(f"Product notification sent for product {instance.id}")
            except Exception as e:
                logger.error(f"Failed to send product notification: {e}")

except ImportError:
    logger.warning("Products app not found, product notifications disabled")

# إشارات العروض والخصومات
try:
    from pricing.models import Promotion
    
    @receiver(post_save, sender=Promotion)
    def send_promotion_notification(sender, instance, created, **kwargs):
        """إرسال إشعار عند إنشاء عرض جديد"""
        if created and instance.active:
            try:
                # تحديد المستخدمين المستهدفين حسب نطاق العرض
                target_users = []
                
                if instance.stores.exists():
                    # العرض خاص بمتاجر محددة - إرسال لعملاء هذه المتاجر
                    # يمكن تطوير هذا المنطق لاحقاً
                    pass
                elif instance.categories.exists():
                    # العرض خاص بفئات محددة - إرسال للمهتمين بهذه الفئات
                    # يمكن تطوير هذا المنطق لاحقاً
                    pass
                else:
                    # عرض عام - إرسال لجميع المستخدمين النشطين
                    target_users = User.objects.filter(is_active=True)[:100]  # حد أقصى 100 مستخدم
                
                if target_users:
                    NotificationService.send_promotion_notification(target_users, instance)
                    logger.info(f"Promotion notification sent for promotion {instance.id}")
                    
            except Exception as e:
                logger.error(f"Failed to send promotion notification: {e}")

except ImportError:
    logger.warning("Pricing app not found, promotion notifications disabled")

# إشارات المستخدمين
@receiver(post_save, sender=User)
def send_welcome_notification(sender, instance, created, **kwargs):
    """إرسال إشعار ترحيب للمستخدمين الجدد"""
    if created:
        try:
            NotificationService.send_notification_to_user(
                user=instance,
                title='مرحباً بك!',
                body=f'أهلاً وسهلاً بك {instance.get_full_name()} في منصتنا. نتمنى لك تجربة رائعة!',
                notification_type='system',
                priority='normal',
                send_fcm=False  # لا نرسل FCM للمستخدمين الجدد لأنهم لم يسجلوا أجهزتهم بعد
            )
            logger.info(f"Welcome notification sent to user {instance.email}")
        except Exception as e:
            logger.error(f"Failed to send welcome notification: {e}")

# إشارات المتاجر
try:
    from stores.models import Store
    
    @receiver(post_save, sender=Store)
    def send_store_notification(sender, instance, created, **kwargs):
        """إرسال إشعار عند إنشاء متجر جديد"""
        if created:
            try:
                # إشعار لصاحب المتجر
                if hasattr(instance, 'owner') and instance.owner:
                    NotificationService.send_notification_to_user(
                        user=instance.owner,
                        title='تم إنشاء متجرك بنجاح!',
                        body=f'تم إنشاء متجر "{instance.name}" بنجاح. يمكنك الآن البدء في إضافة المنتجات.',
                        notification_type='store',
                        priority='high',
                        related_id=instance.id,
                        data={'store_id': str(instance.id)}
                    )
                    logger.info(f"Store creation notification sent for store {instance.id}")
                    
                # إشعار للمشرفين (اختياري)
                admin_users = User.objects.filter(is_staff=True, is_active=True)
                if admin_users.exists():
                    NotificationService.send_notification_to_users(
                        user_ids=[user.id for user in admin_users],
                        title='متجر جديد',
                        body=f'تم إنشاء متجر جديد: {instance.name}',
                        notification_type='system',
                        priority='normal',
                        related_id=instance.id,
                        data={'store_id': str(instance.id)},
                        send_fcm=False
                    )
                    
            except Exception as e:
                logger.error(f"Failed to send store notification: {e}")

except ImportError:
    logger.warning("Stores app not found, store notifications disabled")

# إشارات التقييمات
try:
    from reviews.models import ProductReview, StoreReview
    
    @receiver(post_save, sender=ProductReview)
    def send_product_review_notification(sender, instance, created, **kwargs):
        """إرسال إشعار عند إضافة تقييم منتج جديد"""
        if created:
            try:
                # إشعار لصاحب المتجر
                if instance.product and hasattr(instance.product.store, 'owner'):
                    target_user = instance.product.store.owner
                    NotificationService.send_notification_to_user(
                        user=target_user,
                        title='تقييم جديد لمنتجك',
                        body=f'تم إضافة تقييم جديد ({instance.rating}★) لمنتج {instance.product.name}',
                        notification_type='review',
                        priority='normal',
                        related_id=instance.id,
                        data={
                            'review_id': str(instance.id),
                            'rating': str(instance.rating),
                            'product_id': str(instance.product.id)
                        }
                    )
                    logger.info(f"Product review notification sent for review {instance.id}")
            except Exception as e:
                logger.error(f"Failed to send product review notification: {e}")
    
    @receiver(post_save, sender=StoreReview)
    def send_store_review_notification(sender, instance, created, **kwargs):
        """إرسال إشعار عند إضافة تقييم متجر جديد"""
        if created:
            try:
                # إشعار لصاحب المتجر
                if instance.store and hasattr(instance.store, 'owner'):
                    target_user = instance.store.owner
                    NotificationService.send_notification_to_user(
                        user=target_user,
                        title='تقييم جديد لمتجرك',
                        body=f'تم إضافة تقييم جديد ({instance.rating}★) لمتجر {instance.store.name}',
                        notification_type='review',
                        priority='normal',
                        related_id=instance.id,
                        data={
                            'review_id': str(instance.id),
                            'rating': str(instance.rating),
                            'store_id': str(instance.store.id)
                        }
                    )
                    logger.info(f"Store review notification sent for review {instance.id}")
            except Exception as e:
                logger.error(f"Failed to send store review notification: {e}")

except ImportError:
    logger.warning("Reviews app not found, review notifications disabled")
