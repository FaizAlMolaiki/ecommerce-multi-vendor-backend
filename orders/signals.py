# """
# Django signals for sending notifications on order events
# دعم WebSocket والإشعارات في قاعدة البيانات
# """
# from django.db.models.signals import post_save, post_delete, pre_save
# from django.dispatch import receiver
# from .models import Order
# from project.websocket_utils import notify_new_order, notify_order_status_change, notify_stats_update, get_dashboard_stats
# from notifications.services import NotificationService
# from notifications.models import NotificationType, NotificationPriority
# import logging
# from project.websocket_utils import notify_new_order, notify_order_status_change, notify_stats_update, get_dashboard_stats
# # ===== إضافة WebSocket للموصل - بداية التعديل =====
# from project.driver_notifications_service import notify_new_order_available
# # ===== إضافة WebSocket للموصل - نهاية التعديل =====


# logger = logging.getLogger(__name__)

# @receiver(post_save, sender=Order)
# def order_saved(sender, instance, created, **kwargs):
#     """
#     إرسال إشعار عند إنشاء أو تحديث طلب
#     """
#     if created:
#         # طلب جديد - WebSocket
#         notify_new_order(instance)
        
#         # إشعار للعميل
#         if instance.user:
#             try:
#                 NotificationService.send_notification_to_user(
#                     user=instance.user,
#                     title='تم استلام طلبك! 🎉',
#                     body=f'طلب رقم #{instance.id} بقيمة {instance.grand_total} ريال',
#                     notification_type=NotificationType.ORDER,
#                     priority=NotificationPriority.HIGH,
#                     related_id=instance.id,
#                     data={
#                         'type': 'order',
#                         'order_id': str(instance.id),
#                         'related_id': str(instance.id),
#                         'grand_total': str(instance.grand_total),
#                         'payment_status': instance.payment_status,
#                         'fulfillment_status': instance.fulfillment_status
#                     }
#                 )
#                 logger.info(f"Order notification sent to customer for order {instance.id}")
#             except Exception as e:
#                 logger.error(f"Failed to send order notification to customer: {e}")
        
#         # إشعار للبائع (صاحب المتجر)
#         if instance.store and hasattr(instance.store, 'owner'):
#             try:
#                 NotificationService.send_notification_to_user(
#                     user=instance.store.owner,
#                     title='طلب جديد! 🛒',
#                     body=f'طلب رقم #{instance.id} من متجرك بقيمة {instance.grand_total} ريال',
#                     notification_type=NotificationType.ORDER,
#                     priority=NotificationPriority.HIGH,
#                     related_id=instance.id,
#                     data={
#                         'type': 'order',
#                         'order_id': str(instance.id),
#                         'related_id': str(instance.id),
#                         'store_id': str(instance.store.id),
#                         'grand_total': str(instance.grand_total),
#                         'action': 'vendor_notification'
#                     }
#                 )
#                 logger.info(f"Order notification sent to vendor for order {instance.id}")
#             except Exception as e:
#                 logger.error(f"Failed to send order notification to vendor: {e}")
#     else:
#         # تحديث حالة الطلب - WebSocket
#         notify_order_status_change(instance)
    
#     # تحديث الإحصائيات
#     stats = get_dashboard_stats()
#     notify_stats_update(stats)


# @receiver(pre_save, sender=Order)
# def order_status_changed(sender, instance, **kwargs):
#     """
#     إرسال إشعار عند تغيير حالة الطلب
#     """
#     if instance.pk:  # التأكد من أن الطلب موجود مسبقاً
#         try:
#             old_order = Order.objects.get(pk=instance.pk)
            
#             # تحقق من تغيير حالة الدفع
#             if old_order.payment_status != instance.payment_status:
#                 payment_messages = {
#                     'PENDING_PAYMENT': 'في انتظار الدفع ⏳',
#                     'PAID': 'تم الدفع بنجاح ✅',
#                     'CANCELLED': 'تم إلغاء الطلب ❌',
#                     'REFUNDED': 'تم استرداد المبلغ 💰'
#                 }
                
