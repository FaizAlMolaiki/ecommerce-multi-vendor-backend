"""
Django signals for sending notifications on product events
استخدام تطبيق wishlist الموجود بدلاً من إنشاء نماذج جديدة
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Product
from notifications.services import NotificationService
from notifications.models import NotificationType, NotificationPriority
from decimal import Decimal


@receiver(post_save, sender=Product)
def product_created_notification(sender, instance, created, **kwargs):
    """إرسال إشعار عند إضافة منتج جديد"""
    if created:
        product = instance
        store = product.store
        
        # ✅ استخدام UserStoreFavorite من wishlist الموجود
        from wishlist.models import UserStoreFavorite
        
        # جلب المستخدمين الذين أضافوا المتجر للمفضلة وفعّلوا الإشعارات
        followers = UserStoreFavorite.objects.filter(
            store=store
        ).select_related('user')
        
        if followers.exists():
            follower_users = [f.user for f in followers]
            NotificationService.send_notification_to_users(
                user_ids=[u.id for u in follower_users],
                title=f'منتج جديد في {store.name}! 🎁',
                body=f'{product.name} - متوفر الآن',
                notification_type=NotificationType.PRODUCT,
                priority=NotificationPriority.NORMAL,
                related_id=product.id,
                image_url=product.cover_image_url,
                data={
                    'type': 'product',
                    'product_id': str(product.id),
                    'related_id': str(product.id),
                    'store_id': str(store.id),
                    'store_name': store.name
                }
            )
        
        # إشعار لصاحب المتجر (تأكيد)
        NotificationService.send_notification_to_user(
            user=store.owner,
            title='تم إضافة منتج جديد ✅',
            body=f'تم إضافة {product.name} إلى متجرك بنجاح',
            notification_type=NotificationType.PRODUCT,
            priority=NotificationPriority.NORMAL,
            related_id=product.id,
            image_url=product.cover_image_url,
            data={
                'type': 'product',
                'product_id': str(product.id),
                'related_id': str(product.id),
                'action': 'created'
            }
        )


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


@receiver(post_save, sender=Product)
def product_price_drop_notification(sender, instance, created, **kwargs):
    """إرسال إشعار عند تخفيض سعر المنتج"""
    if not created and instance.pk:
        try:
            old_product = Product.objects.get(pk=instance.pk)
            
            # الحصول على السعر من أول variant
            old_price = old_product.variants.first().price if old_product.variants.exists() else None
            new_price = instance.variants.first().price if instance.variants.exists() else None
            
            # إذا انخفض السعر بنسبة 10% أو أكثر ✅
            # if old_price and new_price and new_price < old_price * 0.9:
            # ===============
            if old_price and new_price and new_price < old_price * Decimal('0.9'):
            # ===============
                discount_percentage = int((1 - new_price / old_price) * 100)
                
                # ✅ استخدام UserProductFavorite من wishlist
                from wishlist.models import UserProductFavorite
                
                wishlist_users = UserProductFavorite.objects.filter(
                    product=instance
                ).select_related('user')
                
                if wishlist_users.exists():
                    NotificationService.send_notification_to_users(
                        user_ids=[w.user.id for w in wishlist_users],
                        title=f'تخفيض {discount_percentage}% على المنتج! 🔥',
                        body=f'{instance.name} - السعر الجديد: {new_price} ريال',
                        notification_type=NotificationType.PROMOTION,
                        priority=NotificationPriority.HIGH,
                        related_id=instance.id,
                        image_url=instance.cover_image_url,
                        data={
                            'type': 'product',
                            'product_id': str(instance.id),
                            'related_id': str(instance.id),
                            'action': 'price_drop',
                            'old_price': str(old_price),
                            'new_price': str(new_price),
                            'discount_percentage': str(discount_percentage)
                        }
                    )
                
        except Product.DoesNotExist:
            pass

# ✅ NEW CODE - إرسال للجميع
@receiver(post_save, sender=Product)
def product_created_notification(sender, instance, created, **kwargs):
    """إرسال إشعار لجميع المستخدمين عند إضافة منتج جديد"""
    if created:
        product = instance
        store = product.store
        
        # 📢 جلب جميع المستخدمين النشطين (بدون البائعين)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        all_customers = User.objects.filter(
            is_active=True,
            is_vendor=False,  # استبعاد البائعين
            is_staff=False    # استبعاد الموظفين
        )
        
        # ✅ إرسال الإشعار لجميع العملاء
        if all_customers.exists():
            user_ids = list(all_customers.values_list('id', flat=True))
            
            NotificationService.send_notification_to_users(
                user_ids=user_ids,
                title=f'منتج جديد في {store.name}! 🎁',
                body=f'{product.name} - متوفر الآن',
                notification_type=NotificationType.PRODUCT,
                priority=NotificationPriority.NORMAL,
                related_id=product.id,
                image_url=product.cover_image_url,
                data={
                    'type': 'product',
                    'product_id': str(product.id),
                    'related_id': str(product.id),
                    'store_id': str(store.id),
                    'store_name': store.name
                }
            )
            
            # 📊 إشعار للبائع مع عدد المستخدمين
            num_users = all_customers.count()
            NotificationService.send_notification_to_user(
                user=store.owner,
                title='تم إضافة منتج جديد ✅',
                body=f'تم نشر {product.name} لـ {num_users} مستخدم',
                notification_type=NotificationType.PRODUCT,
                priority=NotificationPriority.NORMAL,
                related_id=product.id
            )