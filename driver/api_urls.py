
from django.urls import path, re_path

from . import api_views,api_views_notifications


urlpatterns = [
    # Driver/Delivery endpoints
    path('apply-delivery/', api_views.ApplyDeliveryView.as_view(), name='apply_delivery'),
    path('availability/', api_views.SetAvailabilityView.as_view(), name='set_availability'),
    path('availability-status/', api_views.DriverAvailabilityStatus.as_view(), name='availability_status'),
    
    path('current-orders/', api_views.get_driver_current_orders, name='driver_current_orders'),
    path('available-orders/', api_views.get_driver_available_orders, name='driver_available_orders'),
    path('update-order-status/', api_views.update_order_status, name='update_order_status'),
    path('accept-order/', api_views.accept_order, name='accept_order'),
     # Driver Notifications endpoints
    path('notifications/', api_views_notifications.get_driver_notifications, name='driver_notifications'),
    path('notifications/count/', api_views_notifications.get_notifications_count, name='notifications_count'),
    path('notifications/<int:notification_id>/read/', api_views_notifications.mark_notification_as_read, name='mark_notification_read'),
    path('notifications/read-all/', api_views_notifications.mark_all_notifications_as_read, name='mark_all_notifications_read'),
    path('notifications/<int:notification_id>/delete/', api_views_notifications.delete_notification, name='delete_notification'),

    
]

