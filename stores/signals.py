"""
Django signals for sending notifications on store events
"""
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.db.models import Avg, Count
from .models import Store
from notifications import tasks  # استخدام Celery tasks بدلاً من NotificationService المباشر
from notifications.models import NotificationType, NotificationPriority
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Pre-save signal لحفظ الحالة القديمة (لتجنب N+1 queries)
# ============================================================================

@receiver(pre_save, sender=Store)
def store_pre_save(sender, instance, **kwargs):
    """حفظ الحالة القديمة للمتجر قبل التحديث"""
    if instance.pk:
        try:
            old_store = Store.objects.only('status').get(pk=instance.pk)
            instance._old_status = old_store.status
        except Store.DoesNotExist:
            instance._old_status = None


# ============================================================================
# Post-save signals للإشعارات
# ============================================================================

@receiver(post_save, sender=Store)
def store_created_notification(sender, instance, created, **kwargs):
    """إرسال إشعار عند إضافة متجر جديد"""
    if created:
        try:
            store = instance
            
            # 1. إشعار لصاحب المتجر (مرحباً) - Async via Celery
            tasks.send_custom_notification_async.delay(
                user_id=store.owner.id,
                title='مرحباً بك في منصتنا! 🎉',
                body=f'تم إنشاء متجر {store.name} بنجاح. ابدأ بإضافة منتجاتك الآن!',
                notification_type=NotificationType.STORE,
                priority=NotificationPriority.HIGH,
                content_type_model='stores.store',  # ✅ GenericForeignKey
                object_id=store.id,
                data={
                    'type': 'store',
                    'store_id': str(store.id),
                    'action': 'welcome',
                    'logo_url': store.logo_url or ''
                }
            )
            logger.info(f"Store creation notification task queued for owner, store {store.id}")
        
            # 2. إشعار للمسؤولين (للموافقة) - Async via Celery
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            admin_users = User.objects.filter(is_staff=True, is_active=True).values_list('id', flat=True)
            for admin_id in admin_users:
                tasks.send_custom_notification_async.delay(
                    user_id=admin_id,
                    title='متجر جديد يحتاج موافقة 📋',
                    body=f'{store.name} - بواسطة {store.owner.get_full_name() if hasattr(store.owner, "get_full_name") else store.owner.username}',
                    notification_type=NotificationType.STORE,
                    priority=NotificationPriority.HIGH,
                    content_type_model='stores.store',  # ✅ GenericForeignKey
                    object_id=store.id,
                    data={
                        'type': 'store',
                        'store_id': str(store.id),
                        'action': 'approval_needed'
                    }
                )
            
            logger.info(f"Store approval notifications queued for {len(list(admin_users))} admins, store {store.id}")
            
        except Exception as e:
            logger.error(f"Error queuing store creation notifications: {e}", exc_info=True)


@receiver(post_save, sender=Store)
def store_approved_notification(sender, instance, created, **kwargs):
    """إرسال إشعار عند الموافقة على المتجر - Async"""
    if not created and instance.pk:
        try:
            # استخدام الحالة المحفوظة من pre_save (لتجنب N+1 query)
            old_status = getattr(instance, '_old_status', None)
            
            # إذا تغيرت الحالة من pending إلى approved
            if old_status == 'pending' and instance.status == 'approved':
                # 1. إشعار لصاحب المتجر - Async via Celery
                tasks.send_custom_notification_async.delay(
                    user_id=instance.owner.id,
                    title='تمت الموافقة على متجرك! ✅',
                    body=f'تم تفعيل متجر {instance.name} ويمكن للعملاء الآن الشراء منه',
                    notification_type=NotificationType.STORE,
                    priority=NotificationPriority.HIGH,
                    content_type_model='stores.store',  # ✅ GenericForeignKey
                    object_id=instance.id,
                    data={
                        'type': 'store',
                        'store_id': str(instance.id),
                        'action': 'approved',
                        'logo_url': instance.logo_url or ''
                    }
                )
                logger.info(f"Store approval notification queued for owner, store {instance.id}")
                
                # 2. إشعار لمتابعي المتجر - Async via Celery
                from wishlist.models import UserStoreFavorite
                
                follower_ids = UserStoreFavorite.objects.filter(
                    store=instance
                ).values_list('user_id', flat=True)
                
                for follower_id in follower_ids:
                    tasks.send_custom_notification_async.delay(
                        user_id=follower_id,
                        title=f'{instance.name} متاح الآن! 🎉',
                        body=f'المتجر الذي أضفته للمفضلة أصبح نشطاً ويمكنك التسوق منه',
                        notification_type=NotificationType.STORE,
                        priority=NotificationPriority.NORMAL,
                        content_type_model='stores.store',  # ✅ GenericForeignKey
                        object_id=instance.id,
                        data={
                            'type': 'store',
                            'store_id': str(instance.id),
                            'action': 'store_approved',
                            'logo_url': instance.logo_url or ''
                        }
                    )
                
                logger.info(f"Store approval notifications queued for {len(list(follower_ids))} followers, store {instance.id}")
                
        except Exception as e:
            logger.error(f"Error queuing store approval notifications: {e}", exc_info=True)


