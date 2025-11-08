from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.core.paginator import Paginator

from accounts.models import User, StaffProfile
from accounts.forms import StaffProfileForm, StaffProfileDeleteForm


@staff_member_required
def staff_profiles_list_view(request):
    """List all staff profiles with basic filters"""
    qs = StaffProfile.objects.select_related('user').all().order_by('user__id')

    email = request.GET.get('email')
    job_title = request.GET.get('job_title')

    if email:
        qs = qs.filter(user__email__icontains=email)
    if job_title:
        qs = qs.filter(job_title__icontains=job_title)

    page_number = request.GET.get('page') or 1
    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'object_list': list(page_obj.object_list),
        'is_paginated': page_obj.has_other_pages(),
        'filters': {
            'email': email or '',
            'job_title': job_title or '',
        },
        'page_title': 'ملفات الموظفين',
        'nav_active': 'users',
    }
    return render(request, 'dashboard/pages/staff_profiles/list.html', context)


@staff_member_required
def staff_profile_create_view(request, user_id: int):
    """Create a StaffProfile for a given user id"""
    user = get_object_or_404(User, pk=user_id)
    if hasattr(user, 'staffprofile'):
        messages.info(request, 'لدى هذا المستخدم ملف موظف بالفعل، يمكنك تعديله')
        return redirect('dashboard-staff-profile-edit', user_id=user.id)

    if request.method == 'POST':
        form = StaffProfileForm(request.POST, request.FILES)
        if form.is_valid():
            sp = form.save(commit=False)
            sp.user = user
            sp.save()
            messages.success(request, f'تم إنشاء ملف الموظف للمستخدم "{user.email}" بنجاح')
            return redirect('dashboard-staff-profile-edit', user_id=user.id)
        else:
            messages.error(request, 'يرجى تصحيح الأخطاء أدناه')
    else:
        form = StaffProfileForm()

    context = {
        'form': form,
        'user': user,
        'title': f'إنشاء ملف موظف: {user.email}',
        'nav_active': 'users',
    }
    return render(request, 'dashboard/pages/staff_profiles/form.html', context)


@staff_member_required
def staff_profile_edit_view(request, user_id: int):
    """Edit an existing StaffProfile by user id"""
    user = get_object_or_404(User, pk=user_id)
    sp = getattr(user, 'staffprofile', None)
    if not sp:
        messages.info(request, 'لا يوجد ملف موظف لهذا المستخدم، يمكنك إنشاؤه الآن')
        return redirect('dashboard-staff-profile-create', user_id=user.id)

    if request.method == 'POST':
        form = StaffProfileForm(request.POST, request.FILES, instance=sp)
        if form.is_valid():
            form.save()
            messages.success(request, f'تم تحديث ملف الموظف للمستخدم "{user.email}" بنجاح')
            return redirect('dashboard-staff-profile-edit', user_id=user.id)
        else:
            messages.error(request, 'يرجى تصحيح الأخطاء أدناه')
    else:
        form = StaffProfileForm(instance=sp)

    context = {
        'form': form,
        'user': user,
        'title': f'تعديل ملف الموظف: {user.email}',
        'nav_active': 'users',
    }
    return render(request, 'dashboard/pages/staff_profiles/form.html', context)


@staff_member_required
def staff_profile_delete_view(request, user_id: int):
    """Delete an existing StaffProfile by user id"""
    user = get_object_or_404(User, pk=user_id)
    sp = getattr(user, 'staffprofile', None)
    if not sp:
        messages.error(request, 'لا يوجد ملف موظف لحذفه')
        return redirect('dashboard-users')

    if request.method == 'POST':
        form = StaffProfileDeleteForm(request.POST)
        if form.is_valid():
            sp.delete()
            messages.success(request, f'تم حذف ملف الموظف للمستخدم "{user.email}" بنجاح')
            return redirect('dashboard-users')
        else:
            messages.error(request, 'يرجى تأكيد الحذف')
    else:
        form = StaffProfileDeleteForm()

    context = {
        'form': form,
        'user': user,
        'title': f'حذف ملف الموظف: {user.email}',
        'nav_active': 'users',
    }
    return render(request, 'dashboard/pages/staff_profiles/delete.html', context)
