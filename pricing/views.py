from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse

from .models import Promotion, Coupon, Offer
from .forms import (
    PromotionForm, PromotionDeleteForm,
    CouponForm, CouponDeleteForm,
    OfferForm, OfferDeleteForm,
)


# ============ Promotions ============
def promotions_list_view(request):
    qs = Promotion.objects.all().select_related('required_coupon')
    context = {
        "page_title": "الخصومات التلقائية",
        "object_list": qs,
        "nav_active": "promotions",
        "create_url": "/dashboard/pricing/promotions/create/",
        "create_text": "إضافة خصم جديد",
    }
    return render(request, "dashboard/pages/pricing/promotion_list.html", context)


def promotion_create_view(request):
    if request.method == "POST":
        form = PromotionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "تم إنشاء الخصم بنجاح")
            return redirect(reverse("dashboard-promotions"))
    else:
        form = PromotionForm()
    
    context = {
        "form": form, 
        "mode": "create",
        "page_title": "إنشاء خصم جديد",
        "nav_active": "promotions",
    }
    return render(request, "dashboard/pages/pricing/promotion_form.html", context)


def promotion_edit_view(request, promotion_id: int):
    obj = get_object_or_404(Promotion, pk=promotion_id)
    if request.method == "POST":
        form = PromotionForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "تم تعديل الخصم بنجاح")
            return redirect(reverse("dashboard-promotions"))
    else:
        form = PromotionForm(instance=obj)
    
    context = {
        "form": form, 
        "mode": "edit", 
        "object": obj,
        "page_title": f"تعديل الخصم: {obj.name}",
        "nav_active": "promotions",
    }
    return render(request, "dashboard/pages/pricing/promotion_form.html", context)


def promotion_delete_view(request, promotion_id: int):
    obj = get_object_or_404(Promotion, pk=promotion_id)
    if request.method == "POST":
        form = PromotionDeleteForm(request.POST)
        if form.is_valid() and form.cleaned_data.get("confirm"):
            obj.delete()
            messages.success(request, "تم حذف الخصم بنجاح")
            return redirect(reverse("dashboard-promotions"))
    else:
        form = PromotionDeleteForm()
    
    context = {
        "form": form, 
        "object": obj,
        "page_title": f"حذف الخصم: {obj.name}",
        "nav_active": "promotions",
    }
    return render(request, "dashboard/pages/pricing/promotion_delete.html", context)


# ============ Coupons ============
def coupons_list_view(request):
    qs = Coupon.objects.all()
    context = {
        "page_title": "الكوبونات",
        "object_list": qs,
        "nav_active": "coupons",
        "create_url": "/dashboard/pricing/coupons/create/",
        "create_text": "إضافة كوبون جديد",
    }
    return render(request, "dashboard/pages/pricing/coupon_list.html", context)


def coupon_create_view(request):
    if request.method == "POST":
        form = CouponForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "تم إنشاء الكوبون بنجاح")
            return redirect(reverse("dashboard-coupons"))
    else:
        form = CouponForm()
    
    context = {
        "form": form, 
        "mode": "create",
        "page_title": "إنشاء كوبون جديد",
        "nav_active": "coupons",
    }
    return render(request, "dashboard/pages/pricing/coupon_form.html", context)


def coupon_edit_view(request, coupon_id: int):
    obj = get_object_or_404(Coupon, pk=coupon_id)
    if request.method == "POST":
        form = CouponForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "تم تعديل الكوبون بنجاح")
            return redirect(reverse("dashboard-coupons"))
    else:
        form = CouponForm(instance=obj)
    
    context = {
        "form": form, 
        "mode": "edit", 
        "object": obj,
        "page_title": f"تعديل الكوبون: {obj.code}",
        "nav_active": "coupons",
    }
    return render(request, "dashboard/pages/pricing/coupon_form.html", context)


def coupon_delete_view(request, coupon_id: int):
    obj = get_object_or_404(Coupon, pk=coupon_id)
    if request.method == "POST":
        form = CouponDeleteForm(request.POST)
        if form.is_valid() and form.cleaned_data.get("confirm"):
            obj.delete()
            messages.success(request, "تم حذف الكوبون بنجاح")
            return redirect(reverse("dashboard-coupons"))
    else:
        form = CouponDeleteForm()
    
    context = {
        "form": form, 
        "object": obj,
        "page_title": f"حذف الكوبون: {obj.code}",
        "nav_active": "coupons",
    }
    return render(request, "dashboard/pages/pricing/coupon_delete.html", context)


# ============ Offers ============
def offers_list_view(request):
    qs = Offer.objects.all().select_related('required_coupon')
    context = {
        "page_title": "العروض الخاصة",
        "object_list": qs,
        "nav_active": "offers",
        "create_url": "/dashboard/pricing/offers/create/",
        "create_text": "إضافة عرض جديد",
    }
    return render(request, "dashboard/pages/pricing/offer_list.html", context)


def offer_create_view(request):
    if request.method == "POST":
        form = OfferForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "تم إنشاء العرض بنجاح")
            return redirect(reverse("dashboard-offers"))
    else:
        form = OfferForm()
    
    context = {
        "form": form, 
        "mode": "create",
        "page_title": "إنشاء عرض جديد",
        "nav_active": "offers",
    }
    return render(request, "dashboard/pages/pricing/offer_form.html", context)


def offer_edit_view(request, offer_id: int):
    obj = get_object_or_404(Offer, pk=offer_id)
    if request.method == "POST":
        form = OfferForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "تم تعديل العرض بنجاح")
            return redirect(reverse("dashboard-offers"))
    else:
        form = OfferForm(instance=obj)
    
    context = {
        "form": form, 
        "mode": "edit", 
        "object": obj,
        "page_title": f"تعديل العرض: {obj.name}",
        "nav_active": "offers",
    }
    return render(request, "dashboard/pages/pricing/offer_form.html", context)


def offer_delete_view(request, offer_id: int):
    obj = get_object_or_404(Offer, pk=offer_id)
    if request.method == "POST":
        form = OfferDeleteForm(request.POST)
        if form.is_valid() and form.cleaned_data.get("confirm"):
            obj.delete()
            messages.success(request, "تم حذف العرض بنجاح")
            return redirect(reverse("dashboard-offers"))
    else:
        form = OfferDeleteForm()
    
    context = {
        "form": form, 
        "object": obj,
        "page_title": f"حذف العرض: {obj.name}",
        "nav_active": "offers",
    }
    return render(request, "dashboard/pages/pricing/offer_delete.html", context)