#                 status_text = payment_messages.get(instance.payment_status, instance.payment_status)
                
#                 if instance.user:
#                     try:
#                         NotificationService.send_notification_to_user(
#                             user=instance.user,
#                             title='تحديث حالة الدفع',
#                             body=f'طلب #{instance.id}: {status_text}',
#                             notification_type=NotificationType.PAYMENT,
#                             priority=NotificationPriority.HIGH,
#                             related_id=instance.id,
#                             data={
#                                 'type': 'order',
#                                 'order_id': str(instance.id),
#                                 'related_id': str(instance.id),
#                                 'payment_status': instance.payment_status
#                             }
#                         )
#                         logger.info(f"Payment status notification sent for order {instance.id}")
#                     except Exception as e:
#                         logger.error(f"Failed to send payment status notification: {e}")
            
#             # تحقق من تغيير حالة التنفيذ/الشحن
#             if old_order.fulfillment_status != instance.fulfillment_status:
#                 fulfillment_messages = {
#                     'PENDING': 'في انتظار المراجعة ⏳',
#                     'ACCEPTED': 'تم قبول الطلب ✅',
#                     'PREPARING': 'جاري تحضير الطلب 📦',
#                     'SHIPPED': 'تم شحن الطلب 🚚',
#                     'DELIVERED': 'تم توصيل الطلب 🎉',
#                     'REJECTED': 'تم رفض الطلب ❌'
#                 }
                
#                 status_text = fulfillment_messages.get(instance.fulfillment_status, instance.fulfillment_status)
                
#                 if instance.user:
#                     try:
#                         NotificationService.send_notification_to_user(
#                             user=instance.user,
#                             title='تحديث حالة الطلب',
#                             body=f'طلب #{instance.id}: {status_text}',
#                             notification_type=NotificationType.SHIPPING,
#                             priority=NotificationPriority.HIGH,
#                             related_id=instance.id,
#                             data={
#                                 'type': 'order',
#                                 'order_id': str(instance.id),
#                                 'related_id': str(instance.id),
#                                 'fulfillment_status': instance.fulfillment_status,
#                                 'status_text': status_text
#                             }
#                         )
#                         logger.info(f"Fulfillment status notification sent for order {instance.id}")
#                     except Exception as e:
#                         logger.error(f"Failed to send fulfillment status notification: {e}")
            
#             # تحقق من تعيين موصل
#             if old_order.delivery_agent != instance.delivery_agent and instance.delivery_agent:
#                 # إشعار للعميل
#                 if instance.user:
#                     try:
#                         NotificationService.send_notification_to_user(
#                             user=instance.user,
#                             title='تم تعيين موصل لطلبك 🚚',
#                             body=f'طلب #{instance.id}: تم تعيين موصل وسيتم توصيل طلبك قريباً',
#                             notification_type=NotificationType.SHIPPING,
#                             priority=NotificationPriority.NORMAL,
#                             related_id=instance.id,
#                             data={
#                                 'type': 'order',
#                                 'order_id': str(instance.id),
#                                 'related_id': str(instance.id),
#                                 'delivery_agent_id': str(instance.delivery_agent.id)
#                             }
#                         )
#                     except Exception as e:
#                         logger.error(f"Failed to send delivery agent notification to customer: {e}")
                
#                 # إشعار للموصل
#                 try:
#                     NotificationService.send_notification_to_user(
#                         user=instance.delivery_agent,
#                         title='طلب توصيل جديد! 🚚',
#                         body=f'تم تعيينك لتوصيل طلب #{instance.id} بقيمة {instance.grand_total} ريال',
#                         notification_type=NotificationType.ORDER,
#                         priority=NotificationPriority.HIGH,
#                         related_id=instance.id,
#                         data={
#                             'type': 'order',
#                             'order_id': str(instance.id),
#                             'related_id': str(instance.id),
#                             'grand_total': str(instance.grand_total),
#                             'action': 'delivery_assigned'
#                         }
#                     )
#                     logger.info(f"Delivery assignment notification sent for order {instance.id}")
#                 except Exception as e:
#                     logger.error(f"Failed to send delivery assignment notification: {e}")
                    
