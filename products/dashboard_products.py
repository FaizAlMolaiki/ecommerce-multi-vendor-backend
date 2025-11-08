from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.db import transaction

from products.models import Product, ProductCategory
from products.forms import ProductForm, ProductDeleteForm
from stores.models import Store


@staff_member_required
def products_list_view(request):
    """List products with filters: store, category, name"""
    # Toggle activation via POST
    if request.method == 'POST':
        action = request.POST.get('action')
        product_id = request.POST.get('product_id')
        if action in ('activate', 'deactivate') and product_id:
            p = Product.objects.filter(pk=product_id).first()
            if p:
                p.is_active = (action == 'activate')
                p.save(update_fields=['is_active'])
                messages.success(request, 'تم تحديث حالة المنتج')
            else:
                messages.error(request, 'المنتج غير موجود')
        else:
            messages.error(request, 'طلب غير صالح')
        return redirect('dashboard-products')

    qs = Product.objects.select_related('store', 'category').order_by('-id')

    store_id = request.GET.get('store')
    category_id = request.GET.get('category')
    name = request.GET.get('name')
    is_active = request.GET.get('is_active')  # '', '1', '0'

    if store_id:
        qs = qs.filter(store_id=store_id)
    if category_id:
        qs = qs.filter(category_id=category_id)
    if name:
        qs = qs.filter(name__icontains=name)
    if is_active in ('0','1'):
        qs = qs.filter(is_active=(is_active=='1'))

    page_number = request.GET.get('page') or 1
    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(page_number)

    stores = Store.objects.all().values('id', 'name')
    categories = ProductCategory.objects.all().values('id', 'name')

    context = {
        'page_obj': page_obj,
        'object_list': list(page_obj.object_list),
        'is_paginated': page_obj.has_other_pages(),
        'filters': {
            'store': store_id or '',
            'category': category_id or '',
            'name': name or '',
            'is_active': is_active or '',
        },
        'stores': list(stores),
        'categories': list(categories),
        'page_title': 'إدارة المنتجات',
        'create_url': '/dashboard/products/create/',
        'nav_active': 'products',
    }
    return render(request, 'dashboard/pages/products/list.html', context)


@staff_member_required
def product_detail_view(request, product_id: int):
    product = get_object_or_404(
        Product.objects.select_related('store', 'category').prefetch_related('variants', 'images'),
        pk=product_id,
    )
    # Toggle activation via POST
    if request.method == 'POST':
        action = request.POST.get('action')
        if action in ('activate', 'deactivate'):
            product.is_active = (action == 'activate')
            product.save(update_fields=['is_active'])
            messages.success(request, 'تم تحديث حالة المنتج')
        else:
            messages.error(request, 'إجراء غير صالح')
        return redirect('dashboard-product-detail', product_id=product.id)

    context = {
        'object': product,  # expected by templates
        'product': product,  # keep for backwards compatibility
        'variants': product.variants.all(),
        'images': product.images.all(),
        'nav_active': 'products',
    }
    return render(request, 'dashboard/pages/products/detail.html', context)


@staff_member_required
def product_create_view(request):
    """إضافة منتج جديد"""
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'تم إنشاء المنتج "{product.name}" بنجاح')
            return redirect('dashboard-product-detail', product_id=product.id)
        else:
            messages.error(request, 'يرجى تصحيح الأخطاء أدناه')
    else:
        form = ProductForm()
    
    context = {
        'form': form,
        'title': 'إضافة منتج جديد',
        'nav_active': 'products',
    }
    return render(request, 'dashboard/pages/products/form.html', context)


@staff_member_required
def product_edit_view(request, product_id: int):
    """تعديل بيانات المنتج"""
    product = get_object_or_404(Product, pk=product_id)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'تم تحديث المنتج "{product.name}" بنجاح')
            return redirect('dashboard-product-detail', product_id=product.id)
        else:
            messages.error(request, 'يرجى تصحيح الأخطاء أدناه')
    else:
        form = ProductForm(instance=product)
    
    # إعداد محتوى جدول المتغيرات
    from django.template.loader import render_to_string
    variants_table = render_to_string('dashboard/components/tables/variants_table.html', {
        'variants': product.variants.all()
    })
    
    context = {
        'form': form,
        'object': product,  # للتوافق مع القالب
        'product': product,
        'variants_table': variants_table,
        'title': f'تعديل المنتج: {product.name}',
        'nav_active': 'products',
    }
    return render(request, 'dashboard/pages/products/form.html', context)


@staff_member_required
def product_delete_view(request, product_id: int):
    """حذف المنتج"""
    product = get_object_or_404(Product, pk=product_id)
    
    # التحقق من وجود بيانات مرتبطة
    variant_count = product.variants.count()
    image_count = product.images.count()
    
    if request.method == 'POST':
        form = ProductDeleteForm(product, request.POST)
        if form.is_valid():
            product_name = product.name
            store_name = product.store.name
            
            # حذف المنتج مع جميع البيانات المرتبطة
            with transaction.atomic():
                # حذف المتغيرات والصور أولاً
                product.variants.all().delete()
                product.images.all().delete()
                # حذف المنتج
                product.delete()
            
            messages.success(request, f'تم حذف المنتج "{product_name}" من متجر "{store_name}" بنجاح')
            return redirect('dashboard-products')
        else:
            messages.error(request, 'يرجى تأكيد الحذف')
    else:
        form = ProductDeleteForm(product)
    
    context = {
        'form': form,
        'product': product,
        'variant_count': variant_count,
        'image_count': image_count,
        'nav_active': 'products',
    }
    return render(request, 'dashboard/pages/products/delete.html', context)
