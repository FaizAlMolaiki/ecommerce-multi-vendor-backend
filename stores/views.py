from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.views import APIView
from rest_framework import generics
from django.db.models import Q, Case, When, Value, Exists, OuterRef

from core.pagination import CustomCursorPagination
from wishlist.models import UserStoreFavorite
from .models import Store, PlatformCategory
from .serializers import StoreListSerializer, StoreDetailSerializer, PlatformCategorySerializer
from .permissions import IsOwnerOrReadOnly
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound

# كلاس عرض تصنيفات المنصة
class PlatformCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PlatformCategory.objects.all()
    serializer_class = PlatformCategorySerializer
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=['get'], url_path='featured', permission_classes=[permissions.AllowAny])
    def featured(self, request):
        qs = self.get_queryset().filter(is_featured=True)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


# كلاس عرض وإدارة المتاجر
class StoreViewSet(viewsets.ModelViewSet):
    """
    API endpoint يسمح بعرض وإدارة المتاجر.
    - أي شخص يمكنه عرض المتاجر النشطة (GET).
    - المستخدمون المسجلون فقط يمكنهم إنشاء طلب متجر (POST).
    - مالك المتجر فقط يمكنه تعديله أو حذفه (PUT, PATCH, DELETE).
    """
    
    # الصلاحيات: نحدد من يمكنه فعل ماذا
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    # الفلترة والبحث والترتيب
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['platform_category', 'status', 'city']  # ✅ إضافة city
    search_fields = ['name', 'description']  # يسمح بالبحث في اسم المتجر والوصف
    ordering_fields = ['average_rating', 'review_count', 'name', 'created_at']  # يسمح بالترتيب

    def get_queryset(self):
        """
        - للـ list: عرض المتاجر النشطة فقط للجميع
        """
        user = getattr(self.request, 'user', None)
        base_qs = Store.get_active_stores()

        if user and user.is_authenticated:
            is_fav_subq = UserStoreFavorite.objects.filter(
                store=OuterRef('pk'),
                user=user,
            )
            return base_qs.annotate(is_favorite=Exists(is_fav_subq))
        return base_qs.annotate(is_favorite=Value(False))
    
    # اختيار الـ Serializer المناسب تلقائياً
    def get_serializer_class(self):
        if self.action == 'list':
            return StoreListSerializer
        return StoreDetailSerializer
    
    def get_object(self):
        """
        يسمح للمالك والإدارة بالوصول لأي متجر
        والآخرين يشوفون المتاجر النشطة فقط
        """
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        
        # جلب المتجر من قاعدة البيانات (بأي حالة)
        obj = get_object_or_404(Store.objects.all(), **filter_kwargs)
        
        user = self.request.user
        
        # إذا كان المالك أو Admin، يسمح له بالوصول مباشرة
        if user.is_authenticated and (obj.owner == user or user.is_staff):
            # إضافة is_favorite
            if user and user.is_authenticated:
                is_fav = UserStoreFavorite.objects.filter(store=obj, user=user).exists()
                obj.is_favorite = is_fav
            else:
                obj.is_favorite = False
            
            self.check_object_permissions(self.request, obj)
            return obj
        
        # غير المالك يشوف المتاجر النشطة فقط
        if not obj.is_active_store:
            raise NotFound("No Store matches the given query.")
        
        # إضافة is_favorite للمستخدمين الآخرين
        if user.is_authenticated:
            is_fav = UserStoreFavorite.objects.filter(store=obj, user=user).exists()
            obj.is_favorite = is_fav
        else:
            obj.is_favorite = False
        
        self.check_object_permissions(self.request, obj)
        return obj
    
    # ربط المالك تلقائياً عند إنشاء متجر جديد
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    # إضافة متجر إلى المفضلة
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def add_to_favorites(self, request, pk=None):
        """إضافة متجر معين إلى مفضلة المستخدم الحالي."""
        store = self.get_object()
        favorite, created = UserStoreFavorite.objects.get_or_create(
            user=request.user, 
            store=store
        )
        if created:
            return Response({'status': 'store added to favorites'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'status': 'store already in favorites'}, status=status.HTTP_200_OK)
    # ✅ ======================= هذا الإجراء الجديد =======================
    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def promotions(self, request, pk=None):
        """
        جلب جميع العروض الترويجية الخاصة بمتجر واحد محدد.
        Endpoint: GET /api/v1/stores/stores/{id}/promotions/
        """
        store = self.get_object()

        # التحقق من أن المستخدم الحالي هو مالك هذا المتجر
        if store.owner != request.user:
            return Response(
                {'error': 'ليس لديك الصلاحية للوصول إلى عروض هذا المتجر.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # استيراد الموديلات والسيريلايزرز المطلوبة من تطبيق pricing
            from pricing.models import Promotion
            from pricing.serializers import PromotionSerializer

            # جلب جميع الخصومات (بما في ذلك غير النشطة والمستقبلية) المرتبطة بهذا المتجر
            store_promotions = Promotion.objects.filter(stores=store).order_by('-created_at')
            
            # تحويل البيانات إلى JSON وإرجاعها
            # ملاحظة: لا نستخدم pagination هنا لأن عدد العروض للمتجر الواحد عادة ما يكون قليلاً
            serializer = PromotionSerializer(store_promotions, many=True, context={'request': request})
            return Response({'results': serializer.data})

        except ImportError:
            # هذا يحدث فقط إذا كان تطبيق pricing غير مثبت بشكل صحيح
            return Response({'error': 'نظام التسعير غير متاح حالياً.'}, 
                          status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as e:
            # يمكنك تسجيل الخطأ هنا باستخدام logger
            # logger.error(f"Error fetching promotions for store {pk}: {e}")
            return Response({'error': 'حدث خطأ غير متوقع أثناء جلب العروض.'}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    # ====================================================================

    # ✅ ======================= هذا الإجراء للكوبونات =======================
    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def coupons(self, request, pk=None):
        """
        جلب جميع الكوبونات الخاصة بمتجر واحد محدد.
        Endpoint: GET /api/v1/stores/stores/{id}/coupons/
        """
        store = self.get_object()

        # التحقق من الملكية
        if store.owner != request.user:
            return Response(
                {'error': 'ليس لديك صلاحية للوصول إلى كوبونات هذا المتجر.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            from pricing.models import Coupon
            from pricing.serializers import CouponSerializer

            store_coupons = Coupon.objects.filter(stores=store).order_by('-created_at')
            
            serializer = CouponSerializer(store_coupons, many=True, context={'request': request})
            return Response({'results': serializer.data})

        except ImportError:
            return Response({'error': 'نظام التسعير غير متاح.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as e:
            return Response({'error': 'حدث خطأ غير متوقع.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    # ====================================================================


    # ✅ ======================= هذا الإجراء للعروض الخاصة =======================
    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def offers(self, request, pk=None):
        """
        جلب جميع العروض الخاصة (Offers) بمتجر واحد محدد.
        Endpoint: GET /api/v1/stores/stores/{id}/offers/
        """
        store = self.get_object()

        # التحقق من الملكية
        if store.owner != request.user:
            return Response(
                {'error': 'ليس لديك صلاحية للوصول إلى عروض هذا المتجر.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            from pricing.models import Offer
            from pricing.serializers import OfferSerializer
            store_offers = Offer.objects.filter(stores=store).order_by('-created_at')
            
            serializer = OfferSerializer(store_offers, many=True, context={'request': request})
            return Response({'results': serializer.data})

        except ImportError:
            return Response({'error': 'نظام التسعير غير متاح.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as e:
            return Response({'error': 'حدث خطأ غير متوقع.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    # ====================================================================
    # ✅ محدث: عرض المتاجر الشخصية (جميع الحالات)
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_stores(self, request):
        """عرض قائمة المتاجر والطلبات التي يملكها المستخدم الحالي"""
        user_stores = Store.get_user_stores(request.user)
        serializer = self.get_serializer(user_stores, many=True)
        return Response(serializer.data)
    
    # ✅ جديد: عرض طلبات المستخدم فقط
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_requests(self, request):
        """عرض طلبات المتاجر للمستخدم الحالي فقط"""
        user_requests = Store.get_user_requests(request.user)
        serializer = self.get_serializer(user_requests, many=True)
        return Response(serializer.data)
    
    # ✅ جديد: فئات المتجر
    @action(detail=True, methods=['get'], permission_classes=[permissions.AllowAny])
    def categories(self, request, pk=None):
        """Get product categories for a specific store"""
        store = self.get_object()
        try:
            from products.models import ProductCategory
            from products.serializers import ProductCategorySerializer
            categories = ProductCategory.objects.filter(store=store)
            serializer = ProductCategorySerializer(categories, many=True)
            return Response(serializer.data)
        except ImportError:
            return Response({'error': 'Product categories not available'}, 
                          status=status.HTTP_503_SERVICE_UNAVAILABLE)

    # ✅ جديد: منتجات المتجر
    @action(detail=True, methods=['get'], permission_classes=[permissions.AllowAny])
    def products(self, request, pk=None):
        """Get products for a specific store with optional category filter"""
        store = self.get_object()
        try:
            from products.models import Product
            from products.serializers import ProductListSerializer
            
            products = Product.objects.filter(store=store)
            
            # Optional category filter
            category_id = request.query_params.get('category_id')
            if category_id:
                try:
                    category_id = int(category_id)
                    products = products.filter(category_id=category_id)
                except (ValueError, TypeError):
                    return Response({'error': 'Invalid category_id'}, 
                                  status=status.HTTP_400_BAD_REQUEST)
            
            # Pagination support
            page = self.paginate_queryset(products)
            if page is not None:
                serializer = ProductListSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
                
            serializer = ProductListSerializer(products, many=True)
            return Response(serializer.data)
        except ImportError:
            return Response({'error': 'Products not available'}, 
                          status=status.HTTP_503_SERVICE_UNAVAILABLE)

    # ✅ جديد: تبديل حالة المتجر (للمالك فقط)
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def toggle_status(self, request, pk=None):
        """
        تبديل حالة المتجر بين ACTIVE و CLOSED
        لا يمكن تغيير SUSPENDED (يتطلب صلاحية المشرف)
        """
        store = self.get_object()
        
        # التحقق من الملكية
        if store.owner != request.user:
            return Response(
                {'error': 'فقط مالك المتجر يستطيع تغيير هذه الحالة'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            store.toggle_status_by_owner()
            serializer = self.get_serializer(store)
            return Response({
                'message': 'تم تحديث حالة المتجر بنجاح',
                'store': serializer.data
            })
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


# عرض تصنيفات المنصة المميزة
class FeaturedPlatformCategoryList(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        featured_categories = PlatformCategory.objects.filter(is_featured=True)
        serializer = PlatformCategorySerializer(featured_categories, many=True)
        return Response(serializer.data)


# تفاصيل متجر نشط محدد
class StoreDetailView(generics.RetrieveAPIView):
    """
    Returns the details of a specific store by its ID.
    Only active stores are shown.
    """
    queryset = Store.get_active_stores()
    serializer_class = StoreDetailSerializer
    lookup_field = 'pk'
    permission_classes = [permissions.AllowAny]


# أفضل المتاجر تقييماً مع تضمين حالة المفضلة
class TopRatedStoreListView(generics.ListAPIView):
    """
    إرجاع قائمة بأعلى المتاجر تقييماً مع تضمين حالة المفضلة للمستخدم عند تسجيل الدخول.
    """
    serializer_class = StoreDetailSerializer
    pagination_class = CustomCursorPagination
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        user = self.request.user
        category_id = self.request.query_params.get('platform_category', None)

        if category_id:
            try:
                category_id = int(category_id)
                queryset = Store.get_active_stores().filter(
                    platform_category_id=category_id,
                )
            except (ValueError, TypeError):
                queryset = Store.get_active_stores()
        else:
            queryset = Store.get_active_stores()

        if user and user.is_authenticated:
            is_favorite_subquery = UserStoreFavorite.objects.filter(
                store=OuterRef('pk'),
                user=user,
            )
            queryset = queryset.annotate(
                is_favorite=Exists(is_favorite_subquery)
            )
        else:
            queryset = queryset.annotate(is_favorite=Value(False))

        # ترتيب افتراضي: أعلى تقييماً ثم الأحدث
        return queryset.order_by('-average_rating', '-id')


# بحث المتاجر
class StoreSearchView(generics.ListAPIView):
    """
    GET /api/v1/stores/search/?search={query}

    البحث عن المتاجر بالاسم أو الوصف. النتائج تعتمد على Cursor Pagination.
    """
    serializer_class = StoreDetailSerializer
    pagination_class = CustomCursorPagination
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        search_term = self.request.query_params.get('search', None)

        if not search_term or len(search_term.strip()) == 0:
            return Store.objects.none()

        base_queryset = Store.get_active_stores().filter(
            Q(name__icontains=search_term) | Q(description__icontains=search_term),
        )

        user = self.request.user
        queryset = base_queryset

        if user and user.is_authenticated:
            is_favorite_subquery = UserStoreFavorite.objects.filter(
                store=OuterRef('pk'),
                user=user,
            )
            queryset = queryset.annotate(
                is_favorite=Exists(is_favorite_subquery)
            )
        else:
            queryset = queryset.annotate(is_favorite=Value(False))

        ordered_queryset = queryset.annotate(
            relevance=Case(
                When(name__icontains=search_term, then=Value(1)),
                default=Value(2),
            )
        ).order_by('relevance', '-average_rating', '-id')

        return ordered_queryset