"""
Utility functions for sending WebSocket notifications
"""
import json
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging

logger = logging.getLogger(__name__)


def send_dashboard_notification(message_type, data):
    """
    إرسال إشعار إلى جميع المتصلين بلوحة التحكم
    """
    try:
        channel_layer = get_channel_layer()
        if channel_layer:
            # Debug logging to trace outgoing WS messages
            try:
                logger.info(f"WS->dashboard_updates type={message_type} payload_keys={list(data.keys())}")
            except Exception:
                pass
            # Also print to stdout to ensure visibility without logging config
            try:
                print(f"WS->dashboard_updates type={message_type} keys={list(data.keys())}")
            except Exception:
                pass
            async_to_sync(channel_layer.group_send)(
                'dashboard_updates',
                {
                    'type': message_type.replace('_', '_'),  # Ensure proper method name format
                    **data  # Spread data directly instead of nesting
                }
            )
    except Exception as e:
        print(f'Error sending WebSocket notification: {e}')


def notify_new_order(order):
    """
    إرسال إشعار طلب جديد
    """
    try:
        order_data = {
            'id': order.id,
            'user_email': getattr(order.user, 'email', None) or 'غير محدد',
            'store_name': getattr(order.store, 'name', '—'),
            'total_amount': float(order.grand_total or 0),
            'payment_status': getattr(order, 'payment_status', None),
            'fulfillment_status': getattr(order, 'fulfillment_status', None),
            'created_at': order.created_at.isoformat(),
        }
        
        send_dashboard_notification('new_order', {
            'order': order_data,
            'message': f'طلب جديد #{order.id}'
        })
    except Exception as e:
        print(f'Error in notify_new_order: {e}')


def notify_order_status_change(order):
    """
    إرسال إشعار تغيير حالة الطلب
    """
    try:
        order_data = {
            'id': order.id,
            'user_email': getattr(order.user, 'email', None) or 'غير محدد',
            'store_name': getattr(order.store, 'name', '—'),
            'total_amount': float(order.grand_total or 0),
            'payment_status': getattr(order, 'payment_status', None),
            'fulfillment_status': getattr(order, 'fulfillment_status', None),
            'created_at': order.created_at.isoformat(),
        }
        
        send_dashboard_notification('order_status_changed', {
            'order': order_data,
            'message': f'تم تحديث حالة الطلب #{order.id}'
        })
    except Exception as e:
        print(f'Error in notify_order_status_change: {e}')


def notify_stats_update(stats):
    """
    إرسال تحديث الإحصائيات
    """
    send_dashboard_notification('stats_update', {
        'stats': stats
    })


def get_dashboard_stats():
    """
    جلب إحصائيات لوحة التحكم
    """
    from orders.models import Order
    from stores.models import Store
    from products.models import Product
    from accounts.models import User
    
    return {
        'orders': Order.objects.count(),
        'stores': Store.objects.count(),
        'products': Product.objects.count(),
        'users': User.objects.count(),
    }
