from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.db import transaction

from accounts.models import User, StaffProfile
from accounts.forms import UserForm, UserDeleteForm, UserPasswordResetForm


@staff_member_required
def users_list_view(request):
    """List users with role/status filters and pagination"""
    # Handle POST actions for toggling flags
    if request.method == 'POST':
        action = request.POST.get('action')
        user_id = request.POST.get('user_id')
        u = User.objects.filter(pk=user_id).first()
        if u and action:
            if action == 'toggle_active':
                u.is_active = not u.is_active
                u.save(update_fields=['is_active'])
                messages.success(request, 'تم تبديل حالة تنشيط المستخدم')
            elif action == 'toggle_staff':
                u.is_staff = not u.is_staff
                u.save(update_fields=['is_staff'])
                messages.success(request, 'تم تبديل حالة الموظف للمستخدم')
            elif action == 'toggle_vendor' and hasattr(u, 'is_vendor'):
                u.is_vendor = not getattr(u, 'is_vendor')
                u.save(update_fields=['is_vendor'])
                messages.success(request, 'تم تبديل دور البائع')
            elif action == 'toggle_delivery' and hasattr(u, 'is_delivery'):
                u.is_delivery = not getattr(u, 'is_delivery')
                u.save(update_fields=['is_delivery'])
                messages.success(request, 'تم تبديل دور المندوب')
            else:
                messages.error(request, 'إجراء غير مدعوم أو خاصية غير متاحة')
        else:
            messages.error(request, 'مستخدم غير موجود أو طلب غير صالح')
        return redirect('dashboard-users')

    qs = User.objects.all().order_by('-id')

    email = request.GET.get('email')
    is_active = request.GET.get('is_active')  # '', '1', '0'
    is_staff = request.GET.get('is_staff')    # '', '1', '0'
    is_vendor = request.GET.get('is_vendor')  # '', '1', '0'
    is_delivery = request.GET.get('is_delivery')  # '', '1', '0'

    if email:
        qs = qs.filter(email__icontains=email)
    if is_active in ('0','1'):
        qs = qs.filter(is_active=(is_active=='1'))
    if is_staff in ('0','1'):
        qs = qs.filter(is_staff=(is_staff=='1'))
    # Optional fields if exist on custom user
    if hasattr(User, 'is_vendor') and is_vendor in ('0','1'):
        qs = qs.filter(is_vendor=(is_vendor=='1'))
    if hasattr(User, 'is_delivery') and is_delivery in ('0','1'):
        qs = qs.filter(is_delivery=(is_delivery=='1'))

    page_number = request.GET.get('page') or 1
    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'object_list': list(page_obj.object_list),  # required by list_layout.html
        'is_paginated': page_obj.has_other_pages(),
        'filters': {
            'email': email or '',
            'is_active': is_active or '',
            'is_staff': is_staff or '',
            'is_vendor': is_vendor or '',
            'is_delivery': is_delivery or '',
        },
        'page_title': 'إدارة المستخدمين',
        'create_url': '/dashboard/users/create/',
        'nav_active': 'users',
    }
    return render(request, 'dashboard/pages/users/list.html', context)


@staff_member_required
def user_detail_view(request, user_id: int):
    user = get_object_or_404(User.objects.all(), pk=user_id)

    # Optional POST toggles (same as list)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'toggle_active':
            user.is_active = not user.is_active
            user.save(update_fields=['is_active'])
        elif action == 'toggle_staff':
            user.is_staff = not user.is_staff
            user.save(update_fields=['is_staff'])
        elif action == 'toggle_vendor' and hasattr(user, 'is_vendor'):
            user.is_vendor = not getattr(user, 'is_vendor')
            user.save(update_fields=['is_vendor'])
        elif action == 'toggle_delivery' and hasattr(user, 'is_delivery'):
            user.is_delivery = not getattr(user, 'is_delivery')
            user.save(update_fields=['is_delivery'])
        return redirect('dashboard-user-detail', user_id=user.id)

    # Safely fetch related profiles (may not exist)
    try:
        delivery_profile = getattr(user, 'deliveryprofile', None)
    except Exception:
        delivery_profile = None
    try:
        staff_profile = getattr(user, 'staffprofile', None)
    except Exception:
        staff_profile = None

    context = {
        'object': user,
        'u': user,
        'delivery_profile': delivery_profile,
        'staff_profile': staff_profile,
        'nav_active': 'users',
    }
    return render(request, 'dashboard/pages/users/detail.html', context)


@staff_member_required
def user_create_view(request):
    """إضافة مستخدم جديد"""
    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES, is_edit=False)
        if form.is_valid():
            user = form.save()
            # Create DeliveryProfile if role is delivery
            try:
                if getattr(user, 'is_delivery', False):
                    vehicle_type = form.cleaned_data.get('delivery_vehicle_type') or ''
                    id_img = form.cleaned_data.get('delivery_id_card_image')
                    license_img = form.cleaned_data.get('delivery_driver_license_image')
                    # create only if any delivery data provided or simply role is set
                    dp, created = DeliveryProfile.objects.get_or_create(user=user)
                    if vehicle_type:
                        dp.vehicle_type = vehicle_type
                    if id_img:
                        dp.id_card_image = id_img
                    if license_img:
                        dp.driver_license_image = license_img
                    # keep default verification_status (PENDING)
                    dp.save()
            except Exception:
                # fail silently to avoid blocking user creation; detailed logging could be added
                pass

            # Create StaffProfile if role is staff
            try:
                if getattr(user, 'is_staff', False):
                    job_title = form.cleaned_data.get('staff_job_title') or ''
                    staff_id_img = form.cleaned_data.get('staff_id_card_image')
                    staff_cv = form.cleaned_data.get('staff_resume_cv')
                    sp, created = StaffProfile.objects.get_or_create(user=user)
                    if job_title:
                        sp.job_title = job_title
                    if staff_id_img:
                        sp.id_card_image = staff_id_img
                    if staff_cv:
                        sp.resume_cv = staff_cv
                    sp.save()
            except Exception:
                pass
            messages.success(request, f'تم إنشاء المستخدم "{user.email}" بنجاح')
            return redirect('dashboard-user-detail', user_id=user.id)
        else:
            messages.error(request, 'يرجى تصحيح الأخطاء أدناه')
    else:
        form = UserForm(is_edit=False)
    
    context = {
        'form': form,
        'title': 'إضافة مستخدم جديد',
        'nav_active': 'users',
    }
    return render(request, 'dashboard/pages/users/form.html', context)


