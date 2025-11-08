from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required, user_passes_test

from .models import PlatformCategory
from .category_forms import PlatformCategoryForm, PlatformCategoryDeleteForm


def is_staff_user(user):
    """التحقق من أن المستخدم موظف"""
    return user.is_authenticated and user.is_staff


@login_required
@user_passes_test(is_staff_user)
def platform_categories_list_view(request):
    """عرض قائمة تصنيفات المتاجر"""
    
    # البحث والفلترة
    search_query = request.GET.get('search', '').strip()
    
    # الاستعلام الأساسي مع الإحصائيات
    categories = PlatformCategory.objects.annotate(
        stores_count=Count('stores', distinct=True)
    )
    
    # تطبيق البحث
    if search_query:
        categories = categories.filter(
            Q(name__icontains=search_query)
        )
    
    # الترتيب
    sort_by = request.GET.get('sort', 'name')
    if sort_by == 'stores_count':
        categories = categories.order_by('-stores_count', 'name')
    else:
        categories = categories.order_by('name')
    
    # الترقيم
    paginator = Paginator(categories, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'sort_by': sort_by,
        'total_count': paginator.count,
        'nav_active': 'platform_categories'
    }
    
    return render(request, 'dashboard/pages/platform_categories/list.html', context)


@login_required
@user_passes_test(is_staff_user)
def platform_category_create_view(request):
    """إنشاء تصنيف متجر جديد"""
    
    if request.method == 'POST':
        form = PlatformCategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'تم إنشاء تصنيف "{category.name}" بنجاح')
            return redirect('dashboard-platform-categories')
    else:
        form = PlatformCategoryForm()
    
    context = {
        'form': form,
        'title': 'إضافة تصنيف متجر جديد',
        'nav_active': 'platform_categories'
    }
    
    return render(request, 'dashboard/pages/platform_categories/form.html', context)


@login_required
@user_passes_test(is_staff_user)
def platform_category_edit_view(request, category_id):
    """تعديل تصنيف متجر"""
    
    category = get_object_or_404(PlatformCategory, id=category_id)
    
    if request.method == 'POST':
        form = PlatformCategoryForm(request.POST, instance=category)
        if form.is_valid():
            updated_category = form.save()
            messages.success(request, f'تم تحديث تصنيف "{updated_category.name}" بنجاح')
            return redirect('dashboard-platform-categories')
    else:
        form = PlatformCategoryForm(instance=category)
    
    context = {
        'form': form,
        'category': category,
        'title': f'تعديل تصنيف "{category.name}"',
        'nav_active': 'platform_categories'
    }
    
    return render(request, 'dashboard/pages/platform_categories/form.html', context)


@login_required
@user_passes_test(is_staff_user)
def platform_category_delete_view(request, category_id):
    """حذف تصنيف متجر"""
    
    category = get_object_or_404(PlatformCategory, id=category_id)
    
    # جمع إحصائيات البيانات المرتبطة
    stores_count = category.stores.count()
    
    if request.method == 'POST':
        form = PlatformCategoryDeleteForm(request.POST, instance=category)
        if form.is_valid():
            category_name = category.name
            
            # حذف التصنيف (المتاجر ستصبح بدون تصنيف لأن العلاقة SET_NULL)
            category.delete()
            
            messages.success(request, f'تم حذف تصنيف "{category_name}" بنجاح')
            return redirect('dashboard-platform-categories')
    else:
        form = PlatformCategoryDeleteForm(instance=category)
    
    context = {
        'form': form,
        'category': category,
        'stores_count': stores_count,
        'nav_active': 'platform_categories'
    }
    
    return render(request, 'dashboard/pages/platform_categories/delete.html', context)


@login_required
@user_passes_test(is_staff_user)
def platform_category_detail_view(request, category_id):
    """عرض تفاصيل تصنيف متجر"""
    
    category = get_object_or_404(PlatformCategory, id=category_id)
    
    # جلب المتاجر المرتبطة
    stores = category.stores.filter(status='active').order_by('name')[:10]
    stores_count = category.stores.count()
    
    context = {
        'category': category,
        'stores': stores,
        'stores_count': stores_count,
        'nav_active': 'platform_categories'
    }
    
    return render(request, 'dashboard/pages/platform_categories/detail.html', context)
