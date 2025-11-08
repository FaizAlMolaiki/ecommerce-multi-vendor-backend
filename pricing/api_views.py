# from rest_framework import viewsets, status
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated
# from django.utils import timezone
# from .models import Promotion, Coupon, Offer
# from .serializers import PromotionSerializer, CouponSerializer, OfferSerializer

# class PromotionViewSet(viewsets.ModelViewSet):
#     """
#     ViewSet for managing promotions
#     """
#     queryset = Promotion.objects.all()
#     serializer_class = PromotionSerializer
#     permission_classes = [IsAuthenticated]

# class CouponViewSet(viewsets.ModelViewSet):
#     """
#     ViewSet for managing coupons
#     """
#     queryset = Coupon.objects.all()
#     serializer_class = CouponSerializer
#     permission_classes = [IsAuthenticated]

# class OfferViewSet(viewsets.ModelViewSet):
#     """
#     ViewSet for managing offers
#     """
#     queryset = Offer.objects.all()
#     serializer_class = OfferSerializer
#     permission_classes = [IsAuthenticated]

# class ApplyCouponView(APIView):
#     """
#     Apply a coupon to calculate discount
#     """
#     permission_classes = [IsAuthenticated]
    
#     def post(self, request):
#         coupon_code = request.data.get('coupon_code')
#         order_total = request.data.get('order_total', 0)
        
#         if not coupon_code:
#             return Response({'error': 'Coupon code is required'}, status=status.HTTP_400_BAD_REQUEST)
        
#         try:
#             coupon = Coupon.objects.get(
#                 code=coupon_code,
#                 is_active=True,
#                 valid_from__lte=timezone.now(),
#                 valid_to__gte=timezone.now()
#             )
            
#             # Calculate discount
#             if coupon.discount_type == 'percentage':
#                 discount = (order_total * coupon.discount_value) / 100
#                 if coupon.max_discount_amount:
#                     discount = min(discount, coupon.max_discount_amount)
#             else:  # fixed amount
#                 discount = coupon.discount_value
            
#             return Response({
#                 'valid': True,
#                 'discount': discount,
#                 'coupon': CouponSerializer(coupon).data
#             })
            
#         except Coupon.DoesNotExist:
#             return Response({'valid': False, 'error': 'Invalid or expired coupon'}, status=status.HTTP_404_NOT_FOUND)

# class GetActivePromotionsView(APIView):
#     """
#     Get all active promotions
#     """
#     def get(self, request):
#         now = timezone.now()
#         promotions = Promotion.objects.filter(
#             is_active=True,
#             start_date__lte=now,
#             end_date__gte=now
#         )
        
#         serializer = PromotionSerializer(promotions, many=True)
#         return Response(serializer.data)

"""API Views for Pricing Application

يحتوي هذا الملف على جميع ViewSets وAPI Views لإدارة:
- العروض الترويجية (Promotions)
- الكوبونات (Coupons)
- العروض الخاصة (Offers)
- حساب أسعار السلة (Cart Calculation)
"""

import logging

from django.db import models
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import ValidationError, PermissionDenied  # ✅ الاستثناءات الصحيحة

from pricing.utils import get_and_validate_store, parse_aware_datetime
from products.models import Product
from stores.models import Store
from .models import Promotion, Coupon, Offer
from .serializers import PromotionSerializer, CouponSerializer, OfferSerializer
from .permissions import IsVendor, IsObjectOwner  # ✅ استيراد الصلاحيات من ملف منفصل
from .mixins import ApprovalMixin  # ✅ استيراد الـ Mixin من ملف منفصل

logger = logging.getLogger(__name__)

