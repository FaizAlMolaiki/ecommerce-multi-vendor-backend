
from rest_framework.views import APIView
from rest_framework.response import Response



from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from driver.models import User, DeliveryProfile
from driver.permissions import IsDeliveryUser
from rest_framework.permissions import IsAuthenticated
from driver.serializer import DeliveryProfileSerializer
from rest_framework import status  ,viewsets
from orders.models import Order 
# from orders.serializers import OrderReadSerializer
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser
# from rest_framework.authentication import jwt
from rest_framework_simplejwt.authentication import JWTAuthentication
# ===== إضافة WebSocket للموصل - بداية التعديل =====
from project.driver_notifications_service import (
    notify_new_order_available, 
    notify_order_assigned, 
    notify_order_cancelled,
    notify_driver,
    notify_all_drivers
)
# ===== إضافة WebSocket للموصل - نهاية التعديل =====

MAX_VERIFY_ATTEMPTS = 5
# ثابت لمدة صلاحية رمز إعادة التعيين الذي سيتم إنشاؤه (مثلاً 10 دقائق)
RESET_TOKEN_TIMEOUT_SECONDS = 10 * 60



class ApplyDeliveryView(APIView):
    """تطبيق الموصل للانضمام كسائق توصيل"""
    
    def post(self, request):
        try:
            # استخراج البيانات من الطلب
            data = request.data
            
            # التحقق من البيانات المطلوبة
            required_fields = ['first_name', 'last_name', 'phone', 'email', 'password']
            for field in required_fields:
                if not data.get(field):
                    return Response(
                        {'error': f'الحقل {field} مطلوب'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # التحقق من عدم وجود المستخدم مسبقاً
            if User.objects.filter(email=data['email']).exists():
                return Response(
                    {'error': 'البريد الإلكتروني مسجل مسبقاً'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if User.objects.filter(phone_number=data['phone']).exists():
                return Response(
                    {'error': 'رقم الهاتف مسجل مسبقاً'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # إنشاء المستخدم
            user = User.objects.create_user(
                email=data['email'],
                password=data['password'],
                name=f"{data['first_name']} {data['last_name']}",
                phone_number=data['phone'],
                is_delivery=True,
                is_verified=False  # سيتم التحقق لاحقاً من قبل الإدارة
            )
            
            # إنشاء ملف الموصل
            delivery_profile = DeliveryProfile.objects.create(
                user=user,
                vehicle_type=data.get('delivery_type', 'motorcycle'),
                verification_status=DeliveryProfile.VerificationStatus.PENDING
            )
            
            # حفظ الصور إذا كانت موجودة
            if 'profile_image' in request.FILES:
                # يمكن إضافة حقل profile_image للمستخدم أو DeliveryProfile
                pass
                
            if 'identity_image' in request.FILES:
                delivery_profile.id_card_image = request.FILES['identity_image']
                delivery_profile.save()
            
            return Response({
                'message': 'تم تقديم طلب الانضمام بنجاح! سيتم مراجعة طلبك قريباً',
                'user_id': user.id,
                'status': 'pending_review'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': f'حدث خطأ أثناء معالجة الطلب: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# class DeliveryApplicationView(APIView):
#     permission_classes = [IsAuthenticated]
#     parser_classes = [MultiPartParser, FormParser]  # لدعم رفع الملفات

#     def get(self, request):
#         """
#         التحقق من حالة طلب التوصيل للمستخدم الحالي.
#         """
#         try:
#             profile = DeliveryProfile.objects.get(user=request.user)
#             serializer = DeliveryProfileSerializer(profile, context={'request': request})
#             return Response(serializer.data)
#         except DeliveryProfile.DoesNotExist:
#             return Response({"message": "لم تقم بتقديم طلب بعد."}, status=status.HTTP_404_NOT_FOUND)

#     def post(self, request):
#         """
#         إنشاء طلب توصيل جديد.
#         """
#         serializer = DeliveryProfileSerializer(data=request.data, context={'request': request})
#         if serializer.is_valid():
#             serializer.save(user=request.user)
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
       
       
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')
class SetAvailabilityView(APIView):
    permission_classes = [IsAuthenticated, IsDeliveryUser]

    def post(self, request):
        """
        Toggles the 'is_available' status for the delivery person.
        """
        user = request.user
        print(f"DEBUG: user={user}, is_authenticated={user.is_authenticated}")
        try:
            profile = request.user.deliveryprofile
            
            if profile.delivery_state == DeliveryProfile.DeliveryState.AVAILABLE:
                profile.delivery_state=DeliveryProfile.DeliveryState.UNAVAILABLE
            elif profile.delivery_state== DeliveryProfile.DeliveryState.UNAVAILABLE:
                profile.delivery_state=DeliveryProfile.DeliveryState.AVAILABLE
            print(f"DEBUG: found profile {profile}")
            profile.save(update_fields=['delivery_state'])
            return Response({'is_available':profile.delivery_state}, status=status.HTTP_200_OK)
        except DeliveryProfile.DoesNotExist:
            print("DEBUG: DeliveryProfile.DoesNotExist")
            return Response({'error': 'Delivery profile not found.'}, status=status.HTTP_404_NOT_FOUND)

class DriverAvailabilityStatus(APIView):
    permission_classes = [IsAuthenticated, IsDeliveryUser]

    def get(self, request):
        """
        Toggles the 'is_available' status for the delivery person.
        """
        user = request.user
        print(f"DEBUG: user={user}, is_authenticated={user.is_authenticated}")
        try:
            profile = request.user.deliveryprofile
            # profile.is_available = not profile.is_available
            print(f"DEBUG: found profile {profile}")
            # //profile.save(update_fields=['is_available'])
            return Response({'is_available': profile.delivery_state}, status=status.HTTP_200_OK)
        except DeliveryProfile.DoesNotExist:
            print("DEBUG: DeliveryProfile.DoesNotExist")
            return Response({'error': 'Delivery profile not found.'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_driver_current_orders(request):
    """جلب الطلبات الحالية للموصل"""
    
    # التحقق من أن المستخدم موصل
    if not request.user.is_delivery:
        return Response(
            {'error': 'غير مصرح لك بالوصول لهذه البيانات'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        # جلب الطلبات المخصصة للموصل والتي لم يتم تسليمها بعد
        current_orders = Order.objects.filter(
            delivery_agent=request.user,
            fulfillment_status__in=[
                Order.FulfillmentStatus.ACCEPTED,
                Order.FulfillmentStatus.PREPARING,
                Order.FulfillmentStatus.SHIPPED
            ]
        ).select_related('user', 'store').prefetch_related('items__variant__product')
        
        # تحويل البيانات للتنسيق المطلوب
        orders_data = []
        for order in current_orders:
            order_data = {
                'id': str(order.id),
                'order_number': f'ORD-{order.id:06d}',
                'customer': {
                    'id': str(order.user.id) if order.user else '',
                    'name': order.user.name if order.user else 'عميل ضيف',
                    'phone': order.user.phone_number if order.user else '',
                },
                'delivery_address': {
                    'id': '1',
                    'full_address': order.shipping_address_snapshot.get('street', '') + ', ' + 
                                   order.shipping_address_snapshot.get('city', ''),
                    'building_number': order.shipping_address_snapshot.get('building_number', ''),
                    'floor': order.shipping_address_snapshot.get('floor', ''),
                    'apartment': order.shipping_address_snapshot.get('apartment', ''),
                    # 'latitude': order.shipping_address_snapshot.get('latitude'),
                    # 'longitude': order.shipping_address_snapshot.get('longitude'),
                   'latitude': float(order.shipping_address_snapshot.get('latitude')) ,
                    'longitude': float(order.shipping_address_snapshot.get('longitude')) ,

                },
                'items': [
                    {
                        'id': str(item.id),
                        'name': item.product_name_snapshot,
                        'quantity': item.quantity,
                        'price': float(item.price_at_purchase),
                    }
                    for item in order.items.filter(status=order.items.model.Status.ACTIVE)
                ],
                'status': _map_order_status(order.fulfillment_status),
                'order_date': order.created_at.isoformat(),
                'subtotal': float(order.grand_total - order.delivery_fee),
                'delivery_fee': float(order.delivery_fee),
                'total_amount': float(order.grand_total),
                'restaurant_name': order.store.name if order.store else '',
                'estimated_delivery_time': 30,  # يمكن حسابها بناءً على المسافة
                'payment_method': 'cash',  # يمكن إضافة هذا الحقل للنموذج
                'is_paid': order.payment_status == Order.PaymentStatus.PAID,
            }
            orders_data.append(order_data)
        
        return Response({
            'orders': orders_data,
            'count': len(orders_data)
        })
        
    except Exception as e:
        return Response(
            {'error': f'حدث خطأ أثناء جلب الطلبات: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_driver_available_orders(request):
    """جلب الطلبات المتاحة للموصل"""
    
    if not request.user.is_delivery:
        return Response(
            {'error': 'غير مصرح لك بالوصول لهذه البيانات'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        # جلب الطلبات المقبولة والتي لم يتم تخصيص موصل لها بعد
        available_orders = Order.objects.filter(
            delivery_agent__isnull=True,
            fulfillment_status=Order.FulfillmentStatus.ACCEPTED
        ).select_related('user', 'store').prefetch_related('items__variant__product')
        
        orders_data = []
        for order in available_orders:
            order_data = {
                'id': str(order.id),
                'order_number': f'ORD-{order.id:06d}',
                'customer': {
                    'id': str(order.user.id) if order.user else '',
                    'name': order.user.name if order.user else 'عميل ضيف',
                    'phone': order.user.phone_number if order.user else '',
                },
                'delivery_address': {
                    'id': '1',
                    'full_address': order.shipping_address_snapshot.get('street', '') + ', ' + 
                                   order.shipping_address_snapshot.get('city', ''),
                    'building_number': order.shipping_address_snapshot.get('building_number', ''),
                    'floor': order.shipping_address_snapshot.get('floor', ''),
                    'apartment': order.shipping_address_snapshot.get('apartment', ''),
                    'latitude': order.shipping_address_snapshot.get('latitude'),
                    'longitude': order.shipping_address_snapshot.get('longitude'),
                },
                'items': [
                    {
                        'id': str(item.id),
                        'name': item.product_name_snapshot,
                        'quantity': item.quantity,
                        'price': float(item.price_at_purchase),
                    }
                    for item in order.items.filter(status=order.items.model.Status.ACTIVE)
                ],
                'status': 'accepted',
                'order_date': order.created_at.isoformat(),
                'subtotal': float(order.grand_total - order.delivery_fee),
                'delivery_fee': float(order.delivery_fee),
                'total_amount': float(order.grand_total),
                'restaurant_name': order.store.name if order.store else '',
                'estimated_delivery_time': 30,
                'payment_method': 'cash',
                'is_paid': order.payment_status == Order.PaymentStatus.PAID,
            }
            orders_data.append(order_data)
        
        return Response({
            'orders': orders_data,
            'count': len(orders_data)
        })
        
    except Exception as e:
        return Response(
            {'error': f'حدث خطأ أثناء جلب الطلبات المتاحة: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_order_status(request):
    """تحديث حالة الطلب من قبل الموصل"""
    
    if not request.user.is_delivery:
        return Response(
            {'error': 'غير مصرح لك بالوصول لهذه البيانات'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        order_id = request.data.get('order_id')
        new_status = request.data.get('status')
       
        
        if not order_id or not new_status:
            return Response(
                {'error': 'معرف الطلب والحالة الجديدة مطلوبان'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # جلب الطلب والتحقق من أنه مخصص للموصل
        try:
            order = Order.objects.get(id=order_id, delivery_agent=request.user)
        except Order.DoesNotExist:
            return Response(
                {'error': 'الطلب غير موجود أو غير مخصص لك'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # تحديث حالة الطلب
        status_mapping = {
            'preparing': Order.FulfillmentStatus.PREPARING,
            'on_the_way': Order.FulfillmentStatus.SHIPPED,
            'delivered': Order.FulfillmentStatus.DELIVERED,
        }
        print('xxxxxx')
        print(new_status)
        if new_status not in status_mapping:
            return Response(
                {'error': 'حالة غير صحيحة'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.fulfillment_status = status_mapping[new_status]
        order.save()
        
        # ===== إضافة WebSocket للموصل - بداية التعديل =====
        # إرسال إشعار للعميل عبر WebSocket (يمكن إضافة هذا لاحقاً)
        # وإشعار لوحة التحكم بتحديث الطلب
        status_messages = {
            'preparing': 'الموصل بدأ في تحضير طلبك',
            'on_the_way': 'الموصل في الطريق إليك',
            'delivered': 'تم تسليم الطلب بنجاح',
        }
        
        # إشعار الموصل بنجاح التحديث
        notify_driver(
            request.user.id,
            'تحديث الطلب',
            f'تم تحديث حالة الطلب #{order.id} إلى: {status_messages.get(new_status, new_status)}'
        )
        # ===== إضافة WebSocket للموصل - نهاية التعديل =====
        
        return Response({
            'message': 'تم تحديث حالة الطلب بنجاح',
            'order_id': order_id,
            'new_status': new_status
        })
        
    except Exception as e:
        return Response(
            {'error': f'حدث خطأ أثناء تحديث الطلب: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_order(request):
    """قبول طلب متاح من قبل الموصل"""
    
    if not request.user.is_delivery:
        return Response(
            {'error': 'غير مصرح لك بالوصول لهذه البيانات'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        order_id = request.data.get('order_id')
        
        if not order_id:
            return Response(
                {'error': 'معرف الطلب مطلوب'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # جلب الطلب والتحقق من أنه متاح
        try:
            order = Order.objects.get(
                id=order_id, 
                delivery_agent__isnull=True,
                fulfillment_status=Order.FulfillmentStatus.ACCEPTED
            )
        except Order.DoesNotExist:
            return Response(
                {'error': 'الطلب غير متاح أو تم قبوله من موصل آخر'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # تخصيص الطلب للموصل
        order.delivery_agent = request.user
        order.save()
        
        # ===== إضافة WebSocket للموصل - بداية التعديل =====
        # إرسال إشعار للموصل بتأكيد قبول الطلب
        notify_order_assigned(order, request.user)
        
        # إشعار باقي الموصلين أن الطلب لم يعد متاحاً
        notify_order_cancelled(order_id, driver_id=None)
        # ===== إضافة WebSocket للموصل - نهاية التعديل =====
        
        return Response({
            'message': 'تم قبول الطلب بنجاح',
            'order_id': order_id
        })
        
    except Exception as e:
        return Response(
            {'error': f'حدث خطأ أثناء قبول الطلب: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def _map_order_status(django_status):
    """تحويل حالة الطلب من Django إلى Flutter"""
    status_mapping = {
        Order.FulfillmentStatus.ACCEPTED: 'accepted',
        Order.FulfillmentStatus.PREPARING: 'preparing',
        Order.FulfillmentStatus.SHIPPED: 'on_the_way',
        Order.FulfillmentStatus.DELIVERED: 'delivered',
        Order.FulfillmentStatus.REJECTED: 'cancelled',
    }
    return status_mapping.get(django_status, 'accepted')
