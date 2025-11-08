"""
Django signals for sending notifications on store events
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Avg, Count
from .models import Store
from notifications.services import NotificationService
from notifications.models import NotificationType, NotificationPriority


@receiver(post_save, sender=Store)
def store_created_notification(sender, instance, created, **kwargs):
    """إرسال إشعار عند إضافة متجر جديد"""
    if created:
        store = instance
        
        # 1. إشعار لصاحب المتجر (مرحباً)
        NotificationService.send_notification_to_user(
            user=store.owner,
            title='مرحباً بك في منصتنا! 🎉',
            body=f'تم إنشاء متجر {store.name} بنجاح. ابدأ بإضافة منتجاتك الآن!',
            notification_type=NotificationType.STORE,
            priority=NotificationPriority.HIGH,
            related_id=store.id,
            image_url=store.logo_url,
            data={
                'type': 'store',
                'store_id': str(store.id),
                'related_id': str(store.id),
                'action': 'welcome'
            }
        )
        
        # 2. إشعار للمسؤولين (للموافقة) ✅
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        admin_users = User.objects.filter(is_staff=True, is_active=True)
        if admin_users.exists():
            NotificationService.send_notification_to_users(
                user_ids=[u.id for u in admin_users],
                title='متجر جديد يحتاج موافقة 📋',
                body=f'{store.name} - بواسطة {store.owner.get_full_name() if hasattr(store.owner, "get_full_name") else store.owner.username}',
                notification_type=NotificationType.STORE,
                priority=NotificationPriority.HIGH,
                related_id=store.id,
                data={
                    'type': 'store',
                    'store_id': str(store.id),
                    'related_id': str(store.id),
                    'action': 'approval_needed'
                }
            )


@receiver(post_save, sender=Store)
def store_approved_notification(sender, instance, created, **kwargs):
    """إرسال إشعار عند الموافقة على المتجر"""
    if not created and instance.pk:
        try:
            old_store = Store.objects.get(pk=instance.pk)
            
            # إذا تغيرت الحالة من pending إلى approved
            if old_store.status == 'pending' and instance.status == 'approved':
                # 1. إشعار لصاحب المتجر
                NotificationService.send_notification_to_user(
                    user=instance.owner,
                    title='تمت الموافقة على متجرك! ✅',
                    body=f'تم تفعيل متجر {instance.name} ويمكن للعملاء الآن الشراء منه',
                    notification_type=NotificationType.STORE,
                    priority=NotificationPriority.HIGH,
                    related_id=instance.id,
                    image_url=instance.logo_url,
                    data={
                        'type': 'store',
                        'store_id': str(instance.id),
                        'related_id': str(instance.id),
                        'action': 'approved'
                    }
                )
                
                # 2. إشعار لمتابعي المتجر ✅ (استخدام wishlist)
                from wishlist.models import UserStoreFavorite
                
                followers = UserStoreFavorite.objects.filter(
                    store=instance
                ).select_related('user')
                
                if followers.exists():
                    NotificationService.send_notification_to_users(
                        user_ids=[f.user.id for f in followers],
                        title=f'{instance.name} متاح الآن! 🎉',
                        body=f'المتجر الذي أضفته للمفضلة أصبح نشطاً ويمكنك التسوق منه',
                        notification_type=NotificationType.STORE,
                        priority=NotificationPriority.NORMAL,
                        related_id=instance.id,
                        image_url=instance.logo_url,
                        data={
                            'type': 'store',
                            'store_id': str(instance.id),
                            'related_id': str(instance.id),
                            'action': 'store_approved'
                        }
                    )
                
        except Store.DoesNotExist:
            pass


@receiver(post_save, sender=Store)
def store_rejected_notification(sender, instance, created, **kwargs):
    """إرسال إشعار عند رفض المتجر"""
    if not created and instance.pk:
        try:
            old_store = Store.objects.get(pk=instance.pk)
            
            # إذا تغيرت الحالة إلى rejected
            if old_store.status != 'rejected' and instance.status == 'rejected':
                NotificationService.send_notification_to_user(
                    user=instance.owner,
                    title='تم رفض متجرك ❌',
                    body=f'عذراً، لم تتم الموافقة على متجر {instance.name}. يرجى مراجعة المتطلبات والمحاولة مرة أخرى.',
                    notification_type=NotificationType.STORE,
                    priority=NotificationPriority.HIGH,
                    related_id=instance.id,
                    data={
                        'type': 'store',
                        'store_id': str(instance.id),
                        'related_id': str(instance.id),
                        'action': 'rejected'
                    }
                )
                
        except Store.DoesNotExist:
            pass


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
    except Exception:
        pass


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
    except Exception:
        pass


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
    except Exception:
        pass
