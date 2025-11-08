"""
خدمة إرسال الإشعارات للموصلين عبر WebSocket
"""
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
import logging

# ===== إضافة حفظ الإشعارات - بداية التعديل =====
from driver.models_notifications import DriverNotification
# ===== إضافة حفظ الإشعارات - نهاية التعديل =====

logger = logging.getLogger(__name__)
channel_layer = get_channel_layer()
from django.contrib.auth import get_user_model
from orders.models import Order

User = get_user_model()


class DriverNotificationService:
    """خدمة إرسال الإشعارات للموصلين"""
    def __init__(self):
        self.channel_layer = get_channel_layer()
    
    def send_to_driver(self, driver_id, message_type, data):
        """إرسال إشعار لموصل محدد"""
        if not self.channel_layer:
            print("Channel layer not configured")
            return False
            
        group_name = f'driver_{driver_id}'
        
        try:
            async_to_sync(self.channel_layer.group_send)(
                group_name,
                {
                    'type': message_type,
                    **data
                }
            )
            return True
        except Exception as e:
            print(f"Error sending notification to driver {driver_id}: {e}")
            return False
    
    def send_to_all_drivers(self, message_type, data):
        """إرسال إشعار لجميع الموصلين المتصلين"""
        if not self.channel_layer:
            print("Channel layer not configured")
            return False
            
        try:
            async_to_sync(self.channel_layer.group_send)(
                'all_drivers',
                {
                    'type': message_type,
                    **data
                }
            )
            return True
        except Exception as e:
            print(f"Error sending notification to all drivers: {e}")
            return False
    
    def notify_new_order_available(self, order):
        """إشعار جميع الموصلين بطلب جديد متاح"""
        order_data = self._serialize_order(order)
        message = f'طلب جديد متاح للقبول - الطلب #{order.id}'
        
        # ===== إضافة حفظ الإشعارات - بداية التعديل =====
        # حفظ الإشعار في قاعدة البيانات للموصلين المتاحين
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            available_drivers = User.objects.filter(
                is_delivery=True,
                is_active=True
            )
            
            for driver in available_drivers:
                DriverNotification.objects.create(
                    driver=driver,
                    title='طلب جديد متاح',
                    message=message,
                    notification_type='new_order',
                    priority='high',
                    data=order_data
                )
        except Exception as e:
            logger.error(f'خطأ في حفظ إشعار الطلب الجديد: {e}')
        # ===== إضافة حفظ الإشعارات - نهاية التعديل =====
        
        return self.send_to_all_drivers(
            'new_order_available',
            {
                'order': order_data,
                'message': message
            }
        )
    
    def notify_order_assigned(self, order, driver):
        """إشعار موصل محدد بتعيين طلب له"""
        order_data = self._serialize_order(order)
        message = f'تم تعيين الطلب #{order.id} لك'
        
        # ===== إضافة حفظ الإشعارات - بداية التعديل =====
        # حفظ الإشعار في قاعدة البيانات
        try:
            DriverNotification.objects.create(
                driver=driver,
                title='تم تعيين طلب جديد',
                message=message,
                notification_type='order_assigned',
                priority='high',
                data=order_data
            )
        except Exception as e:
            logger.error(f'خطأ في حفظ إشعار تعيين الطلب: {e}')
        # ===== إضافة حفظ الإشعارات - نهاية التعديل =====
        
        return self.send_to_driver(
            driver.id,
            'order_assigned',
            {
                'order': order_data,
                'message': message
            }
        )
    
    def notify_order_cancelled(self, order_id, driver_id=None):
        """إشعار بإلغاء طلب"""
        data = {
            'order_id': order_id,
            'message': f'تم إلغاء الطلب #{order_id}'
        }
        
        if driver_id:
            # إشعار موصل محدد
            return self.send_to_driver(driver_id, 'order_cancelled', data)
        else:
            # إشعار جميع الموصلين
            return self.send_to_all_drivers('order_cancelled', data)
    
    def notify_driver_general(self, driver_id, title, message, data=None):
        """إرسال إشعار عام لموصل"""
        return self.send_to_driver(
            driver_id,
            'driver_notification',
            {
                'title': title,
                'message': message,
                'data': data or {}
            }
        )
    
    def notify_all_drivers_general(self, title, message, data=None):
        """إرسال إشعار عام لجميع الموصلين"""
        return self.send_to_all_drivers(
            'driver_notification',
            {
                'title': title,
                'message': message,
                'data': data or {}
            }
        )
    
    def _serialize_order(self, order):
        """تحويل بيانات الطلب إلى JSON"""
        try:
            # معلومات أساسية عن الطلب
            order_data = {
                'id': order.id,
                'grand_total': float(order.grand_total),
                'delivery_fee': float(order.delivery_fee),
                'payment_status': order.payment_status,
                'fulfillment_status': order.fulfillment_status,
                'created_at': order.created_at.isoformat() if order.created_at else None,
            }
            
            # معلومات المتجر
            if order.store:
                order_data['store'] = {
                    'id': order.store.id,
                    'name': order.store.name,
                    'address': getattr(order.store, 'address', ''),
                }
            
            # معلومات العميل (محدودة للخصوصية)
            if order.user:
                order_data['customer'] = {
                    'name': order.user.name or 'عميل',
                    'phone': getattr(order.user, 'phone_number', ''),
                }
            
            # عنوان التوصيل
            if order.shipping_address_snapshot:
                address = order.shipping_address_snapshot
                order_data['delivery_address'] = {
                    'city': address.get('city', ''),
                    'street': address.get('street', ''),
                    'landmark': address.get('landmark', ''),
                }
            
            # عناصر الطلب (معلومات محدودة)
            items = []
            for item in order.items.all():
                items.append({
                    'product_name': item.product_name_snapshot,
                    'quantity': item.quantity,
                    'price': float(item.price_at_purchase),
                })
            order_data['items'] = items
            order_data['items_count'] = len(items)
            
            return order_data
            
        except Exception as e:
            print(f"Error serializing order {order.id}: {e}")
            return {
                'id': order.id,
                'error': 'خطأ في تحميل بيانات الطلب'
            }


# إنشاء instance واحد للاستخدام في المشروع
driver_notification_service = DriverNotificationService()


# دوال مساعدة للاستخدام المباشر
def notify_new_order_available(order):
    """دالة مساعدة لإشعار الموصلين بطلب جديد"""
    return driver_notification_service.notify_new_order_available(order)


def notify_order_assigned(order, driver):
    """دالة مساعدة لإشعار موصل بتعيين طلب"""
    return driver_notification_service.notify_order_assigned(order, driver)


def notify_order_cancelled(order_id, driver_id=None):
    """دالة مساعدة لإشعار بإلغاء طلب"""
    return driver_notification_service.notify_order_cancelled(order_id, driver_id)


def notify_driver(driver_id, title, message, data=None):
    """دالة مساعدة لإرسال إشعار عام لموصل"""
    return driver_notification_service.notify_driver_general(driver_id, title, message, data)


def notify_all_drivers(title, message, data=None):
    """دالة مساعدة لإرسال إشعار عام لجميع الموصلين"""
    return driver_notification_service.notify_all_drivers_general(title, message, data)
