from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from stores.models import Store
from products.models import Product, ProductVariant
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import CartItem
from .grouped_cart_serializers import GroupedCartByStoreSerializer
from decimal import Decimal
import json


@staff_member_required
def get_stores_api(request):
    """جلب المتاجر النشطة"""
    stores = Store.objects.filter(status='active').values('id', 'name').order_by('name')
    return JsonResponse({'stores': list(stores)})


@staff_member_required
def get_products_by_store_api(request):
    """جلب منتجات المتجر"""
    store_id = request.GET.get('store_id')
    if not store_id:
        return JsonResponse({'error': 'معرف المتجر مطلوب'}, status=400)
    
    # Debug logging
    print(f"Looking for products in store_id: {store_id}")
    
    products = Product.objects.filter(
        store_id=store_id
    ).values('id', 'name').order_by('name')
    
    products_list = list(products)
    print(f"Found {len(products_list)} products: {products_list}")
    
    return JsonResponse({'products': products_list})


@staff_member_required
def get_product_variants_api(request):
    """جلب متغيرات المنتج"""
    product_id = request.GET.get('product_id')
    if not product_id:
        return JsonResponse({'error': 'معرف المنتج مطلوب'}, status=400)
    
    variants = ProductVariant.objects.filter(
        product_id=product_id
    ).values('id', 'options', 'price').order_by('price')
    
    variants_list = []
    for variant in variants:
        # تحسين عرض الخيارات
        options_display = "خيارات افتراضية"
        if variant['options']:
            try:
                options = variant['options']
                if isinstance(options, dict) and options:
                    options_display = " - ".join([f"{k}: {v}" for k, v in options.items()])
            except:
                pass
        
        variants_list.append({
            'id': variant['id'],
            'options_display': options_display,
            'price': float(variant['price'])
        })
    
    return JsonResponse({'variants': variants_list})


# ===================================================================
# ✅ REST API endpoints للـ Cart
# ===================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def grouped_cart_view(request):
    """
    ✅ عرض السلة مجمّعة حسب المتاجر
    
    GET /api/v1/orders/cart/grouped/
    
    Response:
    {
        "stores": [
            {
                "id": 1,
                "name": "متجر أ",
                "logo": "url",
                "cover_image": "url",
                "store_sub_total": 150.00,
                "items": [...]
            }
        ],
        "grand_total": 350.00,
        "total_items": 5
    }
    """
    user = request.user
    cart_items = CartItem.objects.filter(user=user).select_related(
        'variant__product__store'
    ).order_by('variant__product__store__name', 'added_at')
    
    if not cart_items.exists():
        return Response({
            'stores': [],
            'grand_total': 0,
            'total_items': 0
        })
    
    # تجميع العناصر حسب المتجر
    stores_dict = {}
    grand_total = Decimal('0')
    total_items = 0
    
    for item in cart_items:
        store = item.variant.product.store
        store_id = store.id
        
        if store_id not in stores_dict:
            stores_dict[store_id] = {
                'id': store.id,
                'name': store.name,
                'logo': store.logo_url or None,
                'cover_image': store.cover_image_url or None,
                'store_sub_total': Decimal('0'),
                'items': []
            }
        
        # حساب المجموع
        line_total = item.variant.price * item.quantity
        stores_dict[store_id]['store_sub_total'] += line_total
        grand_total += line_total
        total_items += item.quantity
        
        # إضافة العنصر
        stores_dict[store_id]['items'].append(item)
    
    # تحويل القاموس لقائمة
    stores_list = list(stores_dict.values())
    
    # استخدام Serializer
    serializer = GroupedCartByStoreSerializer(
        stores_list, 
        many=True, 
        context={'request': request}
    )
    
    return Response({
        'stores': serializer.data,
        'grand_total': float(grand_total),
        'total_items': total_items
    })
