from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.core.paginator import Paginator

from accounts.models import User
from .models import DeliveryProfile
from .forms import DeliveryProfileForm, DeliveryProfileDeleteForm

@staff_member_required
def delivery_profiles_list_view(request):
    """List all delivery profiles with basic filters"""
    qs = DeliveryProfile.objects.select_related('user').all().order_by('-last_seen_at', 'user__id')

    email = request.GET.get('email')
    status = request.GET.get('verification_status')
    suspended = request.GET.get('suspended')  # '1' or '0'

    if email:
        qs = qs.filter(user__email__icontains=email)
    if status:
        qs = qs.filter(verification_status=status)
    if suspended in ('0', '1'):
        qs = qs.filter(suspended=(suspended == '1'))

    page_number = request.GET.get('page') or 1
    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'object_list': list(page_obj.object_list),
        'is_paginated': page_obj.has_other_pages(),
        'filters': {
            'email': email or '',
            'verification_status': status or '',
            'suspended': suspended or '',
        },
        'page_title': 'ملفات المندوبين',
        'nav_active': 'users',
    }
    return render(request, 'dashboard/pages/delivery_profiles/list.html', context)


@staff_member_required
def delivery_profile_create_view(request, user_id: int):
    """Create a DeliveryProfile for a given user id"""
    user = get_object_or_404(User, pk=user_id)
    if hasattr(user, 'deliveryprofile'):
        messages.info(request, 'لدى هذا المستخدم ملف مندوب بالفعل، يمكنك تعديله')
        return redirect('dashboard-delivery-profile-edit', user_id=user.id)

    if request.method == 'POST':
        form = DeliveryProfileForm(request.POST, request.FILES)
        if form.is_valid():
            dp = form.save(commit=False)
            dp.user = user
            dp.save()
            messages.success(request, f'تم إنشاء ملف المندوب للمستخدم "{user.email}" بنجاح')
            return redirect('dashboard-delivery-profile-edit', user_id=user.id)
        else:
            messages.error(request, 'يرجى تصحيح الأخطاء أدناه')
    else:
        form = DeliveryProfileForm()

    context = {
        'form': form,
        'user': user,
        'title': f'إنشاء ملف مندوب: {user.email}',
        'nav_active': 'users',
    }
    return render(request, 'dashboard/pages/delivery_profiles/form.html', context)


@staff_member_required
def delivery_profile_edit_view(request, user_id: int):
    """Edit an existing DeliveryProfile by user id"""
    user = get_object_or_404(User, pk=user_id)
    dp = getattr(user, 'deliveryprofile', None)
    if not dp:
        messages.info(request, 'لا يوجد ملف مندوب لهذا المستخدم، يمكنك إنشاؤه الآن')
        return redirect('dashboard-delivery-profile-create', user_id=user.id)

    if request.method == 'POST':
        form = DeliveryProfileForm(request.POST, request.FILES, instance=dp)
        if form.is_valid():
            form.save()
            messages.success(request, f'تم تحديث ملف المندوب للمستخدم "{user.email}" بنجاح')
            return redirect('dashboard-delivery-profile-edit', user_id=user.id)
        else:
            messages.error(request, 'يرجى تصحيح الأخطاء أدناه')
    else:
        form = DeliveryProfileForm(instance=dp)

    context = {
        'form': form,
        'user': user,
        'title': f'تعديل ملف المندوب: {user.email}',
        'nav_active': 'users',
    }
    return render(request, 'dashboard/pages/delivery_profiles/form.html', context)


@staff_member_required
def delivery_profile_delete_view(request, user_id: int):
    """Delete an existing DeliveryProfile by user id"""
    user = get_object_or_404(User, pk=user_id)
    dp = getattr(user, 'deliveryprofile', None)
    if not dp:
        messages.error(request, 'لا يوجد ملف مندوب لحذفه')
        return redirect('dashboard-users')

    if request.method == 'POST':
        form = DeliveryProfileDeleteForm(request.POST)
        if form.is_valid():
            dp.delete()
            messages.success(request, f'تم حذف ملف المندوب للمستخدم "{user.email}" بنجاح')
            return redirect('dashboard-users')
        else:
            messages.error(request, 'يرجى تأكيد الحذف')
    else:
        form = DeliveryProfileDeleteForm()

    context = {
        'form': form,
        'user': user,
        'title': f'حذف ملف المندوب: {user.email}',
        'nav_active': 'users',
    }
    return render(request, 'dashboard/pages/delivery_profiles/delete.html', context)