@receiver(post_save, sender=Store)
def store_rejected_notification(sender, instance, created, **kwargs):
    """إرسال إشعار عند رفض المتجر - Async"""
    if not created and instance.pk:
        try:
            # استخدام الحالة المحفوظة من pre_save (لتجنب N+1 query)
            old_status = getattr(instance, '_old_status', None)
            
            # إذا تغيرت الحالة إلى rejected
            if old_status != 'rejected' and instance.status == 'rejected':
                tasks.send_custom_notification_async.delay(
                    user_id=instance.owner.id,
                    title='تم رفض متجرك ❌',
                    body=f'عذراً، لم تتم الموافقة على متجر {instance.name}. يرجى مراجعة المتطلبات والمحاولة مرة أخرى.',
                    notification_type=NotificationType.STORE,
                    priority=NotificationPriority.HIGH,
                    content_type_model='stores.store',  # ✅ GenericForeignKey
                    object_id=instance.id,
                    data={
                        'type': 'store',
                        'store_id': str(instance.id),
                        'action': 'rejected'
                    }
                )
                logger.info(f"Store rejection notification queued for owner, store {instance.id}")
                
        except Exception as e:
            logger.error(f"Error queuing store rejection notification: {e}", exc_info=True)


# ===================================================================
# ✅ Signals لتحديث الإحصائيات (Denormalized Fields)
# ===================================================================

@receiver(post_save, sender='products.Product')
@receiver(post_delete, sender='products.Product')
def update_store_product_count(sender, instance, **kwargs):
    """تحديث عدد المنتجات النشطة في المتجر"""
    try:
        store = instance.store
        # حساب عدد المنتجات النشطة فقط
        active_count = store.products.filter(is_active=True).count()
        if store.product_count != active_count:
            store.product_count = active_count
            store.save(update_fields=['product_count'])
            logger.debug(f"Updated product count for store {store.id}: {active_count}")
    except Exception as e:
        logger.error(f"Error updating store product count: {e}", exc_info=True)


@receiver(post_save, sender='reviews.StoreReview')
@receiver(post_delete, sender='reviews.StoreReview')
def update_store_rating_stats(sender, instance, **kwargs):
    """تحديث متوسط التقييم وعدد التقييمات"""
    try:
        store = instance.store
        from reviews.models import StoreReview
        
        # حساب متوسط التقييم وعددها
        stats = StoreReview.objects.filter(store=store).aggregate(
            avg_rating=Avg('rating'),
            count=Count('id')
        )
        
        avg_rating = round(stats['avg_rating'], 1) if stats['avg_rating'] else 0.0
        review_count = stats['count'] or 0
        
        # تحديث فقط إذا تغيرت القيم
        if store.average_rating != avg_rating or store.review_count != review_count:
            store.average_rating = avg_rating
            store.review_count = review_count
            store.save(update_fields=['average_rating', 'review_count'])
            logger.debug(f"Updated rating stats for store {store.id}: {avg_rating} ({review_count} reviews)")
    except Exception as e:
        logger.error(f"Error updating store rating stats: {e}", exc_info=True)


@receiver(post_save, sender='wishlist.UserStoreFavorite')
@receiver(post_delete, sender='wishlist.UserStoreFavorite')
def update_store_favorites_count(sender, instance, **kwargs):
    """تحديث عدد المفضلات"""
    try:
        store = instance.store
        from wishlist.models import UserStoreFavorite
        
        fav_count = UserStoreFavorite.objects.filter(store=store).count()
        
        if store.favorites_count != fav_count:
            store.favorites_count = fav_count
            store.save(update_fields=['favorites_count'])
            logger.debug(f"Updated favorites count for store {store.id}: {fav_count}")
    except Exception as e:
        logger.error(f"Error updating store favorites count: {e}", exc_info=True)