#         except Order.DoesNotExist:
#             pass
#         except Exception as e:
#             logger.error(f"Error in order_status_changed signal: {e}")

# @receiver(post_delete, sender=Order)
# def order_deleted(sender, instance, **kwargs):
#     """
#     إرسال تحديث الإحصائيات عند حذف طلب
#     """
#     stats = get_dashboard_stats()
#     notify_stats_update(stats)


# # ////////
# """
# Django signals for sending WebSocket notifications on order events
# """

# @receiver(post_save, sender=Order)
# def order_saved(sender, instance, created, **kwargs):
#     """
#     إرسال إشعار عند إنشاء أو تحديث طلب
#     """
#     if created:
#         # طلب جديد
#         notify_new_order(instance)
        
#         # ===== إضافة WebSocket للموصل - بداية التعديل =====
#         # إشعار الموصلين بالطلب الجديد إذا كان مقبولاً ولم يُخصص لموصل بعد
#         if (instance.fulfillment_status == Order.FulfillmentStatus.ACCEPTED and 
#             instance.delivery_agent is None):
#             notify_new_order_available(instance)
#         # ===== إضافة WebSocket للموصل - نهاية التعديل =====
            
#     else:
#         # تحديث حالة الطلب
#         notify_order_status_change(instance)
        
#         # ===== إضافة WebSocket للموصل - بداية التعديل =====
#         # إشعار الموصلين بالطلب الجديد إذا تم قبوله للتو ولم يُخصص لموصل
#         if (instance.fulfillment_status == Order.FulfillmentStatus.ACCEPTED and 
#             instance.delivery_agent is None):
#             notify_new_order_available(instance)
#         # ===== إضافة WebSocket للموصل - نهاية التعديل =====
    
#     # تحديث الإحصائيات
#     stats = get_dashboard_stats()
#     notify_stats_update(stats)

# @receiver(post_delete, sender=Order)
# def order_deleted(sender, instance, **kwargs):
#     """
#     إرسال تحديث الإحصائيات عند حذف طلب
#     """
#     stats = get_dashboard_stats()
#     notify_stats_update(stats)


# # StoreOrder signals removed after unifying order model


"""
Django signals for sending notifications on order events
دعم WebSocket والإشعارات في قاعدة البيانات
"""
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from .models import Order
from project.websocket_utils import notify_new_order, notify_order_status_change, notify_stats_update, get_dashboard_stats
from notifications.models import NotificationType, NotificationPriority
from notifications import tasks  # استخدام Celery tasks بدلاً من NotificationService المباشر
import logging

from project.websocket_utils import notify_new_order, notify_order_status_change, notify_stats_update, get_dashboard_stats

# ===== إضافة WebSocket للموصل - بداية التعديل =====
from project.driver_notifications_service import notify_new_order_available
# ===== إضافة WebSocket للموصل - نهاية التعديل =====





logger = logging.getLogger(__name__)

