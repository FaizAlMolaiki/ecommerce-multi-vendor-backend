"""
API Views للإشعارات الخاصة بالموصلين
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q

from .models_notifications import DriverNotification, NotificationTemplate
from .serializers_notifications import DriverNotificationSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_driver_notifications(request):
    """
    جلب إشعارات الموصل
    """
    try:
        # التحقق من أن المستخدم موصل
        if not getattr(request.user, 'is_delivery', False):
            return Response({
                'success': False,
                'message': 'غير مصرح لك بالوصول لهذه البيانات'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # معاملات الاستعلام
        page = int(request.GET.get('page', 1))
        limit = min(int(request.GET.get('limit', 20)), 50)  # حد أقصى 50
        unread_only = request.GET.get('unread_only', 'false').lower() == 'true'
        notification_type = request.GET.get('type', None)
        
        # بناء الاستعلام
        queryset = DriverNotification.objects.filter(
            driver=request.user
        ).select_related('driver')
        
        # تصفية الإشعارات غير المقروءة فقط
        if unread_only:
            queryset = queryset.filter(is_read=False)
        
        # تصفية حسب نوع الإشعار
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
        
        # استبعاد الإشعارات المنتهية الصلاحية
        queryset = queryset.filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
        )
        
        # ترقيم الصفحات
        offset = (page - 1) * limit
        total_count = queryset.count()
        notifications = queryset[offset:offset + limit]
        
        # إحصائيات
        unread_count = DriverNotification.objects.filter(
            driver=request.user,
            is_read=False
        ).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
        ).count()
        
        # تسلسل البيانات
        serializer = DriverNotificationSerializer(notifications, many=True)
        
        return Response({
            'success': True,
            'data': {
                'notifications': serializer.data,
                'pagination': {
                    'current_page': page,
                    'total_pages': (total_count + limit - 1) // limit,
                    'total_count': total_count,
                    'has_next': offset + limit < total_count,
                    'has_previous': page > 1
                },
                'stats': {
                    'unread_count': unread_count,
                    'total_count': total_count
                }
            }
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'خطأ في جلب الإشعارات: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_notification_as_read(request, notification_id):
    """
    تمييز إشعار كمقروء
    """
    try:
        # التحقق من أن المستخدم موصل
        if not getattr(request.user, 'is_delivery', False):
            return Response({
                'success': False,
                'message': 'غير مصرح لك بالوصول لهذه البيانات'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # البحث عن الإشعار
        notification = get_object_or_404(
            DriverNotification,
            id=notification_id,
            driver=request.user
        )
        
        # تمييز كمقروء
        notification.mark_as_read()
        
        # إحصائيات محدثة
        unread_count = DriverNotification.objects.filter(
            driver=request.user,
            is_read=False
        ).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
        ).count()
        
        return Response({
            'success': True,
            'message': 'تم تمييز الإشعار كمقروء',
            'data': {
                'unread_count': unread_count
            }
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'خطأ في تحديث الإشعار: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_all_notifications_as_read(request):
    """
    تمييز جميع الإشعارات كمقروءة
    """
    try:
        # التحقق من أن المستخدم موصل
        if not getattr(request.user, 'is_delivery', False):
            return Response({
                'success': False,
                'message': 'غير مصرح لك بالوصول لهذه البيانات'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # تحديث جميع الإشعارات غير المقروءة
        updated_count = DriverNotification.objects.filter(
            driver=request.user,
            is_read=False
        ).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
        ).update(
            is_read=True,
            read_at=timezone.now()
        )
        
        return Response({
            'success': True,
            'message': f'تم تمييز {updated_count} إشعار كمقروء',
            'data': {
                'updated_count': updated_count,
                'unread_count': 0
            }
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'خطأ في تحديث الإشعارات: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_notification(request, notification_id):
    """
    حذف إشعار
    """
    try:
        # التحقق من أن المستخدم موصل
        if not getattr(request.user, 'is_delivery', False):
            return Response({
                'success': False,
                'message': 'غير مصرح لك بالوصول لهذه البيانات'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # البحث عن الإشعار
        notification = get_object_or_404(
            DriverNotification,
            id=notification_id,
            driver=request.user
        )
        
        # حذف الإشعار
        notification.delete()
        
        # إحصائيات محدثة
        unread_count = DriverNotification.objects.filter(
            driver=request.user,
            is_read=False
        ).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
        ).count()
        
        return Response({
            'success': True,
            'message': 'تم حذف الإشعار',
            'data': {
                'unread_count': unread_count
            }
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'خطأ في حذف الإشعار: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_notifications_count(request):
    """
    جلب عدد الإشعارات غير المقروءة
    """
    try:
        # التحقق من أن المستخدم موصل
        if not getattr(request.user, 'is_delivery', False):
            return Response({
                'success': False,
                'message': 'غير مصرح لك بالوصول لهذه البيانات'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # عدد الإشعارات غير المقروءة
        unread_count = DriverNotification.objects.filter(
            driver=request.user,
            is_read=False
        ).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
        ).count()
        
        # إجمالي الإشعارات
        total_count = DriverNotification.objects.filter(
            driver=request.user
        ).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
        ).count()
        
        return Response({
            'success': True,
            'data': {
                'unread_count': unread_count,
                'total_count': total_count
            }
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'خطأ في جلب عدد الإشعارات: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