# ======================================================================
#                           ViewSets
# ======================================================================
# ⚠️ OLD: class PromotionViewSet(viewsets.ReadOnlyModelViewSet):
# ✅ NEW: Inherit from ModelViewSet to allow more actions
class PromotionViewSet(ApprovalMixin, viewsets.ModelViewSet):
    """ViewSet لإدارة العروض الترويجية"""
    serializer_class = PromotionSerializer
    
    # ⚠️ OLD: permission_classes = [AllowAny]
    # ✅ NEW: Set default permissions to require authentication
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        للبائعين: إرجاع جميع العروض (للتعديل)
        للعملاء: إرجاع العروض النشطة والمعتمدة فقط
        """
        queryset = Promotion.objects.select_related('required_coupon').prefetch_related(
            'stores', 'categories', 'products', 'variants'
        )
        
        # إذا كان المستخدم بائع ويعدل عروضه، إرجاع الكل
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy', 'toggle_status']:
            return queryset
        
        # للقراءة العامة: العروض النشطة والمعتمدة فقط
        now = timezone.now()
        return queryset.filter(
            active=True,
            approval_status='APPROVED'  # NEW: فقط العروض المعتمدة
        ).filter(
            models.Q(start_at__isnull=True) | models.Q(start_at__lte=now)
        ).filter(
            models.Q(end_at__isnull=True) | models.Q(end_at__gte=now)
        )
    
    # --- هذا الجزء لتحديد الصلاحيات لكل إجراء ---
    def get_permissions(self):
        """
        يسمح لأي شخص بقراءة قائمة العروض (list).
        يتطلب المصادقة + IsObjectOwner لإجراءات التعديل والحذف.
        """
        if self.action == 'list':
            return [AllowAny()]
        elif self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsVendor(), IsObjectOwner()]
        return [IsAuthenticated(), IsVendor()]
    
    # ✅ أضف هذا:
    @action(detail=False, methods=['get'], url_path='active')
    def active(self, request):
        """الحصول على العروض الترويجية النشطة للعملاء"""
        from django.utils import timezone
        
        now = timezone.now()
        promotions = self.get_queryset().filter(
            active=True,
            start_at__lte=now,
            end_at__gte=now
        ).order_by('-priority', '-created_at')
        
        serializer = self.get_serializer(promotions, many=True)
        return Response({
            'success': True,
            'count': promotions.count(),
            'results': serializer.data
        })
    # toggle_status, approve, reject, perform_destroy موجودة في ApprovalMixin ✅


# NEW: Full CRUD with IsObjectOwner protection
class CouponViewSet(ApprovalMixin, viewsets.ModelViewSet):
    """ViewSet للكوبونات مع الحماية عبر IsObjectOwner"""
    serializer_class = CouponSerializer
    
    def get_queryset(self):
        """
        للبائعين: إرجاع جميع الكوبونات (للتعديل)
        للعملاء: إرجاع الكوبونات النشطة والمعتمدة فقط
        """
        queryset = Coupon.objects.prefetch_related('stores')
        
        # إذا كان المستخدم بائع ويعدل كوبوناته، إرجاع الكل
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy', 'toggle_status']:
            return queryset
        
        # للقراءة والتحقق: الكوبونات النشطة والمعتمدة فقط
        return queryset.filter(active=True, approval_status='APPROVED')
    
    def get_permissions(self):
        """
        يسمح للمصادقين بالقراءة والتحقق.
        يتطلب IsObjectOwner لإجراءات التعديل والحذف.
        """
        if self.action in ['list', 'retrieve', 'validate']:
            return [IsAuthenticated()]
        elif self.action in ['update', 'partial_update', 'destroy', 'toggle_status']:
            return [IsAuthenticated(), IsVendor(), IsObjectOwner()]
        return [IsAuthenticated(), IsVendor()]
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def validate(self, request):
        """التحقق من صلاحية الكوبون"""
        code = request.data.get('code', '').strip().upper()
        
        if not code:
            return Response(
                {'valid': False, 'error': 'Coupon code is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            coupon = Coupon.objects.get(code=code, active=True, approval_status='APPROVED')
            now = timezone.now()
            
            if coupon.start_at and now < coupon.start_at:
                return Response({
                    'valid': False,
                    'error': 'هذا الكوبون لم يبدأ بعد',
                    'start_at': coupon.start_at
                })
            
            if coupon.end_at and now > coupon.end_at:
                return Response({
                    'valid': False,
                    'error': 'هذا الكوبون منتهي الصلاحية',
                    'end_at': coupon.end_at
                })
            
            if coupon.usage_limit:
                total_usage = coupon.redemptions.count()
                if total_usage >= coupon.usage_limit:
                    return Response({
                        'valid': False,
                        'error': 'تم استخدام هذا الكوبون بالكامل'
                    })
            
            if coupon.limit_per_user:
                user_usage = coupon.redemptions.filter(user=request.user).count()
                if user_usage >= coupon.limit_per_user:
                    return Response({
                        'valid': False,
                        'error': f'لقد استخدمت هذا الكوبون {user_usage} مرة بالفعل'
                    })
            
            return Response({
                'valid': True,
                'coupon': CouponSerializer(coupon).data,
                'message': 'الكوبون صالح للاستخدام'
            })
            
        except Coupon.DoesNotExist:
            return Response(
                {'valid': False, 'error': 'كوبون غير صالح'},
                status=status.HTTP_404_NOT_FOUND
            )
    # toggle_status, approve, reject, perform_destroy موجودة في ApprovalMixin ✅


# NEW: Full CRUD with IsObjectOwner protection
class OfferViewSet(ApprovalMixin, viewsets.ModelViewSet):
    """عرض لإدارة العروض مع الحماية عبر IsObjectOwner"""
    serializer_class = OfferSerializer
    
    def get_queryset(self):
        """
        للبائعين: إرجاع جميع العروض (للتعديل)
        للعملاء: إرجاع العروض النشطة والمعتمدة فقط
        """
        queryset = Offer.objects.select_related('required_coupon').prefetch_related(
            'stores', 'categories', 'products', 'variants'
        )
        
        # إذا كان المستخدم بائع ويعدل عروضه، إرجاع الكل
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy', 'toggle_status']:
            return queryset
        
        # للقراءة العامة: العروض النشطة والمعتمدة فقط
        now = timezone.now()
        return queryset.filter(
            active=True,
            approval_status='APPROVED'  # NEW: فقط العروض المعتمدة
        ).filter(
            models.Q(start_at__isnull=True) | models.Q(start_at__lte=now)
        ).filter(
            models.Q(end_at__isnull=True) | models.Q(end_at__gte=now)
        )
    
    def get_permissions(self):
        """
        يسمح للجميع بقراءة العروض النشطة.
        يتطلب IsObjectOwner لإجراءات التعديل والحذف.
        """
        if self.action in ['list', 'retrieve', 'active_offers']:
            return [AllowAny()]
        elif self.action in ['update', 'partial_update', 'destroy', 'toggle_status']:
            return [IsAuthenticated(), IsVendor(), IsObjectOwner()]
        return [IsAuthenticated(), IsVendor()]
    
    # ✅ NEW: Custom action للعروض النشطة
    @action(detail=False, methods=['get'], url_path='active')
    def active_offers(self, request):
        """
        Get all active offers for customers (home page)
        Endpoint: /api/v1/pricing/offers/active/
        """
        now = timezone.now()
        
        # Get active offers - استخدم get_queryset() بدلاً من self.queryset
        active_offers = self.get_queryset()
        
        # Serialize
        serializer = self.get_serializer(active_offers, many=True)
        
        return Response({
            'success': True,
            'count': active_offers.count(),
            'results': serializer.data
        })
    # toggle_status, approve, reject, perform_destroy موجودة في ApprovalMixin ✅

class CalculateCartView(APIView):
    """حساب إجمالي السلة الكامل مع الخصومات والعروض"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        items = request.data.get('items', [])
        coupon_code = request.data.get('coupon_code', '').strip().upper() or None
        
        if not items:
            return Response(
                {'error': 'السلة فارغة'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        for idx, item in enumerate(items):
            required_fields = ['product_id', 'qty', 'unit_price']
            for field in required_fields:
                if field not in item:
                    return Response(
                        {'error': f'Item {idx}: missing field "{field}"'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
        
        try:
            from orders.services.pricing_engine import price_cart
            
            cart = {
                'user_id': request.user.id,
                'items': items,
                'coupon_code': coupon_code,
                'currency': 'SAR'
            }
            
            result = price_cart(cart)
            
            return Response({
                'subtotal': str(result['subtotal']),
                'discounts_total': str(result['discounts_total']),
                'shipping': str(result['shipping']),
                'grand_total': str(result['grand_total']),
                'applied_rules': result['applied_rules'],
                'line_discounts': {k: str(v) for k, v in result['line_discounts'].items()},
                'free_shipping': result['free_shipping'],
                'gifts': result['gifts'],
                'notes': result['notes']
            })
            
        except Exception as e:
            logger.error(f"Error calculating cart: {e}", exc_info=True)
            return Response(
                {'error': f'خطأ في حساب السلة: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# ========================================================================
# NEW: Vendor Management APIs - إدارة العروض والكوبونات للبائع
# ========================================================================

class MyPromotionsView(APIView):
    """الحصول على جميع العروض الخاصة بمتجر البائع"""
    permission_classes = [IsAuthenticated, IsVendor]
    
    def get(self, request):
        try:
            from stores.models import Store

            # 1. Get ALL stores owned by the user
            user_stores = Store.objects.filter(owner=request.user)
            
            if not user_stores.exists():
                return Response(
                    {'error': 'لا يوجد متاجر مرتبطة بهذا المستخدم'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # 2. Filter promotions that are in ANY of the user's stores
            promotions = Promotion.objects.filter(
                stores__in=user_stores
            ).prefetch_related(
                'stores', 'categories', 'products', 'variants'
            ).order_by('-created_at').distinct() # Use distinct to avoid duplicates if a promotion is in multiple stores
            
            serializer = PromotionSerializer(promotions, many=True, context={'request': request})
            return Response({'results': serializer.data})
            
        except Exception as e:
            logger.error(f"Error fetching vendor promotions: {e}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class MyCouponsView(APIView):
    """الحصول على جميع الكوبونات الخاصة بمتجر البائع"""
    permission_classes = [IsAuthenticated, IsVendor]
    
    def get(self, request):
        try:
            # ✅ استخدام utility function - يدعم store_id من query params
            store_id = request.query_params.get('store_id')
            
            if store_id:
                # إذا تم تمرير store_id، التحقق من الملكية
                store = get_and_validate_store(request, store_id)
                coupons = Coupon.objects.filter(
                    stores=store
                ).prefetch_related('stores').order_by('-created_at')
            else:
                # إذا لم يتم تمرير store_id، إرجاع كوبونات جميع متاجر المستخدم
                user_stores = Store.objects.filter(owner=request.user)
                coupons = Coupon.objects.filter(
                    stores__in=user_stores
                ).prefetch_related('stores').order_by('-created_at').distinct()
            
            serializer = CouponSerializer(coupons, many=True, context={'request': request})
            return Response({'results': serializer.data})
        
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except PermissionDenied as e:
            return Response(e.detail, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            logger.error(f"Error fetching vendor coupons: {e}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class MyOffersView(APIView):
    """الحصول على جميع العروض الخاصة بمتجر البائع"""
    permission_classes = [IsAuthenticated, IsVendor]
    
    def get(self, request):
        try:
            # ✅ استخدام utility function - يدعم store_id من query params
            store_id = request.query_params.get('store_id')
            
            if store_id:
                # إذا تم تمرير store_id، التحقق من الملكية
                store = get_and_validate_store(request, store_id)
                offers = Offer.objects.filter(stores=store).select_related('required_coupon').prefetch_related(
                    'stores', 'categories', 'products', 'variants'
                ).order_by('-created_at')
            else:
                # إذا لم يتم تمرير store_id، إرجاع عروض جميع متاجر المستخدم
                user_stores = Store.objects.filter(owner=request.user)
                offers = Offer.objects.filter(
                    stores__in=user_stores
                ).select_related('required_coupon').prefetch_related(
                    'stores', 'categories', 'products', 'variants'
                ).order_by('-created_at').distinct()
            
            serializer = OfferSerializer(offers, many=True, context={'request': request})
            return Response({'results': serializer.data})
        
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except PermissionDenied as e:
            return Response(e.detail, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            logger.error(f"Error fetching vendor offers: {e}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CreatePromotionView(APIView):
    """إنشاء عرض جديد للبائع - يدعم categories, products, variants"""
    permission_classes = [IsAuthenticated, IsVendor]
    
    def post(self, request):
        try:
            data = request.data
            
            # ✅ استخدام utility function للتحقق من المتجر
            store = get_and_validate_store(request, data.get('store_id'))
            
            # استخراج البيانات
            name = data.get('name', '').strip()
            description = data.get('description', '')  # ✅ NEW
            image = request.FILES.get('image')  # ✅ NEW - رفع الصورة
            discount_type = data.get('discount_type', 'percentage')
            discount_value = data.get('discount_value', 0)
            scope = data.get('scope', 'product')  # ✅ NEW
            
            # ✅ NEW: استخراج IDs حسب scope
            category_ids = data.get('categories', [])
            product_ids = data.get('products', [])
            variant_ids = data.get('variants', [])

            start_date = parse_aware_datetime(data.get('start_date'))
            end_date = parse_aware_datetime(data.get('end_date'))

            priority = data.get('priority', 100)
            is_active = data.get('is_active', True)
            
            # ✅ NEW: حقول إضافية من DiscountRuleBase
            min_purchase_amount = data.get('min_purchase_amount')
            stackable = data.get('stackable', True)
            required_coupon_id = data.get('required_coupon_id')
            
            # التحقق من البيانات
            if not name:
                return Response(
                    {'error': 'اسم العرض مطلوب'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # ✅ NEW: التحقق حسب scope
            if scope == 'product' and not product_ids:
                return Response(
                    {'error': 'يجب اختيار منتج واحد على الأقل'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            elif scope == 'category' and not category_ids:
                return Response(
                    {'error': 'يجب اختيار فئة واحدة على الأقل'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            elif scope == 'variant' and not variant_ids:
                return Response(
                    {'error': 'يجب اختيار متغير واحد على الأقل'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # تحويل discount_type
            promotion_type_map = {
                'percentage': 'PRODUCT_PERCENTAGE',
                'fixed': 'PRODUCT_FIXED_AMOUNT',
            }
            promotion_type = promotion_type_map.get(discount_type, 'PRODUCT_PERCENTAGE')
            
            # إنشاء العرض
            promotion = Promotion.objects.create(
                name=name,
                description=description,  # ✅ NEW
                image=image,  # ✅ NEW
                promotion_type=promotion_type,
                value=discount_value,
                start_at=start_date,
                end_at=end_date,
                priority=priority,
                active=is_active,
                min_purchase_amount=min_purchase_amount,  # ✅ NEW
                stackable=stackable,  # ✅ NEW
                required_coupon_id=required_coupon_id,  # ✅ NEW
            )
            
            # ربط المتجر
            promotion.stores.add(store)
            
            # ✅ NEW: ربط حسب scope
            if category_ids:
                from products.models import ProductCategory
                categories = ProductCategory.objects.filter(id__in=category_ids)
                if categories.exists():
                    promotion.categories.set(categories)
            
            if product_ids:
                products = Product.objects.filter(id__in=product_ids, store=store)
                if products.exists():
                    promotion.products.set(products)
                else:
                    promotion.delete()
                    return Response(
                        {'error': 'المنتجات المحددة غير صحيحة'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            if variant_ids:
                from products.models import ProductVariant
                variants = ProductVariant.objects.filter(id__in=variant_ids)
                if variants.exists():
                    promotion.variants.set(variants)
            
            serializer = PromotionSerializer(promotion)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        except ValidationError as e:
            # معالجة أخطاء التحقق من البيانات
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except PermissionDenied as e:
            # معالجة أخطاء الصلاحيات
            return Response(e.detail, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            logger.error(f"Error creating promotion: {e}", exc_info=True)
            return Response(
                {'error': 'حدث خطأ غير متوقع'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CreateCouponView(APIView):
    """إنشاء كوبون جديد للبائع"""
    permission_classes = [IsAuthenticated, IsVendor]
    
    def post(self, request):
        try:
            data = request.data
            
            # ✅ استخدام utility function للتحقق من المتجر
            store = get_and_validate_store(request, data.get('store_id'))
            
            # استخراج البيانات
            code = data.get('code', '').strip().upper()
            
            # تحويل تاريخ البدء والانتهاء New ✅
            start_date = parse_aware_datetime(data.get('valid_from'))
            end_date = parse_aware_datetime(data.get('valid_to'))
            
            if not code:
                return Response(
                    {'error': 'كود الكوبون مطلوب'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # التحقق من عدم وجود كوبون بنفس الكود
            if Coupon.objects.filter(code=code).exists():
                return Response(
                    {'error': 'هذا الكود مستخدم بالفعل'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # إنشاء الكوبون
            coupon = Coupon.objects.create(
                code=code,
                active=data.get('is_active', True),
                start_at= start_date, # Updated
                end_at= end_date, # Updated
                usage_limit=data.get('usage_limit'),
                limit_per_user=data.get('limit_per_user', 1),
            )
            
            # ربط المتجر
            coupon.stores.add(store)
            
            serializer = CouponSerializer(coupon)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        except ValidationError as e:
            # معالجة أخطاء التحقق من البيانات
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except PermissionDenied as e:
            # معالجة أخطاء الصلاحيات
            return Response(e.detail, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            logger.error(f"Error creating coupon: {e}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class CreateOfferView(APIView):
    """إنشاء عرض جديد للبائع"""
    permission_classes = [IsAuthenticated, IsVendor]
    
    def post(self, request):
        try:
            data = request.data
            
            # ✅ استخدام utility function للتحقق من المتجر
            store = get_and_validate_store(request, data.get('store_id'))

            # تحويل تاريخ البدء والانتهاء New ✅
            start_date = parse_aware_datetime(data.get('start_at'))
            end_date = parse_aware_datetime(data.get('end_at'))

            name = data.get('name', '').strip()
            description = data.get('description', '')  # ✅ NEW
            image = request.FILES.get('image')  # ✅ NEW - رفع الصورة
            offer_type = data.get('offer_type')
            configuration = data.get('configuration', {})
            
            # ✅ NEW: استخراج IDs للعلاقات
            product_ids = data.get('products', [])
            category_ids = data.get('categories', [])
            variant_ids = data.get('variants', [])
            
            active = data.get('active', True)
            priority = data.get('priority', 100)
            
            # ✅ NEW: حقول إضافية من DiscountRuleBase
            min_purchase_amount = data.get('min_purchase_amount')
            stackable = data.get('stackable', True)
            required_coupon_id = data.get('required_coupon_id')

            if not name:
                return Response({'error': 'اسم العرض مطلوب'}, status=400)
            if not offer_type:
                return Response({'error': 'نوع العرض مطلوب'}, status=400)

            offer = Offer.objects.create(
                name=name,
                description=description,  # ✅ NEW
                image=image,  # ✅ NEW
                offer_type=offer_type,
                configuration=configuration,
                start_at=start_date,
                end_at=end_date,
                active=active,
                priority=priority,  # ✅ NEW
                min_purchase_amount=min_purchase_amount,  # ✅ NEW
                stackable=stackable,  # ✅ NEW
                required_coupon_id=required_coupon_id,  # ✅ NEW
            )
            
            # ربط المتجر والعلاقات
            offer.stores.add(store)
            
            # ✅ NEW: ربط المنتجات
            if product_ids:
                products = Product.objects.filter(id__in=product_ids, store=store)
                offer.products.set(products)
            
            # ✅ NEW: ربط الفئات
            if category_ids:
                from products.models import ProductCategory
                categories = ProductCategory.objects.filter(id__in=category_ids)
                if categories.exists():
                    offer.categories.set(categories)
            
            # ✅ NEW: ربط المتغيرات
            if variant_ids:
                from products.models import ProductVariant
                variants = ProductVariant.objects.filter(id__in=variant_ids)
                if variants.exists():
                    offer.variants.set(variants)
            
            serializer = OfferSerializer(offer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        except ValidationError as e:
            # معالجة أخطاء التحقق من البيانات
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except PermissionDenied as e:
            # معالجة أخطاء الصلاحيات
            return Response(e.detail, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            logger.error(f"Error creating offer: {e}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

