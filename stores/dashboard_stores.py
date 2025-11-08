from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.db import transaction

from stores.models import Store, PlatformCategory
from stores.forms import StoreForm, StoreDeleteForm
from orders.models import Order
from products.models import Product


@staff_member_required
def stores_list_view(request):
    """List stores with filters and pagination"""
    # Toggle activation via POST
    if request.method == 'POST':
        action = request.POST.get('action')
        store_id = request.POST.get('store_id')
        
        # Debug logging
        print(f"DEBUG: action={action}, store_id={store_id}")
        print(f"DEBUG: POST data={request.POST}")
        
        if action in ('activate', 'deactivate') and store_id:
            try:
                st = Store.objects.get(pk=store_id)
                st.status = 'active' if action == 'activate' else 'suspended'
                st.save(update_fields=['status'])
                action_text = 'تفعيل' if action == 'activate' else 'تعطيل'
                messages.success(request, f'تم {action_text} المتجر "{st.name}" بنجاح')
            except Store.DoesNotExist:
                messages.error(request, 'المتجر غير موجود')
            except Exception as e:
                messages.error(request, f'حدث خطأ: {str(e)}')
        else:
            messages.error(request, f'طلب غير صالح - action: {action}, store_id: {store_id}')
        return redirect('dashboard-stores')

    qs = Store.objects.select_related('owner', 'platform_category').order_by('-id')

    # Filters
    status_filter = request.GET.get('status')  # 'active', 'pending', 'suspended', etc.
    name = request.GET.get('name')
    owner = request.GET.get('owner')  # owner email
    category = request.GET.get('category')  # platform_category id

    if status_filter:
        qs = qs.filter(status=status_filter)
    if name:
        qs = qs.filter(name__icontains=name)
    if owner:
        qs = qs.filter(owner__email__icontains=owner)
    if category:
        qs = qs.filter(platform_category_id=category)

    # Pagination
    page_number = request.GET.get('page') or 1
    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(page_number)

    categories = PlatformCategory.objects.all().values('id', 'name')

    context = {
        'page_obj': page_obj,
        'object_list': list(page_obj.object_list),  # for list_layout.html
        'is_paginated': page_obj.has_other_pages(),
        'filters': {
            'status': status_filter or '',
            'name': name or '',
            'owner': owner or '',
            'category': category or '',
        },
        'categories': list(categories),
        # Header and actions for list_layout.html
        'page_title': 'إدارة المتاجر',
        'create_url': '/dashboard/stores/create/',
        'nav_active': 'stores',
    }
    return render(request, 'dashboard/pages/stores/list.html', context)


@staff_member_required
def store_detail_view(request, store_id: int):
    store = get_object_or_404(Store.objects.select_related('owner', 'platform_category'), pk=store_id)

    # Toggle activation via POST
    if request.method == 'POST':
        action = request.POST.get('action')
        if action in ('activate', 'deactivate'):
            store.status = 'active' if action == 'activate' else 'suspended'
            store.save(update_fields=['status'])
            messages.success(request, 'تم تحديث حالة المتجر')
        else:
            messages.error(request, 'إجراء غير صالح')
        return redirect('dashboard-store-detail', store_id=store.id)

    product_count = store.products.count()
    # Orders related to this store (unified model)
    o_qs = Order.objects.filter(store=store)
    pending_count = o_qs.filter(fulfillment_status=Order.FulfillmentStatus.PENDING).count()
    in_delivery_count = o_qs.filter(fulfillment_status=Order.FulfillmentStatus.SHIPPED).count()
    latest_store_orders = o_qs.select_related('user').order_by('-id')[:10]

    # Top products in this store by selling_count
    top_products = Product.objects.filter(store=store).order_by('-selling_count')[:5]

    context = {
        'object': store,  # For detail_layout.html compatibility
        'store': store,   # Keep for backward compatibility
        'metrics': {
            'product_count': product_count,
            'pending_count': pending_count,
            'in_delivery_count': in_delivery_count,
        },
        'latest_store_orders': latest_store_orders,
        'top_products': top_products,
        'nav_active': 'stores',
    }
    return render(request, 'dashboard/pages/stores/detail.html', context)


@staff_member_required
def store_create_view(request):
    """إضافة متجر جديد"""
    if request.method == 'POST':
        form = StoreForm(request.POST)
        if form.is_valid():
            store = form.save()
            messages.success(request, f'تم إنشاء المتجر "{store.name}" بنجاح')
            return redirect('dashboard-store-detail', store_id=store.id)
        else:
            messages.error(request, 'يرجى تصحيح الأخطاء أدناه')
    else:
        form = StoreForm()
    
    context = {
        'form': form,
        'title': 'إضافة متجر جديد',
        'nav_active': 'stores',
    }
    return render(request, 'dashboard/pages/stores/form.html', context)


@staff_member_required
def store_edit_view(request, store_id: int):
    """تعديل بيانات المتجر"""
    store = get_object_or_404(Store, pk=store_id)
    
    if request.method == 'POST':
        form = StoreForm(request.POST, instance=store)
        if form.is_valid():
            store = form.save()
            messages.success(request, f'تم تحديث المتجر "{store.name}" بنجاح')
            return redirect('dashboard-store-detail', store_id=store.id)
        else:
            messages.error(request, 'يرجى تصحيح الأخطاء أدناه')
    else:
        form = StoreForm(instance=store)
    
    context = {
        'form': form,
        'store': store,
        'object': store,
        'title': f'تعديل المتجر: {store.name}',
        'nav_active': 'stores',
    }
    return render(request, 'dashboard/pages/stores/form.html', context)


@staff_member_required
def store_delete_view(request, store_id: int):
    """حذف المتجر"""
    store = get_object_or_404(Store, pk=store_id)
    
    # التحقق من وجود بيانات مرتبطة
    product_count = store.products.count()
    order_count = Order.objects.filter(store=store).count()
    
    if request.method == 'POST':
        form = StoreDeleteForm(store, request.POST)
        if form.is_valid():
            store_name = store.name
            
            # حذف المتجر مع جميع البيانات المرتبطة
            with transaction.atomic():
                # حذف المنتجات أولاً
                store.products.all().delete()
                # حذف المتجر
                store.delete()
            
            messages.success(request, f'تم حذف المتجر "{store_name}" وجميع بياناته بنجاح')
            return redirect('dashboard-stores')
        else:
            messages.error(request, 'يرجى تأكيد الحذف')
    else:
        form = StoreDeleteForm(store)
    
    context = {
        'form': form,
        'store': store,
        'product_count': product_count,
        'order_count': order_count,
        'nav_active': 'stores',
    }
    return render(request, 'dashboard/pages/stores/delete.html', context)
