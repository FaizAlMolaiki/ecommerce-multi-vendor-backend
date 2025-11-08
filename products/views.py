# from rest_framework import viewsets, permissions, status
# from rest_framework.decorators import action
# from rest_framework.response import Response
# from rest_framework.filters import SearchFilter, OrderingFilter
# from django_filters.rest_framework import DjangoFilterBackend
# from django.db.models import Q

# from .models import Product, ProductCategory
# from .serializers import ProductSerializer, ProductCategorySerializer

# class ProductViewSet(viewsets.ModelViewSet):
#     """
#     API endpoint للمنتجات - يدعم CRUD كامل
#     """
#     serializer_class = ProductSerializer
#     permission_classes = [permissions.AllowAny]
#     filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
#     search_fields = ['name', 'description']
#     ordering_fields = ['created_at', 'price', 'name']
    
#     def get_queryset(self):
#         """تخصيص queryset حسب المعاملات"""
#         queryset = Product.objects.all()
        
#         # فلترة حسب المتجر
#         store_id = self.request.query_params.get('store_id', None)
#         if store_id:
#             queryset = queryset.filter(store_id=store_id)
        
#         # فلترة حسب الفئة
#         category_id = self.request.query_params.get('category_id', None)
#         if category_id:
#             queryset = queryset.filter(category_id=category_id)
        
#         # ترتيب حسب المعامل
#         sort_by = self.request.query_params.get('sort-by', None)
#         if sort_by == 'top-rated':
#             queryset = queryset.order_by('-average_rating')
#         elif sort_by == 'top-sale':
#             queryset = queryset.order_by('-sales_count')
#         elif sort_by == 'recent':
#             queryset = queryset.order_by('-created_at')
        
#         # إذا لم يتم تحديد store_id أو category_id، أرجع منتجات عامة
#         if not store_id and not category_id:
#             # يمكن إرجاع منتجات مميزة أو الأكثر مبيعاً
#             queryset = queryset.filter(is_featured=True) if hasattr(Product, 'is_featured') else queryset[:20]
        
#         return queryset
    
#     def list(self, request, *args, **kwargs):
#         """تخصيص response للقائمة"""
#         store_id = request.query_params.get('store_id', None)
#         category_id = request.query_params.get('category_id', None)
        
#         # التحقق من وجود أحد المعاملات المطلوبة للفلترة الكاملة
#         if not store_id and not category_id:
#             # السماح بعرض منتجات عامة مع تحذير
#             pass
        
#         return super().list(request, *args, **kwargs)
    
#     def destroy(self, request, *args, **kwargs):
#         """حذف المنتج مع حذف جميع البيانات المرتبطة"""
#         from rest_framework.response import Response
#         from django.http import Http404
#         from django.db import transaction
        
#         try:
#             # محاولة الحصول على المنتج أولاً
#             instance = self.get_object()
#             product_id = instance.id
            
#             # حذف المنتج وجميع البيانات المرتبطة في transaction واحد
#             with transaction.atomic():
#                 # حذف الصور المرتبطة
#                 instance.images.all().delete()
#                 # حذف المتغيرات المرتبطة
#                 instance.variants.all().delete()
#                 # حذف المنتج نفسه
#                 instance.delete()
            
#             return Response({
#                 'message': 'تم حذف المنتج بنجاح',
#                 'deleted_product_id': product_id
#             }, status=200)
            
#         except Http404:
#             return Response({'error': 'المنتج غير موجود'}, status=404)
#         except Exception as e:
#             return Response({'error': f'فشل في حذف المنتج: {str(e)}'}, status=400)


# class ProductCategoryViewSet(viewsets.ModelViewSet):
#     """
#     API endpoint لفئات المنتجات - يدعم CRUD كامل
#     """
#     serializer_class = ProductCategorySerializer
#     permission_classes = [permissions.AllowAny]
#     filter_backends = [DjangoFilterBackend]
#     filterset_fields = ['store']
    
#     def get_queryset(self):
#         """تخصيص queryset حسب المعاملات"""
#         queryset = ProductCategory.objects.all()
        
#         # فلترة حسب المتجر
#         store_id = self.request.query_params.get('store_id', None)
#         if store_id:
#             queryset = queryset.filter(store_id=store_id)
        
#         return queryset
    
#     def list(self, request, *args, **kwargs):
#         """تخصيص response للقائمة - إرجاع قائمة فارغة بدلاً من 404"""
#         queryset = self.get_queryset()
        
#         # إذا كانت القائمة فارغة، أرجع قائمة فارغة بدلاً من 404
#         if not queryset.exists():
#             return Response([])
        
#         return super().list(request, *args, **kwargs)


from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django.http import Http404
from django.db import transaction

