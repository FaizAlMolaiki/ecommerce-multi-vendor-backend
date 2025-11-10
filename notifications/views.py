from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db import transaction, IntegrityError
import logging

logger = logging.getLogger(__name__)

from .models import Notification, FCMDevice, NotificationTemplate
from .serializers import (
    NotificationSerializer, 
    FCMDeviceSerializer, 
    NotificationTemplateSerializer,
    NotificationCreateSerializer,
    NotificationStatsSerializer
)
from .services import NotificationService


class NotificationPagination(PageNumberPagination):
    """تخصيص pagination للإشعارات"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class NotificationListView(generics.ListAPIView):
    """عرض قائمة إشعارات المستخدم"""
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = NotificationPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['type', 'priority', 'is_read']
    search_fields = ['title', 'body']
    ordering_fields = ['created_at', 'priority']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """الحصول على إشعارات المستخدم الحالي فقط"""
        # Fix: N+1 Query - إضافة select_related('user') لتحسين الأداء
        queryset = Notification.objects.filter(user=self.request.user).select_related('user')
        
        # فلترة حسب حالة القراءة
        is_read = self.request.query_params.get('is_read')
        if is_read is not None:
            queryset = queryset.filter(is_read=is_read.lower() == 'true')
            
        # فلترة حسب النوع
        notification_type = self.request.query_params.get('type')
        if notification_type:
            queryset = queryset.filter(type=notification_type)
            
        # فلترة حسب الأولوية
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
            
        return queryset


class NotificationDetailView(generics.RetrieveAPIView):
    """عرض تفاصيل إشعار محدد"""
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
    
    def retrieve(self, request, *args, **kwargs):
        """تعليم الإشعار كمقروء عند عرضه"""
        instance = self.get_object()
        if not instance.is_read:
            instance.mark_as_read()
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_notification_as_read(request, notification_id):
    """تعليم إشعار محدد كمقروء"""
    try:
        notification = get_object_or_404(
            Notification, 
            id=notification_id, 
            user=request.user
        )
        notification.mark_as_read()
        
        return Response({
            'success': True,
            'message': 'تم تعليم الإشعار كمقروء'
        })
    except Notification.DoesNotExist:
        logger.warning(f"Notification {notification_id} not found for user {request.user.id}")
        return Response({
            'success': False,
            'error': 'الإشعار غير موجود'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error marking notification {notification_id} as read: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': 'حدث خطأ أثناء تحديث الإشعار'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_all_as_read(request):
    """تعليم جميع إشعارات المستخدم كمقروءة"""
    try:
        updated_count = NotificationService.mark_all_as_read(request.user)
        
        return Response({
            'success': True,
            'message': f'تم تعليم {updated_count} إشعار كمقروء',
            'updated_count': updated_count
        })
    except Exception as e:
        logger.error(f"Error marking all notifications as read for user {request.user.id}: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': 'حدث خطأ أثناء تحديث الإشعارات'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def delete_notification(request, notification_id):
    """حذف إشعار محدد"""
    try:
        notification = get_object_or_404(
            Notification, 
            id=notification_id, 
            user=request.user
        )
        notification.delete()
        
        return Response({
            'success': True,
            'message': 'تم حذف الإشعار'
        })
    except Notification.DoesNotExist:
        logger.warning(f"Notification {notification_id} not found for deletion by user {request.user.id}")
        return Response({
            'success': False,
            'error': 'الإشعار غير موجود'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error deleting notification {notification_id}: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': 'حدث خطأ أثناء حذف الإشعار'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def delete_all_read_notifications(request):
    """حذف جميع الإشعارات المقروءة"""
    try:
        deleted_count = request.user.notifications.filter(is_read=True).delete()[0]
        
        return Response({
            'success': True,
            'message': f'تم حذف {deleted_count} إشعار مقروء',
            'deleted_count': deleted_count
        })
    except Exception as e:
        logger.error(f"Error deleting read notifications for user {request.user.id}: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': 'حدث خطأ أثناء حذف الإشعارات'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def notification_stats(request):
    """الحصول على إحصائيات إشعارات المستخدم"""
    try:
        stats = NotificationService.get_user_notification_stats(request.user)
        serializer = NotificationStatsSerializer(stats)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
    except Exception as e:
        logger.error(f"Error getting notification stats for user {request.user.id}: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': 'حدث خطأ أثناء جلب الإحصائيات'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def unread_notification_count(request):
    """الحصول على عدد الإشعارات غير المقروءة"""
    try:
        unread_count = request.user.notifications.filter(is_read=False).count()
        
        return Response({
            'unread_count': unread_count
        })
    except Exception as e:
        logger.error(f"Error getting unread count for user {request.user.id}: {str(e)}", exc_info=True)
        return Response({
            'unread_count': 0
        }, status=status.HTTP_200_OK)  # Return 0 on error instead of 500


class FCMDeviceCreateView(generics.CreateAPIView):
    """تسجيل جهاز FCM جديد"""
    serializer_class = FCMDeviceSerializer
    permission_classes = [permissions.AllowAny]  # السماح للجميع بتسجيل الأجهزة
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Fix: Race Condition - استخدام get_or_create مع transaction.atomic
        لمنع إنشاء أجهزة مكررة عند الطلبات المتزامنة
        """
        registration_token = request.data.get('registration_token')
        
        if not registration_token:
            return Response({
                'success': False,
                'error': 'رمز التسجيل مطلوب'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # استخدام get_or_create بدلاً من filter().first()
            device, created = FCMDevice.objects.get_or_create(
                registration_token=registration_token,
                defaults={
                    'device_type': request.data.get('device_type', 'android'),
                    'device_name': request.data.get('device_name', ''),
                    'user': request.user if request.user.is_authenticated else None,
                    'last_used_at': timezone.now(),
                    'is_active': True
                }
            )
            
            if not created:
                # تحديث الجهاز الموجود
                device.device_type = request.data.get('device_type', device.device_type)
                device.device_name = request.data.get('device_name', device.device_name)
                device.last_used_at = timezone.now()
                device.is_active = True
                
                if request.user.is_authenticated:
                    device.user = request.user
                
                device.save()
                
                logger.info(f"Updated existing FCM device {device.id} for user {device.user.id if device.user else 'anonymous'}")
                
                return Response({
                    'success': True,
                    'message': 'تم تحديث الجهاز بنجاح',
                    'device_id': device.id
                }, status=status.HTTP_200_OK)
            else:
                logger.info(f"Created new FCM device {device.id} for user {device.user.id if device.user else 'anonymous'}")
                
                return Response({
                    'success': True,
                    'message': 'تم تسجيل الجهاز بنجاح',
                    'device_id': device.id
                }, status=status.HTTP_201_CREATED)
                
        except IntegrityError as e:
            # في حالة حدوث خطأ integrity (نادر جداً مع get_or_create + transaction)
            logger.error(f"IntegrityError creating FCM device: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': 'حدث خطأ في تسجيل الجهاز. يرجى المحاولة مرة أخرى'
            }, status=status.HTTP_409_CONFLICT)
        except Exception as e:
            logger.error(f"Error creating/updating FCM device: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': 'حدث خطأ أثناء معالجة الطلب'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def update_fcm_token(request):
    """تحديث رمز FCM للجهاز"""
    try:
        old_token = request.data.get('old_token')
        new_token = request.data.get('new_token')
        
        if not old_token or not new_token:
            return Response({
                'success': False,
                'error': 'مطلوب الرمز القديم والجديد'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # البحث عن الجهاز بالرمز القديم
        device = FCMDevice.objects.filter(
            user=request.user,
            registration_token=old_token
        ).first()
        
        if device:
            device.registration_token = new_token
            device.last_used_at = timezone.now()
            device.save()
            
            logger.info(f"FCM token updated for user {request.user.id}")
            
            return Response({
                'success': True,
                'message': 'تم تحديث رمز الجهاز'
            })
        else:
            logger.warning(f"FCM device not found for user {request.user.id} with old_token")
            return Response({
                'success': False,
                'error': 'الجهاز غير موجود'
            }, status=status.HTTP_404_NOT_FOUND)
            
    except IntegrityError as e:
        logger.error(f"IntegrityError updating FCM token for user {request.user.id}: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': 'الرمز الجديد مستخدم بالفعل'
        }, status=status.HTTP_409_CONFLICT)
    except Exception as e:
        logger.error(f"Error updating FCM token for user {request.user.id}: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': 'حدث خطأ أثناء تحديث رمز الجهاز'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def deactivate_fcm_device(request):
    """إلغاء تفعيل جهاز FCM"""
    try:
        token = request.data.get('token')
        
        if not token:
            return Response({
                'success': False,
                'error': 'مطلوب رمز الجهاز'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        updated_count = FCMDevice.objects.filter(
            user=request.user,
            registration_token=token
        ).update(is_active=False)
        
        if updated_count > 0:
            logger.info(f"FCM device deactivated for user {request.user.id}")
            return Response({
                'success': True,
                'message': 'تم إلغاء تفعيل الجهاز'
            })
        else:
            logger.warning(f"FCM device not found for deactivation by user {request.user.id}")
            return Response({
                'success': False,
                'error': 'الجهاز غير موجود'
            }, status=status.HTTP_404_NOT_FOUND)
            
    except Exception as e:
        logger.error(f"Error deactivating FCM device for user {request.user.id}: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': 'حدث خطأ أثناء إلغاء تفعيل الجهاز'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Views للمشرفين فقط
class NotificationCreateView(generics.CreateAPIView):
    """إنشاء إشعار جديد (للمشرفين فقط)"""
    serializer_class = NotificationCreateSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        notification = serializer.save()
        
        return Response({
            'success': True,
            'message': 'تم إرسال الإشعار بنجاح',
            'notification_id': notification.id if notification else None
        }, status=status.HTTP_201_CREATED)


class NotificationTemplateListCreateView(generics.ListCreateAPIView):
    """عرض وإنشاء قوالب الإشعارات (للمشرفين فقط)"""
    queryset = NotificationTemplate.objects.all()
    serializer_class = NotificationTemplateSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['type', 'is_active']
    search_fields = ['name', 'title_template']


class NotificationTemplateDetailView(generics.RetrieveUpdateDestroyAPIView):
    """تفاصيل وتحديث وحذف قالب إشعار (للمشرفين فقط)"""
    queryset = NotificationTemplate.objects.all()
    serializer_class = NotificationTemplateSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, permissions.IsAdminUser])
def send_template_notification(request):
    """
    إرسال إشعار من قالب
    
    Body:
    {
        "template_name": "order_confirmed",  // أو template_id
        "user_ids": [1, 2, 3],  // اختياري - إذا لم يُرسل، سيُرسل للجميع
        "context_data": {  // البيانات الديناميكية
            "order_id": "123",
            "total": "500"
        },
        "send_fcm": true,  // اختياري - افتراضياً true
        "send_email": false  // اختياري - افتراضياً false
    }
    """
    try:
        template_identifier = request.data.get('template_name') or request.data.get('template_id')
        user_ids = request.data.get('user_ids')
        context_data = request.data.get('context_data', {})
        send_fcm = request.data.get('send_fcm', True)
        send_email = request.data.get('send_email', False)
        
        if not template_identifier:
            return Response({
                'success': False,
                'error': 'يجب تحديد template_name أو template_id'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # إرسال الإشعارات
        notifications = NotificationService.send_template_notification(
            template_name_or_id=template_identifier,
            user_ids=user_ids,
            context_data=context_data,
            send_fcm=send_fcm,
            send_email=send_email
        )
        
        return Response({
            'success': True,
            'message': f'تم إرسال {len(notifications)} إشعار بنجاح',
            'count': len(notifications)
        }, status=status.HTTP_200_OK)
        
    except NotificationTemplate.DoesNotExist:
        logger.warning(f"Template not found for identifier: {template_identifier}")
        return Response({
            'success': False,
            'error': 'القالب غير موجود'
        }, status=status.HTTP_404_NOT_FOUND)
    except KeyError as e:
        logger.error(f"Missing template variable: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': 'بيانات القالب غير مكتملة. يرجى التحقق من المتغيرات المطلوبة'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error sending template notification: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': 'حدث خطأ أثناء إرسال الإشعارات'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
