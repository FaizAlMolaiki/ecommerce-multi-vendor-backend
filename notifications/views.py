from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone
from django.shortcuts import get_object_or_404

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
        queryset = Notification.objects.filter(user=self.request.user)
        
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
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


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
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


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
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


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
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


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
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


class FCMDeviceCreateView(generics.CreateAPIView):
    """تسجيل جهاز FCM جديد"""
    serializer_class = FCMDeviceSerializer
    permission_classes = [permissions.AllowAny]  # السماح للجميع بتسجيل الأجهزة
    
    def create(self, request, *args, **kwargs):
        registration_token = request.data.get('registration_token')
        
        # البحث عن جهاز موجود بنفس الـ token
        device = FCMDevice.objects.filter(registration_token=registration_token).first()
        
        if device:
            # تحديث الجهاز الموجود
            serializer = self.get_serializer(device, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            
            # تحديث المستخدم والبيانات الأخرى
            if request.user.is_authenticated:
                device = serializer.save(user=request.user, last_used_at=timezone.now(), is_active=True)
            else:
                device = serializer.save(last_used_at=timezone.now(), is_active=True)
            
            return Response({
                'success': True,
                'message': 'تم تحديث الجهاز بنجاح',
                'device_id': device.id
            }, status=status.HTTP_200_OK)
        else:
            # إنشاء جهاز جديد
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            if request.user.is_authenticated:
                device = serializer.save(user=request.user, last_used_at=timezone.now())
            else:
                device = serializer.save(user=None, last_used_at=timezone.now())
            
            return Response({
                'success': True,
                'message': 'تم تسجيل الجهاز بنجاح',
                'device_id': device.id
            }, status=status.HTTP_201_CREATED)


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
            
            return Response({
                'success': True,
                'message': 'تم تحديث رمز الجهاز'
            })
        else:
            return Response({
                'success': False,
                'error': 'الجهاز غير موجود'
            }, status=status.HTTP_404_NOT_FOUND)
            
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


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
            return Response({
                'success': True,
                'message': 'تم إلغاء تفعيل الجهاز'
            })
        else:
            return Response({
                'success': False,
                'error': 'الجهاز غير موجود'
            }, status=status.HTTP_404_NOT_FOUND)
            
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


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
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