from .models import Product, ProductCategory, ProductVariant, ProductImage
from .serializers import (
    ProductSerializer, 
    ProductCategorySerializer, 
    ProductVariantSerializer, 
    ProductImageSerializer
)


# =================================
# Product ViewSet (النسخة المعدلة والمحسنة)
# =================================

class ProductViewSet(viewsets.ModelViewSet):
    """
    API endpoint للمنتجات - يدعم CRUD كامل مع فلترة مخصصة.
    """
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]  # يمكنك تغييرها إلى IsAuthenticated إذا لزم الأمر

    def get_queryset(self):
        """
        إرجاع القائمة الأساسية للمنتجات.
        هذا يضمن أن دوال retrieve, update, destroy يمكنها الوصول إلى أي منتج.
        """
        return Product.objects.all()

    def list(self, request, *args, **kwargs):
        """
        تخصيص منطق عرض قائمة المنتجات مع الفلترة والترتيب.
        """
        queryset = self.get_queryset()

        # فلترة حسب المتجر
        store_id = self.request.query_params.get('store_id', None)
        if store_id:
            queryset = queryset.filter(store_id=store_id)

        # فلترة حسب الفئة
        category_id = self.request.query_params.get('category_id', None)
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        # ترتيب حسب المعامل (sort-by)
        sort_by = self.request.query_params.get('sort-by', None)
        if sort_by == 'top-rated':
            queryset = queryset.order_by('-average_rating')
        elif sort_by == 'top-sale':
            # ملاحظة: اسم الحقل في الموديل هو selling_count
            queryset = queryset.order_by('-selling_count')
        elif sort_by == 'recent':
            # ملاحظة: لا يوجد حقل created_at في الموديل، يمكنك إضافته أو استخدام حقل آخر
            # queryset = queryset.order_by('-created_at')
            pass

        # إذا لم يتم تحديد فلتر، أرجع مجموعة منتجات عامة (مثلاً، أول 20)
        if not store_id and not category_id:
            # يمكنك هنا تطبيق منطق لإرجاع المنتجات المميزة أو الأكثر مبيعًا كقيمة افتراضية
            queryset = queryset[:20]

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """
        حذف المنتج مع التأكد من التعامل مع الأخطاء بشكل صحيح.
        """
        try:
            instance = self.get_object()
            
            # يمكنك وضع الحذف داخل transaction لضمان حذف كل شيء أو لا شيء
            with transaction.atomic():
                # حذف الصور المرتبطة (إذا وجدت)
                if hasattr(instance, 'images'):
                    instance.images.all().delete()
                # حذف المتغيرات المرتبطة (إذا وجدت)
                if hasattr(instance, 'variants'):
                    instance.variants.all().delete()
                # حذف المنتج نفسه
                instance.delete()
            
            return Response({"message": "تم حذف المنتج بنجاح"}, status=status.HTTP_200_OK)

        except Http404:
            return Response({'error': 'المنتج غير موجود'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            # لتسجيل أي أخطاء غير متوقعة أثناء الحذف
            return Response({'error': f'فشل في حذف المنتج: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =================================
# Product Category ViewSet
# =================================

class ProductCategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint لفئات المنتجات - يدعم CRUD كامل
    """
    serializer_class = ProductCategorySerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """
        تخصيص queryset حسب المعاملات
        """
        queryset = ProductCategory.objects.all()
        
        # فلترة حسب المتجر
        store_id = self.request.query_params.get('store_id', None)
        if store_id:
            queryset = queryset.filter(store_id=store_id)
        
        return queryset

    def list(self, request, *args, **kwargs):
        """
        تخصيص response للقائمة - إرجاع قائمة فارغة إذا لم توجد نتائج
        """
        queryset = self.filter_queryset(self.get_queryset())
        
        if not queryset.exists():
            return Response([]) # إرجاع قائمة فارغة بدلاً من خطأ
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


# =================================
# Product Variant Views (باستخدام APIView كما كانت)
# =================================

class ProductVariantListCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, product_id, format=None):
        product = get_object_or_404(Product, pk=product_id)
        variants = ProductVariant.objects.filter(product=product)
        serializer = ProductVariantSerializer(variants, many=True)
        return Response(serializer.data)

    def post(self, request, product_id, format=None):
        product = get_object_or_404(Product, pk=product_id)
        data = request.data.copy()
        data['product'] = product.id
        serializer = ProductVariantSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductVariantRetrieveUpdateDestroyAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, pk):
        return get_object_or_404(ProductVariant, pk=pk)

    def get(self, request, pk, format=None):
        variant = self.get_object(pk)
        serializer = ProductVariantSerializer(variant)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        variant = self.get_object(pk)
        serializer = ProductVariantSerializer(variant, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        variant = self.get_object(pk)
        variant.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# يمكنك إضافة الـ Views الخاصة بالصور هنا بنفس الطريقة إذا كنت تحتاجها