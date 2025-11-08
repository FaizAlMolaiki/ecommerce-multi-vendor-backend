from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from wishlist.models import UserProductFavorite, UserStoreFavorite
from wishlist.forms import UserProductFavoriteForm, UserStoreFavoriteForm, ProductFavoriteDeleteForm, StoreFavoriteDeleteForm
from products.models import Product
from stores.models import Store
from accounts.models import User


@staff_member_required
def wishlist_list_view(request):
    """
    Dashboard list for users' favorites with filters and pagination.
    Shows favorite products and favorite stores in the same page using two paginated lists.
    """
    # Filters
    email = request.GET.get('email')
    product_id = request.GET.get('product')
    store_id = request.GET.get('store')

    upf_qs = UserProductFavorite.objects.select_related('user', 'product').order_by('-created_at')
    usf_qs = UserStoreFavorite.objects.select_related('user', 'store').order_by('-created_at')

    if email:
        upf_qs = upf_qs.filter(user__email__icontains=email)
        usf_qs = usf_qs.filter(user__email__icontains=email)
    if product_id:
        upf_qs = upf_qs.filter(product_id=product_id)
    if store_id:
        usf_qs = usf_qs.filter(store_id=store_id)

    upf_page_number = request.GET.get('upf_page') or 1
    usf_page_number = request.GET.get('usf_page') or 1
    upf_page = Paginator(upf_qs, 20).get_page(upf_page_number)
    usf_page = Paginator(usf_qs, 20).get_page(usf_page_number)

    products = Product.objects.all().values('id', 'name')
    stores = Store.objects.all().values('id', 'name')

    context = {
        'upf_page': upf_page,
        'usf_page': usf_page,
        'filters': {
            'email': email or '',
            'product': product_id or '',
            'store': store_id or '',
        },
        'products': list(products),
        'stores': list(stores),
        'nav_active': 'wishlist',
    }
    return render(request, 'dashboard/pages/wishlist/list.html', context)


@staff_member_required
def product_favorite_create_view(request):
    """إضافة منتج جديد للمفضلة"""
    if request.method == 'POST':
        form = UserProductFavoriteForm(request.POST)
        if form.is_valid():
            favorite = form.save()
            messages.success(request, f'تم إضافة المنتج "{favorite.product.name}" إلى مفضلة {favorite.user.email} بنجاح')
            return redirect('dashboard-wishlist')
        else:
            messages.error(request, 'يرجى تصحيح الأخطاء أدناه')
    else:
        form = UserProductFavoriteForm()
    
    return render(request, 'dashboard/pages/wishlist/product_favorite_form.html', {
        'form': form,
        'title': 'إضافة منتج للمفضلة'
    })


@staff_member_required
def store_favorite_create_view(request):
    """إضافة متجر جديد للمفضلة"""
    if request.method == 'POST':
        form = UserStoreFavoriteForm(request.POST)
        if form.is_valid():
            favorite = form.save()
            messages.success(request, f'تم إضافة المتجر "{favorite.store.name}" إلى مفضلة {favorite.user.email} بنجاح')
            return redirect('dashboard-wishlist')
        else:
            messages.error(request, 'يرجى تصحيح الأخطاء أدناه')
    else:
        form = UserStoreFavoriteForm()
    
    return render(request, 'dashboard/pages/wishlist/store_favorite_form.html', {
        'form': form,
        'title': 'إضافة متجر للمفضلة'
    })


@staff_member_required
def product_favorite_delete_view(request, favorite_id):
    """حذف منتج من المفضلة"""
    favorite = get_object_or_404(UserProductFavorite, id=favorite_id)
    
    if request.method == 'POST':
        # دعم كل من confirm (التخطيط الموحد) و confirm_delete (النموذج القديم)
        confirmed = request.POST.get('confirm') or request.POST.get('confirm_delete')
        form = ProductFavoriteDeleteForm(request.POST)
        if confirmed or form.is_valid():
            product_name = favorite.product.name
            user_email = favorite.user.email
            favorite.delete()
            messages.success(request, f'تم حذف المنتج "{product_name}" من مفضلة {user_email} بنجاح')
            return redirect('dashboard-wishlist')
        else:
            messages.error(request, 'يجب تأكيد الحذف للمتابعة')
    else:
        form = ProductFavoriteDeleteForm()

    item_obj = favorite.product
    context = {
        'form': form,
        'favorite': favorite,
        'object': item_obj,
        'item_type': 'المنتج',
        'page_title': 'حذف منتج من المفضلة',
        'back_url': '/dashboard/wishlist/',
        'cancel_url': '/dashboard/wishlist/',
        'title': 'حذف منتج من المفضلة',
    }
    return render(request, 'dashboard/pages/wishlist/product_favorite_delete.html', context)


@staff_member_required
def store_favorite_delete_view(request, favorite_id):
    """حذف متجر من المفضلة"""
    favorite = get_object_or_404(UserStoreFavorite, id=favorite_id)
    
    if request.method == 'POST':
        # دعم كل من confirm (التخطيط الموحد) و confirm_delete (النموذج القديم)
        confirmed = request.POST.get('confirm') or request.POST.get('confirm_delete')
        form = StoreFavoriteDeleteForm(request.POST)
        if confirmed or form.is_valid():
            store_name = favorite.store.name
            user_email = favorite.user.email
            favorite.delete()
            messages.success(request, f'تم حذف المتجر "{store_name}" من مفضلة {user_email} بنجاح')
            return redirect('dashboard-wishlist')
        else:
            messages.error(request, 'يجب تأكيد الحذف للمتابعة')
    else:
        form = StoreFavoriteDeleteForm()

    item_obj = favorite.store
    context = {
        'form': form,
        'favorite': favorite,
        'object': item_obj,
        'item_type': 'المتجر',
        'page_title': 'حذف متجر من المفضلة',
        'back_url': '/dashboard/wishlist/',
        'cancel_url': '/dashboard/wishlist/',
        'title': 'حذف متجر من المفضلة',
    }
    return render(request, 'dashboard/pages/wishlist/store_favorite_delete.html', context)
