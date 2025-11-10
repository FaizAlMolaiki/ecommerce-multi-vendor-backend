"""
Django signals for sending notifications on product events
استخدام تطبيق wishlist الموجود بدلاً من إنشاء نماذج جديدة
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Product
from notifications import tasks  # استخدام Celery tasks بدلاً من NotificationService المباشر
from notifications.models import NotificationType, NotificationPriority
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

# تم حذف الدالة المكررة - انظر product_created_notification_all_users بالأسفل


# @receiver(pre_save, sender=Product)
# def product_stock_notification(sender, instance, **kwargs):
#     """إرسال إشعار عند عودة المنتج للمخزون"""
#     if instance.pk:  # إذا كان تحديث وليس إنشاء
#         try:
#             old_product = Product.objects.get(pk=instance.pk)
            
#             # تحقق من توفر المنتج (عبر variants)
#             old_in_stock = old_product.variants.filter(stock_quantity__gt=0).exists() if hasattr(old_product, 'variants') else True
#             new_in_stock = instance.variants.filter(stock_quantity__gt=0).exists() if hasattr(instance, 'variants') else True
            
#             # إذا كان المنتج غير متوفر وأصبح متوفر ✅
#             if not old_in_stock and new_in_stock:
#                 # ✅ استخدام UserProductFavorite من wishlist
#                 from wishlist.models import UserProductFavorite
                
#                 wishlist_users = UserProductFavorite.objects.filter(
#                     product=instance
#                 ).select_related('user')
                
#                 if wishlist_users.exists():
#                     NotificationService.send_notification_to_users(
#                         user_ids=[w.user.id for w in wishlist_users],
#                         title='المنتج متوفر الآن! 🎉',
#                         body=f'{instance.name} عاد إلى المخزون',
#                         notification_type=NotificationType.PRODUCT,
#                         priority=NotificationPriority.HIGH,
#                         related_id=instance.id,
#                         image_url=instance.cover_image_url,
#                         data={
#                             'type': 'product',
#                             'product_id': str(instance.id),
#                             'related_id': str(instance.id),
#                             'action': 'back_in_stock'
#                         }
#                     )
                
#         except Product.DoesNotExist:
#             pass


@receiver(pre_save, sender=Product)
def store_old_price(sender, instance, **kwargs):
    """حفظ السعر القديم قبل التحديث لتجنب N+1 query"""
    if instance.pk:
        try:
            # حفظ السعر القديم في instance مؤقتاً
            old_product = Product.objects.only('id').prefetch_related('variants').get(pk=instance.pk)
            instance._old_price = old_product.variants.first().price if old_product.variants.exists() else None
        except Product.DoesNotExist:
            instance._old_price = None


@receiver(post_save, sender=Product)
def product_price_drop_notification(sender, instance, created, **kwargs):
    """إرسال إشعار عند تخفيض سعر المنتج - Async via Celery"""
    if not created and instance.pk:
        try:
            # استخدام السعر المحفوظ بدلاً من query إضافي
            old_price = getattr(instance, '_old_price', None)
            new_price = instance.variants.first().price if instance.variants.exists() else None
            
            # إذا انخفض السعر بنسبة 10% أو أكثر
            if old_price and new_price and new_price < old_price * Decimal('0.9'):
                discount_percentage = int((1 - new_price / old_price) * 100)
                
                # ✅ استخدام UserProductFavorite من wishlist
                from wishlist.models import UserProductFavorite
                
                wishlist_user_ids = UserProductFavorite.objects.filter(
                    product=instance
                ).values_list('user_id', flat=True)
                
                if wishlist_user_ids:
                    # إرسال الإشعار بشكل async لكل مستخدم
                    for user_id in wishlist_user_ids:
                        tasks.send_custom_notification_async.delay(
                            user_id=user_id,
                            title=f'تخفيض {discount_percentage}% على المنتج! 🔥',
                            body=f'{instance.name} - السعر الجديد: {new_price} ريال',
                            notification_type=NotificationType.PROMOTION,
                            priority=NotificationPriority.HIGH,
                            content_type_model='products.product',  # ✅ GenericForeignKey
                            object_id=instance.id,                   # ✅ GenericForeignKey
                            data={
                                'type': 'product',
                                'product_id': str(instance.id),
                                'action': 'price_drop',
                                'old_price': str(old_price),
                                'new_price': str(new_price),
                                'discount_percentage': str(discount_percentage),
                                'image_url': instance.cover_image_url or ''
                            }
                        )
                    
                    logger.info(f"Price drop notification tasks queued for product {instance.id}, {len(wishlist_user_ids)} users")
                
        except Exception as e:
            logger.error(f"Error queuing price drop notifications: {e}", exc_info=True)

# ✅ إرسال للجميع - Async via Celery
@receiver(post_save, sender=Product)
def product_created_notification_all_users(sender, instance, created, **kwargs):
    """إرسال إشعار لجميع المستخدمين عند إضافة منتج جديد - Async"""
    if created:
        try:
            product = instance
            store = product.store
            
            # 📢 جلب جميع المستخدمين النشطين (بدون البائعين)
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            all_customers = User.objects.filter(
                is_active=True,
                is_vendor=False,
                is_staff=False
            ).values_list('id', flat=True)  # فقط IDs لتوفير الذاكرة
            
            # ✅ إرسال الإشعار لجميع العملاء (Async)
            for user_id in all_customers:
                tasks.send_custom_notification_async.delay(
                    user_id=user_id,
                    title=f'منتج جديد في {store.name}! 🎁',
                    body=f'{product.name} - متوفر الآن',
                    notification_type=NotificationType.PRODUCT,
                    priority=NotificationPriority.NORMAL,
                    content_type_model='products.product',  # ✅ GenericForeignKey
                    object_id=product.id,                    # ✅ GenericForeignKey
                    data={
                        'type': 'product',
                        'product_id': str(product.id),
                        'store_id': str(store.id),
                        'store_name': store.name,
                        'image_url': product.cover_image_url or ''
                    }
                )
            
            # 📊 إشعار للبائع (Async)
            num_users = all_customers.count()
            tasks.send_custom_notification_async.delay(
                user_id=store.owner.id,
                title='تم إضافة منتج جديد ✅',
                body=f'تم نشر {product.name} لـ {num_users} مستخدم',
                notification_type=NotificationType.PRODUCT,
                priority=NotificationPriority.NORMAL,
                content_type_model='products.product',  # ✅ GenericForeignKey
                object_id=product.id,                    # ✅ GenericForeignKey
                data={
                    'type': 'product',
                    'product_id': str(product.id),
                    'action': 'created',
                    'num_notified': str(num_users)
                }
            )
            
            logger.info(f"Product notification tasks queued for {num_users} users, product {product.id}")
            
        except Exception as e:
            logger.error(f"Error queuing product creation notifications: {e}", exc_info=True)