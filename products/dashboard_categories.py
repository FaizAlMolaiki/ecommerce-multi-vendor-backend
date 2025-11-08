from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required, user_passes_test

from .models import ProductCategory
from .category_forms import ProductCategoryForm, ProductCategoryDeleteForm
from stores.models import Store


def is_staff_user(user):
    """التحقق من أن المستخدم موظف"""
    return user.is_authenticated and user.is_staff


@login_required
@user_passes_test(is_staff_user)
def product_categories_list_view(request):
    """عرض قائمة تصنيفات المنتجات"""
    
    # البحث والفلترة
    search_query = request.GET.get('search', '').strip()
    store_filter = request.GET.get('store', '').strip()
    
    # الاستعلام الأساسي مع الإحصائيات
    categories = ProductCategory.objects.select_related('store', 'parent').annotate(
        products_count=Count('products', distinct=True),
        children_count=Count('children', distinct=True)
    )
    
    # تطبيق البحث
    if search_query:
        categories = categories.filter(
            Q(name__icontains=search_query) |
            Q(store__name__icontains=search_query)
        )
    
    # فلترة حسب المتجر
    if store_filter:
        try:
            store_id = int(store_filter)
            categories = categories.filter(store_id=store_id)
        except (ValueError, TypeError):
            pass
    
    # الترتيب
    sort_by = request.GET.get('sort', 'store__name')
    if sort_by == 'products_count':
        categories = categories.order_by('-products_count', 'store__name', 'name')
    elif sort_by == 'children_count':
        categories = categories.order_by('-children_count', 'store__name', 'name')
    else:
        categories = categories.order_by('store__name', 'tree_id', 'lft')
    
    # الترقيم
    paginator = Paginator(categories, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # قائمة المتاجر للفلترة
    stores = Store.objects.filter(status=Store.StoreStatus.ACTIVE).order_by('name').values('id', 'name')
    
    context = {
        'page_obj': page_obj,
        'object_list': list(page_obj.object_list),
        'is_paginated': page_obj.has_other_pages(),
        'search_query': search_query,
        'store_filter': store_filter,
        'sort_by': sort_by,
        'stores': list(stores),
        'total_count': paginator.count,
        'page_title': 'تصنيفات المنتجات',
        'create_url': '/dashboard/product-categories/create/',
        'nav_active': 'product_categories'
    }
    
    return render(request, 'dashboard/pages/categories/list.html', context)


@login_required
@user_passes_test(is_staff_user)
def product_category_create_view(request):
    """إنشاء تصنيف منتج جديد"""
    
    if request.method == 'POST':
        form = ProductCategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'تم إنشاء قسم "{category.name}" في متجر "{category.store.name}" بنجاح')
            return redirect('dashboard-product-categories')
    else:
        form = ProductCategoryForm()
    
    context = {
        'form': form,
        'title': 'إضافة قسم منتجات جديد',
        'nav_active': 'product_categories'
    }
    
    return render(request, 'dashboard/pages/categories/form.html', context)


@login_required
@user_passes_test(is_staff_user)
def product_category_edit_view(request, category_id):
    """تعديل تصنيف منتج"""
    
    category = get_object_or_404(ProductCategory, id=category_id)
    
    if request.method == 'POST':
        form = ProductCategoryForm(request.POST, instance=category)
        if form.is_valid():
            updated_category = form.save()
            messages.success(request, f'تم تحديث قسم "{updated_category.name}" بنجاح')
            return redirect('dashboard-product-categories')
    else:
        form = ProductCategoryForm(instance=category)
    
    context = {
        'form': form,
        'category': category,
        'title': f'تعديل قسم "{category.name}"',
        'nav_active': 'product_categories'
    }
    
    return render(request, 'dashboard/pages/categories/form.html', context)


@login_required
@user_passes_test(is_staff_user)
def product_category_delete_view(request, category_id):
    """حذف تصنيف منتج"""
    
    category = get_object_or_404(ProductCategory, id=category_id)
    
    # جمع إحصائيات البيانات المرتبطة
    products_count = category.products.count()
    children_count = category.get_children().count()
    
    if request.method == 'POST':
        form = ProductCategoryDeleteForm(request.POST, instance=category)
        if form.is_valid():
            category_name = category.name
            store_name = category.store.name
            
            # حذف القسم (سيحذف الأقسام الفرعية والمنتجات ستصبح بدون قسم)
            category.delete()
            
            messages.success(request, f'تم حذف قسم "{category_name}" من متجر "{store_name}" بنجاح')
            return redirect('dashboard-product-categories')
    else:
        form = ProductCategoryDeleteForm(instance=category)
    
    context = {
        'form': form,
        'category': category,
        'products_count': products_count,
        'children_count': children_count,
        'nav_active': 'product_categories'
    }
    
    return render(request, 'dashboard/pages/categories/delete.html', context)


@login_required
@user_passes_test(is_staff_user)
def product_category_detail_view(request, category_id):
    """عرض تفاصيل تصنيف منتج"""
    
    category = get_object_or_404(ProductCategory, id=category_id)
    
    # جلب المنتجات المرتبطة
    products = category.products.order_by('name')[:10]
    products_count = category.products.count()
    
    # جلب الأقسام الفرعية
    children = category.get_children().order_by('name')
    
    context = {
        'category': category,
        'products': products,
        'products_count': products_count,
        'children': children,
        'nav_active': 'product_categories'
    }
    
    return render(request, 'dashboard/pages/categories/detail.html', context)


@login_required
@user_passes_test(is_staff_user)
def get_categories_by_store(request):
    """API لجلب الأقسام حسب المتجر (للاستخدام في JavaScript)"""
    
    store_id = request.GET.get('store_id')
    if not store_id:
        return JsonResponse({'categories': []})
    
    try:
        store_id = int(store_id)
        categories = ProductCategory.objects.filter(store_id=store_id).order_by('name')
        categories_data = [
            {
                'id': cat.id,
                'name': cat.name,
                'level': cat.level
            }
            for cat in categories
        ]
        return JsonResponse({'categories': categories_data})
    except (ValueError, TypeError):
        return JsonResponse({'categories': []})
