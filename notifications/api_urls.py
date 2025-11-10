from django.urls import path
from . import views

urlpatterns = [
    # إشعارات المستخدم
    path('', views.NotificationListView.as_view(), name='notification-list'),
    path('<int:pk>/', views.NotificationDetailView.as_view(), name='notification-detail'),
    path('<int:notification_id>/read/', views.mark_notification_as_read, name='mark-notification-as-read'),
    path('mark-all-read/', views.mark_all_as_read, name='mark-all-as-read'),
    path('<int:notification_id>/delete/', views.delete_notification, name='delete-notification'),
    path('delete-all-read/', views.delete_all_read_notifications, name='delete-all-read'),
    path('stats/', views.notification_stats, name='notification-stats'),
    path('unread-count/', views.unread_notification_count, name='notification-unread-count'),
    
    # إدارة أجهزة FCM
    path('fcm-device/', views.FCMDeviceCreateView.as_view(), name='fcm-device-create'),
    path('fcm-device/update-token/', views.update_fcm_token, name='fcm-update-token'),
    path('fcm-device/deactivate/', views.deactivate_fcm_device, name='fcm-deactivate'),
    
    # إدارة الإشعارات (للمشرفين فقط)
    path('admin/create/', views.NotificationCreateView.as_view(), name='admin-notification-create'),
    path('admin/templates/', views.NotificationTemplateListCreateView.as_view(), name='admin-templates'),
    path('admin/templates/<int:pk>/', views.NotificationTemplateDetailView.as_view(), name='admin-template-detail'),
    path('admin/send-template/', views.send_template_notification, name='admin-send-template'),
]
