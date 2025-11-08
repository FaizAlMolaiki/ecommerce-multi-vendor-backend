from django.db import transaction
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.pagination import PageNumberPagination

from .models import CartItem, Order, OrderItem
from .serializers import (
    CartItemSerializer,
    OrderReadSerializer,
    CreateOrderSerializer,
)


class IsAuthenticated(permissions.IsAuthenticated):
    pass


class OrderPagination(PageNumberPagination):
    """Pagination للطلبات - 20 طلب في كل صفحة"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class CartItemViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CartItemSerializer

    def get_queryset(self):
        return CartItem.objects.filter(user=self.request.user).select_related(
            'variant', 'variant__product', 'variant__product__store'
        )

    def perform_create(self, serializer):
        serializer.save()


class CreateOrderView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = CreateOrderSerializer(
            data=request.data,
            context={'request': request}  # ✅ إضافة context
        )
        serializer.is_valid(raise_exception=True)

        user = request.user
        cart_items = list(
            CartItem.objects.filter(user=user)
            .select_related('variant', 'variant__product', 'variant__product__store')
        )

        if not cart_items:
            return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ الحصول على shipping_address من address_id أو مباشرة
        shipping_address = serializer.validated_data.get('shipping_address')
        if not shipping_address and 'address' in serializer.context:
            # تحويل UserAddress إلى dict
            address = serializer.context['address']
            shipping_address = {
                'label': address.label,
                'city': address.city,
                'street': address.street,
                'landmark': address.landmark,
                'latitude': str(address.latitude) if address.latitude else None,
                'longitude': str(address.longitude) if address.longitude else None,
            }

        # Create separate Order per store, add items, and compute totals
        created_orders = []
        store_groups = {}
        for ci in cart_items:
            store = ci.variant.product.store
            store_groups.setdefault(store.id, {'store': store, 'items': []})['items'].append(ci)

        for store_id, data in store_groups.items():
            order = Order.objects.create(
                user=user,
                store=data['store'],
                grand_total=0,
                shipping_address_snapshot=shipping_address,
            )

            total = 0
            for ci in data['items']:
                price = ci.variant.price
                qty = ci.quantity
                OrderItem.objects.create(
                    order=order,
                    variant=ci.variant,
                    quantity=qty,
                    price_at_purchase=price,
                    product_name_snapshot=ci.variant.product.name,
                    variant_options_snapshot=ci.variant.options or {},
                )
                total += price * qty

            order.grand_total = total
            order.save(update_fields=['grand_total'])
            # الإشعارات تُرسل تلقائياً عبر signals.py
            created_orders.append(order)

        # clear cart
        CartItem.objects.filter(user=user).delete()

        # Return list of created orders (one per store)
        return Response({'orders': [OrderReadSerializer(o).data for o in created_orders]}, status=status.HTTP_201_CREATED)


class MyOrdersListView(ListAPIView):
    """قائمة طلبات المستخدم مع Pagination"""
    permission_classes = [IsAuthenticated]
    serializer_class = OrderReadSerializer
    pagination_class = OrderPagination  # ✅ إضافة Pagination

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related(
            'items'
        ).select_related('store').order_by('-created_at')  # ✅ ترتيب الأحدث أولاً


class OrderDetailView(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderReadSerializer
    lookup_url_kwarg = 'order_id'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related('items').select_related('store')


# StoreOrder status update view removed in unified model design.


class MarkOrderPaidView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

        order.payment_status = Order.PaymentStatus.PAID
        order.save(update_fields=['payment_status'])
        return Response(OrderReadSerializer(order).data)


# ============================================================================
# ✅ New Endpoints for Flutter Improvements
# ============================================================================

class OrderStatusView(APIView):
    """
    Get order status for real-time polling
    GET /api/v1/orders/{order_id}/status/
    
    Response:
    {
        "id": 123,
        "fulfillment_status": "SHIPPED",
        "payment_status": "PAID",
        "created_at": "2025-10-19T00:00:00Z"
    }
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'id': order.id,
            'fulfillment_status': order.fulfillment_status,
            'payment_status': order.payment_status,
            'created_at': order.created_at,
        })


class OrderRatingView(APIView):
    """
    Rate an order
    POST /api/v1/orders/{order_id}/rate/
    
    Body:
    {
        "delivery_speed_rating": 5,
        "service_quality_rating": 4
    }
    
    Response:
    {
        "success": true,
        "message": "تم حفظ تقييمك بنجاح"
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

        # Validate order is delivered
        if order.fulfillment_status != Order.FulfillmentStatus.DELIVERED:
            return Response(
                {'error': 'يمكن تقييم الطلب فقط بعد التوصيل'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get ratings from request
        delivery_speed = request.data.get('delivery_speed_rating')
        service_quality = request.data.get('service_quality_rating')

        # Validate ratings
        if not delivery_speed or not service_quality:
            return Response(
                {'error': 'يجب توفير التقييمين'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            delivery_speed = float(delivery_speed)
            service_quality = float(service_quality)
            
            if not (1 <= delivery_speed <= 5) or not (1 <= service_quality <= 5):
                raise ValueError
        except (ValueError, TypeError):
            return Response(
                {'error': 'التقييم يجب أن يكون بين 1 و 5'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Import OrderReview model
        from reviews.models import OrderReview

        # Create or update review
        review, created = OrderReview.objects.update_or_create(
            user=request.user,
            order=order,
            defaults={
                'delivery_speed_rating': int(delivery_speed),
                'service_quality_rating': int(service_quality),
            }
        )

        return Response({
            'success': True,
            'message': 'تم حفظ تقييمك بنجاح' if created else 'تم تحديث تقييمك بنجاح',
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
