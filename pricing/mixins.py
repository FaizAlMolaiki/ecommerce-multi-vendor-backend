"""
ViewSet Mixins for Pricing Application
========================================
يحتوي هذا الملف على جميع الـ Mixins المشتركة التي يمكن استخدامها
مع أي ViewSet في تطبيق التسعير.
"""

import logging
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response


logger = logging.getLogger(__name__)


class ApprovalMixin:
    """
    Mixin شامل لإضافة وظائف الموافقة والرفض والإجراءات المشتركة.
    
    يوفر الدوال التالية:
    - approve(): الموافقة على عرض/كوبون (للمسؤولين فقط)
    - reject(): رفض عرض/كوبون (للمسؤولين فقط)
    - toggle_status(): تفعيل/تعطيل عرض/كوبون (للبائع)
    - perform_destroy(): حذف عرض/كوبون (للبائع)
    
    الاستخدام:
    ```python
    class PromotionViewSet(ApprovalMixin, viewsets.ModelViewSet):
        queryset = Promotion.objects.all()
        serializer_class = PromotionSerializer
    ```
    
    متطلبات:
    - يجب أن يكون الموديل يحتوي على الحقول:
      * approval_status
      * reviewed_at
      * reviewed_by
      * rejection_reason
      * active
    """
    
    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        """
        الموافقة على العرض/الكوبون - للمسؤولين فقط.
        
        Endpoint: POST /api/v1/pricing/{model}/{id}/approve/
        
        Permissions:
        - is_staff=True أو is_superuser=True
        
        Response:
        ```json
        {
            "success": true,
            "message": "تمت الموافقة على العرض بنجاح",
            "data": {...}
        }
        ```
        """
        # التحقق من أن المستخدم هو مسؤول
        if not request.user.is_staff and not request.user.is_superuser:
            return Response(
                {'error': 'هذه العملية متاحة للمسؤولين فقط'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            instance = self.get_object()
            
            # تحديث حالة الموافقة
            instance.approval_status = 'APPROVED'
            instance.reviewed_at = timezone.now()
            instance.reviewed_by = request.user
            instance.rejection_reason = ''  # مسح سبب الرفض إن وجد
            instance.save()
            
            serializer = self.get_serializer(instance)
            return Response({
                'success': True,
                'message': f'تمت الموافقة على {self._get_item_name()} بنجاح',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"خطأ في الموافقة على {self._get_item_name()} {pk}: {e}", exc_info=True)
            return Response(
                {'error': 'حدث خطأ غير متوقع'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        """
        رفض العرض/الكوبون - للمسؤولين فقط.
        
        Endpoint: POST /api/v1/pricing/{model}/{id}/reject/
        
        Permissions:
        - is_staff=True أو is_superuser=True
        
        Body:
        ```json
        {
            "reason": "سبب الرفض (اختياري)"
        }
        ```
        
        Response:
        ```json
        {
            "success": true,
            "message": "تم رفض العرض",
            "data": {...}
        }
        ```
        """
        # التحقق من أن المستخدم هو مسؤول
        if not request.user.is_staff and not request.user.is_superuser:
            return Response(
                {'error': 'هذه العملية متاحة للمسؤولين فقط'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            instance = self.get_object()
            rejection_reason = request.data.get('reason', '')
            
            # تحديث حالة الرفض
            instance.approval_status = 'REJECTED'
            instance.reviewed_at = timezone.now()
            instance.reviewed_by = request.user
            instance.rejection_reason = rejection_reason
            instance.save()
            
            serializer = self.get_serializer(instance)
            return Response({
                'success': True,
                'message': f'تم رفض {self._get_item_name()}',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"خطأ في رفض {self._get_item_name()} {pk}: {e}", exc_info=True)
            return Response(
                {'error': 'حدث خطأ غير متوقع'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'], url_path='toggle-status')
    def toggle_status(self, request, pk=None):
        """
        تغيير حالة التفعيل (active) للعرض/الكوبون.
        
        Endpoint: POST /api/v1/pricing/{model}/{id}/toggle-status/
        
        Permissions:
        - يجب أن يكون البائع مالك العرض (IsObjectOwner)
        
        Response:
        ```json
        {
            "id": 1,
            "name": "خصم الصيف",
            "active": false,
            ...
        }
        ```
        """
        try:
            instance = self.get_object()
            
            # عكس قيمة الحقل 'active'
            instance.active = not instance.active
            instance.save()
            
            serializer = self.get_serializer(instance)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except self.queryset.model.DoesNotExist:
            return Response(
                {'error': f'{self._get_item_name()} غير موجود'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"خطأ في تغيير حالة {self._get_item_name()} {pk}: {e}", exc_info=True)
            return Response(
                {'error': 'حدث خطأ غير متوقع'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def perform_destroy(self, instance):
        """
        حذف العرض/الكوبون.
        
        ملاحظة:
        - يتم التحقق من الملكية تلقائياً عبر IsObjectOwner
        - يُستدعى تلقائياً عند استخدام DELETE method
        """
        instance.delete()
    
    def _get_item_name(self):
        """
        الحصول على اسم العنصر بالعربية للاستخدام في الرسائل.
        
        Returns:
            str: اسم العنصر بالعربية
        """
        model_name = self.queryset.model.__name__
        names = {
            'Promotion': 'العرض الترويجي',
            'Coupon': 'الكوبون',
            'Offer': 'العرض الخاص'
        }
        return names.get(model_name, 'العنصر')