@receiver(post_save, sender=Order)
def order_saved(sender, instance, created, **kwargs):
    """
    إرسال إشعار عند إنشاء أو تحديث طلب
    """
    if created:
        # طلب جديد - WebSocket
        notify_new_order(instance)
        # ===== إضافة WebSocket للموصل - بداية التعديل =====
       
        # ===== إضافة WebSocket للموصل - بداية التعديل =====
        # إشعار الموصلين بالطلب الجديد إذا تم قبوله للتو ولم يُخصص لموصل
        if (instance.fulfillment_status == Order.FulfillmentStatus.ACCEPTED and 
            instance.delivery_agent is None):
            notify_new_order_available(instance)
        # ===== إضافة WebSocket للموصل - نهاية التعديل =====
    
        # إشعار للعميل - Async via Celery
        if instance.user:
            try:
                tasks.send_custom_notification_async.delay(
                    user_id=instance.user.id,
                    title='تم استلام طلبك! 🎉',
                    body=f'طلب رقم #{instance.id} بقيمة {instance.grand_total} ريال',
                    notification_type=NotificationType.ORDER,
                    priority=NotificationPriority.HIGH,
                    content_type_model='orders.order',  # ✅ GenericForeignKey
                    object_id=instance.id,               # ✅ GenericForeignKey
                    data={
                        'type': 'order',
                        'order_id': str(instance.id),
                        'grand_total': str(instance.grand_total),
                        'payment_status': instance.payment_status,
                        'fulfillment_status': instance.fulfillment_status
                    }
                )
                logger.info(f"Order notification task queued for customer, order {instance.id}")
            except Exception as e:
                logger.error(f"Failed to queue order notification to customer: {e}")
        
        # إشعار للبائع (صاحب المتجر) - Async via Celery
        if instance.store and hasattr(instance.store, 'owner'):
            try:
                tasks.send_custom_notification_async.delay(
                    user_id=instance.store.owner.id,
                    title='طلب جديد! 🛒',
                    body=f'طلب رقم #{instance.id} من متجرك بقيمة {instance.grand_total} ريال',
                    notification_type=NotificationType.ORDER,
                    priority=NotificationPriority.HIGH,
                    content_type_model='orders.order',
                    object_id=instance.id,
                    data={
                        'type': 'order',
                        'order_id': str(instance.id),
                        'store_id': str(instance.store.id),
                        'grand_total': str(instance.grand_total),
                        'action': 'vendor_notification'
                    }
                )
                logger.info(f"Order notification task queued for vendor, order {instance.id}")
            except Exception as e:
                logger.error(f"Failed to queue order notification to vendor: {e}")
    else:
        
        # تحديث حالة الطلب - WebSocket
        notify_order_status_change(instance)
         # ===== إضافة WebSocket للموصل - بداية التعديل =====
        # إشعار الموصلين بالطلب الجديد إذا تم قبوله للتو ولم يُخصص لموصل
        if (instance.fulfillment_status == Order.FulfillmentStatus.ACCEPTED and 
            instance.delivery_agent is None):
            notify_new_order_available(instance)
        # ===== إضافة WebSocket للموصل - نهاية التعديل =====
    
    
    # تحديث الإحصائيات
    stats = get_dashboard_stats()
    notify_stats_update(stats)