@staff_member_required
def user_edit_view(request, user_id: int):
    """تعديل بيانات المستخدم"""
    user = get_object_or_404(User, pk=user_id)
    
    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES, instance=user, is_edit=True)
        if form.is_valid():
            user = form.save()
            # Update/Create DeliveryProfile if role is delivery
            try:
                if getattr(user, 'is_delivery', False):
                    vehicle_type = form.cleaned_data.get('delivery_vehicle_type') or ''
                    id_img = form.cleaned_data.get('delivery_id_card_image')
                    license_img = form.cleaned_data.get('delivery_driver_license_image')
                    dp, created = DeliveryProfile.objects.get_or_create(user=user)
                    if vehicle_type:
                        dp.vehicle_type = vehicle_type
                    if id_img:
                        dp.id_card_image = id_img
                    if license_img:
                        dp.driver_license_image = license_img
                    dp.save()
                else:
                    # If role delivery unchecked, do nothing or optionally delete profile
                    pass
            except Exception:
                pass

            # Update/Create StaffProfile if role is staff
            try:
                if getattr(user, 'is_staff', False):
                    job_title = form.cleaned_data.get('staff_job_title') or ''
                    staff_id_img = form.cleaned_data.get('staff_id_card_image')
                    staff_cv = form.cleaned_data.get('staff_resume_cv')
                    sp, created = StaffProfile.objects.get_or_create(user=user)
                    if job_title:
                        sp.job_title = job_title
                    if staff_id_img:
                        sp.id_card_image = staff_id_img
                    if staff_cv:
                        sp.resume_cv = staff_cv
                    sp.save()
                else:
                    # if staff unchecked, do nothing (retain profile) or delete it based on policy
                    pass
            except Exception:
                pass
            messages.success(request, f'تم تحديث المستخدم "{user.email}" بنجاح')
            return redirect('dashboard-user-detail', user_id=user.id)
        else:
            messages.error(request, 'يرجى تصحيح الأخطاء أدناه')
    else:
        form = UserForm(instance=user, is_edit=True)
    
    context = {
        'form': form,
        'user': user,
        'title': f'تعديل المستخدم: {user.email}',
        'nav_active': 'users',
    }
    return render(request, 'dashboard/pages/users/form.html', context)


@staff_member_required
def user_delete_view(request, user_id: int):
    """حذف المستخدم"""
    user = get_object_or_404(User, pk=user_id)
    
    # منع حذف المستخدم الحالي
    if user == request.user:
        messages.error(request, 'لا يمكنك حذف حسابك الخاص')
        return redirect('dashboard-user-detail', user_id=user.id)
    
    # التحقق من وجود بيانات مرتبطة
    stores_count = getattr(user, 'stores', None)
    stores_count = stores_count.count() if stores_count else 0
    addresses_count = getattr(user, 'addresses', None)
    addresses_count = addresses_count.count() if addresses_count else 0
    
    if request.method == 'POST':
        form = UserDeleteForm(user, request.POST)
        if form.is_valid():
            user_email = user.email
            user_name = user.name or 'غير محدد'
            
            # حذف المستخدم مع جميع البيانات المرتبطة
            with transaction.atomic():
                # حذف العناوين أولاً
                if hasattr(user, 'addresses'):
                    user.addresses.all().delete()
                # حذف المستخدم (المتاجر ستحذف تلقائياً حسب on_delete)
                user.delete()
            
            messages.success(request, f'تم حذف المستخدم "{user_email}" ({user_name}) بنجاح')
            return redirect('dashboard-users')
        else:
            messages.error(request, 'يرجى تأكيد الحذف')
    else:
        form = UserDeleteForm(user)
    
    context = {
        'form': form,
        'user': user,
        'stores_count': stores_count,
        'addresses_count': addresses_count,
        'nav_active': 'users',
    }
    return render(request, 'dashboard/pages/users/delete.html', context)


@staff_member_required
def user_password_reset_view(request, user_id: int):
    """إعادة تعيين كلمة مرور المستخدم"""
    user = get_object_or_404(User, pk=user_id)
    
    if request.method == 'POST':
        form = UserPasswordResetForm(user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f'تم تغيير كلمة مرور المستخدم "{user.email}" بنجاح')
            return redirect('dashboard-user-detail', user_id=user.id)
        else:
            messages.error(request, 'يرجى تصحيح الأخطاء أدناه')
    else:
        form = UserPasswordResetForm(user)
    
    context = {
        'form': form,
        'user': user,
        'title': f'إعادة تعيين كلمة مرور: {user.email}',
        'nav_active': 'users',
    }
    return render(request, 'dashboard/pages/users/password_reset.html', context)