@receiver(pre_save, sender=Order)
def order_status_changed(sender, instance, **kwargs):
    """
    إرسال إشعار عند تغيير حالة الطلب
    """
    if instance.pk:  # التأكد من أن الطلب موجود مسبقاً
        try:
            old_order = Order.objects.get(pk=instance.pk)
            
            # تحقق من تغيير حالة الدفع
            if old_order.payment_status != instance.payment_status:
                payment_messages = {
                    'PENDING_PAYMENT': 'في انتظار الدفع ⏳',
                    'PAID': 'تم الدفع بنجاح ✅',
                    'CANCELLED': 'تم إلغاء الطلب ❌',
                    'REFUNDED': 'تم استرداد المبلغ 💰'
                }
                
                status_text = payment_messages.get(instance.payment_status, instance.payment_status)
                
                if instance.user:
                    try:
                        tasks.send_custom_notification_async.delay(
                            user_id=instance.user.id,
                            title='تحديث حالة الدفع',
                            body=f'طلب #{instance.id}: {status_text}',
                            notification_type=NotificationType.PAYMENT,
                            priority=NotificationPriority.HIGH,
                            content_type_model='orders.order',
                            object_id=instance.id,
                            data={
                                'type': 'order',
                                'order_id': str(instance.id),
                                        'payment_status': instance.payment_status
                            }
                        )
                        logger.info(f"Payment status notification task queued for order {instance.id}")
                    except Exception as e:
                        logger.error(f"Failed to queue payment status notification: {e}")
            
            # تحقق من تغيير حالة التنفيذ/الشحن
            if old_order.fulfillment_status != instance.fulfillment_status:
                fulfillment_messages = {
                    'PENDING': 'في انتظار المراجعة ⏳',
                    'ACCEPTED': 'تم قبول الطلب ✅',
                    'PREPARING': 'جاري تحضير الطلب 📦',
                    'SHIPPED': 'تم شحن الطلب 🚚',
                    'DELIVERED': 'تم توصيل الطلب 🎉',
                    'REJECTED': 'تم رفض الطلب ❌'
                }
                
                status_text = fulfillment_messages.get(instance.fulfillment_status, instance.fulfillment_status)
                
                if instance.user:
                    try:
                        tasks.send_custom_notification_async.delay(
                            user_id=instance.user.id,
                            title='تحديث حالة الطلب',
                            body=f'طلب #{instance.id}: {status_text}',
                            notification_type=NotificationType.SHIPPING,
                            priority=NotificationPriority.HIGH,
                            content_type_model='orders.order',
                            object_id=instance.id,
                            data={
                                'type': 'order',
                                'order_id': str(instance.id),
                                        'fulfillment_status': instance.fulfillment_status,
                                'status_text': status_text
                            }
                        )
                        logger.info(f"Fulfillment status notification task queued for order {instance.id}")
                    except Exception as e:
                        logger.error(f"Failed to queue fulfillment status notification: {e}")
            
            # تحقق من تعيين موصل
            if old_order.delivery_agent != instance.delivery_agent and instance.delivery_agent:
                # إشعار للعميل - Async via Celery
                if instance.user:
                    try:
                        tasks.send_custom_notification_async.delay(
                            user_id=instance.user.id,
                            title='تم تعيين موصل لطلبك 🚚',
                            body=f'طلب #{instance.id}: تم تعيين موصل وسيتم توصيل طلبك قريباً',
                            notification_type=NotificationType.SHIPPING,
                            priority=NotificationPriority.NORMAL,
                            content_type_model='orders.order',
                            object_id=instance.id,
                            data={
                                'type': 'order',
                                'order_id': str(instance.id),
                                        'delivery_agent_id': str(instance.delivery_agent.id)
                            }
                        )
                    except Exception as e:
                        logger.error(f"Failed to queue delivery agent notification to customer: {e}")
                
                # إشعار للموصل - Async via Celery
                try:
                    tasks.send_custom_notification_async.delay(
                        user_id=instance.delivery_agent.id,
                        title='طلب توصيل جديد! 🚚',
                        body=f'تم تعيينك لتوصيل طلب #{instance.id} بقيمة {instance.grand_total} ريال',
                        notification_type=NotificationType.ORDER,
                        priority=NotificationPriority.HIGH,
                        content_type_model='orders.order',
                        object_id=instance.id,
                        data={
                            'type': 'order',
                            'order_id': str(instance.id),
                                'grand_total': str(instance.grand_total),
                            'action': 'delivery_assigned'
                        }
                    )
                    logger.info(f"Delivery assignment notification task queued for order {instance.id}")
                except Exception as e:
                    logger.error(f"Failed to queue delivery assignment notification: {e}")
                    
        except Order.DoesNotExist:
            pass
        except Exception as e:
            logger.error(f"Error in order_status_changed signal: {e}")

@receiver(post_delete, sender=Order)
def order_deleted(sender, instance, **kwargs):
    """
    إرسال تحديث الإحصائيات عند حذف طلب
    """
    stats = get_dashboard_stats()
    notify_stats_update(stats)

